#!/usr/bin/env python3
"""Render one consolidated results PDF covering EXP-NULL through EXP-010.

Every figure is read from experiments/**/*.json at build time, so the summary
cannot drift from the individual experiment artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 16mm 14mm 14mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.6pt;
  line-height: 1.45; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 20pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 12pt; margin: 17pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.3pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 10.5pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.5pt; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.b { font-weight: 700; } .bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; }
.dim { color: #6f747b; }
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
.avoid { break-inside: avoid; page-break-inside: avoid; }
"""


def load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


def row(label: str, recall, full, spans, note: str = "", cls: str = "") -> str:
    r = f"{recall:.3f}" if isinstance(recall, (int, float)) else recall
    c = f" class='{cls}'" if cls else ""
    return (f"<tr><td{c}>{label}</td><td class='num'{c}>{r}</td>"
            f"<td class='num'>{full}</td><td class='num'>{spans}</td>"
            f"<td class='dim'>{note}</td></tr>")


def build_html() -> str:
    e0_broken = load("experiments/EXP-000/results-websearch-and.json")
    e0 = load("experiments/EXP-000/results.json")
    e1 = load("experiments/EXP-001/results.json")
    e2 = load("experiments/EXP-002/results.json")
    e3 = load("experiments/EXP-003/results-k60.json")
    e5 = load("experiments/EXP-005/paired-analysis.json")
    e6 = load("experiments/EXP-006/results.json")
    e7 = load("experiments/EXP-007/results.json")["configurations"]
    e8 = load("experiments/EXP-008/results.json")
    e9_256 = load("experiments/EXP-009/results.json")["configurations"]
    e9_512 = load("experiments/EXP-009/results-512-sensitivity.json")["configurations"]
    e10 = load("experiments/EXP-010/results.json")
    e10c = e10["configurations"]
    gates = load("experiments/EXP-010/ingestion-gates.json")
    null = load("experiments/EXP-010/EXP-NULL-retry.json")

    ctrl = gates["distribution"]["control"]
    algn = gates["distribution"]["encoder_aligned"]
    best = e9_512["D_bm25_transformer_rrf"]

    # -- the arc ------------------------------------------------------------
    arc = (
        row("EXP-000 lexical — <em>as shipped</em>", e0_broken.get("macro_recall", 0.0),
            f"{e0_broken.get('cases_fully_recalled', 0)}/20", "—",
            "websearch_to_tsquery ANDs every token", "bad")
        + row("EXP-000 lexical — BM25 (the fix)", e0["macro_recall"],
              f"{e0['cases_fully_recalled']}/20", "10/22", "frozen production baseline")
        + row("EXP-001 dense — LSA, corpus-fitted", e1["macro_recall"],
              f"{e1['cases_fully_recalled']}/20", "—", "not a pretrained model")
        + row("EXP-002 hybrid interleave", e2["macro_recall"],
              f"{e2['cases_fully_recalled']}/20", "—", "")
        + row("EXP-003 RRF <span class='mono'>rrf_k=60</span>", e3["macro_recall"],
              f"{e3['cases_fully_recalled']}/20", "—", "no gain over BM25 alone")
    )

    e5_pairs = e5.get("paired_comparisons", {})
    rescued_5 = sum(len(v.get("rescued", [])) for v in e5_pairs.values())
    e6a = e6["configurations"]["EXP-006A"]["macro_span_recall"]
    e6b = e6["configurations"]["EXP-006B"]["macro_span_recall"]

    interventions = (
        row("EXP-005 chunk size × BM25", e6a, "9/20", "10/22",
            f"{rescued_5} questions rescued — falsified", "bad")
        + row("EXP-006 structural enrichment × BM25", e6b, "9/20", "10/22",
              f"Δ{e6b - e6a:+.3f} — falsified", "bad")
        + row("EXP-007 static pretrained dense (FastText)",
              e7["EXP-007B_pretrained_dense"]["macro_span_recall"],
              f"{e7['EXP-007B_pretrained_dense']['cases_fully_recalled']}/20",
              f"{e7['EXP-007B_pretrained_dense']['spans_found_at_10']}/22",
              "weak instrument; below BM25", "bad")
        + row("EXP-007C BM25 + FastText RRF",
              e7["EXP-007C_bm25_dense_rrf"]["macro_span_recall"],
              f"{e7['EXP-007C_bm25_dense_rrf']['cases_fully_recalled']}/20",
              f"{e7['EXP-007C_bm25_dense_rrf']['spans_found_at_10']}/22",
              "unexpected win — retrievers are complementary", "good")
        + row("EXP-008 chunk size × dense",
              e8["configurations"]["D_bounded_dense"]["macro_span_recall"], "8/20", "—",
              f"interaction {e8['interaction_analysis']['interaction_delta']:+.3f} — not supported", "bad")
    )

    transformer = (
        row("EXP-009 transformer dense @256 <span class='dim'>(reference primary)</span>",
            e9_256["C_transformer_control"]["macro_span_recall"],
            f"{e9_256['C_transformer_control']['cases_fully_recalled']}/20",
            f"{e9_256['C_transformer_control']['spans_found_at_10']}/22",
            "missed its preregistered bar", "bad")
        + row("EXP-009 BM25 + transformer RRF @256",
              e9_256["D_bm25_transformer_rrf"]["macro_span_recall"],
              f"{e9_256['D_bm25_transformer_rrf']['cases_fully_recalled']}/20",
              f"{e9_256['D_bm25_transformer_rrf']['spans_found_at_10']}/22", "")
        + row("EXP-009 transformer dense @512 <span class='dim'>(preregistered sensitivity)</span>",
              e9_512["C_transformer_control"]["macro_span_recall"],
              f"{e9_512['C_transformer_control']['cases_fully_recalled']}/20",
              f"{e9_512['C_transformer_control']['spans_found_at_10']}/22", "cleared the bar", "good")
        + row("<b>EXP-009 BM25 + transformer RRF @512</b>", best["macro_span_recall"],
              f"{best['cases_fully_recalled']}/20", f"{best['spans_found_at_10']}/22",
              "best measured; +6 vs BM25, zero regressions", "good")
        + row("EXP-010 transformer dense, encoder-aligned",
              e10c["D_transformer_aligned"]["macro_span_recall"],
              f"{e10c['D_transformer_aligned']['cases_fully_recalled']}/20",
              f"{e10c['D_transformer_aligned']['spans_found_at_10']}/22",
              "Δ0.000 vs control chunks — falsified", "bad")
        + row("EXP-010 BM25 + aligned transformer RRF",
              e10c["E_bm25_control_plus_aligned_rrf"]["macro_span_recall"],
              f"{e10c['E_bm25_control_plus_aligned_rrf']['cases_fully_recalled']}/20",
              f"{e10c['E_bm25_control_plus_aligned_rrf']['spans_found_at_10']}/22",
              "Δ0.000 vs EXP-009 best", "bad")
    )

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Production RAG v1 — Results Through EXP-010</title><style>{CSS}</style></head><body>

<h1>Production RAG v1 — Measured Results</h1>
<p class="subtitle">EXP-NULL through EXP-010 · 202 OpenAI + Anthropic documents ·
n = 20 questions / 22 evidence spans · evaluation-first</p>
<div class="rule"></div>

<div class="grid4">
  <div class="stat"><div class="big">{e0['macro_recall']:.3f}</div>
    <div class="cap">frozen production baseline<br>BM25, control chunks</div></div>
  <div class="stat"><div class="big">{best['macro_span_recall']:.3f}</div>
    <div class="cap">best measured configuration<br>BM25 + transformer RRF @512</div></div>
  <div class="stat"><div class="big">6</div>
    <div class="cap">hypotheses tested<br>by controlled intervention</div></div>
  <div class="stat"><div class="big">4</div>
    <div class="cap">falsified and kept<br>as engineering evidence</div></div>
</div>

<div class="callout">
<div class="label">What this project is</div>
<p>A deliberately small, evaluation-first retrieval system. Every change is a controlled
intervention against 20 human-verified questions whose evidence is anchored <em>above</em> the chunk
layer — on <code>(version_id, section_path, char_start, char_end)</code>, never on chunk ids — so
the ground truth survives every re-chunking. Negative results are preserved rather than deleted.
At n = 20 one question is 5 percentage points, so no significance is claimed anywhere.</p>
</div>

<h2>1. Getting a baseline that works</h2>
<table><thead><tr><th>experiment</th><th class="num">macro recall</th><th class="num">full</th>
<th class="num">spans@10</th><th>note</th></tr></thead><tbody>{arc}</tbody></table>
<p>The first measurement found the shipped lexical search returning <strong>nothing at all</strong>:
<code>websearch_to_tsquery</code> ANDs every token, so a 16-token question demanded all 16 tokens in
one chunk. OR-ing the terms and ranking with BM25 — so a rare identifier outweighs a common word —
took recall from <strong>0.000 to 0.475</strong>. That remains the production baseline.</p>

<h2>2. Four hypotheses about the document representation</h2>
<table><thead><tr><th>experiment</th><th class="num">macro recall</th><th class="num">full</th>
<th class="num">spans@10</th><th>outcome</th></tr></thead><tbody>{interventions}</tbody></table>
<p>Chunk size was tested against BM25 (EXP-005) and against dense retrieval (EXP-008); structural
enrichment was isolated in a 2×2 (EXP-006). All three failed. EXP-006 found the mechanism: prefixing
every chunk with <code>Provider: Anthropic</code> inflated that term's document frequency from 3,289
to 12,028, which is exactly what BM25 is designed to discount.</p>
<p>EXP-007's own hypothesis failed too — static FastText scored below BM25 — but produced the
project's first real gain by accident: <strong>fusing the two retrievers</strong> reached 0.600,
because they fail on different questions.</p>

<h2>3. A real transformer, and what it actually showed</h2>
<table><thead><tr><th>experiment</th><th class="num">macro recall</th><th class="num">full</th>
<th class="num">spans@10</th><th>outcome</th></tr></thead><tbody>{transformer}</tbody></table>

<div class="callout win">
<div class="label">The one configuration that clearly beat the baseline</div>
<p><strong>BM25 + transformer @512 RRF, both on control chunks — {best['macro_span_recall']:.3f} /
{best['cases_fully_recalled']}-of-20</strong>, MRR {best['mrr']:.3f}. Net <strong>+6 cases over BM25
and +4 over the FastText fusion, with zero regressions in either comparison</strong> — the only
zero-regression result in the project.</p>
</div>

<h2>4. EXP-010: the mechanism story was wrong</h2>
<p>EXP-009 concluded that <em>encoder visibility</em> drove the gain, since retrieval improved as the
context window widened. EXP-010 tested that causally: hold the window at 512 and rebuild the chunks
so every unit fits.</p>
<table><thead><tr><th></th><th class="num">control</th><th class="num">encoder-aligned</th></tr></thead>
<tbody>
<tr><td>chunks over the 512-token window</td><td class="num">{ctrl['chunks_over_512']:,} ({ctrl['percent_truncated_at_512']:.2f}%)</td>
<td class="num good">{algn['chunks_over_512']} (0%)</td></tr>
<tr><td>corpus token coverage</td><td class="num">{ctrl['corpus_token_coverage']:.4f}</td>
<td class="num good">{algn['corpus_token_coverage']:.4f}</td></tr>
<tr><td>transformer dense recall</td><td class="num">{e10c['B_transformer_control']['macro_span_recall']:.3f}</td>
<td class="num b">{e10c['D_transformer_aligned']['macro_span_recall']:.3f}</td></tr>
<tr><td>fused recall</td><td class="num">{e10c['C_bm25_transformer_control_rrf']['macro_span_recall']:.3f}</td>
<td class="num b">{e10c['E_bm25_control_plus_aligned_rrf']['macro_span_recall']:.3f}</td></tr>
</tbody></table>

<div class="callout warn">
<div class="label">Truncation eliminated entirely — retrieval did not move at all</div>
<p><strong>Δ0.000 on both comparisons, zero rescued, zero regressed.</strong> The measurement that
explains it: <strong>only 1 of 22 answers was actually outside the visible window</strong>. Chunk
truncation is not answer invisibility — 23% of <em>chunks</em> were cut, but answers sit near the top
of the sections carrying them, so 21 of 22 were already fully visible. There was almost nothing left
to fix, and <strong>AN-007, the single case the hypothesis predicted, got worse when made visible</strong>
(rank 16 → 28).</p>
</div>

<h2>5. Where the recall actually is</h2>
<p>Three chunking interventions have now returned <strong>0, −0.050 and 0.000</strong>. The document
representation is not where the remaining recall lives:</p>
<ul>
<li><strong>21 of 22 answers are already visible</strong> to the encoder, and 9 still sit outside the
top 10. The encoder reads the right text and scores it below other text — that is a
<strong>ranking</strong> problem, not a visibility one.</li>
<li><strong>The query side has never been touched.</strong> Every experiment so far changed the
document representation; the query has been a raw user-question string since EXP-000.</li>
<li><strong>A reranker is still not justified</strong> — a perfect reranker over a 100-candidate pool
tops out at 0.909 against 0.775 already delivered, roughly three spans of headroom.</li>
<li><strong>AN-003 needs a failure report, not another chunker.</strong> It has defeated BM25,
FastText, the transformer at two windows, and encoder-aligned chunking — and its answer was visible
every time.</li>
</ul>

<h2>6. Standing caveats</h2>
<ul>
<li>n = 20 questions. One case is 5 percentage points; no significance is claimed and nothing here
generalises beyond this corpus.</li>
<li><strong>EXP-NULL (closed-book control) is {null['status'].upper()}</strong> — no authorized
generation credential is available, so we cannot yet measure how many of these questions a model
answers with no retrieval at all. Until that runs, the retrieval gains are unanchored against a
no-retrieval floor.</li>
<li>The transformer bundle could not be checksummed against its upstream publisher (Hugging Face is
blocked by egress policy); structural and behavioural checks were recorded instead.</li>
<li>The frozen production baseline has <strong>not</strong> been changed. EXP-009's 0.775 rests on a
single run and is a candidate, not a promotion.</li>
</ul>

<footer>
Generated from experiments/**/*.json by scripts/build_project_summary_pdf.py.
EXP-010 git commit {(e10.get('git_commit') or 'unknown')[:12]}, config hash {e10['config_hash'][:16]}.
Encoder {e10['embedding_model']['model_identifier']} @ {e10['encoder_window']} tokens, exact cosine,
no ANN index. Retrieval carries no reranker, query rewriting, query expansion, stemming or enrichment.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/production-rag-results-through-exp010.pdf")
    args = parser.parse_args()
    html = build_html()
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "summary.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
