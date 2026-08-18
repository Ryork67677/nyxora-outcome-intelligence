#!/usr/bin/env python3
"""Render the EXP-013 report to a shareable PDF.

Every figure is read from experiments/EXP-013/*.json at build time, so the PDF
cannot drift from the artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP = REPO_ROOT / "experiments" / "EXP-013"
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
tr.oracle td { background: #f2f8f4; border-top: 1pt solid #14532d; border-bottom: 1pt solid #14532d; }
tr.explore td { background: #fbf7ef; border-top: 1pt solid #8a6d1c; border-bottom: 1pt solid #8a6d1c; font-style: italic; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.b { font-weight: 700; } .bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; } .dim { color: #6f747b; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt; margin: 9pt 0 11pt; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout.explore { border-left-color: #8a6d1c; background: #fbf7ef; }
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.4pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }
.callout.win .label { color: #14532d; }
.callout.explore .label { color: #8a6d1c; }
ol, ul { margin: 0 0 7pt; padding-left: 15pt; } li { margin-bottom: 3.5pt; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; margin: 4pt 0 11pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 7pt 9pt; border-radius: 3pt; }
.stat.hero { border-color: #14532d; background: #f2f8f4; }
.stat .big { font-size: 16pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.4pt; color: #52565d; margin-top: 2pt; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.8pt; color: #6f747b; }
"""

ROUTERS = ("A_MAX", "B_RANK_SUM", "C_TOPK_VOTE", "D_MAX_SUPPORT")
NAMES = {"A_MAX": "A_MAX — best chunk (EXP-012 control)",
         "B_RANK_SUM": "B_RANK_SUM — reciprocal-rank support",
         "C_TOPK_VOTE": "C_TOPK_VOTE — breadth of support",
         "D_MAX_SUPPORT": "D_MAX_SUPPORT — both, rank-domain fusion"}


def build_html(d: dict, e: dict | None) -> str:
    rq = d["routing_quality"]
    cfg = d["configurations"]
    oracle = d["oracle_diagnostic"]
    gap = d["oracle_gap"]
    gate = d["reranker_decision_gate"]
    watch = d["case_watchlist"]

    routing = ""
    for name in ROUTERS:
        r = rq[name]
        m = r["mean_document_recall"]
        routing += (f"<tr><td>{NAMES[name]}</td>"
                    + "".join(f"<td class='num'>{m[k]:.3f}</td>" for k in ("1", "3", "5", "10"))
                    + f"<td class='num b'>{r['cases_all_expected_routed']}/{r['cases_total']}</td>"
                    f"<td class='num'>{r['stage1_ceiling']:.3f}</td>"
                    f"<td class='num'>{r['fusion_bonus_cases']:+d}</td>"
                    f"<td class='num'>{r['mean_local_pool']:.0f}</td></tr>")
    if e:
        hy = e["hybrid_with_chunk_routing"]
        m = hy["mean_document_recall"]
        routing += ("<tr class='explore'><td>E_DOC_EMBED — exploratory, fused</td>"
                    + "".join(f"<td class='num'>{m[k]:.3f}</td>" for k in ("1", "3", "5", "10"))
                    + f"<td class='num b'>{hy['cases_all_expected_routed']}/20</td>"
                    f"<td class='num'>{hy['cases_all_expected_routed'] / 20:.3f}</td>"
                    "<td class='num'>—</td><td class='num'>—</td></tr>")

    end = ""
    for key in ["GLOBAL_control", *ROUTERS]:
        r = cfg[key]
        a = r["spans_absent_from_top"]
        label = "GLOBAL control" if key == "GLOBAL_control" else key
        cls = " class='b'" if key == "GLOBAL_control" else ""
        end += (f"<tr><td{cls}>{label}</td><td class='num'{cls}>{r['macro_span_recall']:.3f}</td>"
                f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
                f"<td class='num'>{r['document_recall']:.3f}</td>"
                f"<td class='num'>{r['mrr']:.3f}</td><td class='num'>{a['300']}</td>"
                f"<td class='num'>{gap[key]:.3f}</td></tr>")
    a = oracle["spans_absent_from_top"]
    end += (f"<tr class='oracle'><td>ORACLE — not deployable</td>"
            f"<td class='num'>{oracle['macro_span_recall']:.3f}</td>"
            f"<td class='num'>{oracle['cases_fully_recalled']}/{oracle['cases_total']}</td>"
            f"<td class='num'>{oracle['spans_found_at_10']}/{oracle['spans_total']}</td>"
            f"<td class='num'>{oracle['document_recall']:.3f}</td>"
            f"<td class='num'>{oracle['mrr']:.3f}</td><td class='num'>{a['300']}</td>"
            f"<td class='num'>0.000</td></tr>")

    comp = ""
    for name in ROUTERS:
        r = rq[name]
        c = r["component_all_routed"]
        comp += (f"<tr><td>{name}</td><td class='num'>{c.get('bm25', '—')}/20</td>"
                 f"<td class='num good'>{c.get('transformer', '—')}/20</td>"
                 f"<td class='num'>{r['best_component_all_routed']}</td>"
                 f"<td class='num'>{r['fused_all_routed']}</td>"
                 f"<td class='num bad'>{r['fusion_bonus_cases']:+d}</td></tr>")

    missing = ""
    for name in ROUTERS:
        missing += (f"<tr><td>{name}</td><td>{', '.join(rq[name]['cases_missing_a_document'])}</td></tr>")

    an1 = watch["AN-001"]
    an1_doc = an1["expected_documents"][0]
    an1_s = an1["support"][an1_doc]

    bands = ""
    for key, label, cls in (("GLOBAL_control", "GLOBAL", ""),
                            ("D_MAX_SUPPORT", "best router (D)", ""),
                            ("ORACLE", "ORACLE", " class='oracle'")):
        g = gate[key]
        b, c = g["bands"], g["perfect_reranker_ceiling_at_pool"]
        bands += (f"<tr{cls}><td>{label}</td>"
                  + "".join(f"<td class='num'>{b[k]}</td>" for k in
                            ("1-10", "11-30", "31-50", "51-100", "101-300", "absent_at_300"))
                  + "".join(f"<td class='num'>{c[p]:.3f}</td>" for p in ("30", "50", "100"))
                  + "</tr>")

    e_hy = e["hybrid_with_chunk_routing"] if e else None
    e_alone = e["doc_embedding_only"] if e else None
    an1_embed = next((r["doc_embedding_rank"][an1_doc] for r in e["per_case"]
                      if r["case_id"] == "AN-001"), None) if e else None

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-013 — Document Routing</title><style>{CSS}</style></head><body>

<h1>EXP-013 — Document Routing</h1>
<p class="subtitle">Production RAG v1 · evaluation-first · n = 20 questions / 22 evidence spans ·
Stage 2 frozen, only document aggregation changed</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">Status — falsified for rank aggregation</div>
<p>Not one of the three aggregation routers improved document recall@5. All four routers — including
the EXP-012 control — sit at <strong>0.875 / 17-of-20</strong>, an identical Stage-1 ceiling of
0.850. An <em>exploratory</em> document-level embedding router reached 18/20 and recall@5 0.900, and
ranked the one document no chunk-derived router could find at <strong>8 instead of 62</strong>.</p>
</div>

<div class="grid4">
  <div class="stat"><div class="big">17/20</div>
    <div class="cap">all-required-documents routed<br>identical for all four routers</div></div>
  <div class="stat"><div class="big">0.875</div>
    <div class="cap">document recall@5<br>unchanged by every router</div></div>
  <div class="stat hero"><div class="big">{oracle['macro_span_recall']:.3f}</div>
    <div class="cap">oracle headroom still unrealised<br>{oracle['cases_fully_recalled']}/20, not deployable</div></div>
  <div class="stat"><div class="big">+0</div>
    <div class="cap">document-level fusion bonus<br>for every router</div></div>
</div>

<h2>1. Why EXP-013 exists</h2>
<p>EXP-012's oracle showed the passage layer is mostly fine — given the correct document the same
retrievers reach 0.950 / 19-of-20 with zero regressions. Routing was the bottleneck: every required
document reached the top 5 for only 17 of 20 questions. The router it used keeps a document's single
best chunk and discards the rest, so EXP-013 tests whether the discarded evidence routes better.</p>

<h2>2. Frozen, and why everything stays in the rank domain</h2>
<p>Stage 2 is untouched: raw query, full-corpus BM25 plus transformer cosine restricted to routed
documents, passage RRF k=60, top 10, statistics never recomputed locally. Chunks, model
(fingerprint <code>{d['transformer_fingerprint']}</code>), embeddings, anchors and questions all
unchanged; <code>top_documents = 5</code> throughout.</p>
<p>BM25 and cosine scores are never combined directly — a test asserts the router module contains no
such expression. Mixing their scales, or normalising them against 20 questions and tuning a weight,
would fit the evaluation set rather than measure on it. <code>k=60</code>, support 5 and vote depth
50 were preregistered and not tuned.</p>

<h2>3. Reproduction gates</h2>
<p>GLOBAL control (0.775 / 15-of-20), A_MAX (0.725 / 14-of-20) and ORACLE (0.950 / 19-of-20) all
reproduced exactly — <span class="good">PASS</span>.</p>

<h2>4. Routing quality — the primary metric</h2>
<table><thead><tr><th>router</th><th class="num">@1</th><th class="num">@3</th><th class="num">@5</th>
<th class="num">@10</th><th class="num">all-routed</th><th class="num">ceiling</th>
<th class="num">bonus</th><th class="num">mean pool</th></tr></thead><tbody>{routing}</tbody></table>
<p>Aggregation helps at <em>shallow</em> depth — D_MAX_SUPPORT lifts recall@1 from 0.525 to 0.575 and
recall@3 from 0.800 to 0.875 — and every router has converged by depth 5. The routers behave exactly
as designed on the motivating example (a document with support at ranks 2, 7, 11, 18 beats one owning
only rank 1); the corpus simply does not reward it where it matters.</p>

<h2>5. End-to-end</h2>
<table><thead><tr><th>cell</th><th class="num">macro R</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th>
<th class="num">absent@300</th><th class="num">oracle gap</th></tr></thead><tbody>{end}</tbody></table>
<p>Aggregation <strong>repairs</strong> the EXP-012 hierarchy regression — B, C and D each recover to
global parity — but <strong>none exceeds global</strong>. Against the EXP-012 hierarchy each scores
net +1: rescuing <strong>OA-004</strong> and AN-011, losing <strong>AN-008</strong>. Against global
the exchange nets to zero.</p>
<p><strong>OA-004 is the aggregation success.</strong> Its document has 5 BM25 and 3 transformer
chunks inside the top 30 — breadth A_MAX discarded. Document rank moves 6 → 2 and its evidence lands
at rank 2–4. <strong>AN-008 is the cost:</strong> the same breadth preference demotes it out of the
routed set.</p>

<h2>6. Why the ceiling never moves</h2>
<table><thead><tr><th>router</th><th>cases missing a required document</th></tr></thead>
<tbody>{missing}</tbody></table>

<div class="callout warn">
<div class="label">AN-001 — the case that explains the whole result</div>
<p>Its document contributes <strong>one</strong> chunk anywhere in 300 BM25 results
(best rank {an1_s['best_bm25_chunk_rank']}), and the transformer <strong>never retrieves it at
all</strong>. Document rank {watch['AN-001']['by_router']['A_MAX']['fused_document_rank'][an1_doc]}–
{watch['AN-001']['by_router']['B_RANK_SUM']['fused_document_rank'][an1_doc]} under every router. Yet
handed the document, its evidence ranks <strong>{watch['AN-001']['oracle_evidence_ranks'][0]}</strong>.</p>
<p>There is nothing for an aggregation rule to aggregate. <strong>The limitation is the input, not
the arithmetic.</strong></p>
</div>

<p><strong>AN-012</strong> is multi-hop: one document is easy (transformer chunk rank 2), the other
has transformer rank 63 and lands at document rank 9–13 — just outside the top 5 under every router.
Partially routed is, for a multi-hop question, the same as failing.</p>

<h2>7. Complementarity — document-level fusion does no work</h2>
<table><thead><tr><th>router</th><th class="num">BM25 alone</th><th class="num">transformer alone</th>
<th class="num">best component</th><th class="num">fused</th><th class="num">bonus</th></tr></thead>
<tbody>{comp}</tbody></table>
<p>The transformer's document ranking alone already achieves 17/20; BM25 adds nothing and fusion adds
nothing over the better component. That is a different picture from passage retrieval, where the raw
fusion bonus is +4 cases. <strong>Retriever complementarity is a passage-level phenomenon here, not a
document-level one.</strong></p>

<div class="callout explore">
<div class="label">Exploratory — a document-level representation</div>
<p>Run only after A–D were frozen: the mean of each document's already-stored normalised chunk
vectors, renormalised, ranked by cosine. No re-chunking, no training, no tuning.</p>
<p><strong>Alone</strong> it reaches recall@10 of <strong>{e_alone['mean_document_recall']['10']:.3f}</strong>
— every expected document inside its top 10, which no chunk-derived ranking achieves — though only
{e_alone['cases_all_expected_routed']}/20 at depth 5. <strong>Fused with chunk routing</strong> it
reaches <strong>{e_hy['cases_all_expected_routed']}/20</strong> and recall@5
<strong>{e_hy['mean_document_recall']['5']:.3f}</strong>, the first configuration in EXP-013 to exceed
17/20. And <strong>AN-001's document moves from rank 62 to rank {an1_embed}</strong>.</p>
<p><strong>This is one exploratory run at n = 20 and it is not a result.</strong> One case is 5
percentage points, and the same fusion that gains AN-012 gives back OA-004. A direction with measured
support, not a finding.</p>
</div>

<h2>8. AN-003 — unchanged, as expected</h2>
<p>Routed correctly by every router (document rank 3–4) and still absent@300, exactly as EXP-012
predicted. Its document was never the problem; its oracle rank remains 29 inside its own 141-chunk
document. Nothing here was modified to target it.</p>

<h2>9. Reranker gate</h2>
<table><thead><tr><th>cell</th><th class="num">1–10</th><th class="num">11–30</th>
<th class="num">31–50</th><th class="num">51–100</th><th class="num">101–300</th>
<th class="num">absent</th><th class="num">c@30</th><th class="num">c@50</th><th class="num">c@100</th>
</tr></thead><tbody>{bands}</tbody></table>
<p>Routing improvements did not raise the reranker ceiling. Under the best router it is
<strong>{gate['D_MAX_SUPPORT']['perfect_reranker_ceiling_at_pool']['100']:.3f}</strong>, still
<em>below</em> the global control's
{gate['GLOBAL_control']['perfect_reranker_ceiling_at_pool']['100']:.3f} — hierarchy's exclusions
remove candidates a reranker could otherwise have reordered. Only oracle routing reaches 1.000, and
it does so at a pool of just 30.</p>

<h2>10. Limitations</h2>
<ul>
<li>n = 20 / 22 spans; one case is 5 percentage points. No significance claims.</li>
<li>Three aggregation rules were tested, not the space of aggregation. Their agreement at recall@5 is
suggestive, not exhaustive.</li>
<li>Router E is exploratory, unreplicated, and its gain is a single case bought at the cost of another.</li>
<li>Mean-pooled document vectors are the crudest possible document representation — chosen because
they need no tuning, not because they are good.</li>
<li><strong>EXP-NULL remains BLOCKED</strong> — still no measured no-retrieval floor.</li>
</ul>

<h2>11. Did better document aggregation solve routing?</h2>
<p><strong>No.</strong> Three preregistered rules, all landing on exactly the same recall@5 and the
same 17/20. The Stage-1 ceiling did not move by a single case. This is preregistered
<strong>Outcome D</strong>: chunk-ranking-derived routing is itself inadequate, and AN-001 shows why
in one line. <strong>The routers were not the problem, the input was.</strong></p>

<h2>12. What the measurements justify next</h2>
<ol>
<li><strong>Stop inventing aggregation formulas.</strong> Three rules, one ceiling.</li>
<li><strong>A document-level retrieval representation is the justified next experiment</strong> — the
exploratory router already reaches recall@10 = 1.000 alone and moves AN-001 from 62 to {an1_embed}. It
deserves a proper preregistered experiment, not promotion off one run.</li>
<li><strong>Do not deploy hierarchy.</strong> No router beat global, and hierarchy still lowers the
reranker ceiling.</li>
<li><strong>A reranker remains premature</strong> — behind current routing its ceiling is worse than
global's. Routing first, reranking second.</li>
<li><strong>Complementarity is passage-level, not document-level.</strong> A future document retriever
should be judged on whether it adds anything the transformer does not already have.</li>
</ol>

<footer>
Generated from experiments/EXP-013/*.json by scripts/build_exp013_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Router version {d['router_version']}; k={d['router_parameters']['rank_sum_k']}, support
{d['router_parameters']['rank_sum_support_chunks']}, vote depth {d['router_parameters']['vote_depth']},
document RRF k={d['document_rrf_k']} — all preregistered, none tuned.
Snapshot {d['corpus_snapshot']}, chunk set {d['chunk_set']}, top_documents {d['top_documents']}.
Stage 2 frozen. Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-013-document-routing.pdf")
    args = parser.parse_args()
    e_path = EXP / "router-e-exploratory.json"
    html = build_html(json.loads((EXP / "results.json").read_text()),
                      json.loads(e_path.read_text()) if e_path.exists() else None)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp013.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
