#!/usr/bin/env python3
"""Render the EXP-005 re-chunking report to a shareable PDF.

Figures are read from experiments/EXP-005/*.json at build time, so the PDF cannot
drift from the artifacts. Re-run scripts/analyze_exp005.py and
scripts/chunk_diagnostics.py first if the experiment has changed.
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

CSS = """
@page { size: Letter; margin: 18mm 16mm 16mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 10pt; line-height: 1.5; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
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
.b { font-weight: 700; }
.bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; }

.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt; margin: 10pt 0 12pt; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.5pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }

ol, ul { margin: 0 0 8pt; padding-left: 15pt; }
li { margin-bottom: 4pt; }
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


def build_html(pa: dict, dist: dict) -> str:
    cfg = pa["configurations"]
    ctrl, v2, v3 = cfg["EXP-000_control"], cfg["EXP-005A_bounded"], cfg["EXP-005B_technical"]
    comp2 = pa["paired_comparisons"]["EXP-000_control -> EXP-005A_bounded"]
    comp3 = pa["paired_comparisons"]["EXP-000_control -> EXP-005B_technical"]
    sets = {d["chunker"]: d for d in dist["chunk_sets"]}

    def res_row(label, r, comp=None):
        moved = "—" if comp is None else (
            f"{len(comp['rescued'])} / {len(comp['regressed'])}"
        )
        return (
            f"<tr><td>{label}</td>"
            f"<td class='num'>{r['macro_span_recall']:.3f}</td>"
            f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
            f"<td class='num'>{r['spans_found']}/{r['spans_total']}</td>"
            f"<td class='num'>{r['document_recall']:.3f}</td>"
            f"<td class='num'>{moved}</td></tr>"
        )

    def dist_row(key, label):
        d = sets[key]
        hard = d["hard_max_chars"]
        limit = "none" if not hard else f"{d['over_hard_max']}"
        return (
            f"<tr><td>{label}</td><td class='num'>{d['total_chunks']:,}</td>"
            f"<td class='num'>{d['mean_chars']:,}</td><td class='num'>{d['median_chars']:,}</td>"
            f"<td class='num'>{d['p90_chars']:,}</td><td class='num'>{d['p99_chars']:,}</td>"
            f"<td class='num b'>{d['max_chars']:,}</td><td class='num'>{d['over_2000']:,}</td>"
            f"<td class='num'>{limit}</td></tr>"
        )

    # Span-level rank movement.
    moves = {}
    for label in ("EXP-005A_bounded", "EXP-005B_technical"):
        better = worse = same = gained = 0
        for cid, before in ctrl["cases"].items():
            for b, a in zip(before["spans"], cfg[label]["cases"][cid]["spans"], strict=True):
                if b["rank"] is None and a["rank"] is None:
                    same += 1
                elif b["rank"] is None:
                    gained += 1
                elif a["rank"] is None or a["rank"] > b["rank"]:
                    worse += 1
                elif a["rank"] < b["rank"]:
                    better += 1
                else:
                    same += 1
        moves[label] = (better, worse, same, gained)

    case_rows = ""
    for cid, before in ctrl["cases"].items():
        ranks = []
        for label in ("EXP-000_control", "EXP-005A_bounded", "EXP-005B_technical"):
            spans = cfg[label]["cases"][cid]["spans"]
            ranks.append(",".join(str(s["rank"]) if s["rank"] else "—" for s in spans))
        after3 = cfg["EXP-005B_technical"]["cases"][cid]["recall"]
        cls = " class='good'" if after3 > before["recall"] else ""
        case_rows += (
            f"<tr><td>{cid}</td><td>{before['category']}</td>"
            f"<td class='num'>{before['recall']:.2f}</td>"
            f"<td class='num'>{cfg['EXP-005A_bounded']['cases'][cid]['recall']:.2f}</td>"
            f"<td class='num'{cls}>{after3:.2f}</td>"
            f"<td class='num'>{ranks[0]}</td><td class='num'>{ranks[1]}</td><td class='num'>{ranks[2]}</td></tr>"
        )

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-005 Re-Chunking Results</title><style>{CSS}</style></head><body>

<h1>EXP-005 — Re-Chunking Results</h1>
<p class="subtitle">Testing whether chunk granularity is the retrieval bottleneck the
previous failure report said it was.</p>
<div class="rule"></div>

<div class="callout warn">
  <div class="label">Verdict</div>
  <p><strong>The chunk-granularity hypothesis is not supported.</strong> Bounding chunk size
  — the intervention the hypothesis actually names — rescued <strong>zero</strong> of the 20
  questions, despite cutting the corpus maximum from 16,096 characters to 1,999.</p>
  <p>The one case that motivated the entire hypothesis is still unretrievable after its
  evidence share of its chunk improved 2.9×. Its real cause is vocabulary mismatch, which
  no chunker can fix.</p>
</div>

<div class="grid2 avoid">
  <div class="stat"><div class="big">0 rescued</div>
    <div class="cap">Questions recovered by bounded chunking (EXP-005A), the isolated
    granularity intervention</div></div>
  <div class="stat"><div class="big">8 up / 9 down</div>
    <div class="cap">Span ranks that improved vs worsened under bounded chunking — a coin
    flip, and no span became newly reachable</div></div>
</div>

<h2>Controls</h2>
<p>Held constant: the same 202 document versions, the same 20 questions and 22 evidence
spans, the same anchors <span class="mono">(version_id, section_path, char_start, char_end)</span>,
the same BM25 implementation and parameters, the same <span class="mono">k=10</span>, the
same scoring code. No reranker, no query rewriting, no BM25 retuning, no larger k.</p>
<p>Storing a second chunking of the same versions required a chunk-set dimension in the
schema. After migrating, EXP-000 was re-run against the control set and its results file is
<strong>byte-identical</strong> to the committed one.</p>

<h2>Chunk distribution — the intervention was real</h2>
<table>
<thead><tr><th>Chunker</th><th class="num">chunks</th><th class="num">mean</th>
<th class="num">median</th><th class="num">p90</th><th class="num">p99</th>
<th class="num">max</th><th class="num">&gt;2000</th><th class="num">&gt; own limit</th></tr></thead>
<tbody>
{dist_row("chunker_v1_control", "v1 control")}
{dist_row("chunker_v2_bounded", "v2 bounded")}
{dist_row("chunker_v3_technical", "v3 technical")}
</tbody></table>
<p>Mean chunk length fell 31%, p90 fell from 3,466 to 1,193, and 3,069 chunks over 2,000
characters became none. Evidence mapping was validated: 22/22 spans still map to a chunk
with the same section path in all three sets, with zero offset mismatches.</p>

<h2>Results</h2>
<table>
<thead><tr><th>Configuration</th><th class="num">macro recall</th><th class="num">fully recalled</th>
<th class="num">spans</th><th class="num">doc recall</th><th class="num">rescued / regressed</th></tr></thead>
<tbody>
{res_row("EXP-000 control", ctrl)}
{res_row("EXP-005A bounded", v2, comp2)}
{res_row("EXP-005B technical", v3, comp3)}
</tbody></table>

<h3>Span-level rank movement (all 22 spans)</h3>
<table>
<thead><tr><th>Configuration</th><th class="num">improved</th><th class="num">worsened</th>
<th class="num">unchanged</th><th class="num">newly reachable</th></tr></thead>
<tbody>
<tr><td>EXP-005A bounded</td><td class="num">{moves['EXP-005A_bounded'][0]}</td>
<td class="num bad">{moves['EXP-005A_bounded'][1]}</td><td class="num">{moves['EXP-005A_bounded'][2]}</td>
<td class="num bad">{moves['EXP-005A_bounded'][3]}</td></tr>
<tr><td>EXP-005B technical</td><td class="num">{moves['EXP-005B_technical'][0]}</td>
<td class="num">{moves['EXP-005B_technical'][1]}</td><td class="num">{moves['EXP-005B_technical'][2]}</td>
<td class="num bad">{moves['EXP-005B_technical'][3]}</td></tr>
</tbody></table>

<h2>Per-question movement</h2>
<table>
<thead><tr><th>Case</th><th>Category</th><th class="num">ctrl</th><th class="num">V2</th>
<th class="num">V3</th><th class="num">rank ctrl</th><th class="num">rank V2</th><th class="num">rank V3</th></tr></thead>
<tbody>{case_rows}</tbody></table>

<h2>The three cases that explain the result</h2>

<div class="q"><span class="t">Major rescue — AN-010, rank 49 → 1 (V3 only)</span>
The evidence is a row in a model-status table. Control: a 2,317-character chunk, rank 49.
V2 shrank it to 1,871 and the rank got <strong>worse</strong> (62), because splitting removed
the surrounding prose carrying <span class="mono">state</span> and
<span class="mono">model</span>. V3 emitted a 415-character row group with a context header
repeating <span class="mono">[Model status] | API model name | Current state | …</span> —
rank 1. The mechanism is the header, not the size, and V2 proves it.</div>

<div class="q"><span class="t">Regression — AN-002, rank 27 → 172 (V2)</span>
Splitting a 3,327-character chunk to 1,121 cut query-term coverage from
<strong>12 of 13</strong> to <strong>7 of 13</strong>. The control's oversized chunk was
accidentally helping, because BM25 rewards co-occurrence and that chunk concatenated the
whole HTTP-error list. AN-007 (18→41) and AN-011 (54→139) fail the same way.</div>

<div class="q"><span class="t">Persistent failure — AN-003, the case that motivated the hypothesis</span>
The answer is a 57-character sentence. Its share of its chunk improved from 1.65% to 4.79%
— a 2.9× improvement on exactly the quantity that was diagnosed — and it is
<strong>still not retrieved at depth 300</strong> in any configuration. Every low-df term in
the question is absent from the chunk holding the answer:
<span class="mono">contain</span> (df 111), <span class="mono">Batches</span> (df 286),
<span class="mono">requests</span> (df 1,218 — only the singular appears). This is
vocabulary mismatch.</div>

<h2>Answers to the pre-registered questions</h2>
<div class="q"><span class="t">A. Did span recall move toward the 0.818 document ceiling?</span>
Partially, and not by the mechanism under test. V2, which isolates granularity: 0.475 →
0.500, entirely one half-case.</div>
<div class="q"><span class="t">B. Did document recall stay stable?</span>
For V2 yes (0.825). For V3 no — it rose to 0.900, because context headers add section-path
terms to the index. V3 is therefore not a pure chunking intervention.</div>
<div class="q"><span class="t">C. Did oversized answer-containing units become retrievable?</span>
<strong>No.</strong> Zero spans moved from unreachable to reachable in either configuration.</div>
<div class="q"><span class="t">D. Did smaller chunks introduce fragmentation regressions?</span>
<strong>Yes.</strong> Under V2, 9 of 22 spans ranked worse against 8 better.</div>
<div class="q"><span class="t">E. Does V3 justify its complexity?</span>
On the numbers yes (+3 rescued, 0 regressed). But the justification is for contextual
enrichment, which V3 bundles — not for its parameter-entry logic, which produced only 60
chunks across 202 documents and rescued nothing.</div>

<h2>Limitations</h2>
<ol>
<li><strong>V2 is not a single-variable ablation</strong> — it changes both the grouping
target and hard-limit enforcement. Since its result is null, the confound does not rescue
the hypothesis, but a stricter design would vary one at a time.</li>
<li><strong>V3 confounds granularity with enrichment.</strong> Separating them is the
obvious follow-up.</li>
<li><strong>n = 20 is development scale.</strong> Two of the three V3 rescues turned on rank
movements of 1–3 positions across the k boundary. Nothing here is statistically significant.</li>
<li><strong>EXP-NULL still has not run</strong> — no generation credential and the provider
host is egress-blocked. Retrieval lift over the model's own knowledge remains unknown.</li>
<li><strong>Dense retrieval remains unmeasured in any real sense.</strong> Earlier dense
numbers used an offline TF-IDF+SVD substitute. Nothing supports "BM25 beats dense
retrieval" — only that it beat that substitute on this corpus. EXP-005 is BM25-only.</li>
<li><strong>Corpus skew persists:</strong> 139 Anthropic documents to 63 OpenAI. All three
V3 rescues are Anthropic-side; the OpenAI cases are unchanged across all configurations.</li>
</ol>

<h2>What the data justifies next</h2>
<p>The bottleneck is <strong>lexical matching</strong>, not chunk size.</p>
<ol>
<li><strong>A real pretrained embedding model</strong> — highest value. AN-003 fails on pure
vocabulary mismatch, the canonical case for semantic retrieval. Blocked only on network
egress.</li>
<li><strong>Separate enrichment from granularity:</strong> run V2 plus context headers alone.
If it reproduces most of V3's +3, adopt enrichment and drop the parameter-entry machinery.</li>
<li><strong>Revisit the unstemmed <span class="mono">simple</span> configuration</strong> as a
third ranked list, keeping identifier precision while recovering plural/singular matches.</li>
</ol>
<p><strong>Not justified:</strong> a reranker (cannot rescue evidence absent from the top 300),
a larger k (inflates the metric without improving retrieval), or a confidence threshold (no
calibration failure was observed). <strong>V3 is not frozen as the new baseline</strong>,
because its gain is attributable to a mechanism this experiment did not isolate.</p>

<footer>
Generated from experiments/EXP-005/*.json by scripts/build_exp005_pdf.py.
Git commit {pa['provenance']['git_commit'][:12] if pa['provenance']['git_commit'] else 'unknown'}.
Control snapshot {ctrl['snapshot_id']}; bounded {v2['snapshot_id']}; technical {v3['snapshot_id']}.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-005-rechunking.pdf")
    args = parser.parse_args()

    pa = json.loads((REPO_ROOT / "experiments/EXP-005/paired-analysis.json").read_text())
    dist = json.loads((REPO_ROOT / "experiments/EXP-005/chunk-distribution.json").read_text())
    html = build_html(pa, dist)

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit(f"No Chromium binary found; looked in {CHROME_CANDIDATES}")

    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp005.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run(
            [chrome, "--headless", "--no-sandbox", "--disable-gpu",
             f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
             f"--print-to-pdf={out}", src.as_uri()],
            check=True, capture_output=True,
        )
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
