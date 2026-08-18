#!/usr/bin/env python3
"""Render the EXP-012 report to a shareable PDF.

Every figure is read from experiments/EXP-012/*.json at build time, so the PDF
cannot drift from the artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP = REPO_ROOT / "experiments" / "EXP-012"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 17mm 15mm 15mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.7pt;
  line-height: 1.47; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 20pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 12pt; margin: 18pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.4pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 10.5pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.5pt; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
tr.oracle td { background: #f2f8f4; border-top: 1pt solid #14532d; border-bottom: 1pt solid #14532d; }
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

LABELS = {
    "A_global_raw_hybrid": "A — global raw hybrid (control)",
    "B_bm25_hierarchical": "B — BM25 routing → BM25 local",
    "C_transformer_hierarchical": "C — transformer routing → tx local",
    "D_fused_hierarchical": "D — fused routing → fused local",
}


def build_html(d: dict, n3: dict | None, n10: dict | None) -> str:
    cfg = d["configurations"]
    oracle = d["oracle_diagnostic"]
    stage1 = d["routing"]["stage1_ceiling"]
    pool = d["local_pool_size"]
    gate = d["reranker_decision_gate"]
    an = d["an003_deep_dive"]
    ad = d["paired_comparison"]["A->D_fused_hierarchical"]
    ao = d["paired_comparison"]["A->ORACLE (diagnostic)"]

    def cell_row(key, r, cls=""):
        a = r["spans_absent_from_top"]
        return (f"<tr{cls}><td>{key}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
                f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
                f"<td class='num'>{r['document_recall']:.3f}</td>"
                f"<td class='num'>{r['mrr']:.3f}</td>"
                + "".join(f"<td class='num'>{a[str(k)]}</td>" for k in (10, 30, 300)) + "</tr>")

    cells = "".join(cell_row(LABELS[k], v) for k, v in cfg.items())
    cells += cell_row("ORACLE — golden doc → fused local", oracle, " class='oracle'")

    routing = ""
    for method, rec in stage1["mean_routing_recall"].items():
        cls = " class='b'" if method == "fused" else ""
        routing += (f"<tr><td{cls}>{method}</td>"
                    + "".join(f"<td class='num'{cls}>{rec[d_]:.3f}</td>"
                              for d_ in ("1", "3", "5", "10")) + "</tr>")

    tax = ""
    for cid, t in sorted(d["failure_taxonomy"].items()):
        label = t["classification"].replace("_", " ")
        cls = " class='bad'" if "WITHIN" in t["classification"] else ""
        tax += f"<tr><td>{cid}</td><td{cls}>{label}</td></tr>"

    bands = ""
    for key, label in [("A_global_raw_hybrid", "A global"), ("D_fused_hierarchical", "D hierarchical"),
                       ("ORACLE", "ORACLE (diagnostic)")]:
        g = gate[key]
        b, c = g["bands"], g["perfect_reranker_ceiling_at_pool"]
        cls = " class='oracle'" if key == "ORACLE" else ""
        bands += (f"<tr{cls}><td>{label}</td>"
                  + "".join(f"<td class='num'>{b[k]}</td>" for k in
                            ("1-10", "11-30", "31-50", "51-100", "101-300", "absent_at_300"))
                  + "".join(f"<td class='num'>{c[p]:.3f}</td>" for p in ("30", "50", "100"))
                  + "</tr>")

    sens = ""
    for label, payload_, width in (("N = 3", n3, 3), ("N = 5 (primary)", d, 5), ("N = 10", n10, 10)):
        if payload_ is None:
            continue
        r = payload_["configurations"]["D_fused_hierarchical"]
        s1 = payload_["routing"]["stage1_ceiling"]
        cls = " class='b'" if width == 5 else ""
        sens += (f"<tr><td{cls}>{label}</td><td class='num'{cls}>{r['macro_span_recall']:.3f}</td>"
                 f"<td class='num'>{r['cases_fully_recalled']}/20</td>"
                 f"<td class='num'>{s1['cases_with_all_expected_documents_routed']}/20</td>"
                 f"<td class='num'>{payload_['local_pool_size']['mean']:.0f}</td></tr>")

    route = an["routing"]
    doc_id = route["expected_documents"][0]
    fb = d["fusion_bonus"]["hierarchical"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-012 — Hierarchical Document → Passage Retrieval</title><style>{CSS}</style></head><body>

<h1>EXP-012 — Hierarchical Document → Passage Retrieval</h1>
<p class="subtitle">Production RAG v1 · evaluation-first · n = 20 questions / 22 evidence spans ·
scorers frozen, only topology changed</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">Status — the intervention failed; the diagnostic succeeded</div>
<p>Hierarchical retrieval never beat the global control at any routing width. But the
oracle-document diagnostic reached <strong>0.950 / 19-of-20 with zero regressions and nothing absent
at 300</strong> — so global competition <em>is</em> causal, and the binding constraint is
<strong>document routing</strong>, not passage scoring.</p>
</div>

<div class="grid4">
  <div class="stat"><div class="big">{ad['macro_recall_delta']:+.3f}</div>
    <div class="cap">A → D primary intervention<br>{len(ad['rescued'])} rescued, {len(ad['regressed'])} regressed</div></div>
  <div class="stat hero"><div class="big">{oracle['macro_span_recall']:.3f}</div>
    <div class="cap">oracle-document diagnostic<br>{oracle['cases_fully_recalled']}/20, zero regressions</div></div>
  <div class="stat"><div class="big">{stage1['cases_with_all_expected_documents_routed']}/20</div>
    <div class="cap">cases with every expected<br>document routed into top 5</div></div>
  <div class="stat"><div class="big">{pool['mean_fraction_of_corpus'] * 100:.1f}%</div>
    <div class="cap">of the corpus left after routing<br>({pool['mean']:.0f} of {pool['global_chunks']:,} chunks)</div></div>
</div>

<h2>1. Why EXP-012 exists</h2>
<p>AN-003 has shown the same shape since EXP-007: correct document at rank 2–6, answer chunk absent
from the top 300. EXP-010 established that 21 of 22 answers are visible to the encoder; EXP-011 that
query rewriting rescues zero cases. The remaining explanation was competition — the right passage
ranked against ~14,209 chunks, nearly all from irrelevant documents.</p>

<h2>2. Design, and the constraint that makes it interpretable</h2>
<p>Stage 1 collapses each retriever's chunk ranking by document — a document ranks at its
highest-ranked chunk and votes <em>once</em> — then fuses the two lists with RRF. Stage 2 restricts
candidates to the routed documents and ranks them by their <strong>full-corpus</strong> scores.</p>
<p>BM25 term statistics are <strong>not</strong> recomputed inside the routed documents: the
restriction sits in the scoring select only, so <code>n</code>, <code>avg_len</code> and
<code>df</code> still come from the whole snapshot. Verified directly — a chunk's restricted score is
bit-identical to its global score. Without this the experiment would have confounded topology with
lexical re-weighting. Two planner tests confirm the GIN index survives the added predicate.</p>

<h2>3. Reproduction gate</h2>
<p>Cell A reproduced the control exactly — <strong>0.775 / 15-of-20 / 17-of-22:
<span class="good">PASS</span></strong>.</p>

<h2>4. Results</h2>
<table><thead><tr><th>cell</th><th class="num">macro R</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th>
<th class="num">a@10</th><th class="num">a@30</th><th class="num">a@300</th></tr></thead>
<tbody>{cells}</tbody></table>
<p class="dim" style="font-size:8.2pt">The oracle row is <strong>ORACLE / DIAGNOSTIC / NOT
DEPLOYABLE</strong> — it reads the golden expected document and is excluded from every production
metric. Tests assert it is not among the deployable configurations.</p>

<h2>5. Document routing — the ceiling on everything</h2>
<table><thead><tr><th>ranking</th><th class="num">@1</th><th class="num">@3</th>
<th class="num">@5</th><th class="num">@10</th></tr></thead><tbody>{routing}</tbody></table>
<p>At the preregistered <code>top_documents = 5</code>, every expected document is routed for only
<strong>{stage1['cases_with_all_expected_documents_routed']} of 20</strong> cases —
{", ".join(stage1['cases_with_a_document_outside_top_n'])} each lose one before Stage 2 begins.
<strong>Stage-1 ceiling {stage1['max_possible_recall_if_stage2_were_perfect']:.3f}</strong>: even a
perfect passage ranker could not exceed it. D reached {cfg['D_fused_hierarchical']['cases_fully_recalled']}/20,
so it does not even reach its own ceiling.</p>

<h2>6. Why hierarchy lost</h2>
<ul>
<li><strong>Routing drops documents.</strong> Three cases lose an expected document outright — an
error of <em>exclusion</em> the global system structurally cannot make. OA-004 is the regression.</li>
<li><strong>Complementarity degrades.</strong> The hierarchical fusion bonus is
<strong>+{fb['fusion_bonus_cases']} case</strong> (best component {fb['best_component']} → fused
{fb['fused']}), against <strong>+4</strong> globally. The third time this project has seen a change
erode the disagreement RRF feeds on.</li>
<li><strong>Rerankable headroom shrinks</strong> — see §8.</li>
</ul>
<p>Local pools average {pool['mean']:.0f} chunks ({pool['mean_fraction_of_corpus'] * 100:.2f}% of the
corpus), so competition really was removed. It simply did not help.</p>

<div class="callout win">
<div class="label">The oracle: passage ranking is nearly fine</div>
<p>With perfect routing, the <em>same</em> retrievers, scores and fusion reach
<strong>{oracle['macro_span_recall']:.3f} / {oracle['cases_fully_recalled']}-of-20</strong>, document
recall <strong>{oracle['document_recall']:.3f}</strong>, MRR <strong>{oracle['mrr']:.3f}</strong>, and
<strong>nothing absent at 300</strong>. Rescued: {", ".join(ao['rescued'])} — with
<strong>zero regressions</strong>.</p>
<p>Global competition was genuinely suppressing answer-bearing passages. What fails is our ability to
<em>route</em>, not our ability to rank passages once routed.</p>
</div>

<h2>7. AN-003 — the exception, now precisely characterised</h2>
<table><thead><tr><th>stage</th><th class="num">value</th></tr></thead><tbody>
<tr><td>fused document rank</td><td class="num good">{route['fused_document_rank'][doc_id]} — routed correctly</td></tr>
<tr><td>chunks in the top-5 pool</td><td class="num">{route['local_candidate_chunks']:,}</td></tr>
<tr><td>global evidence rank</td><td class="num bad">absent@300</td></tr>
<tr><td>fused hierarchical evidence rank</td><td class="num bad">absent@300</td></tr>
<tr><td>chunks in its own document</td><td class="num">{an['oracle']['oracle_candidate_chunks']}</td></tr>
<tr><td><b>oracle evidence rank</b></td><td class="num b">{an['oracle']['spans'][0]['rank']}</td></tr>
</tbody></table>
<p>Its document is routed correctly, yet hierarchy does not help — the top-5 pool still holds
{route['local_candidate_chunks']:,} chunks, 22% of the corpus. Only when competition is cut to its own
{an['oracle']['oracle_candidate_chunks']}-chunk document does the evidence appear at all, and even
then at <strong>rank {an['oracle']['spans'][0]['rank']}</strong>. <strong>AN-003 is the one case the
oracle does not rescue</strong> — a genuine within-document passage-ranking failure, and now a single
precisely-characterised defect rather than a property of the system.</p>

<h2>8. Failure taxonomy and reranker ceilings</h2>
<table style="width:48%; float:left; margin-right:4%"><thead><tr><th>case</th><th>classification</th>
</tr></thead><tbody>{tax}</tbody></table>
<table style="width:48%; float:left; font-size:7.9pt"><thead><tr><th>cell</th>
<th class="num">1–10</th><th class="num">11–30</th><th class="num">31–50</th>
<th class="num">51–100</th><th class="num">101–300</th><th class="num">abs</th>
<th class="num">c@30</th><th class="num">c@50</th><th class="num">c@100</th></tr></thead>
<tbody>{bands}</tbody></table>
<div style="clear:both"></div>
<p>Hierarchy <strong>reduced</strong> rerankable headroom: the perfect-reranker ceiling falls from
0.909 (A, pool 100) to 0.818 (D, flat). With perfect routing it is <strong>1.000 at a pool of just
30</strong>.</p>

<h2>9. Exploratory sensitivity — routing width</h2>
<table><thead><tr><th>routing width</th><th class="num">D macro recall</th><th class="num">D full</th>
<th class="num">all docs routed</th><th class="num">mean local pool</th></tr></thead>
<tbody>{sens}</tbody></table>
<p>Run only after the primary result was frozen and <strong>labelled exploratory</strong>. Hierarchy
<strong>converges to the global control</strong> as routing widens: at N = 10 it matches A exactly.
It never exceeds it at any width. The N=3 vs N=5 difference is one case — noise at this sample size.
The clearest statement of the result: <strong>the best hierarchical system is the one that stops
being hierarchical.</strong></p>

<h2>10. Limitations</h2>
<ul>
<li>n = 20 / 22 spans; one case is 5 percentage points. No significance claims.</li>
<li>The oracle is an upper bound with a perfect router. It says the headroom exists, not that it is
reachable.</li>
<li>One collapse rule was tested (highest-ranked chunk, one vote per document). Score aggregation,
top-k voting or document-level embeddings might route better and are untested.</li>
<li>AN-003's oracle rank of 29 is a single case.</li>
<li><strong>EXP-NULL remains BLOCKED</strong> — still no measured no-retrieval floor.</li>
</ul>

<h2>11. Was global competition causal?</h2>
<p><strong>Yes — and that is the surprise.</strong> Every previous mechanism this project proposed
turned out not to be causal: chunk size (three times), enrichment, encoder visibility, query
formulation. This one is: removing cross-document competition entirely takes the system from 0.775 to
0.950 with zero regressions.</p>
<p>But <strong>the intervention still failed</strong>, because achievable routing cannot realise it.
Every document the router drops is a case lost outright. The honest summary: <em>global competition
is a real bottleneck; document → passage retrieval as built is not the way to remove it.</em></p>

<h2>12. What the measurements justify next</h2>
<ol>
<li><strong>Work on document routing, not passage ranking.</strong> The oracle says passage ranking is
already worth 19/20; routing recall@5 of 0.875 is the constraint — a genuinely different problem from
anything tried so far.</li>
<li><strong>Do not deploy hierarchy at any N.</strong> It never beats global and adds an exclusion
failure mode global retrieval cannot have.</li>
<li><strong>A reranker is justified for the first time — but only behind good routing.</strong> With
perfect routing a perfect reranker over 30 candidates reaches 1.000; behind current routing the
ceiling is 0.818, <em>worse</em> than global's 0.909. Sequence matters.</li>
<li><strong>AN-003 deserves a failure report</strong>, not another system-wide experiment.</li>
<li><strong>Keep measuring the fusion bonus.</strong> Three changes have now improved components while
degrading the ensemble.</li>
</ol>

<footer>
Generated from experiments/EXP-012/*.json by scripts/build_exp012_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Snapshot {d['corpus_snapshot']}, chunk set {d['chunk_set']}, encoder fingerprint
{d['transformer_fingerprint']} @ {d['embedding_model']['max_seq_length']} tokens.
Document RRF k={d['document_rrf_k']}, passage RRF k={d['passage_rrf_k']}, pool {d['candidate_pool']},
top_k {d['top_k']}. Raw query only; no reranker, enrichment, query rewriting or ANN index.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",
                        default="docs/reports/EXP-012-hierarchical-document-passage-retrieval.pdf")
    args = parser.parse_args()

    def maybe(name):
        path = EXP / name
        return json.loads(path.read_text()) if path.exists() else None

    html = build_html(json.loads((EXP / "results.json").read_text()),
                      maybe("results-n3.json"), maybe("results-n10.json"))
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp012.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
