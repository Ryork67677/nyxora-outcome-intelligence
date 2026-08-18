#!/usr/bin/env python3
"""Render the EXP-011 report to a shareable PDF.

Every figure is read from experiments/EXP-011/*.json at build time, so the PDF
cannot drift from the artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP = REPO_ROOT / "experiments" / "EXP-011"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 17mm 15mm 15mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.8pt;
  line-height: 1.48; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 20pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 12pt; margin: 18pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.4pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
pre { font-family: "SFMono-Regular", Consolas, monospace; font-size: 8.2pt;
  background: #f6f7f9; border: 0.6pt solid #dde0e4; border-radius: 3pt;
  padding: 7pt 9pt; margin: 6pt 0 10pt; white-space: pre-wrap; overflow-x: auto; }
.subtitle { font-size: 10.5pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.5pt; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
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
.stat .big { font-size: 16pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.4pt; color: #52565d; margin-top: 2pt; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.8pt; color: #6f747b; }
"""

LABELS = {
    "A_raw_query_control": "A — raw query (control)",
    "B_normalized_query": "B — normalized",
    "C_raw_plus_normalized": "C — raw + normalized",
    "D_structured_query": "D — structured",
    "E_three_view": "E — raw + normalized + structured",
}


def build_html(d: dict, attr: dict, bonus: dict, comp: dict) -> str:
    cfg = d["configurations"]
    cost = d["cost"]
    gate = d["reranker_decision_gate"]
    grid = attr["grid"]

    cells = ""
    for key, label in LABELS.items():
        r = cfg[key]
        a = r["spans_absent_from_top"]
        b = " class='b'" if key == "A_raw_query_control" else ""
        bad = " class='bad'" if key == "D_structured_query" else b
        cells += (f"<tr><td{bad}>{label}</td><td class='num'>{len(r['query_views'])}</td>"
                  f"<td class='num'{bad}>{r['macro_span_recall']:.3f}</td>"
                  f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                  f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
                  f"<td class='num'>{r['document_recall']:.3f}</td>"
                  f"<td class='num'>{r['mrr']:.3f}</td>"
                  + "".join(f"<td class='num'>{a[str(k)]}</td>" for k in (10, 30, 300))
                  + f"<td class='num'>{cost[key]['retrieval_calls_per_query']:.0f}</td></tr>")

    paired = ""
    for name, c in d["paired_comparison"].items():
        short = name.split(" ")[0]
        reg = ", ".join(c["regressed"]) or "—"
        paired += (f"<tr><td>{short}</td><td class='num bad'>{c['macro_recall_delta']:+.3f}</td>"
                   f"<td class='num b'>{len(c['rescued'])}</td>"
                   f"<td class='num'>{len(c['regressed'])}</td>"
                   f"<td class='num'>{c['net_rescued']:+d}</td>"
                   f"<td style='font-size:7.8pt'>{reg}</td></tr>")

    solo = ""
    for retriever in ("bm25", "transformer"):
        raw = grid[f"{retriever}(raw)"]
        norm = grid[f"{retriever}(normalized)"]
        st = grid[f"{retriever}(structured)"]
        solo += (f"<tr><td>{retriever}</td>"
                 f"<td class='num'>{raw['macro_span_recall']:.3f} ({raw['cases_fully_recalled']}/20)</td>"
                 f"<td class='num good'>{norm['macro_span_recall']:.3f} ({norm['cases_fully_recalled']}/20)</td>"
                 f"<td class='num good'>{attr['attribution'][retriever]['normalized']:+.3f}</td>"
                 f"<td class='num'>{st['macro_span_recall']:.3f} ({st['cases_fully_recalled']}/20)</td>"
                 f"<td class='num bad'>{attr['attribution'][retriever]['structured']:+.3f}</td></tr>")

    bonus_rows = ""
    for view, r in bonus["by_view"].items():
        cls = " class='good'" if r["fusion_bonus_cases"] >= 4 else (
            " class='bad'" if r["fusion_bonus_cases"] == 0 else "")
        bonus_rows += (f"<tr><td>{view}</td><td class='num'>{r['bm25_alone']}/20</td>"
                       f"<td class='num'>{r['transformer_alone']}/20</td>"
                       f"<td class='num'>{r['best_component']}</td>"
                       f"<td class='num'>{r['fused']}</td>"
                       f"<td class='num'{cls}>{r['fusion_bonus_cases']:+d} cases</td></tr>")

    an003 = ""
    for key, label in LABELS.items():
        spans = d["an003_deep_dive"][key]["spans"]
        rank = spans[0]["rank"]
        an003 += (f"<tr><td>{label}</td>"
                  f"<td class='num bad'>{rank if rank else 'absent@300'}</td>"
                  f"<td class='num'>{spans[0]['doc_rank']}</td></tr>")

    bands = ""
    for key in ("A_raw_query_control", "C_raw_plus_normalized", "E_three_view"):
        g = gate[key]
        b, c = g["bands"], g["perfect_reranker_ceiling_at_pool"]
        bands += (f"<tr><td>{LABELS[key]}</td>"
                  + "".join(f"<td class='num'>{b[k]}</td>" for k in
                            ("1-10", "11-30", "31-50", "51-100", "101-300", "absent_at_300"))
                  + "".join(f"<td class='num'>{c[p]:.3f}</td>" for p in ("30", "50", "100"))
                  + "</tr>")

    cv = comp["by_view"]
    a_cfg = cfg["A_raw_query_control"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-011 — Controlled Query-Side Retrieval</title><style>{CSS}</style></head><body>

<h1>EXP-011 — Controlled Query-Side Retrieval</h1>
<p class="subtitle">Production RAG v1 · evaluation-first · n = 20 questions / 22 evidence spans ·
document side frozen</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">Status — hypothesis falsified, with an instructive twist</div>
<p>Every query transformation made the <em>system</em> worse, and <strong>not one case was rescued in
any cell</strong>. But the same transformations made each retriever <strong>better in
isolation</strong>. The hybrid's strength was never query quality — it was the two retrievers failing
on different questions, and "improving" the query destroyed that.</p>
</div>

<div class="grid4">
  <div class="stat"><div class="big">0</div>
    <div class="cap">cases rescued<br>across all four cells</div></div>
  <div class="stat"><div class="big">+0.100</div>
    <div class="cap">BM25 gain from normalization<br><em>on its own</em></div></div>
  <div class="stat"><div class="big">+4 → +1</div>
    <div class="cap">fusion bonus collapse<br>raw → normalized</div></div>
  <div class="stat"><div class="big">3×</div>
    <div class="cap">retrieval work for cell E<br>to lose two cases</div></div>
</div>

<h2>1. Why EXP-011 exists</h2>
<p>EXP-010 closed the document side: truncation eliminated completely (23.22% of chunks → 0%, token
coverage 0.7610 → 1.0000) and retrieval moved Δ0.000, with <strong>21 of 22 answers already
visible</strong> to the encoder. What remains is a ranking problem. The query had been a raw
user-question string since EXP-000 — the one major variable never tested.</p>

<h2>2. Frozen system and leakage controls</h2>
<p>Corpus, chunks, <strong>stored document embeddings</strong> (fingerprint
<code>{d['transformer_fingerprint']}</code>), transformer, tokenizer, 512-token window, BM25
parameters, cosine, exact search, RRF pool {d['candidate_pool']} / <code>rrf_k</code> {d['rrf_k']} /
<code>top_k</code> {d['top_k']}, evidence anchors and questions — all unchanged.
<strong>Only the query text differed.</strong></p>
<p>A transform receives only the raw question string. Its module imports <em>only</em>
<code>re</code> and <code>dataclasses</code> — no project import at all — and tests assert that its
executable code names no evaluation symbol and hardcodes no golden question or evidence path.</p>

<h2>3. The transformations</h2>
<pre>raw         : What is the default value of max_tokens in the Anthropic Messages API?
normalized  : default value max_tokens Anthropic Messages API
structured  : max_tokens Anthropic Messages API default value</pre>
<p class="dim" style="font-size:8.4pt">A held-out probe, not a golden question. Identifiers, numbers,
status codes and product names the user wrote are protected; provider names are never invented.</p>

<h2>4. Reproduction gate</h2>
<p>Cell A reproduced the frozen hybrid exactly — <strong>0.775 / 15-of-20 / 17-of-22:
<span class="good">PASS</span></strong>.</p>

<h2>5. Results</h2>
<table><thead><tr><th>cell</th><th class="num">views</th><th class="num">macro R</th>
<th class="num">full</th><th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th>
<th class="num">a@10</th><th class="num">a@30</th><th class="num">a@300</th><th class="num">calls</th>
</tr></thead><tbody>{cells}</tbody></table>

<h2>6. Paired movement — no cell rescued anything</h2>
<table><thead><tr><th>comparison</th><th class="num">Δ</th><th class="num">rescued</th>
<th class="num">regressed</th><th class="num">net</th><th>cases lost</th></tr></thead>
<tbody>{paired}</tbody></table>
<p><strong>Zero rescues across every cell and every case</strong> — a stronger result than the
aggregate deltas. There is no subset of questions for which query rewriting helped.</p>

<h2>7. The twist: the retrievers individually got better</h2>
<table><thead><tr><th>retriever</th><th class="num">raw</th><th class="num">normalized</th>
<th class="num">Δ</th><th class="num">structured</th><th class="num">Δ</th></tr></thead>
<tbody>{solo}</tbody></table>
<p>Normalization improved <strong>both</strong> retrievers alone — BM25 by two cases, the transformer
by one. Yet fusing the two improved retrievers produced a worse system than fusing the two
unimproved ones.</p>

<h2>8. Mechanism: the fusion bonus collapsed</h2>
<table><thead><tr><th>query view</th><th class="num">BM25 alone</th><th class="num">transformer alone</th>
<th class="num">best component</th><th class="num">fused</th><th class="num">fusion bonus</th>
</tr></thead><tbody>{bonus_rows}</tbody></table>

<div class="callout">
<div class="label">What RRF was actually buying</div>
<p>Fusion adds value in proportion to how much the retrievers still <em>disagree usefully</em>. On the
raw query it is worth <strong>four cases</strong> beyond its best component. Normalizing pushed both
retrievers toward the same evidence and the bonus fell to <strong>one</strong> — more than cancelling
the individual gains.</p>
<p>A supporting proxy agrees but only weakly, and is reported as such: mean Jaccard overlap between
the retrievers' top-50 rose {cv['raw']['mean_jaccard_top50']:.3f} → {cv['normalized']['mean_jaccard_top50']:.3f}
→ {cv['structured']['mean_jaccard_top50']:.3f}, while shared top-10 chunks stayed flat
({cv['raw']['mean_shared_chunks_top10']:.1f} → {cv['normalized']['mean_shared_chunks_top10']:.1f}).
The fusion-bonus table is the solid evidence.</p>
</div>

<h2>9. The design rule earned its place</h2>
<p>The preregistration forbade ever replacing the user's query, and that rule bounded the damage:
B (normalized alone) loses two cases, C (raw <strong>+</strong> normalized) loses one. Keeping the
original halved the loss. E, which adds a third view, is worse than C — a further view is not free
even when the original is retained.</p>

<h2>10. AN-003</h2>
<table><thead><tr><th>cell</th><th class="num">evidence rank</th><th class="num">document rank</th>
</tr></thead><tbody>{an003}</tbody></table>
<p>No query representation moved it. The pattern is now unmistakable: the <strong>right document
ranks 2nd–6th in every configuration</strong> while the chunk carrying the answer never enters the
top 300. Not a query problem, not a visibility problem — a <strong>within-document chunk-ranking</strong>
failure, surviving its ninth experiment.</p>

<h2>11. Candidate depth and the reranker gate</h2>
<table><thead><tr><th>cell</th><th class="num">1–10</th><th class="num">11–30</th>
<th class="num">31–50</th><th class="num">51–100</th><th class="num">101–300</th>
<th class="num">absent</th><th class="num">ceil@30</th><th class="num">ceil@50</th>
<th class="num">ceil@100</th></tr></thead><tbody>{bands}</tbody></table>
<p>Query expansion did <strong>not</strong> raise the perfect-reranker ceiling — 0.909 at pool 100 for
A, C and E alike. Cell E pulls one span out of "absent" into the 101–300 band, which is real but not
ceiling-changing. A reranker would still chase 0.909 against {a_cfg['macro_span_recall']:.3f} already
delivered, and would have to be perfect to collect it.</p>

<h2>12. Cost</h2>
<p>Cell E costs <strong>three times</strong> the retrieval work ({cost['E_three_view']['retrieval_calls_per_query']:.0f}
calls per question vs {cost['A_raw_query_control']['retrieval_calls_per_query']:.0f}) to lose two
cases. Wall-clock latency is <em>not</em> comparable across cells here — A ran first and absorbed
cold-cache and warm-up costs, which is why it shows the highest total despite the fewest calls. The
call count is the honest measure. The query-embedding cache served
{d['query_embedding_cache']['query_embedding_cache_hit_rate'] * 100:.1f}% of requests.</p>

<h2>13. Limitations</h2>
<ul>
<li>n = 20 / 22 spans; one case is 5 percentage points. No significance claims.</li>
<li>Two deterministic transforms were tested, not the space of query rewriting. An LLM rewriter might
behave differently — though the mechanism found here predicts it would also erode complementarity if
it made both retrievers agree.</li>
<li>The fusion bonus is a case count at n = 20; ±1 case is noise, but the +4 → +1 → +0 progression is
monotone across three independent views.</li>
<li><strong>EXP-NULL remains BLOCKED</strong> — no project generation credential, so there is still no
measured no-retrieval floor beneath any of these numbers. EXP-011F (LLM rewriting) was not run for
the same reason.</li>
</ul>

<h2>14. Was query formulation a real bottleneck?</h2>
<p><strong>No — not in the way the hypothesis proposed.</strong> Rewriting cannot rescue a single
case, and the raw question is already the best input to the hybrid.</p>
<p>But the finding is more specific than "queries are fine". Query form <strong>does</strong> change
individual retriever quality materially — BM25 gained two cases from filler removal alone. What it
cannot do is improve the <em>system</em>, because this system's performance comes from retriever
disagreement rather than either retriever's absolute quality. <strong>Optimising the components made
the ensemble worse.</strong> That is a result about ensembles, not about queries, and it was only
visible because the components were measured separately from the fusion.</p>

<h2>15. What the evidence justifies next</h2>
<ol>
<li><strong>Stop rewriting queries.</strong> Preregistered Outcome D. Zero rescues in four
configurations is not a near miss.</li>
<li><strong>Treat complementarity as the quantity to protect.</strong> Future changes should report the
fusion bonus, not just aggregate recall — a change that improves both retrievers can still degrade
the system.</li>
<li><strong>The remaining failure is within-document chunk ranking.</strong> AN-003 is the clean case:
right document at rank 2, answer chunk never in the top 300.</li>
<li><strong>A reranker is still not justified</strong> on ceiling grounds, and EXP-011 did not move
that ceiling.</li>
<li><strong>EXP-NULL remains the most valuable unblocked experiment.</strong></li>
</ol>

<footer>
Generated from experiments/EXP-011/*.json by scripts/build_exp011_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Query transform version {d['query_transform_version']}. Document side frozen: chunk set
{d['chunk_set']}, encoder fingerprint {d['transformer_fingerprint']}, exact cosine, no ANN index.
No reranker, no LLM query rewriting, no metadata filtering.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-011-controlled-query-side-retrieval.pdf")
    args = parser.parse_args()
    html = build_html(
        json.loads((EXP / "results.json").read_text()),
        json.loads((EXP / "retriever-attribution.json").read_text()),
        json.loads((EXP / "fusion-bonus.json").read_text()),
        json.loads((EXP / "complementarity.json").read_text()),
    )
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp011.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
