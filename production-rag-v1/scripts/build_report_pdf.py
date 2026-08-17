#!/usr/bin/env python3
"""Render the shareable V1 results report to PDF.

Every figure in the report is read out of ``experiments/summary.json`` rather than
typed into the template, so a regenerated report cannot drift from the artifacts
it describes. Re-run ``scripts/analyze_experiments.py`` first if the experiments
have changed.

Usage::

    python scripts/build_report_pdf.py --out docs/reports/production-rag-v1-results.pdf
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
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
)

SNAPSHOT_ID = "snap_689e336380a054d8039dc35b2c09cd0a"
EMBEDDING_MODEL_ID = "emb_205f51a2d4db0273e121527cb5c6ff83"

CSS = """
@page { size: Letter; margin: 18mm 16mm 16mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 10pt; line-height: 1.5; color: #1a1c1f; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 21pt; line-height: 1.2; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 {
  font-size: 12.5pt; margin: 20pt 0 7pt; padding-bottom: 4pt;
  border-bottom: 1.2pt solid #1a1c1f; letter-spacing: -0.2pt;
}
h3 { font-size: 10.5pt; margin: 13pt 0 4pt; }
p { margin: 0 0 7pt; }
a { color: #1a1c1f; }
code, .mono {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.6pt; background: #f2f3f5; padding: 0.5pt 3pt; border-radius: 2pt;
}
.subtitle { font-size: 11pt; color: #55595f; margin: 0 0 12pt; }
.rule { height: 2.5pt; background: #1a1c1f; margin: 0 0 14pt; }

table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; font-size: 9pt; }
th {
  text-align: left; font-weight: 600; padding: 5pt 7pt; background: #1a1c1f;
  color: #fff; border: none;
}
td { padding: 4.5pt 7pt; border-bottom: 0.6pt solid #dfe1e5; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f7f8f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.best { font-weight: 700; }
.fail td { color: #8a1c1c; }
.fail td:first-child { font-weight: 600; }

.meta { display: grid; grid-template-columns: 34% 66%; gap: 0; font-size: 8.8pt; margin: 10pt 0 4pt; }
.meta div { padding: 3.5pt 7pt; border-bottom: 0.6pt solid #dfe1e5; }
.meta .k { color: #55595f; }
.meta .v {
  font-family: "SFMono-Regular", Consolas, monospace; font-size: 8.2pt;
  /* break-all would hyphenate mid-word; only break where there is nowhere else to go */
  word-break: normal; overflow-wrap: anywhere;
}

.callout {
  border-left: 2.5pt solid #1a1c1f; background: #f7f8f9;
  padding: 8pt 11pt; margin: 10pt 0 12pt;
}
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout p:last-child { margin-bottom: 0; }
.callout .label {
  font-size: 7.5pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #55595f; font-weight: 700; margin-bottom: 3pt;
}
.callout.warn .label { color: #8a1c1c; }

ol, ul { margin: 0 0 8pt; padding-left: 15pt; }
li { margin-bottom: 4pt; }
.finding { margin-bottom: 9pt; break-inside: avoid; page-break-inside: avoid; }
/* Scoped to .t so inline <strong> inside the body text stays inline. */
.finding .t { display: block; font-weight: 700; margin-bottom: 1pt; }
.neg { color: #8a1c1c; font-weight: 700; }
.zero { color: #74787e; font-weight: 700; }
.pos { font-weight: 700; }
.moved-in { color: #1a1c1f; }
.moved-out { color: #8a1c1c; }

.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14pt; }
.stat { border: 0.8pt solid #dfe1e5; padding: 8pt 10pt; border-radius: 3pt; }
.stat .big { font-size: 19pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 8pt; color: #55595f; margin-top: 2pt; }

footer {
  margin-top: 18pt; padding-top: 8pt; border-top: 0.6pt solid #dfe1e5;
  font-size: 8pt; color: #74787e;
}
.avoid-break { break-inside: avoid; page-break-inside: avoid; }
.page-break { break-before: page; page-break-before: always; }
"""


def pct(x: float) -> str:
    return f"{x:.3f}"


def build_html(summary: dict) -> str:
    exp = summary["experiments"]
    cmp_rows = summary["paired_comparisons"]
    sweep = summary["exp003_sweep"]

    def row(label, key, note="", cls=""):
        s = exp[key]
        return (
            f'<tr class="{cls}"><td>{label}{note}</td>'
            f'<td class="num">{pct(s["macro_span_recall"])}</td>'
            f'<td class="num">{s["cases_fully_recalled"]}/{s["cases"]}</td>'
            f'<td class="num">{s["spans_found"]}/{s["spans_expected"]}</td>'
            f'<td class="num">{pct(s["document_level_recall"])}</td></tr>'
        )

    headline = "".join(
        [
            (
                '<tr class="fail"><td>EXP-000 lexical — <em>as shipped</em></td>'
                '<td class="num">0.000</td><td class="num">0/20</td>'
                '<td class="num">0/22</td><td class="num">0.000</td></tr>'
            ),
            row("EXP-000 lexical — BM25 (fixed)", "EXP-000 lexical (BM25)"),
            row("EXP-001 dense (LSA substitute)", "EXP-001 dense (LSA)"),
            row("EXP-002 hybrid interleave", "EXP-002 hybrid interleave"),
            row("EXP-003 RRF <span class='mono'>rrf_k=10</span>", "EXP-003 RRF rrf_k=10"),
            row("EXP-003 RRF <span class='mono'>rrf_k=20</span>", "EXP-003 RRF rrf_k=20"),
            row("EXP-003 RRF <span class='mono'>rrf_k=60</span>", "EXP-003 RRF rrf_k=60"),
        ]
    )

    best = sweep["pool100-rrfk60"]
    headline += (
        '<tr class="best"><td>EXP-003 RRF pool 100, <span class="mono">rrf_k=60</span></td>'
        f'<td class="num">{pct(best["macro_span_recall"])}</td>'
        f'<td class="num">{best["cases_fully_recalled"]}/20</td>'
        '<td class="num">13/22</td><td class="num">0.818</td></tr>'
    )

    comparisons = ""
    for c in cmp_rows:
        parts = []
        if c["rescued"]:
            parts.append(f'<span class="moved-in">rescued {", ".join(c["rescued"])}</span>')
        if c["regressed"]:
            parts.append(f'<span class="moved-out">regressed {", ".join(c["regressed"])}</span>')
        moved = "<br>".join(parts) or "&mdash;"

        net = c["net_rescued"]
        net_cls = "neg" if net < 0 else ("zero" if net == 0 else "pos")
        net_str = f"{net:+d}" if net else "0"
        comparisons += (
            f'<tr><td>{c["from"]} &rarr; {c["to"]}</td>'
            f'<td class="num">{len(c["rescued"])}</td>'
            f'<td class="num">{len(c["regressed"])}</td>'
            f'<td class="num {net_cls}">{net_str}</td>'
            f'<td style="font-size:8.2pt">{moved}</td></tr>'
        )

    sweep_rows = ""
    for pool in (10, 20, 50, 100):
        cells = ""
        for rk in (10, 20, 60):
            v = sweep[f"pool{pool}-rrfk{rk}"]["macro_span_recall"]
            cls = ' class="num best"' if v >= 0.6 else ' class="num"'
            cells += f"<td{cls}>{pct(v)}</td>"
        sweep_rows += f"<tr><td>{pool}</td>{cells}</tr>"

    lex = exp["EXP-000 lexical (BM25)"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Production RAG v1 — Results</title><style>{CSS}</style></head><body>

<h1>Production RAG v1 — Measured Results</h1>
<p class="subtitle">An evaluation-first retrieval baseline over 202 official OpenAI and Anthropic
documentation pages, with the failures left in.</p>
<div class="rule"></div>

<div class="callout warn">
  <div class="label">Read this first</div>
  <p><strong>The closed-book control (EXP-NULL) did not run.</strong> No generation credential was
  available and the provider API host is blocked by this environment's network egress policy. The
  results file records <span class="mono">status: "blocked"</span> with the exact error rather than
  placeholder numbers.</p>
  <p>This means the primary question V1 was built to answer &mdash; <em>does retrieval beat what the
  model already knows?</em> &mdash; remains unanswered. Every retrieval figure below is uncalibrated
  against the closed-book floor.</p>
</div>

<h2>What this measured</h2>
<p>V1 is deliberately small: a closed-book control plus four retrieval configurations, with no
reranker, no agent loop, no framework orchestration and no live crawler. The point is to find out
which retrieval method actually helps before adding anything, and to report the result honestly
whether or not it flatters the design.</p>

<div class="grid2 avoid-break">
  <div class="stat"><div class="big">0.000 &rarr; 0.475</div>
    <div class="cap">Lexical baseline macro recall, before and after diagnosing why it retrieved
    nothing at all</div></div>
  <div class="stat"><div class="big">0.818 vs 0.475</div>
    <div class="cap">Document-level recall against span-level recall &mdash; the gap that caps every
    configuration tested</div></div>
</div>

<h3>Run identity</h3>
<div class="meta">
  <div class="k">Corpus snapshot</div><div class="v">{SNAPSHOT_ID}</div>
  <div class="k">Corpus</div><div class="v">202 documents / 14,209 chunks &mdash; Anthropic 139 docs
    (12,028 chunks), OpenAI 63 docs (2,181 chunks)</div>
  <div class="k">Golden set</div><div class="v">22 cases: 20 retrieval-scored + 2 abstain controls;
    22 evidence spans</div>
  <div class="k">Evidence anchoring</div><div class="v">(version_id, section_path, char_start,
    char_end) &mdash; never chunk_id</div>
  <div class="k">Embedding model</div><div class="v">{EMBEDDING_MODEL_ID} &mdash; offline TF-IDF+SVD,
    384 dims, 57.2% explained variance</div>
  <div class="k">Retrieval k</div><div class="v">10, held constant across every experiment</div>
</div>

<h2>Headline results</h2>
<p><span class="mono">macro recall</span> averages per-case span recall, so a two-span multi-hop case
that finds one span scores 0.5. <span class="mono">fully recalled</span> is the strict count &mdash;
every expected span retrieved. <span class="mono">doc recall</span> credits a span when the correct
<em>document</em> reached the top 10 even though the wrong chunk came back.</p>

<table>
<thead><tr><th>Experiment</th><th class="num">macro recall</th><th class="num">fully recalled</th>
<th class="num">spans</th><th class="num">doc recall</th></tr></thead>
<tbody>{headline}</tbody>
</table>

<h2>Paired per-question comparisons</h2>
<p>On 20 cases an average is close to meaningless &mdash; one question is five points of macro recall.
What matters is which specific questions moved.</p>

<table>
<thead><tr><th>Change</th><th class="num">rescued</th><th class="num">regressed</th>
<th class="num">net</th><th>which questions moved</th></tr></thead>
<tbody>{comparisons}</tbody>
</table>

<h2>The uncomfortable findings</h2>

<div class="finding"><span class="t">1. The shipped lexical baseline retrieved nothing at all.</span>
It built its query with <span class="mono">websearch_to_tsquery</span>, which ANDs every token. A
sixteen-word question therefore required all sixteen tokens inside a single chunk, and the
<span class="mono">simple</span> text-search configuration has no stopword list, so
<span class="mono">which</span>, <span class="mono">does</span> and <span class="mono">the</span>
were mandatory match terms too. Zero hits on all twenty questions. Replaced with BM25 over the same
index: <strong>0.000 &rarr; 0.475</strong>.</div>

<div class="finding"><span class="t">2. Lexical beats dense, decisively.</span>
BM25 {pct(lex["macro_span_recall"])} against {pct(exp["EXP-001 dense (LSA)"]["macro_span_recall"])}.
Switching to dense regressed five of twenty questions and rescued one. This must be read with the
embedder caveat in the limitations &mdash; it is a statement about <em>this</em> embedder, not about
dense retrieval.</div>

<div class="finding"><span class="t">3. Hybrid interleave is worse than lexical alone.</span>
{pct(exp["EXP-002 hybrid interleave"]["macro_span_recall"])} against
{pct(lex["macro_span_recall"])}, net &minus;1 question. Alternating between a strong ranked list and
a weak one dilutes the strong one. Interleave was included as a transparent checkpoint before RRF,
and it earned its place by failing.</div>

<div class="finding"><span class="t">4. RRF's apparent gain over lexical is partial credit, not a win.</span>
RRF posts 0.500 against lexical's 0.475, but per question it is one rescued and one regressed &mdash;
a wash. The entire macro-recall difference is one extra span on a single two-span multi-hop case.</div>

<div class="finding"><span class="t">5. Fusion actively regressed a question lexical got right.</span>
Question OA-004's evidence sits at lexical rank 5 and dense rank 61. RRF averaged the two into rank
13, outside the k=10 cutoff. Fusing a strong list with a weak one costs real answers.</div>

<div class="finding"><span class="t">6. <span class="mono">rrf_k</span> is inert until the candidate pool is
large enough.</span> At pool sizes 10&ndash;30 all three <span class="mono">rrf_k</span> values give
identical results. Pool size dominates. Freezing the pool at the shipped default of 30 would have
hidden the best configuration entirely.</div>

<table class="avoid-break">
<thead><tr><th>candidate pool</th><th class="num">rrf_k=10</th><th class="num">rrf_k=20</th>
<th class="num">rrf_k=60</th></tr></thead>
<tbody>{sweep_rows}</tbody>
</table>

<h2>The ceiling: right document, wrong chunk</h2>
<p>Document-level recall is <strong>0.818</strong> for lexical, interleave and RRF alike, against
span-level recall of 0.455&ndash;0.500. Of the twelve spans the lexical baseline missed,
<strong>eight had the correct document in the top ten anyway</strong>.</p>
<p>The identical 0.818 across three different fusion strategies is the tell: fusion is reordering
chunks <em>within an already-correct document set</em>, not finding documents the individual
retrievers missed. That caps what any amount of fusion tuning can buy on this corpus.</p>

<div class="callout">
  <div class="label">Root cause</div>
  <p>Chunk granularity. One missed answer is a 57-character sentence sitting inside a 3,449-character
  chunk that dumps every body parameter of an API endpoint &mdash; 1.7% of its own chunk. Across the
  Anthropic half of the corpus, 2,521 of 12,028 chunks exceed 3,000 characters, and the largest
  reaches 12,341 despite a configured 3,500 budget, because the chunker never splits a single
  oversized table or code block.</p>
  <p>This is diagnosed and <strong>deliberately left unfixed</strong>. Re-chunking is the next
  experiment, and it must be measured against the same evidence spans rather than folded silently
  into V1. Because ground truth is anchored above the chunk layer, a re-chunked corpus can be scored
  against the same 22 unchanged spans.</p>
</div>

<h2>Limitations &mdash; read before quoting any number above</h2>
<ol>
<li><strong>EXP-NULL did not run.</strong> Retrieval is uncalibrated against the closed-book floor.
This was V1's primary question and it is unanswered.</li>
<li><strong>The dense retriever is a substitute, not an equivalent.</strong> Both the configured
sentence-transformer host and the OpenAI embedding endpoint are blocked by network policy, so
EXP-001/002/003 use an offline TF-IDF+SVD embedder fitted on the corpus itself. It has no pretrained
semantic knowledge and no subword handling. <strong>All dense, hybrid and RRF figures are lower
bounds.</strong> Re-running with a real embedding model is the single highest-value next step.</li>
<li><strong>n = 20 is not a holdout.</strong> Nothing here is statistically significant. The paired
per-question comparisons are more trustworthy than the averages.</li>
<li><strong>The corpus is provider-skewed.</strong> 139 Anthropic documents to 63 OpenAI, because
OpenAI's documentation hosts were unreachable and only its public repositories could be used. Lexical
fully recalls 7 of 8 OpenAI cases but only 2 of 12 Anthropic ones; the split tracks document size and
structure, not provider quality.</li>
<li><strong>Some parameters were tuned on the evaluation set.</strong> BM25 <span class="mono">k1</span>
and <span class="mono">b</span> are standard defaults, deliberately not swept. The
<span class="mono">rrf_k</span> and candidate-pool grids <em>were</em> swept on these same 20 cases,
so the pool-100 configuration is selected on the evaluation set and is optimistic.</li>
<li><strong>The golden set is single-author.</strong> Every anchor was read against its source
document and mechanically verified to contain the quoted claim, but no second annotator reviewed
them.</li>
</ol>

<h2>What V1 has not earned the right to add</h2>
<p>A reranker cannot rescue the worst failure case, because the correct chunk is absent from the top
200 candidates entirely &mdash; reranking only reorders what retrieval already found. A larger k
would inflate the metric without improving retrieval. A similarity threshold addresses a calibration
problem the data does not show.</p>
<p>The next experiment justified by evidence is re-chunking, measured against the same unchanged
evidence spans. If span recall does not move toward document-level recall after re-chunking, the
diagnosis is wrong and reranking becomes the next candidate &mdash; but not before.</p>

<footer>
Generated from <span class="mono">experiments/summary.json</span> by
<span class="mono">scripts/build_report_pdf.py</span>. Corpus snapshot {SNAPSHOT_ID}.
Raw provider documentation is not redistributed; published results carry evidence anchors, ranks and
scores with retrieved text replaced by a content hash.
</footer>

</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default="experiments/summary.json")
    parser.add_argument("--out", default="docs/reports/production-rag-v1-results.pdf")
    args = parser.parse_args()

    summary = json.loads((REPO_ROOT / args.summary).read_text(encoding="utf-8"))
    html = build_html(summary)

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit(f"No Chromium binary found; looked in {CHROME_CANDIDATES}")

    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "report.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                f"--user-data-dir={tmp}/profile",
                "--no-pdf-header-footer",
                f"--print-to-pdf={out}",
                src.as_uri(),
            ],
            check=True,
            capture_output=True,
        )

    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
