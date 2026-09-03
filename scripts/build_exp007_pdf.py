#!/usr/bin/env python3
"""Render the EXP-007 report to a shareable PDF.

Figures are read from experiments/EXP-007/*.json at build time so the PDF cannot
drift from the artifacts. Re-run scripts/run_exp007.py first if anything changed.
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
    "EXP-007A_bm25_control": "A — BM25 control",
    "EXP-007B_pretrained_dense": "B — pretrained dense",
    "EXP-007C_bm25_dense_rrf": "C — BM25 + dense RRF",
}


def build_html(d: dict, sem: dict) -> str:
    cfg = d["configurations"]
    pr = d["paired_results"]
    m = d["embedding_model"]

    rows = ""
    for key, label in LABELS.items():
        r = cfg[key]
        a = r["spans_absent_from_top"]
        cls = " class='good'" if key.endswith("rrf") else (" class='bad'" if key.endswith("dense") else "")
        rows += (
            f"<tr><td{cls}>{label}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
            f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
            f"<td class='num'>{r['spans_found_at_10']}/{r['spans_total']}</td>"
            f"<td class='num'>{r['document_recall']:.3f}</td><td class='num'>{r['mrr']:.3f}</td>"
            f"<td class='num'>{a['10']}</td><td class='num'>{a['20']}</td><td class='num'>{a['50']}</td>"
            f"<td class='num'>{a['100']}</td><td class='num'>{a['300']}</td>"
            f"<td class='num'>{r['mean_query_ms']:.0f}</td></tr>"
        )

    pairs = ""
    for name, c in pr.items():
        pairs += (
            f"<tr><td>{name}</td><td class='num'>{c['macro_recall_delta']:+.3f}</td>"
            f"<td>{', '.join(c['rescued']) or '—'}</td><td>{', '.join(c['regressed']) or '—'}</td>"
            f"<td class='num'>{c['net_rescued']:+d}</td></tr>"
        )

    quad = pr["BM25 -> dense"]["quadrant"]
    quad_rows = "".join(
        f"<tr><td>{label}</td><td class='num'>{len(quad[key])}</td><td>{', '.join(quad[key]) or '—'}</td></tr>"
        for key, label in (("both_correct", "BM25 correct / dense correct"),
                           ("only_a", "BM25 correct / dense wrong"),
                           ("only_b", "BM25 wrong / dense correct"),
                           ("neither", "both wrong"))
    )

    ranks = ""
    for cid in cfg["EXP-007A_bm25_control"]["cases"]:
        cells = []
        for key in LABELS:
            sp = cfg[key]["cases"][cid]["spans"]
            cells.append(",".join(str(s["rank"]) if s["rank"] else "—" for s in sp))
        cat = cfg["EXP-007A_bm25_control"]["cases"][cid]["category"]
        hl = " class='b'" if cid == "AN-003" else ""
        ranks += (f"<tr><td{hl}>{cid}</td><td>{cat}</td>"
                  + "".join(f"<td class='num'>{c}</td>" for c in cells) + "</tr>")

    an003 = ""
    for key, label in LABELS.items():
        s = cfg[key]["cases"]["AN-003"]["spans"][0]
        w = s["within"]
        an003 += (f"<tr><td>{label}</td><td class='num'>{s['rank'] or '—'}</td>"
                  f"<td class='num'>{s['doc_rank']}</td>"
                  + "".join(f"<td>{'yes' if w[str(k)] else 'no'}</td>" for k in (10, 20, 50, 100, 300))
                  + "</tr>")

    sc = sem["semantic_contribution_analysis"]
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-007 Pretrained Semantic Retrieval</title><style>{CSS}</style></head><body>

<h1>EXP-007 — Pretrained Semantic Retrieval</h1>
<p class="subtitle">Testing whether a genuinely pretrained embedding model bridges the
vocabulary gap that BM25 cannot.</p>
<div class="rule"></div>

<div class="callout warn">
  <div class="label">Executive result</div>
  <p><strong>The vocabulary-mismatch hypothesis was not supported.</strong> Standalone
  dense retrieval is worse than BM25 (0.425 vs 0.475) and far worse at depth — 5 spans
  unreachable at 300 against BM25's 1. <strong>Neither of its two rescues was a
  vocabulary rescue</strong>: both already had ≥92% of their query terms present.
  <strong>AN-003, the canonical case, was not rescued.</strong></p>
  <p>The unexpected finding is complementarity. <strong>BM25 + dense RRF reaches 0.600
  and 11/20</strong> — the best configuration measured in this project — because the
  two retrievers fail on different questions.</p>
</div>

<div class="grid2 avoid">
  <div class="stat"><div class="big">0.920</div>
    <div class="cap">Mean lexical overlap of the spans dense "rescued" — the query terms
    were already there, so this was a ranking fix, not a vocabulary fix</div></div>
  <div class="stat"><div class="big">AN-003: —</div>
    <div class="cap">Still absent at depth 300 under dense, though dense ranked its
    <em>document</em> first</div></div>
</div>

<h2>Model, selected before any result was seen</h2>
<table>
<tr><td style="width:30%">identifier</td><td><span class="mono">{m['model_identifier']}</span> ({m['provider']})</td></tr>
<tr><td>origin / revision</td><td>{m['origin']}<br><span class="mono">{m['revision'][:78]}…</span></td></tr>
<tr><td>training corpus</td><td>{m['training_corpus']}</td></tr>
<tr><td>dimension / metric</td><td>{m['dimension']}, {m['distance_metric']}; pooling: {m['pooling']}</td></tr>
<tr><td>corpus-fitted?</td><td class="good">No — trained entirely independently of this project</td></tr>
</table>
<p><strong>Why not a transformer encoder:</strong> measured, not assumed —
<span class="mono">huggingface.co</span> returns <span class="mono">CONNECT tunnel failed,
403</span>, and every embedding API is equally blocked. GitHub release assets are
reachable, which is how a pretrained model was obtained at all. Corpus-fitted TF-IDF+SVD
was forbidden and was not used.</p>

<div class="callout">
  <div class="label">Instrument strength — this qualifies the negative result</div>
  <p>This is a genuinely pretrained model but a <strong>static word-embedding</strong> one.
  Mean-pooled static vectors are order-insensitive and wash out over long chunks. A
  positive result would have been strong evidence; the negative result obtained is
  <strong>weak</strong> evidence against the hypothesis. It shows this class of embedding
  cannot bridge the gap — not that a transformer could not. The hypothesis is
  <strong>unsupported, not falsified</strong>.</p>
</div>

<h2>Results</h2>
<table>
<thead><tr><th>Configuration</th><th class="num">macro</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc</th><th class="num">MRR</th>
<th class="num">a@10</th><th class="num">a@20</th><th class="num">a@50</th>
<th class="num">a@100</th><th class="num">a@300</th><th class="num">ms</th></tr></thead>
<tbody>{rows}</tbody></table>
<p>Dense has the <strong>highest MRR</strong> despite the lowest macro recall — when it
finds evidence it ranks it near the top — but the <strong>worst deep reachability</strong>.
EXP-007A reproduced the frozen BM25 baseline exactly (0.475, 9/20, identical hit ordering),
so the comparison is sound.</p>

<h2>BM25 vs dense — paired</h2>
<table>
<thead><tr><th>Quadrant</th><th class="num">n</th><th>cases</th></tr></thead>
<tbody>{quad_rows}</tbody></table>
<table>
<thead><tr><th>Comparison</th><th class="num">Δ macro</th><th>rescued</th><th>regressed</th><th class="num">net</th></tr></thead>
<tbody>{pairs}</tbody></table>

<h2>What dense actually bought</h2>
<p>{sc['headline']}</p>
<table>
<thead><tr><th>Rescue</th><th>BM25 → dense</th><th class="num">lexical overlap</th><th>mechanism</th></tr></thead>
<tbody>
<tr><td>AN-002</td><td>27 → 1</td><td class="num">12/13</td><td>topical coherence, not a vocabulary gap</td></tr>
<tr><td>AN-007</td><td>18 → 2</td><td class="num">11/12</td><td>topical coherence, not a vocabulary gap</td></tr>
</tbody></table>
<p>Both live in the same 3,327-character <span class="mono">HTTP errors</span> chunk — a
homogeneous list of status codes. BM25 ranked it 27th and 18th because its length
normalization penalises a long chunk; dense matched the chunk's topic to the query's.
<strong>Dense fixed a BM25 ranking failure, not a lexical coverage failure.</strong></p>

<h2>Per-question ranks</h2>
<table>
<thead><tr><th>Case</th><th>Category</th><th class="num">BM25</th><th class="num">dense</th><th class="num">RRF</th></tr></thead>
<tbody>{ranks}</tbody></table>

<h2>AN-003 — the canonical case</h2>
<table>
<thead><tr><th>Retriever</th><th class="num">evidence rank</th><th class="num">doc rank</th>
<th>@10</th><th>@20</th><th>@50</th><th>@100</th><th>@300</th></tr></thead>
<tbody>{an003}</tbody></table>
<p><strong>Outcome: failure.</strong> But the trace shows why, and it is not what the
hypothesis predicted. Dense put the correct <em>document</em> at rank 1 (BM25: 6) and its
top five hits were all <span class="mono">Create a Message Batch</span> chunks at cosine
<strong>0.9417</strong> — the model <em>did</em> associate the query with the right
material. It failed to surface the answer because that chunk is 3,449 characters of
heterogeneous parameter documentation and its mean-pooled vector is diluted.</p>
<p>The evidence never entered a rerankable range under any configuration, so
<strong>a reranker could not rescue AN-003.</strong></p>
<p><strong>New observation:</strong> chunk length predicts dense reachability (median 897
chars reachable vs 1,754 unreachable) in a way it did not predict BM25 reachability.
EXP-005 tested chunk size against BM25 alone and found nothing; it has never been tested
against dense retrieval.</p>

<h2>Fusion</h2>
<p>Preregistered before any result: pool 50 per retriever, <span class="mono">rrf_k=60</span>,
<span class="mono">top_k=10</span>. Not tuned; no sweep run. RRF beats both parents and
restores what each broke — AN-005 (dense lost it entirely) returns at rank 8, OA-007 at
rank 2.</p>
<p><strong>The fusion regression the brief warned about did occur:</strong> OA-004 sits at
BM25 rank 5, dense rank 73, and <strong>RRF rank 17</strong> — dragged outside
<span class="mono">top_k</span> by a weak dense rank. One case, reported rather than
absorbed into the average.</p>

<h2>EXP-NULL — still blocked</h2>
<p>Retried. Still no generation credential and the provider host is egress-blocked; the
results file records <span class="mono">status: "blocked"</span> with the exact error.
Retrieval remains uncalibrated against what the model already knows.</p>

<h2>Updated root-cause conclusion</h2>
<table>
<thead><tr><th>#</th><th>Hypothesis</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td>1</td><td>Oversized chunks hide evidence</td><td class="bad">falsified — 0 rescued</td></tr>
<tr><td>2</td><td>Missing structural context</td><td class="bad">falsified — Δ0.000</td></tr>
<tr><td>3</td><td>Lexical vocabulary mismatch</td><td class="bad">unsupported — no rescue was a vocabulary rescue; canonical case failed</td></tr>
</tbody></table>
<p>What EXP-007 established instead: <strong>BM25 and dense fail on disjoint questions.</strong>
The residual failures look less like a vocabulary problem and more like a
<strong>retrieval-unit</strong> problem — AN-003's evidence is a 57-character sentence
inside a 3,449-character heterogeneous chunk, and both retrievers fail on it for their own
reasons.</p>

<h2>Limitations</h2>
<ol>
<li><strong>The instrument is weak</strong> — static vectors, not a transformer encoder,
because every transformer host is blocked. The negative result is weak evidence.</li>
<li><strong>n = 20.</strong> One case is five percentage points of macro recall. Every
movement here is 1–3 cases. Nothing supports "dense beats BM25" or the reverse in general.</li>
<li><strong>Mean pooling is crude</strong> and order-insensitive; some failures are the
pooling, not the vectors.</li>
<li><strong>117 chunks (0.8%) have all-zero embeddings</strong> and are unreachable by dense.</li>
<li><strong>EXP-NULL never ran.</strong></li>
<li><strong>No parameter was swept</strong>; BM25 and RRF settings are fixed.</li>
</ol>

<h2>What is justified next</h2>
<ol>
<li><strong>Bounded chunking × dense retrieval.</strong> The strongest lead: EXP-005 already
built the bounded chunk set, and EXP-007 shows dense reachability tracks chunk size. A cheap
2×2 that directly targets AN-003.</li>
<li><strong>A transformer retrieval encoder, if egress ever permits.</strong> The hypothesis
is unsupported, not falsified, and the instrument is the reason.</li>
<li><strong>Not a reranker.</strong> AN-003 is absent at depth 300 under every configuration
including fusion. The condition that would justify one — evidence routinely at rank 15–100
but not top 10 — is not what the data shows.</li>
</ol>
<p><strong>Promotion decision: the frozen baseline does not change</strong> (control chunking,
no enrichment, BM25, top_k=10). RRF is the best-measured configuration and the leading
candidate, but it is a +2-case movement on a 20-case development set, it carries a real
regression, and it doubles latency. Not enough to change a production baseline.</p>

<footer>
Generated from experiments/EXP-007/*.json by scripts/build_exp007_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
Snapshot {d['corpus_snapshot_id']}; chunk set {d['chunker']['chunk_set_id']}, enrichment none.
Exact cosine search, no ANN index. Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-007-pretrained-semantic-retrieval.pdf")
    args = parser.parse_args()
    data = json.loads((REPO_ROOT / "experiments/EXP-007/results.json").read_text())
    sem = json.loads((REPO_ROOT / "experiments/EXP-007/semantic-contribution.json").read_text())
    html = build_html(data, sem)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp007.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
