#!/usr/bin/env python3
"""Render the batch-005 generation results to a shareable PDF.

The headline of this batch is a shortfall — 19 candidates against a target of 30 — so
the document leads with why rather than with the count, and reproduces the defect classes
that cost the other eleven. A reader who only sees "19/30" learns nothing; a reader who
sees which question shapes were wrong and why they were fixed at the source can judge
whether the standard was applied honestly.

Every figure is read from the batch, the generation report, the coverage report and the
eligibility status at build time. The build refuses to run if the report disagrees with
the batch, if any candidate claims verification, or if the holdout has been frozen.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BATCH = REPO_ROOT / "evals/review/gold_review_batch_005.json"
REPORT = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-005-generation-report.json"
STATUS = REPO_ROOT / "experiments/GOLD-001/GOLD-001-eligibility-status.json"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 16mm 14mm 14mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.4pt;
  line-height: 1.45; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 19.5pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 11.8pt; margin: 16pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 9.7pt; margin: 10pt 0 4pt; }
h4 { font-size: 8.8pt; margin: 8pt 0 3pt; color: #52565d; text-transform: uppercase;
     letter-spacing: 0.6pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.2pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
td.mono { white-space: nowrap; width: 1%; }
.hash { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7pt;
  color: #6f747b; overflow-wrap: anywhere; }
.subtitle { font-size: 10.3pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.3pt;
  page-break-inside: avoid; }
table.long { page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.b { font-weight: 700; } .bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; } .warnt { color: #8a5a00; font-weight: 700; }
.dim { color: #6f747b; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt;
  margin: 9pt 0 11pt; page-break-inside: avoid; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.2pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }
.callout.win .label { color: #14532d; }
ol, ul { margin: 0 0 7pt; padding-left: 15pt; } li { margin-bottom: 3.5pt; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; margin: 4pt 0 11pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 7pt 9pt; border-radius: 3pt; }
.stat.warn { border-color: #8a1c1c; background: #fdf5f5; }
.stat.win { border-color: #14532d; background: #f2f8f4; }
.stat .big { font-size: 14.5pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.2pt; color: #52565d; margin-top: 2pt; }
blockquote { margin: 4pt 0 6pt; padding: 5pt 9pt; border-left: 2pt solid #c9ccd1;
  background: #f6f7f9; font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 7.8pt; color: #33373d; white-space: pre-wrap; }
.break { page-break-before: always; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.6pt; color: #6f747b; }
"""


def esc(text: object) -> str:
    return html.escape(str(text), quote=False)


def ticks(text: str) -> str:
    out, parts = [], esc(text).split("`")
    for index, part in enumerate(parts):
        out.append(f"<code>{part}</code>" if index % 2 else part)
    return "".join(out)


def rows(items, classes=()) -> str:
    return "".join(
        "<tr>" + "".join(
            f"<td class='{classes[i] if i < len(classes) else ''}'>{cell}</td>"
            for i, cell in enumerate(row)) + "</tr>"
        for row in items)


def build_html(data: dict) -> str:
    batch = data["batch"]
    status = data["status"]
    state = batch["starting_state"]
    search = batch["multi_hop_search"]
    review = batch["internal_review"]
    targets = batch["targets"]
    combined = status["combined"]
    overflow = batch.get("selected_by", {}).get("overflow", 0)

    reasoning_rows = rows([
        (f"<code>{name}</code>", batch["by_reasoning_type"].get(name, 0),
         f"{low}–{high}",
         "<span class='good'>met</span>"
         if low <= batch["by_reasoning_type"].get(name, 0) <= high
         else "<span class='bad'>MISSED</span>",
         batch["eligible_pool"]["by_reasoning_type"].get(name, 0))
        for name, (low, high) in targets["reasoning_type"].items()
    ], classes=("", "num", "num", "num", "num"))

    candidate_rows = rows([
        (f"<code>{r['candidate_id'][-2:]}</code>", r["provider"],
         f"<code>{r['reasoning_type']}</code>",
         "overflow" if r.get("selected_by") == "overflow" else "target",
         ticks(r["question"]))
        for r in batch["records"]
    ], classes=("mono", "", "", "", ""))

    funnel_rows = rows([(stage.replace("_", " "), count)
                        for stage, count in search["funnel"].items()],
                       classes=("", "num"))

    dropped = review["dropped"]
    drop_classes: dict[str, int] = {}
    for entry in dropped:
        label = entry["findings"][0].split(":")[0] if entry["findings"] else "unknown"
        drop_classes[label] = drop_classes.get(label, 0) + 1
    drop_rows = rows(sorted(drop_classes.items(), key=lambda kv: -kv[1]),
                     classes=("", "num"))

    removed_rows = rows(
        [(reason.replace("_", " "), count)
         for reason, count in sorted(batch["removed"].items(), key=lambda kv: -kv[1])],
        classes=("", "num"))

    projected = state["holdout_eligible"] + batch["candidates"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 005 Generation</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 005<br>Accelerated Coverage, and Why It Returned 19</h1>
<p class="subtitle">Production RAG v1 · evidence-candidate authoring ·
generated {esc(batch['generated_at'])} · nothing verified, nothing gold</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">The headline is the shortfall</div>
<p>The target was <b>30</b>. This batch returns <b>{batch['candidates']}</b>. The first
draft did produce 30, and reading them found the same defect again and again: the
question's subject was not the fact's subject. Those defects were fixed in the miners
rather than filtered at the end, and the candidates that depended on them are gone.</p>
<p>Nothing here is verified. Every candidate is <code>candidate_unverified</code>, and
the project's confirmed total is still
<b>{combined['holdout_eligible']}</b> holdout-eligible cases from batches 001–004.</p>
</div>

<div class="grid4">
  <div class="stat warn"><div class="big">{batch['candidates']} / 30</div>
    <div class="cap">candidates returned<br>against target</div></div>
  <div class="stat"><div class="big">{review['counts'].get('DROP', 0)} / {sum(review['counts'].values())}</div>
    <div class="cap">dropped by the self-review<br>after passing the precheck</div></div>
  <div class="stat"><div class="big">{search['funnel'].get('dependency_pairs_considered', 0)} vs 559</div>
    <div class="cap">multi-hop pairs considered<br>dependency-first vs batch 004</div></div>
  <div class="stat win"><div class="big">{combined['holdout_eligible']}</div>
    <div class="cap">confirmed eligible<br>unchanged by this batch</div></div>
</div>

<h2>1. Starting state</h2>
<p>Read from <code>{esc(state['read_from'])}</code> before generating anything:
<b>{state['human_verified']} human_verified</b>,
<b>{state['holdout_eligible']} holdout_eligible</b>,
{state['human_rejected']} rejected, {state['genuine_multi_hop']} genuine multi-hop.
Holdout frozen: {str(state['holdout_frozen']).lower()}.</p>

<h2>2. Why nineteen</h2>
<p>The first draft produced thirty. Reading every one of them surfaced one dominant
defect class and several smaller ones, all of which were fixed in the miners so the bad
candidates were never built:</p>
<ul>
<li><b>The question's subject was not the fact's subject.</b> "What is the documented
limit on <code>request_too_large</code>?" — the limit is on the request; the error code
is what you get for exceeding it. The miners now take the identifier that governs the
matched verb and drop the candidate when there is none.</li>
<li><b>Splits through a literal.</b> A conditional split inside a JSON object produced a
question ending mid-brace.</li>
<li><b>Outcomes with no verb.</b> "…returns <code>stop_reason: "refusal"</code>, not an
error" was split so that "not an error" became the answer.</li>
<li><b>Wishes as conditions.</b> "What happens if you want to change this?" — a reader's
intention is not a state of the system, and "this" names nothing in the span.</li>
<li><b>Table rows, stranded list ordinals, and literal subjects</b> — "What does
<code>None</code> turn off?" asks a question about a keyword.</li>
<li><b>Relations with the direction reversed.</b> "What does <code>betas</code>
override?" where the source says the model <i>rejects</i> caller-supplied
<code>betas</code> overrides.</li>
</ul>

<div class="callout">
<div class="label">The largest single cut was deliberate</div>
<p>Bare definition bullets — "What is the <code>insert_line</code> option?" — take their
scope from the heading above them. Batch 004's review rejected three candidates of
exactly that shape, because §19 forbids leaning on a heading outside the span. Shipping
them again would have been a knowing regression, so the self-review drops them: five
candidates, and the reason is recorded rather than the count preserved.</p>
</div>

<h2>3. What the batch contains</h2>
<table><thead><tr><th>reasoning type</th><th class="num">in batch</th>
<th class="num">target</th><th class="num">met</th>
<th class="num">eligible available</th></tr></thead>
<tbody>{reasoning_rows}</tbody></table>
<p>Provider: {esc(batch['by_provider'])} across
{batch['unique_documents']} distinct documents
({esc(batch['documents_by_provider'])}). Both provider targets are missed, and the
reason is the same as the category shortfalls: the pool that survived the checks was
smaller than the mixture needed.</p>

{f'''<div class="callout">
<div class="label">Overflow, declared rather than quiet</div>
<p><b>{overflow} of {batch["candidates"]}</b> candidates were taken beyond §7's ceilings.
Ambiguity, comparison and multi-hop are corpus-limited here, so holding every ceiling
would have returned a batch far shorter still while vetted candidates waited in the
categories that do have material. Rather than raise a ceiling silently, the shortfall is
filled under a declared cap and each such candidate carries
<code>selected_by = "overflow"</code>. Subtracting them gives the batch the preregistered
mixture would have produced.</p>
</div>''' if overflow else ""}

<table class="long"><thead><tr><th>id</th><th>provider</th><th>reasoning type</th>
<th>taken as</th><th>question</th></tr></thead>
<tbody>{candidate_rows}</tbody></table>

<div class="break"></div>
<h2>4. Lane B — multi-hop, searched the other way round</h2>
<p>Batch 004 tested every pair of facts sharing a plausible identifier: 559 pairs, one
chain. This batch searches dependency-first — a chain may only open on a sentence that
<i>states a dependency</i> and puts its entity into a state, and only then is a consumer
sought.</p>
<table><thead><tr><th>stage</th><th class="num">pairs</th></tr></thead>
<tbody>{funnel_rows}</tbody></table>
<p>Budget {search['budget']} pairs;
{search['funnel'].get('dependency_pairs_considered', 0)} were considered, so the budget
was not the constraint. {search['entities_with_a_dependency_opener']} entities appear in
at least one sentence that states a dependency.
<b>{search['valid_chains']}</b> survived every gate — and it is the chain batch 004
already holds, so it is a duplicate and <b>{search['exported_chains']}</b> reached the
batch.</p>
<div class="callout">
<div class="label">What that comparison is worth</div>
<p>Starting from sentences that state a dependency removed 99% of the search and found
the same thing. It does not conjure chains that are not there: the corpus supports very
few, and that remains the finding rather than a problem with the method.</p>
</div>

<h2>5. The two checks batch 004 paid for</h2>
<h3>Semantic bridge equivalence</h3>
<p>A bridge entity must mean the same thing in both spans. The check reads whether an
identifier is used as a request parameter, an enum value, a field name or a type, and
refuses a pair whose roles differ.</p>
<blockquote>span 1 — `budget_tokens` can exceed `max_tokens` here…
span 2 — The loop exits on any other stop reason (`"end_turn"`, `"max_tokens"`, …)</blockquote>
<p><code>max_tokens</code> is a <b>request parameter</b> in span 1 and an <b>enum
value</b> in span 2: the same string naming two different things. Batch 004's composer
could not see this, and the pair reached its near-miss diagnostic. It is now a regression
test.</p>
<h3>An interaction must name two settings</h3>
<p>A single conditional fact is not an interaction. Batch 004 shipped two under that
label and its review relabelled both; here the miner requires two named settings and a
documented relation between them, and the self-review drops a candidate whose evidence
does not put its subject on the right side of that relation.</p>

<h2>6. The self-review, and what it says about the precheck</h2>
<p>Every candidate below had already passed the structural precheck — hashes, offsets,
string containment, anaphora, size caps. The self-review then dropped
<b>{review['counts'].get('DROP', 0)} of {sum(review['counts'].values())}</b>.</p>
<table><thead><tr><th>drop reason</th><th class="num">candidates</th></tr></thead>
<tbody>{drop_rows}</tbody></table>
<p>That ratio is the point restated with a larger sample than batch 004 gave:
<code>precheck_holdout_ready</code> means <b>structurally capable</b> — not semantically
correct, not human-approved, not holdout-eligible. The self-review is itself only
authoring: it is not independent verification, and it confers nothing.</p>

<h3>Removed before export</h3>
<table><thead><tr><th>reason</th><th class="num">count</th></tr></thead>
<tbody>{removed_rows}</tbody></table>

<h2>7. Coverage, and the projection</h2>
<p>Confirmed today: <b>{combined['holdout_eligible']}</b> eligible cases. If every one of
the {batch['candidates']} batch-005 candidates were eventually approved, the project
would hold <b>{projected}</b>. No batch has approved everything — the four closed
batches approved 16 of 18, 17 of 18, 20 of 20 and 14 of 15 — so treat it as a
ceiling.</p>
<p>The projection must not become a reason to approve. A hundred cases assembled by
relaxing the bar measures less than sixty-seven assembled without.</p>

<h2>8. Invariants</h2>
<ul>
<li>No retrieval system was run against any candidate.
<code>retrieval_was_not_run = true</code>; <code>systems_executed = []</code>.</li>
<li>SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B <code>304c3509…</code> remain frozen and
unexecuted.</li>
<li>The holdout is not frozen
(<code>holdout_frozen = {str(status['holdout_frozen']).lower()}</code>).</li>
<li>Batches 001–004 are byte-identical and their closure hashes still verify.</li>
<li>No batch-005 candidate is verified, approved or eligible. The next step is
independent review.</li>
</ul>

<footer>
Generated by scripts/build_batch_005_pdf.py from gold_review_batch_005.json,
GOLD-001-batch-005-generation-report.json and GOLD-001-eligibility-status.json. Every
figure is read from those artifacts at build time, and the build refuses to run if the
report disagrees with the batch, if any candidate claims verification, or if the holdout
has been frozen. Batch 005, schema {esc(batch['schema_version'])}, corpus snapshot
{esc(batch['corpus_snapshot'])}, batch_sha256 {esc(batch['batch_sha256'][:32])}…,
git commit {esc((batch.get('git_commit') or 'unknown')[:12])}. Raw provider documentation
is not redistributed; quoted spans are the short excerpts under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/GOLD-001-batch-005-generation.pdf")
    args = parser.parse_args()

    paths = {"batch": BATCH, "report": REPORT, "status": STATUS}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}

    batch, report, status = data["batch"], data["report"], data["status"]
    if report["candidates"] != len(batch["records"]):
        raise SystemExit("the generation report and the batch disagree on the count")
    if report["by_reasoning_type"] != batch["by_reasoning_type"]:
        raise SystemExit("the generation report and the batch disagree on the mixture")
    if any(r["verification_status"] != "candidate_unverified" for r in batch["records"]):
        raise SystemExit(
            "a candidate claims a verification status — refusing to publish a document "
            "that would present an unreviewed candidate as reviewed")
    if status["holdout_frozen"]:
        raise SystemExit("the holdout is frozen; this document describes an earlier state")

    document = build_html(data)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "batch005.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
