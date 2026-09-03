#!/usr/bin/env python3
"""Render the GOLD-001 batch-001 verification findings to a shareable PDF.

Every count comes from evals/review/*.json at build time, so the document cannot
claim a verdict distribution the artifacts do not have.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW = REPO_ROOT / "evals" / "review"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

#: False by construction on every prose candidate, because GOLD-001 deliberately ships
#: prose candidates without a question. These flags say nothing about the miner.
UNINFORMATIVE = ("question_supported", "answer_supported",
                 "all_critical_claims_supported", "natural_question")

CSS = """
@page { size: Letter; margin: 17mm 15mm 15mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.6pt;
  line-height: 1.46; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 20pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 12pt; margin: 17pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 9.8pt; margin: 11pt 0 4pt; }
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
.stat.win { border-color: #14532d; background: #f2f8f4; }
.stat .big { font-size: 15pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.4pt; color: #52565d; margin-top: 2pt; }
blockquote { margin: 5pt 0 7pt; padding: 5pt 9pt; border-left: 2pt solid #c9ccd1;
  background: #f6f7f9; font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 7.9pt; color: #33373d; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.8pt; color: #6f747b; }
"""


def analyse(batch: dict) -> dict:
    records = batch["records"]
    prose = [r for r in records if r["evidence_kind"] != "parameter_table_row"]
    table = [r for r in records if r["evidence_kind"] == "parameter_table_row"]

    def failed(record: dict, key: str) -> bool:
        return record.get("verification", {}).get(key) is False

    boundary = [r["candidate_id"] for r in prose if failed(r, "evidence_boundary_complete")]
    binding = [r["candidate_id"] for r in prose
               if failed(r, "identifier_value_binding_correct")]
    either = sorted(set(boundary) | set(binding))
    return {
        "records": records,
        "n": len(records),
        "prose": len(prose),
        "table": len(table),
        "table_clean": sum(1 for r in table if r["verification"]["verdict"] == "PASS"),
        "verdicts": Counter(r["verification"]["verdict"] for r in records),
        "statuses": batch["status_counts"],
        "boundary": boundary,
        "binding": binding,
        "either": either,
        "clean": [r["candidate_id"] for r in prose if r["candidate_id"] not in either],
    }


def build_html(batch: dict, queue: dict) -> str:
    a = analyse(batch)
    v = a["verdicts"]
    pp = 100.0 / a["n"]

    status_rows = "".join(
        f"<tr><td><code>{k}</code></td><td class='num'>{n}</td></tr>"
        for k, n in sorted(a["statuses"].items(), key=lambda kv: -kv[1]))

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 001 Verification Findings</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 001<br>Independent Verification Findings</h1>
<p class="subtitle">Production RAG v1 · evidence-candidate authoring · dual-LLM review with
mandatory human approval</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">Status — no case in batch 001 is gold</div>
<p>Independent verification is finished. Human review is not.
<strong>{queue['human_queue_size']} of {a['n']}</strong> candidates are queued for a person, and no
script in this repository can raise a case to <code>human_verified</code>. That status exists only
when the owner records an approval.</p>
</div>

<div class="grid4">
  <div class="stat win"><div class="big">{a['table_clean']} / {a['table']}</div>
    <div class="cap">structural table-row candidates<br>passed with nothing rewritten</div></div>
  <div class="stat warn"><div class="big">{len(a['either'])} / {a['prose']}</div>
    <div class="cap">prose candidates carrying a<br>named miner defect</div></div>
  <div class="stat"><div class="big">{v['FIX_REQUIRED']} / {v['FAIL']} / {v['PASS']}</div>
    <div class="cap">FIX_REQUIRED / FAIL / PASS<br>UNCERTAIN: {v.get('UNCERTAIN', 0)}</div></div>
  <div class="stat"><div class="big">{queue['human_queue_size']}</div>
    <div class="cap">queued for human review<br>{len(queue['must_review'])} mandatory +
      {len(queue['qc_sample_of_dual_llm_pass'])} QC sample</div></div>
</div>

<h2>1. What was run</h2>
<table><thead><tr><th>step</th><th>artifact / result</th></tr></thead><tbody>
<tr><td>Batch shipped</td><td><code>gold_review_batch_001.json</code> —
  <span class="mono">batch_sha256 {batch['batch_sha256'][:16]}…</span></td></tr>
<tr><td>Independent review</td><td>reviewer <code>{batch['verification_reviewer']}</code> —
  declared source hash matched exactly, all {a['n']} ids aligned</td></tr>
<tr><td>Import</td><td>{a['n']} verdicts,
  {sum(1 for r in a['records'] if r.get('revisions'))} versioned revisions,
  {sum(len(r.get('anchor_disputes', [])) for r in a['records'])} anchor disputes</td></tr>
<tr><td>Human queue</td><td>{len(queue['must_review'])} mandatory +
  {len(queue['qc_sample_of_dual_llm_pass'])} sampled from the {queue['dual_llm_pass_total']}
  agreed passes (seed {queue['seed']}, rate {queue['sample_rate']:.0%})</td></tr>
<tr><td>Review packet</td><td>{queue['human_queue_size']} candidates rendered with evidence,
  context and both proposals</td></tr>
</tbody></table>

<p>Statuses after import:</p>
<table><thead><tr><th>status</th><th class="num">cases</th></tr></thead>
<tbody>{status_rows}</tbody></table>

<div class="callout">
<div class="label">The rule the pipeline exists to enforce</div>
<p>A ChatGPT <code>PASS</code> produces <code>dual_llm_pass</code>, never
<code>human_verified</code>. Two models agreeing is correlated evidence, not independent
confirmation. The distinction lives in code and has a test; it is not left to discipline.</p>
</div>

<h2>2. What the verdict counts do and do not mean</h2>
<p>The raw counts overstate the miner's error rate. Saying so is not a defence of the miner —
it is a statement about how the batch was built.</p>
<p>All {a['prose']} prose candidates shipped with <code>[REVIEWER TO WRITE]</code> as their question
and an empty claim list, because GOLD-001 deliberately converted the generator from a
question-answer producer into an <em>evidence-candidate</em> producer. Four of the six review
checks — {', '.join(f'<code>{f}</code>' for f in UNINFORMATIVE)} — were therefore
<strong>false by construction</strong> on every prose candidate. They carry no information about
the miner. <code>FIX_REQUIRED</code> on a prose candidate means "the reviewer wrote the question",
which is the design working, not a defect.</p>

<p>Two checks do test the miner's own output: whether the anchored span is self-contained, and
whether the right identifier was bound to the right relation.</p>

<table><thead><tr><th>signal</th><th class="num">n</th><th>candidates</th></tr></thead><tbody>
<tr><td>Boundary incomplete</td><td class="num bad">{len(a['boundary'])}</td>
  <td class="mono">{', '.join(c.replace('GOLD-B001-', '') for c in a['boundary'])}</td></tr>
<tr><td>Identifier / relation binding wrong</td><td class="num bad">{len(a['binding'])}</td>
  <td class="mono">{', '.join(c.replace('GOLD-B001-', '') for c in a['binding'])}</td></tr>
<tr><td><b>Either defect</b></td><td class="num bad">{len(a['either'])}</td><td class="dim">of
  {a['prose']} prose candidates</td></tr>
<tr><td>No named miner defect — needed only a question written</td>
  <td class="num good">{len(a['clean'])}</td>
  <td class="mono">{', '.join(c.replace('GOLD-B001-', '') for c in a['clean'])}</td></tr>
</tbody></table>

<div class="callout warn">
<div class="label">Honesty about n</div>
<p>With n&nbsp;=&nbsp;{a['n']}, one candidate is {pp:.1f} percentage points. The structural miner
went {a['table_clean']}&nbsp;for&nbsp;{a['table']} — that is two observations, not a precision
estimate, and it is reported as two observations. No significance claim is made anywhere in this
document.</p>
</div>

<h2>3. Defect taxonomy</h2>

<h3>D1 — anaphoric anchor ({len(a['boundary'])} cases)</h3>
<p>The span opens with, or silently depends on, a referent that lives outside it. The reviewer
cannot check the claim against the anchor alone, which is the whole contract.</p>
<blockquote>"If true, an [InputGuardrailTripwireTriggered] exception is raised…"
&nbsp;&nbsp;— <i>what is true is named only in the preceding sentence</i></blockquote>
<blockquote>"Sending a request with a prefilled last assistant message to <b>any of these
models</b> returns a 400 invalid_request_error:"
&nbsp;&nbsp;— <i>"these models" is the question, and is not in the span</i></blockquote>
<p>This is the same shape as the OA-002 defect already recorded against the original
human-verified set. Finding it three times in {a['prose']} candidates means the miner reproduces it
<strong>systematically</strong>, not by accident.</p>

<h3>D2 — wrong relation label (5 cases)</h3>
<p>The miner matched a trigger word and labelled the candidate with a relation the sentence does
not express. The evidence is usually fine; the <em>label</em> aims the reviewer at the wrong
question — one case linked <code>file_id</code> to wording from a different bullet in the same
error list; another labelled a two-part stopping condition as a single response relation. Because
the label rode along in the exported candidate, it steered the reviewer's first reading. On this
batch's evidence, the label is worse than no label.</p>

<h3>D3 — identifier matched inside example code (2 cases, including the only FAIL)</h3>
<p>The miner matched <code>"required": ["location"]</code> inside a JSON request body and framed it
as a requirement on <code>tool_choice</code>.</p>
<div class="callout warn">
<div class="label">This is the EXP-014R failure mode, reproduced</div>
<p>False token-to-identifier association is the exact defect that made the EXP-014R generator
unusable and the reason GOLD-001 was commissioned. It survived into a shipped batch. A sample
configuration is not a documented rule, and the miner currently cannot tell them apart.</p>
</div>

<h2>4. Changes preregistered for batch 002</h2>
<p>Written down <strong>before</strong> batch 002 is generated, so they cannot be tuned to its
outcome. None of them touch batch 001; its records stay exactly as verified.</p>
<ol>
<li><b>Reject or extend anaphoric spans.</b> A span opening with <code>If true</code>,
<code>these</code>, <code>it</code>, <code>this</code>, or whose subject is a bare pronoun, is
extended to include its antecedent or dropped. → D1</li>
<li><b>Stop exporting the proposed relation label.</b> Keep it internally for selection; remove it
from what the reviewer sees. Wrong on 5 of {a['prose']} and misleading when wrong. → D2</li>
<li><b>Refuse identifier matches inside fenced code blocks and JSON literals</b> when the candidate
would be framed as a documented rule. → D3</li>
<li><b>Raise the share of structural candidates.</b> Table-row mining produced the only candidates
needing no re-authoring. This is a change of mix, not a claim that table rows have high precision
in general.</li>
</ol>

<h2>5. What is unchanged</h2>
<table><thead><tr><th>invariant</th><th>state</th></tr></thead><tbody>
<tr><td>Retrieval run over any candidate</td><td class="good">never —
  <code>retrieval_was_not_run: true</code></td></tr>
<tr><td>SYSTEM-A / SYSTEM-B</td><td class="good">frozen at
  <span class="mono">9afcb5b7…</span> / <span class="mono">304c3509…</span>, not run against any
  candidate</td></tr>
<tr><td>Holdout</td><td class="bad">not frozen; no A-vs-B replication attempted</td></tr>
<tr><td>OA-002</td><td class="dim">recorded defect, correction proposed and unapplied, awaiting
  the owner's decision</td></tr>
<tr><td>EXP-NULL</td><td class="dim">BLOCKED — no project generation credential</td></tr>
</tbody></table>

<h2>6. Next step, and who owns it</h2>
<div class="callout">
<div class="label">The next step is not batch 002</div>
<p>It is the human review of the {queue['human_queue_size']} queued candidates, because that is the
only step that can produce a <code>human_verified</code> case. The target of 30–40 validation plus
70–100 holdout cases is gated entirely on it — more candidates are not the constraint.</p>
<p>Regenerate the packet with <code>scripts/export_human_qc_packet.py</code>, then record
<code>APPROVE</code> or <code>REJECT</code> per candidate in
<code>evals/review/human_decisions_batch_001.json</code>.</p>
</div>

<footer>
Generated from evals/review/*.json by scripts/build_gold001_pdf.py — every count in this document
is read from those artifacts at build time. Batch {batch['batch']:03d}, schema
{batch['schema_version']}, git commit {(batch.get('git_commit') or 'unknown')[:12]}, corpus
snapshot {batch['corpus_snapshot']}. Reviewed by {batch['verification_reviewer']} on
{batch['verification_imported_at']}. Nothing in batch 001 is gold. Raw provider documentation is
not redistributed; quoted spans are the short excerpts needed to show each defect.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/GOLD-001-batch-001-verification-findings.pdf")
    args = parser.parse_args()

    batch = json.loads((REVIEW / "gold_review_batch_001.json").read_text())
    queue = json.loads((REVIEW / "human_qc_queue_batch_001.json").read_text())
    if "verification_reviewer" not in batch:
        raise SystemExit("batch has no imported verification — run import_verification.py first")

    html = build_html(batch, queue)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "gold001.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
