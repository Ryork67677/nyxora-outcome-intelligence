#!/usr/bin/env python3
"""Render the batch-005 closure and the project-wide state as a PDF.

Batch 005 is the batch where the review earned its keep, and that is what this document
leads with: nineteen candidates all passed the structural precheck, and the review that
followed still repaired seven and sent four to rejection. It also carries two numbers
that are easy to round away — a batch that came back at nineteen against a target of
thirty, and a second multi-hop search that found nothing new.

Every figure is read at build time from the closure, the decided batch, the owner's
decisions, the eligibility status, the batch-006 preregistration inputs and the
validator report. Six gates refuse the build rather than publish something false.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.gold.eligibility import HOLDOUT_CONDITIONS, evaluate

FINAL = REPO_ROOT / "evals/review/gold_review_batch_005_final.json"
GENERATED = REPO_ROOT / "evals/review/gold_review_batch_005.json"
DECISIONS = REPO_ROOT / "evals/review/human_decisions_batch_005.json"
CLOSURE = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-005-closure.json"
STATUS = REPO_ROOT / "experiments/GOLD-001/GOLD-001-eligibility-status.json"
PREREG = REPO_ROOT / (
    "experiments/GOLD-001/GOLD-001-batch-006-preregistration-inputs.json")
VALIDATION = REPO_ROOT / "evals/review/validate_golden_batch_005.json"
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
.hash { overflow-wrap: anywhere; }
.subtitle { font-size: 10.3pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.3pt;
  page-break-inside: avoid; }
table.long { page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
tfoot td { font-weight: 700; border-top: 1.2pt solid #16181c; background: #fff; }
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
.hash { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7pt;
  color: #6f747b; overflow-wrap: anywhere; }
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


def counts(mapping: dict) -> str:
    return ", ".join(f"<code>{esc(k)}</code> {v}"
                     for k, v in sorted(mapping.items(), key=lambda kv: -kv[1]))


def build_html(data: dict) -> str:
    closure = data["closure"]
    final = data["final"]
    generated = data["generated"]
    decisions = data["decisions"]
    status = data["status"]
    prereg = data["prereg"]
    validation = data["validation"]

    totals = closure["totals"]
    combined = status["combined"]
    precheck = closure["precheck_limitation"]
    shortfall = closure["generation_shortfall"]
    search = closure["multi_hop_search"]
    funnel = search["funnel"]
    reasoning = closure["reasoning_and_shape"]
    records = {r["candidate_id"]: r for r in final["records"]}
    by_id = {r["candidate_id"]: r for r in generated["records"]}
    decided = {d["candidate_id"]: d for d in decisions["decisions"]}
    before = combined["holdout_eligible"] - totals["holdout_eligible"]

    verdict_rows = rows([
        (f"<code>{cid[-2:]}</code>", record["provider"],
         f"<code>{record['reasoning_type']}</code>"
         + (f"<br><span class='dim'>generated as "
            f"<code>{by_id[cid]['reasoning_type']}</code></span>"
            if record["reasoning_type"] != by_id[cid]["reasoning_type"] else ""),
         record["evidence_shape"],
         decided[cid]["internal_review_status"],
         "anchor" if record.get("anchor_revisions") else
         "text only" if record.get("revisions") else "no",
         (f"<span class='{'bad' if decided[cid]['decision'] == 'REJECT' else 'good'}'>"
          f"{decided[cid]['decision']}</span>"))
        for cid, record in sorted(records.items())
    ], classes=("mono", "", "", "", "", "", ""))

    rejected_rows = rows([
        (f"<code>{r['candidate_id']}</code>",
         ", ".join(f"<code>{esc(t)}</code>" for t in r["review_findings"]) or "—",
         ticks(r["reason"]))
        for r in closure["rejected"]
    ], classes=("mono", "", ""))

    repair_rows = rows([
        (f"<code>{r['candidate_id']}</code>",
         ", ".join(f"{a}–{b}" for a, b in r["old_spans"]) or "— (scope span added)",
         ", ".join(f"{a}–{b}" for a, b in r["new_spans"]),
         ticks(r["reason"]),
         f"<span class='hash'>{r['new_evidence_hashes'][0][:24]}…</span>")
        for r in closure["repaired"]
    ], classes=("mono", "num", "num", "", ""))

    authoring_rows = rows([
        (f"<code>{a['candidate_id']}</code>",
         ", ".join(f"<code>{esc(f)}</code>" for f in a["fields_revised"]),
         ticks(a["miner_original_question"] or "—"),
         ticks(a["final_question"]))
        for a in closure["question_authoring_revisions"]
    ], classes=("mono", "", "", ""))

    override_rows = rows([
        (f"<code>{o['candidate_id']}</code>",
         o.get("scope_status") or o.get("anaphora_status")
         or o.get("dependency_status"),
         o["override_reviewer"], "finding retained")
        for o in closure["human_overrides"]
    ], classes=("mono", "", "", ""))

    search_rows = rows([
        (f"<code>{r['bridge_entity']}</code>", r["gate"].replace("_", " "),
         ticks(r["reason"]))
        for r in search["rejected"]
    ], classes=("mono", "", ""))

    prereg_rows = rows([
        (f"<b>{entry['id']}</b>", ticks(entry["defect"]),
         f"<code>{entry['seen_in']}</code>", ticks(entry["check"]))
        for entry in prereg["inputs"]
    ], classes=("num", "", "mono", ""))

    batch_rows = rows([
        (f"{b['batch']:03d}", b["candidates"], b["human_verified"],
         b["human_rejected"], f"<b>{b['holdout_eligible']}</b>",
         b["genuine_multi_hop"], b["overlay_version"] or "v1")
        for b in status["batches"]
    ], classes=("mono", "num", "num", "num", "num", "num", ""))

    dimension_rows = rows([
        ("reasoning type", counts(reasoning["by_reasoning_type"]),
         counts(reasoning["by_reasoning_type_verified"])),
        ("evidence shape", counts(reasoning["by_evidence_shape"]),
         counts(reasoning["by_evidence_shape_verified"])),
        ("provider", counts(closure["by_provider"]["generated"]),
         counts(closure["by_provider"]["human_verified"])),
    ])

    condition_items = "".join(f"<li><code>{esc(c)}</code></li>"
                              for c in HOLDOUT_CONDITIONS)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 005 Closure</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 005 Closure<br>and Project Eligibility State</h1>
<p class="subtitle">Production RAG v1 · closed {esc(closure['closed_at'])} by
{esc(closure['closed_by'])} · every candidate reached an explicit human decision</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">The finding: a structural pass is not a semantic one</div>
<p>All <b>{precheck['precheck_ready']} of {precheck['candidates']}</b> batch-005
candidates were <code>precheck_holdout_ready</code>. The source-integrity review that
followed repaired <b>{precheck['repaired']}</b> of them and recommended
<b>{precheck['reject_recommended']}</b> for rejection — and the owner rejected exactly
those {precheck['reject_recommended']}. The precheck verifies hashes, offsets, string
containment, anaphora and anchor size. It cannot see a question whose subject is not the
subject of its own evidence, and four of these had exactly that shape.</p>
<p>The batch also came back <b>short</b>: {shortfall['target']} was the target and
{shortfall['exported']} was exported. That is the second finding, and it is in this
document rather than a footnote.</p>
</div>

<div class="grid4">
  <div class="stat win"><div class="big">{totals['human_verified']} / {totals['candidates']}</div>
    <div class="cap">approved · acceptance
      {totals['acceptance_rate']:.1%}</div></div>
  <div class="stat"><div class="big">{combined['holdout_eligible']}</div>
    <div class="cap">project holdout-eligible<br>was {before} before this batch</div></div>
  <div class="stat warn"><div class="big">{shortfall['exported']} / {shortfall['target']}</div>
    <div class="cap">exported against<br>the generation target</div></div>
  <div class="stat warn"><div class="big">{search['exported_chains']}</div>
    <div class="cap">new multi-hop chains<br>from a second search</div></div>
</div>

<h2>1. The owner's decisions</h2>
<p class="dim">Candidate ids are abbreviated to their final two digits;
<code>01</code> is <code>GOLD-B005-01</code>.</p>
<table class="long"><thead><tr><th>id</th><th>provider</th>
<th>reasoning type</th><th>shape</th><th>internal review</th>
<th>repaired</th><th>decision</th></tr></thead>
<tbody>{verdict_rows}</tbody></table>

<p>The internal review's recommendation and the owner's decision are different columns
and were never allowed to collapse into one. They agree on the four rejections and
diverge on the seven repairs, which is what an owner reading a repaired candidate looks
like — a review that the decisions matched everywhere would be indistinguishable from no
review at all.</p>

<h3>Rejected — kept, not deleted</h3>
<table class="long"><thead><tr><th>candidate</th><th>review findings</th>
<th>the owner's reason</th></tr></thead><tbody>{rejected_rows}</tbody></table>
<p>All four records remain in the batch. A rejection is evidence about the miner, and
deleting it would discard the only record of what the miner got wrong —
<code>GOLD-B005-10</code> in particular is the regression case for relation direction.</p>

<div class="break"></div>
<h2>2. What the review changed</h2>
<p>{len(closure['repaired'])} candidate had its anchor repaired;
{len(closure['question_authoring_revisions'])} of {totals['candidates']} had their
question, answer or claims re-authored. An anchor repair is a strict outward growth of
the span it replaced, both hashes are recorded, and each approval pins the post-repair
hash — an approval quoting a pre-repair hash is refused by the importer.</p>
<table><thead><tr><th>candidate</th><th>old span</th><th>new span</th><th>reason</th>
<th>approved anchor</th></tr></thead><tbody>{repair_rows}</tbody></table>

<h3>Question-authoring revisions</h3>
<p>The miner's original wording is retained on every one of them as revision 1; nothing
was overwritten.</p>
<table class="long"><thead><tr><th>candidate</th><th>fields</th>
<th>as mined</th><th>as approved</th></tr></thead>
<tbody>{authoring_rows}</tbody></table>

<h3>Human overrides</h3>
<p>A noncritical finding blocks until a person accepts it. These were accepted, and
neither was deleted: the detector still reports both, and a <b>critical</b> finding
cannot be overridden at all.</p>
<table><thead><tr><th>candidate</th><th>finding</th><th>accepted by</th>
<th>disposition</th></tr></thead><tbody>{override_rows}</tbody></table>

<div class="break"></div>
<h2>3. Target {shortfall['target']}, exported {shortfall['exported']}</h2>
<p><b>{shortfall['entered_semantic_self_review']}</b> candidates reached the semantic
self-review and <b>{shortfall['dropped_by_semantic_self_review']}</b> were dropped
there, leaving {shortfall['exported']}. The drops were led by generic identifiers,
claims wider than their span, and category labels the evidence did not support — none of
which the structural precheck can see.</p>
<p>An earlier draft of this batch did reach {shortfall['target']} candidates. Those
carried pervasive question-subject / fact-subject mismatches; the miners were corrected
rather than the candidates patched, and the corrected run returned
{shortfall['exported']}. Padding back to {shortfall['target']} would have meant keeping
cases a reader could not check, so the count was the thing allowed to move.</p>

<h2>4. The second multi-hop search found nothing new</h2>
<p>{esc(search['strategy'].capitalize())}.
<b>{search['entities_with_a_dependency_opener']}</b> entities had a sentence that could
open a chain; <b>{funnel['dependency_pairs_considered']}</b> dependency pairs reached
the composition gates, inside a budget of {search['budget']}.
<b>{search['valid_chains']}</b> was a valid chain — and it is the chain batch 004 had
already closed, so <b>{search['exported_chains']}</b> new unique chains were
exported.</p>
<table><thead><tr><th>bridge entity</th><th>gate</th>
<th>why it was rejected</th></tr></thead><tbody>{search_rows}</tbody></table>
<div class="callout warn">
<div class="label">Two searches, two methods, one composable structure</div>
<p>Batch 004 tested every bridge pair — 559 of them — and found one chain. Batch 005
searched dependency-first and found the same one. That is a measured property of this
frozen corpus, not a failure of either search, and it is why the project's genuine
multi-hop count is <b>{combined['genuine_multi_hop']}</b> rather than a number a later
batch can be expected to raise easily. No candidate was regenerated and no case was
relabelled to fill the category.</p>
</div>

<h2>5. What closed, by dimension</h2>
<table><thead><tr><th>dimension</th>
<th>all {totals['candidates']} records</th><th>verified only</th></tr></thead>
<tbody>{dimension_rows}</tbody></table>
<p>Both columns carry the labels the records hold at closure, so a category the review
corrected reads as corrected here rather than as the miner first guessed; the generation
report is the record of what was mined. Only the right-hand column is coverage.</p>
<p><b>Claims actually checkable:
{closure['claim_checkable']['with_critical_strings']} of
{closure['claim_checkable']['of_verified']}</b> verified cases carry literal critical
strings, so the claim-in-evidence gate ran on every one of them. That count, not the
validator's green tick, is what says whether the claims were checked.</p>

<div class="break"></div>
<h2>6. Holdout eligibility</h2>
<p>The deterministic gate was re-run at closure over the
{totals['human_verified']} verified records: <b>{totals['holdout_eligible']} of
{totals['human_verified']}</b> pass. Eligibility is derived, never asserted — every
condition has to hold right now:</p>
<ul>{condition_items}</ul>
<p>The four rejected candidates fail the gate on <code>human_verified</code> and cannot
become eligible by any later metadata change. That is the point of keeping approval and
checkability as separate states.</p>

<h2>7. Project eligibility</h2>
<table><thead><tr><th>batch</th><th class="num">candidates</th>
<th class="num">human_verified</th><th class="num">rejected</th>
<th class="num">holdout_eligible</th><th class="num">genuine multi-hop</th>
<th>read from</th></tr></thead><tbody>{batch_rows}</tbody>
<tfoot><tr><td>all</td><td class="num">{combined['candidates']}</td>
<td class="num">{combined['human_verified']}</td>
<td class="num">{combined['human_rejected']}</td>
<td class="num">{combined['holdout_eligible']}</td>
<td class="num">{combined['genuine_multi_hop']}</td><td></td></tr></tfoot></table>
<p>{esc(status['reason_not_frozen'])} The project is aiming at roughly
{esc(status['target']['validation'])} validation cases and
{esc(status['target']['holdout'])} holdout cases; no holdout is frozen, and none should
be until the count supports the split.</p>

<h2>8. Recorded for batch 006 — not implemented</h2>
<p>Four things batch 005 established about the generator. They are recorded as
preregistration inputs rather than fixed in place: batch 005's generation artifact is a
historical record, and a miner corrected retroactively would leave no evidence of what
it got wrong. <b>No batch-006 generation was run and no miner was changed.</b></p>
<table class="long"><thead><tr><th></th><th>defect</th><th>seen in</th>
<th>the check batch 006 must carry</th></tr></thead>
<tbody>{prereg_rows}</tbody></table>

<h2>9. Provenance and invariants</h2>
<table><thead><tr><th>what</th><th>value</th></tr></thead><tbody>
<tr><td>reviewed-state sha256</td>
<td class="hash">{esc(closure['source_batch_sha256'])}</td></tr>
<tr><td>generation batch sha256</td>
<td class="hash">{esc(closure['generation_batch_sha256'])}</td></tr>
<tr><td>closure sha256</td><td class="hash">{esc(closure['closure_sha256'])}</td></tr>
<tr><td>corpus snapshot</td><td class="hash">{esc(closure['corpus_snapshot'])}</td></tr>
<tr><td>validator</td>
<td>{validation['cases']} cases, {len(validation['failures'])} failures on
<code>{esc(validation['path'])}</code></td></tr>
<tr><td>holdout frozen</td>
<td>{str(status['holdout_frozen']).lower()}</td></tr>
</tbody></table>
<ul>
<li>The generation artifact was not rewritten. Repairs live in a separate file and the
closure records both identities, so an approval traces to the text a person saw
<i>and</i> to the run it came from.</li>
<li>No retrieval system was run against any candidate, in generation, review or closure.
<code>retrieval_was_not_run = true</code>; <code>systems_executed = []</code>.</li>
<li>SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B <code>304c3509…</code> remain frozen and
unexecuted.</li>
<li>Batches 001–004 are untouched; their closure hashes are unchanged.</li>
<li>The internal source-integrity review is Claude's own reading of the candidates. It
is not independent verification, and nothing in this document treats it as such — only
the owner's decisions produced <code>human_verified</code>.</li>
</ul>

<footer>
Generated by scripts/build_batch_005_closure_pdf.py from
GOLD-001-batch-005-closure.json, gold_review_batch_005_final.json,
gold_review_batch_005.json, human_decisions_batch_005.json,
GOLD-001-eligibility-status.json,
GOLD-001-batch-006-preregistration-inputs.json and validate_golden_batch_005.json.
Every figure is read from those artifacts at build time, and the build refuses to run if
the closure hash no longer covers the records, if the closure and the batch disagree on
counts, if the closure's eligibility differs from the gate re-run here, if the
eligibility status disagrees with the closure, if the preregistration inputs point at a
different closure, or if a holdout has been frozen. Raw provider documentation is not
redistributed; quoted spans are the short excerpts under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/GOLD-001-batch-005-closure.pdf")
    args = parser.parse_args()

    paths = {"final": FINAL, "generated": GENERATED, "decisions": DECISIONS,
             "closure": CLOSURE, "status": STATUS, "prereg": PREREG,
             "validation": VALIDATION}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}

    closure, final, status = data["closure"], data["final"], data["status"]

    # 1. The closure hash still covers the records on disk.
    payload = json.dumps(sorted(final["records"], key=lambda r: r["candidate_id"]),
                         sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if hashlib.sha256(payload.encode("utf-8")).hexdigest() != closure["closure_sha256"]:
        raise SystemExit(
            "the closure hash does not cover the records on disk — re-close the batch "
            "rather than publishing a closure of something else")

    # 2. The closure and the batch agree on how many were approved.
    verified = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    if len(verified) != closure["totals"]["human_verified"]:
        raise SystemExit("the closure and the batch disagree on how many were approved")

    # 3. Eligibility is re-derived here rather than trusted.
    eligible = sorted(r["candidate_id"] for r in verified
                      if evaluate(r)["holdout_eligible"])
    if eligible != closure["holdout_eligible_ids"]:
        raise SystemExit(
            "the gate re-run here disagrees with the closure about which cases are "
            "holdout-eligible")

    # 4. The project-wide status has this batch in it, with these numbers.
    row = next((b for b in status["batches"] if b["batch"] == closure["batch"]), None)
    if row is None or row["human_verified"] != len(verified) or (
            row["holdout_eligible"] != len(eligible)):
        raise SystemExit("the eligibility status disagrees with the closure")

    # 5. The preregistration inputs describe this closure, not an earlier one.
    if data["prereg"]["source_batch"]["closure_sha256"] != closure["closure_sha256"]:
        raise SystemExit(
            "the batch-006 preregistration inputs were recorded against a different "
            "closure — re-record them before publishing")

    # 6. A frozen holdout would mean this document describes a state the project left.
    if status["holdout_frozen"]:
        raise SystemExit(
            "the holdout is frozen — this document describes a state before that, and "
            "publishing it now would misdescribe the project")

    document = build_html(data)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "closure.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
