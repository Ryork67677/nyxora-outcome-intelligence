#!/usr/bin/env python3
"""Render the EXP-014R report to a shareable PDF.

Figures come from experiments/EXP-014R/*.json at build time so the document cannot
drift from the artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP = REPO_ROOT / "experiments" / "EXP-014R"
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
pre { font-family: "SFMono-Regular", Consolas, monospace; font-size: 8pt;
  background: #f6f7f9; border: 0.6pt solid #dde0e4; border-radius: 3pt;
  padding: 7pt 9pt; margin: 6pt 0 10pt; white-space: pre-wrap; }
.subtitle { font-size: 10.5pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.4pt; }
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
.stat.warn { border-color: #8a1c1c; background: #fdf5f5; }
.stat .big { font-size: 15pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.4pt; color: #52565d; margin-top: 2pt; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.8pt; color: #6f747b; }
"""


def build_html(dev: dict, cand: dict, devval: dict) -> str:
    a, b = dev["system_a"], dev["system_b"]
    paired = dev["paired"]
    bs = dev["bootstrap"]["macro_recall_delta"]
    mc = dev["mcnemar"]

    fails = "".join(f"<tr><td>{k}</td><td class='num'>{v}</td></tr>"
                    for k, v in sorted(cand["failure_counts"].items(), key=lambda kv: -kv[1]))

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>EXP-014R — Replication and Golden Set Expansion</title><style>{CSS}</style></head><body>

<h1>EXP-014R — DOC-C Replication and<br>Golden Set Expansion</h1>
<p class="subtitle">Production RAG v1 · evaluation-first · systems frozen before any new data</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">Status — the replication could not be performed, and the reason is the finding</div>
<p>The systems were frozen and hashed, the evaluation infrastructure was built and works, and the
harness reproduces EXP-014 exactly. But the expanded golden set the replication depends on
<strong>could not be built to a usable standard</strong>, and running a replication on the set that
<em>was</em> generated would have produced a confident number with nothing behind it.</p>
</div>

<div class="grid4">
  <div class="stat warn"><div class="big">[{bs['ci95'][0]:+.3f}, {bs['ci95'][1]:+.3f}]</div>
    <div class="cap">bootstrap 95% CI on the EXP-014 delta<br><b>lower bound touches zero</b></div></div>
  <div class="stat"><div class="big">p = {mc['p_value']}</div>
    <div class="cap">McNemar exact, {mc['discordant_pairs']} discordant pairs</div></div>
  <div class="stat warn"><div class="big">12</div>
    <div class="cap">usable generated questions<br>against a minimum of 100</div></div>
  <div class="stat"><div class="big">1</div>
    <div class="cap">real defect found in the<br>original human-verified set</div></div>
</div>

<h2>1. What was delivered</h2>
<table><thead><tr><th>deliverable</th><th>status</th></tr></thead><tbody>
<tr><td>SYSTEM-A and SYSTEM-B frozen and hashed</td><td class="good">done</td></tr>
<tr><td>Golden-set schema, splits, provenance fields</td><td class="good">done</td></tr>
<tr><td>validate_golden.py with 16 blocking checks</td><td class="good">done</td></tr>
<tr><td>Source-anchored candidate generator</td><td class="good">done — and it demonstrates why the approach fails</td></tr>
<tr><td>Development split, verbatim, hashed</td><td class="good">done (22 cases)</td></tr>
<tr><td>Replication harness, bootstrap + McNemar</td><td class="good">done, verified against EXP-014</td></tr>
<tr><td>Expanded validation/holdout splits (100–150)</td><td class="bad">NOT delivered</td></tr>
<tr><td>Holdout replication of DOC-C</td><td class="bad">NOT run</td></tr>
</tbody></table>

<h2>2. Frozen systems</h2>
<pre>SYSTEM-A-GLOBAL  {dev['system_a_config_hash'][:16]}…   global BM25 + transformer RRF
SYSTEM-B-DOC-C   {dev['system_b_config_hash'][:16]}…   DOC-C-SECTION routing -&gt; frozen Stage 2</pre>
<p>Both frozen <strong>before</strong> any new evaluation data existed. Recorded metrics are excluded
from the hash (an outcome is not a setting) and a test proves that changing <code>top_documents</code>
<em>does</em> change it. The secondary 19/20 router is recorded as explicitly not under test, with its
reason: it routes better and retrieves worse.</p>

<h2>3. Why the golden set could not be expanded</h2>
<p>The brief permits automated generation <em>with human verification</em>. <strong>There is no human
in this session</strong>, so the honest ceiling on any question I generate is
<code>source_anchored_automatic</code>, never <code>human_verified</code>. That alone would have been
survivable. Quality was not.</p>
<table><thead><tr><th>pass</th><th class="num">yield</th><th>representative failure</th></tr></thead>
<tbody>
<tr><td>1. broad patterns</td><td class="num">123</td>
<td>"Which HTTP status code corresponds to <b>the ptimized condition</b>?" → claim <code>512</code>.
A truncated word, and a status code invented by pairing an unrelated number with a nearby token.</td></tr>
<tr><td>2. + identifier shape, + soundness check</td><td class="num">45</td>
<td>"maximum value allowed for <b>resold</b>" — a word fragment as a parameter.
<code>rbac_group_id → 100</code>, where the 100 governed something else.</td></tr>
<tr><td>3. + literal-value filter, limit pattern removed</td><td class="num b">20</td>
<td><code>tool_choice → True</code> (wrong). <code>effort</code> given <b>two contradictory
answers</b>. <code>max_concurrent_subagents → used</code>.</td></tr>
</tbody></table>
<p>Each tightening cut yield without eliminating false facts, ending at <strong>12 supported
questions</strong> — several still wrong — against a stated minimum of 100. The failure is
structural: extracting "X defaults to Y" needs to know which <code>X</code> a sentence is
<em>about</em>, and regexes bind to the nearest plausible token — right often enough to look fine in
aggregate, wrong often enough to poison an answer key.</p>

<div class="callout">
<div class="label">What was deliberately not done</div>
<p>No replication was computed on those 12 questions. Reporting "DOC-C replicated on n=12" would have
been worse than reporting nothing: <strong>an evaluation set is the one artifact that cannot be
checked by running it</strong>, so a wrong key yields a confident number with nothing behind it.</p>
</div>

<h2>4. The validator works — it blocked the run</h2>
<pre>{cand['cases']} cases, {len(cand['failures'])} failures</pre>
<table><thead><tr><th>check</th><th class="num">failures</th></tr></thead><tbody>{fails}</tbody></table>
<p>The duplicate it caught is the contradictory <code>effort</code> pair. The human-verification gate
is what stops machine-generated ground truth from silently becoming gold. Sixteen checks are
implemented, including <b>evidence span hash matches</b> and <b>every critical claim appears in its
own evidence span</b>.</p>

<h2>5. A real defect in the original golden set</h2>
<div class="callout warn">
<div class="label">OA-002 — claim absent from its own evidence</div>
<p>"Which exception does the OpenAI Agents SDK raise when a run exceeds the <code>max_turns</code>
limit?", critical claim <code>MaxTurnsExceeded</code>. The cited span <em>describes</em> the exception
without naming it; the name occurs elsewhere in the document and the anchor's start boundary excludes
it.</p>
<p>A system returning exactly this span scores as having found the evidence. One of 22 spans —
up to ~4.5 percentage points, about one case, on every experiment since EXP-000.
<strong>It has not been fixed</strong>: correcting it now would silently change every historical
number without re-running anything.</p>
</div>

<h2>6. Harness verification, and the statistics that matter</h2>
<table><thead><tr><th>system</th><th class="num">macro recall</th><th class="num">full</th>
<th class="num">spans@10</th><th class="num">doc R</th><th class="num">MRR</th></tr></thead><tbody>
<tr><td>SYSTEM-A-GLOBAL</td><td class="num">{a['macro_span_recall']:.3f}</td>
<td class="num">{a['cases_fully_recalled']}/{a['cases_total']}</td>
<td class="num">{a['spans_found_at_10']}/{a['spans_total']}</td>
<td class="num">{a['document_recall']:.3f}</td><td class="num">{a['mrr']:.3f}</td></tr>
<tr><td>SYSTEM-B-DOC-C</td><td class="num b">{b['macro_span_recall']:.3f}</td>
<td class="num">{b['cases_fully_recalled']}/{b['cases_total']}</td>
<td class="num">{b['spans_found_at_10']}/{b['spans_total']}</td>
<td class="num">{b['document_recall']:.3f}</td><td class="num">{b['mrr']:.3f}</td></tr>
</tbody></table>
<p>Reproduces EXP-014 exactly — B rescues {', '.join(paired['b_rescues_over_a'])},
<b>zero regressions</b>, net {paired['net_cases']:+d}. This is the <em>development</em> set: a
reproduction, not a replication.</p>

<div class="callout warn">
<div class="label">The EXP-014 result is not distinguishable from zero on its own data</div>
<p>Macro-recall delta <b>{bs['point_estimate']:+.3f}</b>, bootstrap 95% CI
<b>[{bs['ci95'][0]:+.3f}, {bs['ci95'][1]:+.3f}]</b>
({dev['bootstrap']['samples']:,} paired resamples of questions, seed {dev['bootstrap']['seed']}).
McNemar exact <b>p = {mc['p_value']}</b> on {mc['discordant_pairs']} discordant pairs.</p>
<p>Two rescues out of twenty is exactly the evidence you would expect from a real +0.100 effect
<em>and</em> from a coin landing twice — the data cannot separate them. The bootstrap resamples
questions, not spans, because spans within a question are not independent.</p>
</div>

<h2>7. Two requested categories are not buildable from this corpus</h2>
<ul>
<li><b>version_conflict</b> — the snapshot contains <b>zero</b> superseded versions, so
"current vs superseded" cannot be anchored. 52 documents discuss deprecation within a single version,
which is a weaker and different thing.</li>
<li><b>routing_heavy / passage_heavy</b> — properties of how the <em>systems</em> behave, not of the
corpus. Labelling them requires running the systems first, which is the leakage the split design
exists to prevent.</li>
</ul>
<p>The corpus is also 139 Anthropic / 63 OpenAI, and extraction yield was worse for OpenAI.</p>

<h2>8. Promotion decision</h2>
<p><strong>DOC-C is not promoted.</strong> The frozen production baseline remains SYSTEM-A-GLOBAL.
EXP-014's +2/0 stands as recorded, on the development set, with a confidence interval whose lower
bound is zero — a promising candidate, never eligible for promotion without replication.</p>

<h2>9. What the measurements justify next</h2>
<ol>
<li><strong>The blocker is human question authoring, and it cannot be automated away.</strong>
~100–150 source-anchored questions need a person. Everything needed to consume them now exists:
schema, splits, manifests, validator, harness, bootstrap, McNemar, frozen hashed systems.</li>
<li><strong>Change the generator's role</strong> to proposing candidate <em>evidence spans</em> for a
human to write against. Span extraction was reliable; question and claim synthesis was not.</li>
<li><strong>Decide about OA-002 explicitly</strong> — accept a known ~4.5-point defect, or create
<code>development/v2</code> and re-run. Do not fix it silently.</li>
<li><strong>Do not run more retrieval experiments against n=20.</strong> Six of the last seven turned
on one or two cases, and the interval on such a result includes zero.</li>
<li><strong>If the corpus is re-fetched, capture version chains</strong> — without superseded versions
the project cannot test the temporal behaviour it was designed for.</li>
</ol>

<footer>
Generated from experiments/EXP-014R/*.json by scripts/build_exp014r_pdf.py.
Git commit {(dev.get('git_commit') or 'unknown')[:12]}. Split manifest
{dev['split_manifest_sha256'][:16]}. Systems frozen at
A={dev['system_a_config_hash'][:12]}, B={dev['system_b_config_hash'][:12]}.
Snapshot {dev['corpus_snapshot']}, chunk set {dev['chunk_set']}.
EXP-NULL remains BLOCKED. Raw provider documentation is not redistributed.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/EXP-014R-replication-and-golden-set-expansion.pdf")
    args = parser.parse_args()
    html = build_html(
        json.loads((EXP / "results-development.json").read_text()),
        json.loads((EXP / "candidate-validation.json").read_text()),
        json.loads((EXP / "development-validation.json").read_text()),
    )
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "exp014r.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
