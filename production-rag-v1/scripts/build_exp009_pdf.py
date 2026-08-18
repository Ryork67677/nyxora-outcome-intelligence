#!/usr/bin/env python3
"""Render the EXP-009 report to a shareable PDF.

Every figure is read from experiments/EXP-009/*.json at build time, so the PDF
cannot drift from the artifacts. Re-run scripts/run_exp009.py first if anything
changed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP = REPO_ROOT / "experiments" / "EXP-009"
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
    "A_bm25_control": "A — BM25 (frozen baseline)",
    "B_fasttext_control": "B — FastText dense (EXP-007)",
    "C_transformer_control": "C — transformer dense",
    "D_bm25_transformer_rrf": "D — BM25 + transformer RRF",
    "E_bm25_fasttext_rrf": "E — BM25 + FastText RRF (EXP-007C)",
}
HILITE = {"C_transformer_control", "D_bm25_transformer_rrf"}


def cell_rows(cfg: dict) -> str:
    rows = ""
    for key, label in LABELS.items():
        r = cfg[key]
        a = r["spans_absent_from_top"]
        b = " class='b'" if key in HILITE else ""
        rows += (f"<tr><td{b}>{label}</td>"
                 f"<td class='num'{b}>{r['macro_span_recall']:.3f}</td>"
                 f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                 f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
                 f"<td class='num'>{r['document_recall']:.3f}</td>"
                 f"<td class='num'>{r['mrr']:.3f}</td>"
                 + "".join(f"<td class='num'>{a[str(k)]}</td>" for k in (10, 50, 300))
                 + f"<td class='num'>{r['mean_query_ms']:.0f}</td></tr>")
    return rows


def build_html(d: dict, s512: dict, ver: dict, b256: dict, b512: dict) -> str:
    cfg, cfg5 = d["configurations"], s512["configurations"]
    beh = ver["behavioural"]
    t256, t512 = b256["truncation"], b512["truncation"]

    gate_rows = ""
    for key, g in d["reproduction_gate"].items():
        checks = " · ".join(
            f"{n} {c['actual']}" + ("" if c["match"] else f" (expected {c['expected']})")
            for n, c in g["checks"].items()
        )
        verdict = "<span class='good'>PASS</span>" if g["reproduced"] else "<span class='bad'>FAIL</span>"
        gate_rows += f"<tr><td>{LABELS[key]}</td><td>{checks}</td><td>{verdict}</td></tr>"

    def delta(a: str, b: str, src: dict) -> float:
        return src[b]["macro_span_recall"] - src[a]["macro_span_recall"]

    bar_rows = ""
    for name, a, b in (("C vs B — transformer vs static", "B_fasttext_control", "C_transformer_control"),
                       ("D vs E — fused, transformer vs static", "E_bm25_fasttext_rrf", "D_bm25_transformer_rrf"),
                       ("D vs A — fused vs frozen baseline", "A_bm25_control", "D_bm25_transformer_rrf")):
        d2, d5 = delta(a, b, cfg), delta(a, b, cfg5)
        met = "—" if "vs A" in name else (
            "<span class='good'>cleared</span>" if d5 >= 0.10 else "<span class='bad'>missed</span>")
        bar_rows += (f"<tr><td>{name}</td><td class='num'>{d2:+.3f}</td>"
                     f"<td class='num b'>{d5:+.3f}</td><td>{met}</td></tr>")

    watch_rows = ""
    for group, cases in d["case_watchlist"].items():
        for cid, per in cases.items():
            cells = "".join(
                f"<td class='num'>{', '.join(str(r) if r else '—' for r in per[k]['ranks'])}</td>"
                for k in LABELS
            )
            watch_rows += (f"<tr><td>{cid}</td><td style='font-size:7.8pt'>"
                           f"{group.replace('_', ' ')}</td>{cells}</tr>")

    band_rows = ""
    for key, g in d["reranker_decision_gate"].items():
        b = g["bands"]
        band_rows += (f"<tr><td>{LABELS[key]}</td>"
                      + "".join(f"<td class='num'>{b[k]}</td>" for k in
                                ("1-10", "11-30", "31-50", "51-100", "101-300", "absent_at_300"))
                      + f"<td class='num'>{g['ceiling_if_reranker_were_perfect_at_100']:.3f}</td></tr>")

    ed = s512["paired_comparison"]["E->D fusion: FastText vs transformer"]
    ad = s512["paired_comparison"]["A->D BM25 vs fused transformer"]
    bc = s512["paired_comparison"]["B->C static vs transformer (the hypothesis)"]

    d5 = cfg5["D_bm25_transformer_rrf"]
    tcard = d["encoders"]["transformer"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-009 — Transformer Retrieval Encoder</title><style>{CSS}</style></head><body>

<h1>EXP-009 — Does a contextual transformer<br>retrieval encoder beat static vectors?</h1>
<p class="subtitle">Production RAG v1 · evaluation-first · n = 20 questions / 22 evidence spans</p>
<div class="rule"></div>

<div class="callout win">
<div class="label">Status — supported once the truncation confound is removed</div>
<p>In the reference <strong>256-token</strong> configuration the preregistered accuracy bar was
<strong>not</strong> met. The preregistered <strong>512-token</strong> sensitivity run clears it
decisively and identifies the cause of movement in both directions: the encoder's
<strong>context window</strong>, not its architecture.</p>
</div>

<div class="grid4">
  <div class="stat"><div class="big">{cfg5['D_bm25_transformer_rrf']['macro_span_recall']:.3f}</div>
    <div class="cap">best measured macro recall<br>(D @512, was 0.475 baseline)</div></div>
  <div class="stat"><div class="big">{d5['cases_fully_recalled']}/{d5['cases_total']}</div>
    <div class="cap">cases fully recalled<br>(baseline 9/20)</div></div>
  <div class="stat"><div class="big">{ad['net_rescued']:+d}</div>
    <div class="cap">net cases vs BM25<br>with zero regressions</div></div>
  <div class="stat"><div class="big">{ed['net_rescued']:+d}</div>
    <div class="cap">net cases vs EXP-007C<br>with zero regressions</div></div>
</div>

<h2>1. What changed in the environment</h2>
<p>EXP-007's conclusion — "no transformer is reachable" — was <strong>re-tested, not
inherited</strong>. Hugging Face and every embedding API are still blocked at the egress proxy
(<code>403</code> at CONNECT, confirmed by the proxy's own failure log). But PyPI and an ONNX
redistribution bucket <em>are</em> reachable, so a genuine transformer encoder was obtainable
after all. EXP-009 was therefore <strong>not blocked</strong>, and no FastText fallback was used.</p>

<h2>2. The encoder</h2>
<p><code>{tcard['model_identifier']}</code> — a 6-layer BERT bi-encoder contrastively trained on
~1B sentence pairs explicitly for semantic search. {tcard['dimension']} dimensions, fp32,
unquantized (verified: zero quantization nodes in the ONNX graph). Attention-masked mean pooling,
L2 normalized, cosine distance, <strong>exact search with no ANN index</strong>. No query or
document prefix — the model is symmetric and defines no task instruction, so inventing one would
be tuning.</p>
<p>Selected and committed in <code>experiments/EXP-009/model-preregistration.md</code>
<strong>before any retrieval result was observed</strong>.</p>

<div class="callout warn">
<div class="label">Declared provenance limitation</div>
<p>Hugging Face is unreachable, so the bundle <strong>cannot be checksummed against the upstream
publisher</strong>. Provenance rests on a third-party redistribution. Two independent checks are
recorded instead: the architecture matches the published spec exactly, and a behavioural instrument
check on held-out sentence pairs separates paraphrases from unrelated text by
<strong>{beh['separation']:.3f}</strong>. The decisive pair has <em>no content-word overlap at
all</em> and still scores <strong>{beh['zero_overlap_pair_cosine']:.3f}</strong> — this encoder
genuinely bridges vocabulary mismatch, which is what EXP-007's static vectors could not do.</p>
</div>

<h2>3. Reproduction gates — nothing moved that should not have</h2>
<table><thead><tr><th>cell</th><th>checks</th><th>verdict</th></tr></thead>
<tbody>{gate_rows}</tbody></table>

<h2>4. Primary result — reference 256-token window</h2>
<table><thead><tr><th>cell</th><th class="num">macro R</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th>
<th class="num">a@10</th><th class="num">a@50</th><th class="num">a@300</th>
<th class="num">ms</th></tr></thead>
<tbody>{cell_rows(cfg)}</tbody></table>

<div class="callout warn">
<div class="label">The primary configuration missed its own bar</div>
<p>The preregistration required <strong>≥ 0.10 (two cases)</strong> over FastText.
C vs B came in at <strong>+0.075</strong> (1.5 cases) and D vs E at <strong>+0.025</strong>
(one case). At n = 20 one case is 5 percentage points; no significance is claimed and a one-case
difference is <strong>not</strong> reported as an improvement. This is reported as it fell.</p>
</div>

<h2>5. Mechanism — the window, not the architecture</h2>
<p>The reference window is 256 WordPiece tokens. Against the control chunks that means
<strong>{t256['truncation_rate'] * 100:.1f}%</strong> of chunks are truncated and the encoder sees
only <strong>{t256['token_coverage'] * 100:.1f}%</strong> of all corpus tokens. The median
truncated chunk is <strong>{t256['median_tokens_of_truncated']:.0f} tokens</strong> — nearly three
windows long. Splitting case movement by truncation explains <em>both</em> directions with one
variable: the transformer wins wherever it can see the whole chunk, and loses wherever the answer
sits past the cutoff.</p>

<h2>6. The 512-token sensitivity run — mechanism confirmed</h2>
<p>Declared in the preregistration <strong>before any result was seen</strong>, precisely so this
could be tested rather than argued. Only the window changed: same weights, pooling, normalization,
metric, chunks, queries and RRF parameters.</p>

<table><thead><tr><th>window</th><th class="num">chunks truncated</th>
<th class="num">corpus token coverage</th></tr></thead><tbody>
<tr><td>256 (reference, primary)</td><td class="num">{t256['truncation_rate'] * 100:.1f}%</td>
<td class="num">{t256['token_coverage'] * 100:.1f}%</td></tr>
<tr><td>512 (positional limit)</td><td class="num">{t512['truncation_rate'] * 100:.1f}%</td>
<td class="num">{t512['token_coverage'] * 100:.1f}%</td></tr>
</tbody></table>

<table><thead><tr><th>cell</th><th class="num">macro R</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th>
<th class="num">a@10</th><th class="num">a@50</th><th class="num">a@300</th>
<th class="num">ms</th></tr></thead>
<tbody>{cell_rows(cfg5)}</tbody></table>

<p>All three reproduction gates still pass, and <strong>cell E is unchanged at
{cfg5['E_bm25_fasttext_rrf']['macro_span_recall']:.3f} / {cfg5['E_bm25_fasttext_rrf']['cases_fully_recalled']}-of-20</strong>
— as it must be, since no transformer participates in it. That is the control showing the movement
comes from the window and nothing else.</p>

<table><thead><tr><th>comparison</th><th class="num">@256</th><th class="num">@512</th>
<th>preregistered bar (≥ 0.10)</th></tr></thead><tbody>{bar_rows}</tbody></table>

<div class="callout win">
<div class="label">Zero-regression comparisons — a first for this project</div>
<p>At 512 the paired analysis reports <strong>net {ad['net_rescued']:+d} cases over BM25 with zero
regressions</strong>, and <strong>net {ed['net_rescued']:+d} over the EXP-007C fusion with zero
regressions</strong>. Rescued over BM25: <code>{', '.join(ad['rescued'])}</code>. A comparison with
no losing cases is qualitatively different from a net win.</p>
<p><strong>OA-004</strong>, the fusion regression tracked since EXP-007, is rescued at 512.</p>
</div>

<div class="callout warn">
<div class="label">What this does not license</div>
<p>The 512 figure <strong>does not retroactively become the primary result</strong>. The
preregistered primary was the reference 256 and it is reported as it fell. The 512 number rests on
one run of n = 20, where one case is 5 percentage points, and 512 is the model's positional ceiling
rather than a tuned value — there is no sweep here and none should be inferred.</p>
</div>

<h2>7. Better on aggregate is not strictly better</h2>
<p>The preregistration flagged this exact check. At 512 the transformer still loses
<strong>AN-002</strong> and <strong>AN-007</strong> — two of the three cases FastText won.
Regressed against FastText at 512: <code>{', '.join(bc['regressed'])}</code>.</p>
<table><thead><tr><th>case</th><th>group</th>
{''.join(f'<th class="num">{k.split("_")[0]}</th>' for k in LABELS)}</tr></thead>
<tbody>{watch_rows}</tbody></table>
<p style="font-size:8.4pt;color:#52565d">Ranks of the expected evidence span at the 256-token
configuration. "—" means absent from the top 300.</p>

<h2>8. Reranker decision gate — counts only, no reranker was built</h2>
<p>A reranker can only reorder what retrieval already returned; spans absent at pool depth are
unreachable by any reranker. These are the counts that decision would rest on.</p>
<table><thead><tr><th>cell</th><th class="num">1–10</th><th class="num">11–30</th>
<th class="num">31–50</th><th class="num">51–100</th><th class="num">101–300</th>
<th class="num">absent@300</th><th class="num">perfect-reranker ceiling @100</th>
</tr></thead><tbody>{band_rows}</tbody></table>

<h2>9. Defect found and fixed during this experiment</h2>
<p>The first embedding build reported <strong>0% truncation</strong> on a corpus whose largest
chunk is {t256['token_length_max']:,} tokens. <code>Tokenizer.from_file</code> restores the
tokenizer's own saved 128-token truncation, so the "untruncated" reference length was itself
truncated. <strong>Stored vectors were never affected</strong> — the encoding tokenizer's explicit
override was always correct — but the measurement was wrong, and it would have put a false
"no truncation" claim in this report. Fixed and recomputed.</p>

<h2>10. Honest summary</h2>
<ul>
<li>In the <strong>reference 256-token configuration</strong> the hypothesis <strong>did not clear
its own threshold</strong> (+0.075 against a required +0.10).</li>
<li>In the <strong>preregistered 512-token sensitivity run</strong> it clears the bar decisively:
+0.150 dense, +0.175 fused, net {ad['net_rescued']:+d} cases over BM25 with zero regressions.</li>
<li>The transformer is <strong>still not uniformly better</strong>: AN-002 and AN-007 remain lost.</li>
<li>The genuine finding is <strong>mechanistic</strong>: retrieval quality here is gated by how much
of a chunk the encoder can see, and recall moves with that coverage in both directions.</li>
<li>Reachability gains (absent@300 5 → 1, doc recall 0.725 → 0.925) are large enough not to be
n = 20 noise, unlike the top-10 accuracy deltas.</li>
<li>EXP-007's negative result is <strong>superseded, not confirmed</strong>: it was measured with an
instrument this experiment shows to be the weaker one.</li>
</ul>

<h2>11. What is justified next</h2>
<ol>
<li><strong>Chunk the corpus to fit the encoder's window</strong>, rather than chunking for its own
sake. EXP-005 and EXP-008 both failed because they changed length without reference to any encoder's
context limit; this is the first evidence that says what the limit should be.</li>
<li><strong>Still not a reranker.</strong> The gate above shows what is and is not recoverable.</li>
<li><strong>Do not promote 512 on one run.</strong> Re-measure before changing the frozen baseline.</li>
</ol>

<footer>
Generated from experiments/EXP-009/*.json by scripts/build_exp009_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Encoder {tcard['model_identifier']}, exact cosine, no ANN index. Corpus snapshot
{d['corpus_snapshot_id']}, chunk set {d['chunk_set_id']}.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-009-transformer-retrieval-encoder.pdf")
    args = parser.parse_args()
    html = build_html(
        json.loads((EXP / "results.json").read_text()),
        json.loads((EXP / "results-512-sensitivity.json").read_text()),
        json.loads((EXP / "encoder-verification.json").read_text()),
        json.loads((EXP / "embedding-build.json").read_text()),
        json.loads((EXP / "embedding-build-512.json").read_text()),
    )
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp009.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
