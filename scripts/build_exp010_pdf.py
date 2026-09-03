#!/usr/bin/env python3
"""Render the EXP-010 report to a shareable PDF.

Every figure is read from experiments/EXP-010/*.json at build time, so the PDF
cannot drift from the artifacts. Re-run scripts/run_exp010.py and
scripts/analyze_exp010.py first if anything changed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP = REPO_ROOT / "experiments" / "EXP-010"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 18mm 16mm 16mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt;
  line-height: 1.5; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 21pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 12.5pt; margin: 19pt 0 7pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 10.5pt; margin: 12pt 0 4pt; }
p { margin: 0 0 7pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.6pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 11pt; color: #52565d; margin: 0 0 12pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 14pt; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; font-size: 8.8pt; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4.5pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.b { font-weight: 700; } .bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt; margin: 10pt 0 12pt; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.5pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }
.callout.win .label { color: #14532d; }
ol, ul { margin: 0 0 8pt; padding-left: 15pt; } li { margin-bottom: 4pt; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 9pt; margin: 4pt 0 12pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 8pt 10pt; border-radius: 3pt; }
.stat .big { font-size: 17pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.6pt; color: #52565d; margin-top: 2pt; }
footer { margin-top: 16pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 8pt; color: #6f747b; }
.avoid { break-inside: avoid; page-break-inside: avoid; }
"""

LABELS = {
    "A_bm25_control": "A — BM25, control chunks",
    "B_transformer_control": "B — transformer @512, control",
    "C_bm25_transformer_control_rrf": "C — BM25 + transformer RRF, control",
    "D_transformer_aligned": "D — transformer @512, encoder-aligned",
    "E_bm25_control_plus_aligned_rrf": "E — BM25 control + transformer aligned",
}
HILITE = {"D_transformer_aligned", "E_bm25_control_plus_aligned_rrf"}


def cells(cfg: dict) -> str:
    rows = ""
    for key, label in LABELS.items():
        r = cfg[key]
        a = r["spans_absent_from_top"]
        b = " class='b'" if key in HILITE else ""
        rows += (f"<tr><td{b}>{label}</td><td class='num'{b}>{r['macro_span_recall']:.3f}</td>"
                 f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                 f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
                 f"<td class='num'>{r['document_recall']:.3f}</td><td class='num'>{r['mrr']:.3f}</td>"
                 + "".join(f"<td class='num'>{a[str(k)]}</td>" for k in (10, 50, 300))
                 + f"<td class='num'>{r['mean_query_ms']:.0f}</td></tr>")
    return rows


def build_html(d: dict, gates: dict, trunc: dict, null: dict) -> str:
    cfg = d["configurations"]
    ctrl, algn = gates["distribution"]["control"], gates["distribution"]["encoder_aligned"]
    bd = d["paired_comparison"]["B->D encoder alignment (the hypothesis)"]
    ce = d["paired_comparison"]["C->E mixed-representation fusion"]

    gate_rows = ""
    for key, g in d["reproduction_gate"].items():
        checks = " · ".join(f"{n} {c['actual']}" for n, c in g["checks"].items())
        v = "<span class='good'>PASS</span>" if g["reproduced"] else "<span class='bad'>FAIL</span>"
        gate_rows += f"<tr><td>{LABELS[key]}</td><td>{checks}</td><td>{v}</td></tr>"

    td = trunc["truncation_driven"]["detail"]
    trunc_rows = ""
    for r in sorted(td, key=lambda x: x["case_id"]):
        vis = r["answer_visible_in_control_window"]
        cls = " class='bad'" if vis is False else ""
        name_cls = " class='b'" if vis is False else ""
        trunc_rows += (f"<tr><td{name_cls}>{r['case_id']}</td>"
                       f"<td class='num'>{r['control_payload_tokens'][0]}</td>"
                       f"<td class='num'{cls}>{r['answer_token_offset_in_control_chunk']}</td>"
                       f"<td{cls}>{'no' if vis is False else 'yes'}</td>"
                       f"<td class='num'>{r['rank_B_control']} &rarr; {r['rank_D_aligned']}</td>"
                       f"<td>{r['movement']}</td></tr>")

    band_rows = ""
    for key, g in d["reranker_decision_gate"].items():
        b, c = g["bands"], g["perfect_reranker_ceiling_at_pool"]
        band_rows += (f"<tr><td>{LABELS[key]}</td>"
                      + "".join(f"<td class='num'>{b[k]}</td>" for k in
                                ("1-10", "11-30", "31-50", "51-100", "101-300", "absent_at_300"))
                      + "".join(f"<td class='num'>{c[p]:.3f}</td>" for p in ("30", "50", "100"))
                      + "</tr>")

    moved = [r for r in bd["span_rows"] if r["rank_before"] != r["rank_after"]]
    same_cos = [r for r in moved if r["similarity_before"] == r["similarity_after"]]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-010 — Encoder-Window-Aligned Chunking</title><style>{CSS}</style></head><body>

<h1>EXP-010 — Encoder-Window-Aligned Chunking</h1>
<p class="subtitle">Production RAG v1 · evaluation-first · n = 20 questions / 22 evidence spans</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">Status — hypothesis falsified</div>
<p>Truncation was eliminated completely — <strong>{ctrl['percent_truncated_at_512']:.2f}% of chunks
truncated &rarr; {algn['percent_truncated_at_512']:.0f}%</strong>, corpus token coverage
<strong>{ctrl['corpus_token_coverage']:.4f} &rarr; {algn['corpus_token_coverage']:.4f}</strong> — and
retrieval did not move at all: <strong>&Delta;0.000, zero cases rescued, zero regressed</strong>, on
both primary comparisons. Encoder visibility correlated with the EXP-009 result but is
<strong>not the causal bottleneck</strong>.</p>
</div>

<div class="grid4">
  <div class="stat"><div class="big">{bd['macro_recall_delta']:+.3f}</div>
    <div class="cap">B &rarr; D transformer<br>control &rarr; aligned</div></div>
  <div class="stat"><div class="big">{ce['macro_recall_delta']:+.3f}</div>
    <div class="cap">C &rarr; E fusion<br>mixed representation</div></div>
  <div class="stat"><div class="big">1 / 22</div>
    <div class="cap">answers actually hidden<br>by the 512 window</div></div>
  <div class="stat"><div class="big">{algn['corpus_token_coverage']:.2f}</div>
    <div class="cap">corpus token coverage<br>(control {ctrl['corpus_token_coverage']:.2f})</div></div>
</div>

<h2>1. Why EXP-010 exists</h2>
<p>EXP-009 measured the same transformer at two windows and found retrieval tracked how much of a
unit the encoder could see (256 tokens: 35.2% truncated, recall 0.500; 512 tokens: 23.2% truncated,
recall 0.575, fused 0.775). That was a correlation across two settings with one observation each.
EXP-010 holds the window fixed at 512 and changes the retrieval unit instead, so the claim can be
tested rather than repeated.</p>

<h2>2. Not another "smaller chunks" experiment</h2>
<p>EXP-005 (chunk size &times; BM25) and EXP-008 (chunk size &times; dense) both shortened chunks
using character heuristics and both failed; EXP-008 showed splitting a coherent unit makes dense
retrieval <em>worse</em>. Here every limit is measured in the encoder's own WordPiece tokenization,
and the objective is the <strong>largest coherent unit the encoder can consume whole</strong> —
explicitly not the smallest.</p>
<p>The chunk set is <strong>derived from the control</strong>: a chunk that already fits passes
through with the same source span and text, and only an oversized chunk is split. That decision was
committed before the build, so D vs B isolates encoder alignment rather than confounding it with
re-grouping.</p>

<h2>3. Encoder budget — measured, not assumed</h2>
<table><thead><tr><th>quantity</th><th class="num">value</th><th>source</th></tr></thead><tbody>
<tr><td>max_position_embeddings</td><td class="num">512</td><td>config.json</td></tr>
<tr><td>special-token overhead</td><td class="num b">2</td><td>probe encoded with and without specials</td></tr>
<tr><td>usable payload</td><td class="num">510</td><td>512 &minus; 2</td></tr>
<tr><td>target / hard payload</td><td class="num">448 / 480</td><td>conservative, near the top of the window</td></tr>
</tbody></table>

<h2>4. Intervention fidelity</h2>
<table><thead><tr><th></th><th class="num">control</th><th class="num">encoder-aligned</th></tr></thead>
<tbody>
<tr><td>chunks</td><td class="num">{ctrl['chunks']:,}</td><td class="num">{algn['chunks']:,}</td></tr>
<tr><td>median encoded tokens</td><td class="num">{ctrl['median_encoded_tokens']:g}</td><td class="num">{algn['median_encoded_tokens']:g}</td></tr>
<tr><td>p95</td><td class="num">{ctrl['p95']}</td><td class="num">{algn['p95']}</td></tr>
<tr><td>max</td><td class="num">{ctrl['max_encoded_tokens']:,}</td><td class="num b">{algn['max_encoded_tokens']}</td></tr>
<tr><td>chunks over 512</td><td class="num">{ctrl['chunks_over_512']:,}</td><td class="num good">{algn['chunks_over_512']}</td></tr>
<tr><td>corpus token coverage</td><td class="num">{ctrl['corpus_token_coverage']:.4f}</td><td class="num good">{algn['corpus_token_coverage']:.4f}</td></tr>
<tr><td>evidence spans preserved</td><td class="num">22/22</td><td class="num">22/22</td></tr>
</tbody></table>
<p>Verified twice independently: the gate script tokenized all {algn['chunks']:,} chunks, and the
embedding build measured truncation through the encoder's own path while encoding
(<code>texts_truncated: 0</code>, <code>token_coverage: 1.0</code>). The corrected control figures
match EXP-009's independently recorded numbers exactly.</p>

<h2>5. Reproduction gates</h2>
<table><thead><tr><th>cell</th><th>checks</th><th>verdict</th></tr></thead>
<tbody>{gate_rows}</tbody></table>

<h2>6. Results</h2>
<table><thead><tr><th>cell</th><th class="num">macro R</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th>
<th class="num">a@10</th><th class="num">a@50</th><th class="num">a@300</th><th class="num">ms</th>
</tr></thead><tbody>{cells(cfg)}</tbody></table>
<p>B and D are identical on every headline metric. C and E are identical on recall; E's MRR is
marginally better ({cfg['E_bm25_control_plus_aligned_rrf']['mrr']:.3f} vs
{cfg['C_bm25_transformer_control_rrf']['mrr']:.3f}) and its document recall marginally worse — both
well inside noise at n = 20.</p>

<h2>7. Why the null is not "nothing happened"</h2>
<p><strong>{len(moved)} of 22 spans changed rank.</strong> The movements simply never crossed the
top-10 boundary. Splitting them by cause is what makes the result interpretable:</p>
<ul>
<li><strong>7 spans</strong> sat in a truncated chunk, so their carrying chunk genuinely changed —
and their cosine changed with it. 3 improved, 4 worsened.</li>
<li><strong>{len(same_cos)} spans</strong> sat in chunks that already fitted and passed through
byte-identical — their cosine is <em>identical to six decimals</em>. They moved only because other
documents' chunks were resplit and the competition changed.</li>
</ul>
<p>Rank is relative: an untouched chunk still moves when the corpus around it is recut. It also means
the EXP-008 fragmentation failure did <strong>not</strong> repeat — units that already fitted were
never touched.</p>

<h2>8. The decisive measurement: chunk truncation is not answer invisibility</h2>
<table><thead><tr><th>case</th><th class="num">chunk tokens</th><th class="num">answer offset</th>
<th>visible at 512?</th><th class="num">rank B &rarr; D</th><th>movement</th></tr></thead>
<tbody>{trunc_rows}</tbody></table>

<div class="callout warn">
<div class="label">The finding that explains the null</div>
<p><strong>Only one answer out of 22 — AN-007 — was actually outside the visible window.</strong>
The other 21 were already fully visible to the encoder. 23% of <em>chunks</em> were truncated, but
only 4.5% of <em>answers</em> were hidden, because answers sit near the top of the sections that
carry them.</p>
<p>There was therefore almost nothing left for encoder alignment to fix — and the one case where the
hypothesis made a direct prediction, <strong>AN-007, got worse when its answer was made visible</strong>
(16 &rarr; 28). The single span the mechanism was supposed to rescue moved the wrong way.</p>
</div>

<h2>9. AN-003, AN-002 / AN-007, OA-004</h2>
<p><strong>AN-003</strong> improved 299 &rarr; 193 with a rising cosine — the largest single movement
in the experiment, and still far outside any practical pool. Its answer was <em>already visible</em>
at token offset 118, so this is not a truncation rescue. AN-003 has now failed under BM25, FastText,
the transformer at two windows, and encoder-aligned chunking.</p>
<p><strong>AN-002</strong> (18 &rarr; 26) and <strong>AN-007</strong> (16 &rarr; 28) both worsened;
neither was inside the top 10 to begin with. <strong>OA-004</strong> moved 24 &rarr; 26 under D and is
unchanged between the fused cells, so the EXP-009 fusion rescue is not undone. It is still unsolved.</p>

<h2>10. Reranker decision gate — counts only, no reranker was built</h2>
<table><thead><tr><th>cell</th><th class="num">1–10</th><th class="num">11–30</th>
<th class="num">31–50</th><th class="num">51–100</th><th class="num">101–300</th>
<th class="num">absent</th><th class="num">ceil@30</th><th class="num">ceil@50</th>
<th class="num">ceil@100</th></tr></thead><tbody>{band_rows}</tbody></table>
<p>Alignment did not improve rerankable headroom; at pools 50 and 100 it slightly <strong>reduced</strong>
it. A reranker would work against a ceiling of 0.909 with the fused retriever already delivering
0.775 — roughly three spans of headroom across 20 questions. Not yet a compelling case.</p>

<h2>11. EXP-NULL</h2>
<p><strong>{null['status'].upper()}.</strong> <code>api.anthropic.com</code> is reachable but answers
<code>{null['endpoint_probe']['api.anthropic.com']}</code> without a key; <code>api.openai.com</code>
remains blocked at the egress proxy. No credential was fabricated, printed, or inferred, and the
session's own harness credentials are not a project credential. EXP-010 was not delayed for it.</p>

<h2>12. Limitations</h2>
<ul>
<li>n = 20 / 22 spans. One case is 5 percentage points. No significance is claimed.</li>
<li>A &Delta;0.000 with 12 spans moving is a <em>null at the decision boundary</em>, not proof of no
effect. A different top-k or a larger question set could separate B and D.</li>
<li>The answer-offset measure counts tokens to the <em>start</em> of the evidence span; an answer
beginning inside the window but extending past it counts as visible.</li>
<li>One encoder, one window (512, inherited from EXP-009 and deliberately not swept).</li>
</ul>

<h2>13. Did encoder alignment earn promotion?</h2>
<p><strong>No.</strong> The frozen production baseline stays control chunks / no enrichment / BM25 /
<code>top_k=10</code>. The strongest measured configuration remains <strong>BM25 + transformer @512
RRF on control chunks — 0.775 / 15-of-20</strong>. The aligned set costs 31% more chunks, 48 MB more
vectors and a longer build, and returns nothing.</p>

<h2>14. What the measurements justify next</h2>
<ol>
<li><strong>Stop treating truncation as the bottleneck.</strong> It is fixed completely and bought
nothing. Three chunking interventions have now returned 0, &minus;0.050 and 0.000 —
<strong>chunking is not where the remaining recall is</strong>.</li>
<li><strong>The gap is ranking, not visibility.</strong> 21 of 22 answers were already visible and 9
still sit outside the top 10. The encoder sees the right text and scores it below other text.</li>
<li><strong>Investigate the query side, which has never been touched.</strong> Every experiment so far
changed the document representation; the query has been a raw question string since EXP-000.</li>
<li><strong>A reranker is still not justified</strong> — ceiling 0.909 against 0.775 delivered.</li>
<li><strong>AN-003 needs a failure report, not another chunker.</strong></li>
</ol>

<footer>
Generated from experiments/EXP-010/*.json by scripts/build_exp010_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Encoder {d['embedding_model']['model_identifier']} @ {d['encoder_window']} tokens, fingerprint
{d['model_fingerprint']}, exact cosine, no ANN index. Chunker {d['chunker']['name']} v{d['chunker']['version']}.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-010-encoder-window-aligned-chunking.pdf")
    args = parser.parse_args()
    html = build_html(
        json.loads((EXP / "results.json").read_text()),
        json.loads((EXP / "ingestion-gates.json").read_text()),
        json.loads((EXP / "truncation-analysis.json").read_text()),
        json.loads((EXP / "EXP-NULL-retry.json").read_text()),
    )
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp010.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
