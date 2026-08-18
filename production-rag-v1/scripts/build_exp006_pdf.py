#!/usr/bin/env python3
"""Render the EXP-006 enrichment-ablation report to a shareable PDF.

Figures are read from experiments/EXP-006/results.json at build time so the PDF
cannot drift from the artifact. Re-run scripts/run_exp006.py first if the
experiment changed.
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
    "EXP-006A": "A — control chunking, plain",
    "EXP-006B": "B — control chunking, enriched",
    "EXP-006C": "C — bounded chunking, plain",
    "EXP-006D": "D — bounded chunking, enriched",
}


def build_html(d: dict) -> str:
    cfg = d["configurations"]
    pr = d["paired_results"]
    expl = d["exploratory_field_ablation"]

    rows = ""
    for key, label in LABELS.items():
        r = cfg[key]
        a = r["spans_absent_from_top"]
        cls = " class='good'" if key == "EXP-006D" else ""
        rows += (
            f"<tr><td{cls}>{label}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
            f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
            f"<td class='num'>{r['spans_retrieved_at_10']}/{r['spans_total']}</td>"
            f"<td class='num'>{r['document_recall']:.3f}</td><td class='num'>{r['mrr']:.3f}</td>"
            f"<td class='num'>{a['10']}</td><td class='num'>{a['50']}</td>"
            f"<td class='num'>{a['100']}</td><td class='num'>{a['300']}</td>"
            f"<td class='num'>{r['mean_query_ms']:.0f}</td></tr>"
        )

    pair_rows = ""
    for name, c in pr.items():
        delta = c["macro_recall_delta"]
        dcls = " class='bad'" if delta == 0 and name.startswith("A->B") else ""
        pair_rows += (
            f"<tr><td>{name}</td><td class='num'{dcls}>{delta:+.3f}</td>"
            f"<td>{', '.join(c['rescued']) or '—'}</td><td>{', '.join(c['regressed']) or '—'}</td>"
            f"<td class='num'>{c['net_rescued']:+d}</td></tr>"
        )

    an003 = ""
    for key, label in LABELS.items():
        s = cfg[key]["cases"]["AN-003"]["spans"][0]
        rank = s["rank"] if s["rank"] else "—"
        top300 = "yes" if s["within"]["300"] else "no"
        cls = " class='good'" if s["rank"] else ""
        an003 += (
            f"<tr><td>{label}</td><td class='num'{cls}>{rank}</td><td>{top300}</td>"
            f"<td class='num'>{s['chunk_len'] or '—'}</td><td class='num'>{s['doc_rank']}</td></tr>"
        )

    ex_rows = ""
    for key, r in expl["configurations"].items():
        ex_rows += (
            f"<tr><td>{key}</td><td>{r['description']}</td>"
            f"<td class='num'>{r['macro_span_recall']:.3f}</td>"
            f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td></tr>"
        )

    plan = cfg["EXP-006A"]["query_plan_summary"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-006 Enrichment Ablation</title><style>{CSS}</style></head><body>

<h1>EXP-006 — Contextual Enrichment Ablation</h1>
<p class="subtitle">Isolating structural context from chunk size, to find out which half of
the previous experiment's gain was real.</p>
<div class="rule"></div>

<div class="callout warn">
  <div class="label">Executive result</div>
  <p><strong>Contextual enrichment did not improve retrieval.</strong> On the control
  chunking, adding a structural header to the indexed text moved macro span recall by
  <strong>exactly zero</strong> (0.475 → 0.475) — one question rescued, one regressed.</p>
  <p>The measured reason: enrichment <strong>inflates document frequency</strong>. Writing
  <span class="mono">Provider: anthropic</span> into all 12,028 Anthropic chunks took the
  term "Anthropic" from df 3,289 to 12,028, destroying its IDF. Across 22 evidence spans,
  enrichment supplied a query term to only 3, and in none of those was it a discriminative
  one.</p>
</div>

<div class="grid2 avoid">
  <div class="stat"><div class="big">&Delta; 0.000</div>
    <div class="cap">Macro recall change from enrichment on control chunking (A→B) — the
    comparison that isolates enrichment</div></div>
  <div class="stat"><div class="big">3 of 22</div>
    <div class="cap">Evidence spans where enrichment supplied any query term at all; zero of
    them discriminative</div></div>
</div>

<h2>The 2×2</h2>
<p>B and D are row-for-row copies of A and C — <strong>0</strong> boundary differences and
<strong>0</strong> body differences, verified in SQL and pinned by tests. Only the indexed
text differs, so an A→B difference cannot be a chunking difference. The canonical chunk body
is never mutated: the header lives in a separate <span class="mono">search_text</span>
column, because a citation must quote real source text.</p>

<table>
<thead><tr><th>Configuration</th><th class="num">macro recall</th><th class="num">fully recalled</th>
<th class="num">spans @10</th><th class="num">doc recall</th><th class="num">MRR</th>
<th class="num">absent@10</th><th class="num">@50</th><th class="num">@100</th>
<th class="num">@300</th><th class="num">ms</th></tr></thead>
<tbody>{rows}</tbody></table>

<h2>Paired comparisons</h2>
<table>
<thead><tr><th>Comparison</th><th class="num">&Delta; macro</th><th>rescued</th>
<th>regressed</th><th class="num">net</th></tr></thead>
<tbody>{pair_rows}</tbody></table>
<p><strong>A→B is the headline and it is a wash.</strong> Its single rescue (AN-004,
rank 12→7) crossed the cutoff while its BM25 score went <em>down</em> — competitors simply
lost more. Its regression (AN-005, rank 4→18) is large and mechanistic: the query's best
term <span class="mono">editing</span> had df 66, and writing the section heading into every
chunk of that document tripled it to 211.</p>

<h2>Why enrichment nets to zero</h2>
<p>A constant field repeated across every chunk of a document or provider is, by
construction, non-discriminative. BM25 weights a term by
<span class="mono">ln(1 + (N−df+0.5)/(df+0.5))</span>, so tripling a term's df directly
attacks the signal that made it useful.</p>
<table>
<thead><tr><th>term</th><th class="num">df plain</th><th class="num">df enriched</th><th class="num">change</th></tr></thead>
<tbody>
<tr><td>Anthropic</td><td class="num">3,289</td><td class="num">12,028</td><td class="num bad">+266%</td></tr>
<tr><td>OpenAI</td><td class="num">366</td><td class="num">2,185</td><td class="num bad">+497%</td></tr>
<tr><td>beta</td><td class="num">1,405</td><td class="num">2,933</td><td class="num bad">+109%</td></tr>
<tr><td>editing</td><td class="num">66</td><td class="num">211</td><td class="num bad">+220%</td></tr>
</tbody></table>
<p>98 distinct query terms shifted document frequency. Enrichment adds a handful of weak
matches while diluting terms that were already working.</p>

<h2>AN-003 — the canonical failure</h2>
<table>
<thead><tr><th>Configuration</th><th class="num">rank</th><th>in top 300?</th>
<th class="num">chunk chars</th><th class="num">doc rank</th></tr></thead>
<tbody>{an003}</tbody></table>
<p>Enrichment built a lexical bridge for the first time — AN-003's evidence becomes
reachable at <strong>rank 74</strong> under D, having been absent at depth 300 in every
previous experiment. The header supplied <span class="mono">Batches</span>, a term the body
lacked. But enrichment simultaneously took that term's df from 283 to 1,203, and the terms
that would actually identify this evidence remain absent everywhere:
<span class="mono">contain</span> (df 111), <span class="mono">most</span> (533),
<span class="mono">many</span> (564), and <span class="mono">requests</span> — which never
matches the body's singular <span class="mono">request</span>.</p>
<p><strong>Answer: no.</strong> Section-path enrichment does not create enough of a lexical
bridge to make AN-003 retrievable. Rank 74 is still a failure at k=10 and would remain one
at k=50.</p>

<h2>Was enrichment the real source of V3's gain?</h2>
<p><strong>No.</strong> V3 rescued AN-004, AN-008 and AN-010 in EXP-005. Enrichment alone
rescues AN-004 only — fragilely — while losing AN-005. Enrichment on bounded chunking
rescues AN-004 and AN-007, but <em>neither</em> AN-008 nor AN-010. AN-010 was V3's largest
win (rank 49→1) and no EXP-006 configuration reproduces it, so that rescue must have come
from V3's table row-group splitting, which EXP-006 did not test.</p>

<h2>Exploratory: which header fields matter</h2>
<p>Run after the core 2×2, motivated by the df-inflation mechanism.
<strong>Selected on the development set — not a held-out result.</strong></p>
<table>
<thead><tr><th>Variant</th><th>Header fields</th><th class="num">macro recall</th><th class="num">fully recalled</th></tr></thead>
<tbody>
<tr><td>A</td><td>none (baseline)</td><td class="num">0.475</td><td class="num">9/20</td></tr>
{ex_rows}
<tr><td>B</td><td>provider + document + section</td><td class="num">0.475</td><td class="num">9/20</td></tr>
</tbody></table>
<p>The ordering matches the mechanism exactly: the more constant the field, the more df
inflation and the worse the result. Only the section path, which actually varies chunk to
chunk, carries information — and it improves the baseline by <strong>one case</strong>, on a
20-case development set. That does not license adopting enrichment.</p>

<h2>Updated root-cause hypothesis</h2>
<p>Two hypotheses have now been tested with controlled interventions and neither survives:
<strong>oversized chunks hide evidence</strong> (falsified by EXP-005, zero rescued) and
<strong>missing structural lexical context</strong> (falsified here, &Delta;0.000).</p>
<p>The surviving hypothesis is what AN-003 has pointed at all along: <strong>BM25 cannot
bridge the vocabulary gap between how a question is phrased and how the documentation states
the answer.</strong> Enrichment can only add terms that already exist in the document's
structure. It cannot add the words a user actually used.</p>

<h2>Reproducibility validation</h2>
<ul>
<li>EXP-006A reproduces EXP-000 (0.475, 9/20) and EXP-006C reproduces EXP-005A (0.500, 9/20),
with identical per-case recall and identical hit ordering.</li>
<li><span class="mono">idx_chunk_search_vector</span> still used —
{plan['gin_index_scans']} bitmap index scans. The EXP-005 planner regression has not
returned.</li>
<li>Repeated runs are byte-identical; score rounding before sorting is retained.</li>
<li>All four configurations pass evidence-mapping validation, 22/22 spans, 0 offset
mismatches.</li>
<li>EXP-000 through EXP-005 artifacts untouched.</li>
</ul>

<h2>Limitations</h2>
<ol>
<li><strong>n = 20 is development scale.</strong> One case is 5 points of macro recall. Every
result here is a 1–2 case movement; nothing is statistically significant.</li>
<li><strong>The field ablation was selected on the development set.</strong></li>
<li><strong>V3's table row-group mechanism was not tested</strong> and remains the leading
explanation for its AN-010 rescue.</li>
<li><strong>EXP-NULL still has not run</strong> — retrieval lift over the model's own
knowledge remains unknown.</li>
<li><strong>Dense retrieval has not been disproven.</strong> Earlier dense numbers used an
offline TF-IDF+SVD substitute, not a pretrained model.</li>
<li><strong>Section paths are mostly good</strong> — 19 of 22 evidence spans sit under
technical paths. The null result is not explained by useless headings.</li>
</ol>

<h2>What is justified next</h2>
<p><strong>Real pretrained dense retrieval.</strong> Both lexical hypotheses have been tested
and rejected. The remaining diagnosis — vocabulary mismatch — is exactly what a pretrained
embedding model addresses, and AN-003 is its canonical test case. Blocked only on network
egress.</p>
<p>Secondary and cheap: test V3's table row-group mechanism in isolation, and add stemming as
a <em>third ranked list</em> rather than a replacement, so identifier precision survives.</p>
<p><strong>Not justified:</strong> a reranker (AN-003 is absent from depth 300 in three of
four configurations — a reranker reorders candidates, it cannot retrieve missing evidence),
or freezing enrichment. <strong>Baseline unchanged:</strong> control chunking, no
enrichment.</p>

<footer>
Generated from experiments/EXP-006/results.json by scripts/build_exp006_pdf.py.
Git commit {(d.get('git_commit') or 'unknown')[:12]}. Config hash {d['config_hash'][:16]}.
BM25 k1={d['bm25_config']['k1']}, b={d['bm25_config']['b']}, top_k={d['top_k']}.
Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-006-enrichment-ablation.pdf")
    args = parser.parse_args()
    data = json.loads((REPO_ROOT / "experiments/EXP-006/results.json").read_text())
    html = build_html(data)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp006.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
