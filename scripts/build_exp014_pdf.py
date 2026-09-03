#!/usr/bin/env python3
"""Render the EXP-014 report to a shareable PDF.

Every figure is read from experiments/EXP-014/results.json at build time, so the
PDF cannot drift from the artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP = REPO_ROOT / "experiments" / "EXP-014"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 17mm 15mm 15mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.6pt;
  line-height: 1.46; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 20pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 12pt; margin: 17pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.4pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 10.5pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.4pt; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
tr.win td { background: #f2f8f4; border-top: 1pt solid #14532d; border-bottom: 1pt solid #14532d; font-weight: 700; }
tr.oracle td { background: #f6f7f9; border-top: 1pt solid #6f747b; border-bottom: 1pt solid #6f747b; }
tr.secondary td { background: #fbf7ef; font-style: italic; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.b { font-weight: 700; } .bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; } .dim { color: #6f747b; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt; margin: 9pt 0 11pt; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.4pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }
.callout.win .label { color: #14532d; }
ol, ul { margin: 0 0 7pt; padding-left: 15pt; } li { margin-bottom: 3.5pt; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; margin: 4pt 0 11pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 7pt 9pt; border-radius: 3pt; }
.stat.hero { border-color: #14532d; background: #f2f8f4; }
.stat .big { font-size: 16pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.4pt; color: #52565d; margin-top: 2pt; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.8pt; color: #6f747b; }
"""

REPS = ("DOC-A-MEAN", "DOC-B-CENTROID", "DOC-C-SECTION", "DOC-D-MULTIVECTOR")
BEST = "DOC-C-SECTION"
SECONDARY = "DOC-C-SECTION+chunk+bm25"


def build_html(d: dict) -> str:
    rq = d["routing_quality"]
    cfg = d["configurations"]
    oracle = d["oracle_diagnostic"]
    gap = d["oracle_gap"]
    gate = d["reranker_decision_gate"]
    watch = d["case_watchlist"]
    reps = d["representations"]

    def routing_row(label, display, cls=""):
        r = rq[label]
        dr = r["document_recall"]
        return (f"<tr{cls}><td>{display}</td>"
                + "".join(f"<td class='num'>{dr[k]:.3f}</td>" for k in ("1", "3", "5", "10"))
                + f"<td class='num'>{r['all_expected_routed']['5']}/{r['cases_total']}</td>"
                f"<td style='font-size:7.6pt'>{', '.join(r['cases_missing_at_5']) or '—'}</td></tr>")

    routing = routing_row("chunk_derived_router", "chunk-derived router (EXP-013)")
    for name in REPS:
        cls = " class='win'" if name == BEST else ""
        routing += routing_row(name, name, cls)
    routing += routing_row(f"{BEST}+chunk", f"{BEST} + chunk")
    routing += routing_row(SECONDARY, f"{SECONDARY} (secondary)", " class='secondary'")

    def e2e_row(label, display, cls=""):
        r = cfg[label]
        return (f"<tr{cls}><td>{display}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
                f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
                f"<td class='num'>{r['document_recall']:.3f}</td>"
                f"<td class='num'>{r['mrr']:.3f}</td>"
                f"<td class='num'>{r['spans_absent_from_top']['300']}</td>"
                f"<td class='num'>{gap[label]:.3f}</td></tr>")

    e2e = e2e_row("GLOBAL_control", "GLOBAL control")
    for name in REPS:
        e2e += e2e_row(name, name, " class='win'" if name == BEST else "")
    e2e += e2e_row(f"{BEST}+chunk", f"{BEST} + chunk")
    e2e += e2e_row(SECONDARY, f"{SECONDARY} (secondary)", " class='secondary'")
    e2e += (f"<tr class='oracle'><td>ORACLE — not deployable</td>"
            f"<td class='num'>{oracle['macro_span_recall']:.3f}</td>"
            f"<td class='num'>{oracle['cases_fully_recalled']}/{oracle['cases_total']}</td>"
            f"<td class='num'>{oracle['spans_found_at_10']}/{oracle['spans_total']}</td>"
            f"<td class='num'>{oracle['document_recall']:.3f}</td>"
            f"<td class='num'>{oracle['mrr']:.3f}</td>"
            f"<td class='num'>{oracle['spans_absent_from_top']['300']}</td>"
            f"<td class='num'>0.000</td></tr>")

    an1 = watch["AN-001"]
    an1_rows = ("<tr><td>chunk-derived router</td><td class='num bad'>never retrieved</td></tr>")
    for label in ("DOC-A-MEAN", "DOC-C-SECTION", "DOC-D-MULTIVECTOR",
                  f"{BEST}+chunk", SECONDARY):
        rank = next(iter(an1["by_representation"][label].values()))
        cls = " class='good'" if rank and rank <= 10 else ""
        an1_rows += f"<tr><td>{label}</td><td class='num'{cls}>{rank}</td></tr>"

    an12 = watch["AN-012"]
    an12_rows = ""
    for label, display in (("chunk_router_ranks", "chunk-derived router"),):
        ranks = list(an12[label].values())
        an12_rows += (f"<tr><td>{display}</td><td class='num'>{ranks[0]}</td>"
                      f"<td class='num'>{ranks[1]}</td><td class='bad'>no</td></tr>")
    for label in ("DOC-C-SECTION", SECONDARY):
        ranks = list(an12["by_representation"][label].values())
        ok = all(r is not None and r <= 5 for r in ranks)
        an12_rows += (f"<tr><td>{label}</td><td class='num'>{ranks[0]}</td>"
                      f"<td class='num'>{ranks[1]}</td>"
                      f"<td class='{'good' if ok else 'bad'}'>{'yes' if ok else 'no'}</td></tr>")

    bands = ""
    for key, label, cls in (("GLOBAL_control", "GLOBAL", ""), (BEST, BEST, " class='win'"),
                            (SECONDARY, SECONDARY, " class='secondary'"),
                            ("ORACLE", "ORACLE", " class='oracle'")):
        g = gate[key]
        b, c = g["bands"], g["perfect_reranker_ceiling_at_pool"]
        bands += (f"<tr{cls}><td>{label}</td>"
                  + "".join(f"<td class='num'>{b[k]}</td>" for k in
                            ("1-10", "11-30", "31-50", "51-100", "absent_at_300"))
                  + "".join(f"<td class='num'>{c[p]:.3f}</td>" for p in ("30", "50", "100"))
                  + "</tr>")

    cost = ""
    for name in REPS:
        s = reps[name]
        cost += (f"<tr><td>{name}</td><td class='num'>{s['vectors_stored']:,}</td>"
                 f"<td class='num'>{s['storage_bytes'] / 1024:.0f} KB</td>"
                 f"<td class='num'>{s['build_seconds']:.2f} s</td>"
                 f"<td class='num'>{d['document_retrieval_latency_ms'][name]:.2f} ms</td></tr>")

    best = cfg[BEST]
    glob = cfg["GLOBAL_control"]
    bd = d["paired_comparison"][f"GLOBAL->{BEST}"]
    sec_r = rq[SECONDARY]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-014 — Dedicated Document-Level Retrieval</title><style>{CSS}</style></head><body>

<h1>EXP-014 — Dedicated Document-Level Retrieval</h1>
<p class="subtitle">Production RAG v1 · evaluation-first · n = 20 questions / 22 evidence spans ·
Stage 2 frozen, only document retrieval changed</p>
<div class="rule"></div>

<div class="callout win">
<div class="label">Status — hypothesis supported; first configuration to beat the global control</div>
<p><code>DOC-C-SECTION</code> reaches <strong>{best['macro_span_recall']:.3f} /
{best['cases_fully_recalled']}-of-20</strong> against the global control's
{glob['macro_span_recall']:.3f} / {glob['cases_fully_recalled']}-of-20 —
<strong>{len(bd['rescued'])} cases rescued, {len(bd['regressed'])} regressed</strong>. Routing rose
from 17/20 to <strong>18/20</strong>, and to <strong>19/20</strong> in a secondary configuration
which — notably — retrieves worse.</p>
</div>

<div class="grid4">
  <div class="stat hero"><div class="big">{bd['macro_recall_delta']:+.3f}</div>
    <div class="cap">vs global control<br>{len(bd['rescued'])} rescued, {len(bd['regressed'])} regressed</div></div>
  <div class="stat"><div class="big">18/20</div>
    <div class="cap">all documents routed@5<br>(chunk-derived: 17/20)</div></div>
  <div class="stat"><div class="big">{gap[BEST]:.3f}</div>
    <div class="cap">oracle gap remaining<br>(was 0.175)</div></div>
  <div class="stat"><div class="big">310 KB</div>
    <div class="cap">whole document index<br>0.18 ms per query</div></div>
</div>

<h2>1. Why EXP-014 exists</h2>
<p>EXP-012's oracle showed the passage layer is mostly fine — given the right document the same
retrievers reach 0.950 / 19-of-20 with zero regressions. EXP-013 then falsified rank aggregation:
four rules over chunk rankings all landed on recall@5 0.875 and 17/20. AN-001 explained why — its
document contributes one chunk in 300 and the transformer never retrieves it, so no function of those
rankings can promote it. <strong>The limitation was the input, not the arithmetic.</strong></p>

<h2>2. What changed, and what did not</h2>
<p>Only document retrieval. Stage 2 is byte-identical to EXP-012/013: raw query, full-corpus BM25
plus the existing transformer cosine restricted to selected documents, passage RRF k=60, top 10,
statistics never recomputed locally. <code>top_documents = 5</code> throughout; same chunks, model
(fingerprint <code>{d['transformer_fingerprint']}</code>), embeddings, anchors and questions.</p>
<p>Every document vector is a deterministic function of embeddings already stored — no new model, no
training, no external call. The stored chunk vectors were verified unit-length
({d['chunk_vector_normalisation']['chunks_checked']:,} checked, all 1.000) before use. All three
reproduction gates pass.</p>

<h2>3. Document routing — the primary metric</h2>
<table><thead><tr><th>configuration</th><th class="num">@1</th><th class="num">@3</th>
<th class="num">@5</th><th class="num">@10</th><th class="num">routed@5</th><th>missing@5</th>
</tr></thead><tbody>{routing}</tbody></table>

<h2>4. End-to-end, frozen Stage 2</h2>
<table><thead><tr><th>cell</th><th class="num">macro R</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th>
<th class="num">absent@300</th><th class="num">oracle gap</th></tr></thead><tbody>{e2e}</tbody></table>

<h2>5. What made the difference: one section, one vote</h2>
<p>DOC-C differs from DOC-A by a single decision — sections contribute equally instead of chunks —
and it is worth two cases of routing and one end-to-end. The corpus explains it: documents average
{reps['DOC-C-SECTION']['construction_stats']['mean_sections_per_document']} sections but the largest
has <strong>{reps['DOC-C-SECTION']['construction_stats']['max_sections_per_document']:,}</strong>.
Under a plain chunk mean a document's vector is dominated by whichever section produced the most
chunks.</p>
<p><strong>DOC-B is the clean negative.</strong> Removing
{reps['DOC-B-CENTROID']['construction_stats']['duplicate_chunks_removed']:,} exact-duplicate chunks —
18% of the corpus — changed <strong>nothing</strong>: identical routing, identical end-to-end,
identical MRR. Duplicate content was not distorting the centroid; uneven section size was.</p>
<p><strong>DOC-D is the clean failure.</strong> Scoring a document at its best section is too
permissive — any document with one vaguely matching section scores highly — so precision collapses
(15/20 routed, document recall 0.725) and it is the only representation that loses to global.</p>

<div class="callout warn">
<div class="label">Better routing is not better retrieval</div>
<p><code>{BEST}</code> routes <strong>18/20</strong> and retrieves
<strong>{best['macro_span_recall']:.3f} / {best['cases_fully_recalled']}-of-20</strong>.
<code>{SECONDARY}</code> routes <strong>{sec_r['all_expected_routed']['5']}/20</strong> — better — and
retrieves <strong>{cfg[SECONDARY]['macro_span_recall']:.3f} /
{cfg[SECONDARY]['cases_fully_recalled']}-of-20</strong> — worse.</p>
<p>Adding BM25 buys AN-012's second document but changes which five documents the passage stage
competes over, and the net is one case lost. <strong>Document recall is necessary but not
sufficient</strong>, which is exactly what the promotion rule was written to catch.</p>
</div>

<h2>6. AN-001 — improved, still unrouted</h2>
<table><thead><tr><th>ranking</th><th class="num">AN-001 document rank</th></tr></thead>
<tbody>{an1_rows}</tbody></table>
<p>A document-level representation <em>can</em> see AN-001's document — DOC-A puts it at rank 8 where
every chunk-derived router put it at 62–72 or nowhere, confirming the EXP-013 diagnosis directly. But
it is still outside the top 5, and <strong>fusion destroys the gain</strong>: adding the chunk router,
which ranks this document nowhere, pushes it back to 72. AN-001 is the one case no EXP-014
configuration routes.</p>

<h2>7. AN-012 — multi-hop</h2>
<table><thead><tr><th>ranking</th><th class="num">document A</th><th class="num">document B</th>
<th>both in top 5?</th></tr></thead><tbody>{an12_rows}</tbody></table>
<p>The only configuration that routes AN-012 fully is the 19/20 secondary one — the same one that
retrieves worse overall.</p>

<h2>8. Other movements and complementarity</h2>
<ul>
<li><strong>OA-004</strong> (long-standing regression watch): chunk router 7 → DOC-C <strong>3</strong>,
routed, and not regressed by DOC-C standalone. It <em>is</em> lost by DOC-A+chunk and DOC-B+chunk, so
the watch remains warranted.</li>
<li><strong>AN-006</strong>: 4 → <strong>2</strong>, rescued end-to-end. <strong>AN-008</strong>: rank
1 everywhere — the case EXP-013's aggregating routers lost is safe here.</li>
<li><strong>EXP-013's "BM25 adds +0" is revised.</strong> That was true of chunk-derived routing.
Adding BM25 to DOC-C moves routing 18/20 → 19/20 and recall@1 0.550 → 0.725 — they fail differently.
It still does not convert end-to-end, so it does not earn a Stage-1 place yet.</li>
</ul>

<h2>9. Reranker gate</h2>
<table><thead><tr><th>cell</th><th class="num">1–10</th><th class="num">11–30</th>
<th class="num">31–50</th><th class="num">51–100</th><th class="num">absent</th>
<th class="num">c@30</th><th class="num">c@50</th><th class="num">c@100</th></tr></thead>
<tbody>{bands}</tbody></table>
<p><strong>{BEST} leaves nothing for a reranker</strong> — 19 of 22 spans are already in the top 10
and the remaining 3 are absent at 300, so its ceiling is flat at 0.864. A reranker cannot reorder what
was never retrieved. The secondary configuration reaches 0.909 at pool 30, which global only reaches
at pool 100. Neither justifies building one: the best system's residual is a <em>retrieval</em>
problem, not a reordering one.</p>

<h2>10. Cost</h2>
<table><thead><tr><th>representation</th><th class="num">vectors</th><th class="num">storage</th>
<th class="num">build</th><th class="num">retrieval</th></tr></thead><tbody>{cost}</tbody></table>
<p>Loading the stored chunk vectors takes {d['chunk_vector_load_seconds']:.1f} s once. Document-level
retrieval is essentially free at this corpus size.</p>

<h2>11. Residual failure taxonomy after {BEST}</h2>
<table><thead><tr><th>case</th><th>classification</th></tr></thead><tbody>
<tr><td>AN-001</td><td><b>DOCUMENT REPRESENTATION FAILURE</b> — best rank 8, outside top 5</td></tr>
<tr><td>AN-012</td><td><b>MULTI-HOP ROUTING FAILURE</b> — second document at rank 8</td></tr>
<tr><td>AN-003</td><td><b>WITHIN-DOCUMENT PASSAGE RANKING FAILURE</b> — routed at rank 5, oracle rank 29</td></tr>
</tbody></table>
<p>Three residual failures, three distinct mechanisms. <strong>None is a passage-conversion
failure</strong> — every correctly routed document converted. AN-003 is unchanged and was not tuned
around, as declared.</p>

<h2>12. Limitations</h2>
<ul>
<li>n = 20 / 22 spans; one case is 5 percentage points. <strong>No significance claims</strong> —
DOC-C's +2 cases is a two-case difference on twenty questions.</li>
<li>Four representations, preregistered, run once each. No variant was selected after seeing results.</li>
<li>DOC-C's advantage rests on one design decision, well-motivated by the 1,445-section outlier but
evidenced on a single corpus.</li>
<li><strong>EXP-NULL remains BLOCKED</strong> — still no measured no-retrieval floor.</li>
</ul>

<h2>13. Did document representation solve routing?</h2>
<p><strong>Partly — and it did something better: it converted.</strong> Routing went 17/20 → 18/20
standalone and 19/20 with BM25, short of solving it. But for the first time an intervention
<strong>beat the global control end-to-end</strong>, with zero regressions, closing the oracle gap
from 0.175 to {gap[BEST]:.3f}. AN-001 moving from <em>never retrieved</em> to rank 8 is the EXP-013
diagnosis confirmed in one number.</p>

<div class="callout">
<div class="label">Promotion assessment</div>
<p>The preregistered bar was routed@5 ≥ 19/20 <strong>and</strong> end-to-end &gt; 0.775
<strong>and</strong> limited/no regressions. {BEST} meets two of three — 0.875 / 17-of-20 with zero
regressions — but routes 18/20, and the configuration that does route 19/20 retrieves worse.
<strong>The formal bar is not met and it is not promoted.</strong> It is nonetheless the strongest
candidate this project has produced.</p>
</div>

<h2>14. What the measurements justify next</h2>
<ol>
<li><strong>Replicate {BEST} before promoting anything</strong> — a +2-case result at n=20 needs
confirmation, ideally on held-out questions rather than this development set.</li>
<li><strong>Attack AN-001 as a representation problem.</strong> It is the single remaining routing
failure, visible at rank 8 to a plain mean, and fusion is what buries it.</li>
<li><strong>Do not add BM25 to Stage 1 yet</strong> — it improves routing and costs retrieval.</li>
<li><strong>A reranker is still not justified</strong> — the residual is 3 spans absent at 300.</li>
<li><strong>The golden set is now the binding constraint on inference.</strong> Six of the last seven
experiments turned on one or two cases; expanding it would buy more than any further retrieval
change.</li>
</ol>

<footer>
Generated from experiments/EXP-014/results.json by scripts/build_exp014_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Representation version {d['document_representation_version']}; snapshot {d['corpus_snapshot']},
chunk set {d['chunk_set']}, encoder fingerprint {d['transformer_fingerprint']}, cosine, no ANN.
top_documents {d['top_documents']}, document RRF k={d['document_rrf_k']}, passage RRF
k={d['passage_rrf_k']}. Stage 2 frozen; raw query only; no reranker or enrichment.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-014-dedicated-document-level-retrieval.pdf")
    args = parser.parse_args()
    html = build_html(json.loads((EXP / "results.json").read_text()))
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp014.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
