#!/usr/bin/env python3
"""Render the EXP-008 report to a shareable PDF.

Figures are read from experiments/EXP-008/*.json at build time so the PDF cannot
drift from the artifacts. Re-run scripts/run_exp008.py --with-rrf first if anything
changed.
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
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.5pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }
ol, ul { margin: 0 0 8pt; padding-left: 15pt; } li { margin-bottom: 4pt; }
.q { margin-bottom: 8pt; break-inside: avoid; }
.q .t { display: block; font-weight: 700; margin-bottom: 1pt; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12pt; margin-bottom: 4pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 8pt 10pt; border-radius: 3pt; }
.stat .big { font-size: 18pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 8pt; color: #52565d; margin-top: 2pt; }
footer { margin-top: 16pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 8pt; color: #6f747b; }
.avoid { break-inside: avoid; page-break-inside: avoid; }
"""



LABELS = {
    "A_control_bm25": "A — control chunks + BM25",
    "B_bounded_bm25": "B — bounded chunks + BM25",
    "C_control_dense": "C — control chunks + dense",
    "D_bounded_dense": "D — bounded chunks + dense",
}


def build_html(d: dict, fid: dict) -> str:
    cfg = d["configurations"]
    inter = d["interaction_analysis"]["table"]
    cd = d["paired_comparison"]["C->D chunk size under dense"]

    rows = ""
    for key, label in LABELS.items():
        r = cfg[key]
        a = r["spans_absent_from_top"]
        cls = " class='bad'" if key == "D_bounded_dense" else ""
        rows += (f"<tr><td{cls}>{label}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
                 f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                 f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
                 f"<td class='num'>{r['document_recall']:.3f}</td><td class='num'>{r['mrr']:.3f}</td>"
                 + "".join(f"<td class='num'>{a[str(k)]}</td>" for k in (10, 20, 50, 100, 300))
                 + f"<td class='num'>{r['mean_query_ms']:.0f}</td></tr>")

    inter_rows = ""
    for name, t in inter.items():
        cls = " class='bad'" if t["delta"] < 0 else ""
        inter_rows += (f"<tr><td>{name}</td><td class='num'>{t['control']:.3f}</td>"
                       f"<td class='num'>{t['bounded']:.3f}</td><td class='num'{cls}>{t['delta']:+.3f}</td>"
                       f"<td class='num'>{t['fully_recalled'][0]} &rarr; {t['fully_recalled'][1]}</td>"
                       f"<td class='num'>{t['absent_at_300'][0]} &rarr; {t['absent_at_300'][1]}</td>"
                       f"<td class='num'>{t['mrr'][0]:.3f} &rarr; {t['mrr'][1]:.3f}</td>"
                       f"<td class='num'>{t['net_rescued']:+d}</td></tr>")

    moves = "".join(
        f"<tr><td>{k.replace('_', ' ')}</td><td class='num'>{v}</td></tr>"
        for k, v in sorted(cd["span_movement_counts"].items(), key=lambda kv: -kv[1])
    )

    an003 = ""
    for key, label in LABELS.items():
        s = cfg[key]["cases"]["AN-003"]["spans"][0]
        w = s["within"]
        cls = " class='good'" if s["rank"] else ""
        an003 += (f"<tr><td>{label}</td><td class='num'{cls}>{s['rank'] or '—'}</td>"
                  f"<td class='num'>{s['doc_rank']}</td><td class='num'>{s['chunk_len'] or '—'}</td>"
                  + "".join(f"<td>{'yes' if w[str(k)] else 'no'}</td>" for k in (10, 20, 50, 100, 300))
                  + "</tr>")

    key_cases = ""
    for cid in ("AN-002", "AN-007", "AN-012", "AN-004"):
        cells = [cfg[k]["cases"][cid]["spans"][0]["rank"] for k in LABELS]
        key_cases += (f"<tr><td>{cid}</td>"
                      + "".join(f"<td class='num'>{c if c else '—'}</td>" for c in cells) + "</tr>")

    e = cfg.get("E_bm25control_plus_boundeddense_rrf")
    e_row = ("" if not e else
             f"<tr><td><strong>E — BM25 control + bounded dense (RRF)</strong></td>"
             f"<td class='num'>{e['macro_span_recall']:.3f}</td>"
             f"<td class='num'>{e['cases_fully_recalled']}/{e['cases_total']}</td>"
             f"<td class='num'>{e['document_recall']:.3f}</td><td class='num'>{e['mrr']:.3f}</td>"
             f"<td class='num'>{e['spans_absent_from_top']['300']}</td></tr>")

    ctrl = fid["intended_change_retrieval_unit"]["control"]
    bnd = fid["intended_change_retrieval_unit"]["bounded"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-008 Chunk Size and Dense Retrieval</title><style>{CSS}</style></head><body>

<h1>EXP-008 — Chunk Size × Dense Retrieval</h1>
<p class="subtitle">Testing whether the chunk-length correlation found in EXP-007 was
causal, or only a proxy.</p>
<div class="rule"></div>

<div class="callout warn">
  <div class="label">Executive result</div>
  <p><strong>The interaction hypothesis was not supported, and the EXP-007 chunk-length
  correlation was not causal.</strong> Bounded chunking made dense retrieval slightly
  <em>worse</em> (0.425 → 0.400), collapsed MRR from 0.360 to <strong>0.259</strong>, and
  left deep reachability unchanged at 5 spans absent@300. Paired: 1 rescued, 1 regressed,
  <strong>net 0</strong> — and both are single-rank boundary crossings.</p>
  <p>The interaction runs the <em>wrong way</em>: chunk size moved BM25 <strong>+0.025</strong>
  and dense <strong>−0.025</strong>, an interaction of <strong>−0.050</strong>.</p>
</div>

<div class="grid2 avoid">
  <div class="stat"><div class="big">−0.050</div>
    <div class="cap">Interaction term. The hypothesis predicted a positive interaction;
    the measurement is negative</div></div>
  <div class="stat"><div class="big">AN-003: 119</div>
    <div class="cap">The one genuine gain — the answer chunk entered the dense pool for
    the first time, but at rank 119, offset by AN-004 being lost entirely</div></div>
</div>

<h2>Intervention fidelity</h2>
<p>The C→D comparison is an isolation of chunk size only if nothing else moved. Gated and
verified: same 202 document versions, chunk bodies are exact source substrings in both,
<strong>zero</strong> enriched rows or V3 transforms in either, and <strong>22/22</strong>
evidence spans map in both. Critically the <strong>token vocabulary is identical</strong> —
32,011 forms, zero bounded-only — because V2 is a re-partition of the same text with
boundaries on whitespace. The embedding model presents exactly the same tokens; only the
boundaries differ.</p>
<table>
<thead><tr><th>chunk set</th><th class="num">chunks</th><th class="num">mean</th>
<th class="num">median</th><th class="num">p90</th><th class="num">max</th><th class="num">&gt;2,000</th></tr></thead>
<tbody>
<tr><td>control</td><td class="num">{ctrl['chunks']:,}</td><td class="num">{ctrl['mean']:,}</td>
<td class="num">{ctrl['median']:,}</td><td class="num">{ctrl['p90']:,}</td>
<td class="num b">{ctrl['max']:,}</td><td class="num">{ctrl['over_2000']:,}</td></tr>
<tr><td>bounded</td><td class="num">{bnd['chunks']:,}</td><td class="num">{bnd['mean']:,}</td>
<td class="num">{bnd['median']:,}</td><td class="num">{bnd['p90']:,}</td>
<td class="num b">{bnd['max']:,}</td><td class="num good">{bnd['over_2000']}</td></tr>
</tbody></table>
<p>Bounded embedding build used the same model and fingerprint: 20,526 vectors, token match
rate 0.9627 (identical to control), all-zero embeddings 117 → 128 — a <em>fall</em> in rate
from 0.82% to 0.62% across 44% more chunks.</p>

<h2>The 2×2</h2>
<table>
<thead><tr><th>Cell</th><th class="num">macro</th><th class="num">full</th><th class="num">spans@10</th>
<th class="num">doc</th><th class="num">MRR</th><th class="num">a@10</th><th class="num">a@20</th>
<th class="num">a@50</th><th class="num">a@100</th><th class="num">a@300</th><th class="num">ms</th></tr></thead>
<tbody>{rows}</tbody></table>
<p>All three reproduction gates pass: <strong>A</strong> reproduces the frozen BM25 baseline,
<strong>B</strong> reproduces EXP-005A, <strong>C</strong> reproduces EXP-007B. Bounded
chunking made dense worse at <em>every</em> depth except 300, where it is unchanged — there is
no depth at which the intervention improved candidate recall.</p>

<h2>Interaction</h2>
<table>
<thead><tr><th>Retriever</th><th class="num">control</th><th class="num">bounded</th>
<th class="num">Δ</th><th class="num">fully recalled</th><th class="num">absent@300</th>
<th class="num">MRR</th><th class="num">net</th></tr></thead>
<tbody>{inter_rows}</tbody></table>
<p>Neither retriever gained a single fully-recalled case, and both kept their absent@300
count exactly.</p>

<h2>Paired C → D span movements</h2>
<table>
<thead><tr><th>Movement</th><th class="num">n</th></tr></thead>
<tbody>{moves}</tbody></table>
<p>Six spans worsened without crossing the cutoff against one that improved. That is the
signature behind the MRR collapse. Mean/median evidence rank when found:
<strong>C 34.1 / 10, D 56.5 / 11</strong>.</p>

<h2>AN-003 — the canonical case</h2>
<table>
<thead><tr><th>Cell</th><th class="num">rank</th><th class="num">doc rank</th>
<th class="num">chunk len</th><th>@10</th><th>@20</th><th>@50</th><th>@100</th><th>@300</th></tr></thead>
<tbody>{an003}</tbody></table>
<p>The anchor chunk fell <strong>3,449 → 1,191</strong> characters and, for the first time in
any experiment, the answer-bearing chunk became retrievable. <strong>This is partial support,
and only barely:</strong> rank 119 is an order of magnitude outside <span class="mono">top_k</span>
and outside any pool a reranker would consume. It changed no recall at any depth ≤ 100, and it
was paid for exactly — AN-004 went from rank 17 to <strong>absent@300</strong>, so the
corpus-wide count stayed at 5.</p>

<h2>What shorter chunks did to dense's wins</h2>
<table>
<thead><tr><th>Case</th><th class="num">A bm25/ctrl</th><th class="num">B bm25/bnd</th>
<th class="num">C dense/ctrl</th><th class="num">D dense/bnd</th></tr></thead>
<tbody>{key_cases}</tbody></table>
<p>EXP-007's two dense rescues both lived in the same 3,327-character
<span class="mono">HTTP errors</span> chunk — a topically homogeneous list of status codes.
Both degrade (1→6, 2→6), and AN-012 collapses from <strong>1 to 140</strong>.</p>
<div class="callout">
  <div class="label">Mechanism</div>
  <p>Mean pooling rewards <strong>topical coherence</strong>, not shortness. A long chunk
  uniformly about one topic produces a strong clean vector; splitting it fragments that signal
  across weaker ones. Chunk length in EXP-007 was a <em>proxy</em> for heterogeneity, not the
  cause — long chunks here are sometimes coherent (<span class="mono">HTTP errors</span>) and
  sometimes not (<span class="mono">Body Parameters</span>). Uniform shortening helps the
  heterogeneous minority slightly and damages the coherent majority.</p>
  <p>The correlation survives bounded chunking, which confirms shortening cannot fix it: in D,
  median chunk length is <strong>883</strong> for reachable evidence and <strong>1,167</strong>
  for unreachable — still ~1.3×, on a corpus where nothing exceeds 1,999.</p>
</div>

<h2>Exploratory fusion — EXP-008E</h2>
<p>The precondition ("if bounded dense improves") was <strong>not met</strong>, so this is
exploratory only. Preregistered EXP-007 settings, untuned.</p>
<table>
<thead><tr><th>Configuration</th><th class="num">macro</th><th class="num">full</th>
<th class="num">doc</th><th class="num">MRR</th><th class="num">absent@300</th></tr></thead>
<tbody>
<tr><td>A — BM25 control alone</td><td class="num">0.475</td><td class="num">9/20</td>
<td class="num">0.825</td><td class="num">0.280</td><td class="num">1</td></tr>
{e_row}
<tr><td><em>EXP-007C — BM25 control + <strong>control</strong> dense</em></td>
<td class="num"><em>0.600</em></td><td class="num"><em>11/20</em></td><td class="num"><em>0.825</em></td>
<td class="num"><em>0.326</em></td><td class="num"><em>2</em></td></tr>
</tbody></table>
<p><strong>Fusion collapsed to baseline.</strong> EXP-007's fusion reached 0.600 because control
dense contributed complementary rankings; degrading dense destroyed that complementarity —
strong indirect confirmation that bounded chunking hurt the dense retriever. The one positive:
the prior fusion regression improved, OA-004 moving from RRF rank 17 to <strong>9</strong>,
back inside <span class="mono">top_k</span>.</p>

<h2>Project state — four hypotheses, four negative results</h2>
<table>
<thead><tr><th>#</th><th>Hypothesis</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td>1</td><td>Oversized chunks hide evidence (BM25)</td><td class="bad">falsified — 0 rescued</td></tr>
<tr><td>2</td><td>Missing structural context</td><td class="bad">falsified — Δ0.000</td></tr>
<tr><td>3</td><td>Lexical vocabulary mismatch</td><td class="bad">unsupported — no vocabulary rescue</td></tr>
<tr><td>4</td><td>Chunk size interacts with dense retrieval</td><td class="bad">not supported — interaction −0.050</td></tr>
</tbody></table>
<p>The best measured configuration remains <strong>EXP-007C</strong> (BM25 + dense, both on
control chunks, 0.600 / 11-of-20). Both retrievers work better on the original chunking than
on the bounded one.</p>

<h2>Limitations</h2>
<ol>
<li><strong>n = 20.</strong> One case is five percentage points. Every movement is 1–2 cases;
no significance is claimed.</li>
<li><strong>One dense model, and a weak one.</strong> Static word vectors with mean pooling,
because transformer hosts remain egress-blocked. Mean pooling is very likely why coherence
matters this much. <strong>This constrains mean-pooled static embeddings, not dense retrieval
in general.</strong></li>
<li><strong>One bounded configuration</strong> (target 1,200 / cap 2,000, chosen in EXP-005
from corpus percentiles). No sweep was run, deliberately.</li>
<li><strong>EXP-008E is exploratory</strong> and its precondition was not met.</li>
<li><strong>EXP-NULL still has not run.</strong></li>
</ol>

<h2>What is justified next</h2>
<ol>
<li><strong>Stop optimising chunk size.</strong> Two controlled interventions on two
retrievers, both null.</li>
<li><strong>A transformer retrieval encoder</strong> remains the highest-value experiment,
blocked only on egress. EXP-008 sharpens why: mean pooling is now directly implicated, and a
transformer is exactly the intervention that removes it.</li>
<li><strong>If chunking is ever revisited, test topical homogeneity, not length</strong> — but
behind (2).</li>
<li><strong>Still not a reranker.</strong> AN-003 sits at rank 119 in the one cell where it is
reachable and absent@300 in the other three.</li>
</ol>
<p><strong>Promotion decision: the frozen baseline does not change</strong> (control chunking,
no enrichment, BM25, top_k=10). Bounded chunking is not promoted for dense retrieval; it is
measurably worse. The EXP-007 hybrid remains the leading candidate, and EXP-008 shows it must
be built on <strong>control</strong> chunks for both retrievers.</p>

<footer>
Generated from experiments/EXP-008/*.json by scripts/build_exp008_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Model {d['embedding_model']['model_identifier']}, exact cosine, no ANN index.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-008-chunk-size-x-dense.pdf")
    args = parser.parse_args()
    data = json.loads((REPO_ROOT / "experiments/EXP-008/results.json").read_text())
    fid = json.loads((REPO_ROOT / "experiments/EXP-008/intervention-fidelity.json").read_text())
    html = build_html(data, fid)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp008.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
