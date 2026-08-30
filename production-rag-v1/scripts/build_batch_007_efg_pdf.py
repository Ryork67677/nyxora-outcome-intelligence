#!/usr/bin/env python3
"""Render the batch-007 E/F/G implementation and the blocked calibration pilot as a PDF.

The finding leads: the three preregistered generator fixes are implemented and verified
against the real candidates that revealed them, and the calibration pilot **did not
run**, because the frozen evidence it must draw from is not in this environment. A page
that opened on three green fixes and put the pilot in a footnote would be describing a
batch that is further along than it is.

Every figure is read from the artifacts at build time. Eleven gates refuse the build
rather than publish something false — including one that refuses to render if a batch-007
candidate or pilot artifact has appeared, because then this page is describing a state
the project has left, and one that refuses to render the independent automated review as
anything but a recommendation, because only the project owner approves.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.gold import questionscope, reasoningtype  # noqa: E402
from rag_v1.gold.factidentity import duplicate_facts  # noqa: E402

RECORD = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-007-efg-fixes.json"
PREREG = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-007-preregistration.json"
STATUS = REPO_ROOT / "experiments/GOLD-001/GOLD-001-eligibility-status.json"
BATCH_006 = REPO_ROOT / "evals/review/gold_review_batch_006_final.json"
BATCH_006_GEN = REPO_ROOT / "evals/review/gold_review_batch_006.json"
BATCH_005 = REPO_ROOT / "evals/review/gold_review_batch_005_final.json"
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
h1 { font-size: 19pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 11.8pt; margin: 16pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 9.7pt; margin: 10pt 0 4pt; }
p { margin: 0 0 6pt; }
code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.2pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
td.mono { white-space: nowrap; width: 1%; }
.subtitle { font-size: 10.3pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.3pt;
  page-break-inside: avoid; }
table.long { page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c;
     color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.ok { color: #14532d; font-weight: 700; }
.no { color: #8a1c1c; font-weight: 700; }
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
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt;
  margin: 4pt 0 11pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 7pt 9pt; border-radius: 3pt; }
.stat.warn { border-color: #8a1c1c; background: #fdf5f5; }
.stat.win { border-color: #14532d; background: #f2f8f4; }
.stat .big { font-size: 14.5pt; font-weight: 700; line-height: 1.1;
  letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.2pt; color: #52565d; margin-top: 2pt; }
blockquote { margin: 4pt 0 6pt; padding: 5pt 9pt; border-left: 2pt solid #c9ccd1;
  background: #f6f7f9; font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 7.6pt; color: #33373d; white-space: pre-wrap; }
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
    record = data["record"]
    state = record["state_verified_before_any_change"]
    fix_e, fix_f, fix_g = record["fixes_implemented"]
    pilot = record["calibration_pilot"]
    finding = record["finding_for_reviewer"]
    review = record["independent_automated_review"]
    checklist = record["blocker_recovery_checklist"]
    search = record["recovery_search"]
    host = record["host_side_recovery_evidence"]
    published = record["published_results_evidence"]
    archive = record["chatgpt_project_archive_evidence"]
    safeguards = record["reproducibility_safeguards_added"]

    arc = archive["archive"]
    archive_rows = rows([
        ("path", f"<code>{esc(arc['path'])}</code>"),
        ("size", f"{arc['size_bytes']:,} bytes"),
        ("sha256", f"<code>{esc(arc['sha256'])}</code>"),
        ("root", f"<code>{esc(arc['root'])}</code>"),
        ("top level", ", ".join(f"<code>{esc(t)}</code>" for t in arc["top_level"])),
    ])
    finding_items = "".join(f"<li>{ticks(f)}</li>" for f in archive["audit_findings"])
    corroboration_blocks = "".join(
        f"<h3>{ticks(c['check'])}</h3><p>{ticks(c['result'])}</p>"
        f"<p class='dim'><i>Method:</i> {ticks(c['method'])}"
        + (f"<br><i>Note:</i> {ticks(c['note'])}" if c.get("note") else "")
        + "</p>"
        for c in archive["corroborated_in_session"])

    ref_rows = rows([
        (f"<code>{esc(r['reference'])}</code>", ticks(r["found"]), ticks(r["carries"]))
        for r in published["references_chased"]])
    cov = published["coverage_measured_here"]
    cov_rows = rows([
        ("artifact files scanned", f"{cov['artifact_files_scanned']}"),
        ("distinct version ids persisted",
         f"<b>{cov['distinct_version_ids_persisted']}</b> of {cov['corpus_documents']}"),
        ("distinct version ids from closed GOLD",
         f"{cov['distinct_version_ids_from_closed_gold']}"),
        ("document content hashes persisted",
         f"<b class='no'>{cov['document_content_hashes_persisted']}</b> of "
         f"{cov['corpus_documents']}"),
    ], classes=("", "num"))
    narrow = published["narrowest_remaining_artifact"]

    host_rows = rows([
        (f"<b>{ticks(f['area'])}</b>",
         ticks(f["result"])
         + (f"<br><i>{ticks(f['inference'])}</i>" if f.get("inference") else ""))
        for f in host["findings"]])
    host_locations = ", ".join(f"<code>{esc(loc)}</code>"
                               for loc in host["locations_searched"])
    host_wanted = "".join(f"<li>{ticks(a)}</li>"
                          for a in host["artifacts_looked_for"])
    prereg = data["prereg"]

    search_rows = rows([
        (f"<b>{ticks(ps['path'])}</b>", ticks(ps["method"]), ticks(ps["result"]))
        for ps in search["paths_searched"]])
    constraint_items = "".join(f"<li>{ticks(c)}</li>"
                               for c in search["constraints_observed"])
    required = search["remaining_external_artifact_required"]
    option_blocks = "".join(
        f"<h3>{key.replace('_', ' ').title()} — {ticks(required[key]['artifact'])}</h3>"
        + "<ul>" + "".join(f"<li>{ticks(m)}</li>"
                           for m in required[key]["must_contain"])
        + f"<li><i>Produced by:</i> {ticks(required[key]['produced_by'])}</li>"
        + (f"<li><i>Note:</i> {ticks(required[key]['note'])}</li>"
           if required[key].get("note") else "")
        + "</ul>"
        for key in ("option_a", "option_b"))
    safeguard_rows = rows([
        (f"<b>{sg['id']}</b>", ticks(sg["need"]), ticks(sg["provides"]),
         ticks(sg["verified_by"]))
        for sg in safeguards["safeguards"]], classes=("num", "", "", ""))
    refuse_items = "".join(f"<li>{ticks(r)}</li>"
                           for r in safeguards["harness"]["refuses_unless"])

    review_items = "".join(
        f"<h3>{esc(r['id'])}. {ticks(r['text'])}</h3><p>{ticks(r['rationale'])}</p>"
        for r in review["recommendation"])

    prohibition_items = "".join(f"<li>{ticks(h)}</li>"
                                for h in checklist["hard_prohibitions"])
    step_rows = rows([
        (f"<b>{s['step']}</b>",
         f"<b>{ticks(s['action'])}</b><br>{ticks(s['detail'])}",
         f"<i>Expected:</i> {ticks(s['expected'])}<br>"
         f"<i>Done when:</i> {ticks(s['done_when'])}")
        for s in checklist["steps"]
    ], classes=("num", "", ""))

    state_rows = rows([
        ("human_verified", f"<b>{state['human_verified']}</b>", "<span class='ok'>PASS</span>"),
        ("holdout_eligible", f"<b>{state['holdout_eligible']}</b>", "<span class='ok'>PASS</span>"),
        ("human_rejected", f"<b>{state['human_rejected']}</b>", "<span class='ok'>PASS</span>"),
        ("genuine multi-hop", state["genuine_multi_hop"], "<span class='ok'>PASS</span>"),
        ("closure sha256",
         f"<code>{esc(state['closure_sha256_recomputed'][:24])}…</code>",
         "<span class='ok'>recomputed, PASS</span>"),
        ("retrieval_was_not_run", f"<code>{str(state['retrieval_was_not_run']).lower()}</code>",
         "<span class='ok'>PASS</span>"),
        ("systems_executed", "<code>[]</code>", "<span class='ok'>PASS</span>"),
        ("SYSTEM-A / SYSTEM-B", "<code>9afcb5b7…</code> / <code>304c3509…</code>",
         "<span class='ok'>frozen, unchanged</span>"),
        ("batch-007 candidate or pilot artifact", "none",
         "<span class='ok'>PASS</span>"),
    ], classes=("", "mono", ""))

    f_rows = rows([
        (f"<code>{r['candidate_id'][-2:]}</code>",
         f"<code>{r['generated_label']}</code>",
         f"<code>{r['owner_label']}</code>",
         f"<code>{r['derived_label']}</code>",
         ("<span class='ok'>PASS</span>" if r["agrees_with_owner"]
          else "<span class='no'>FAIL</span>")
         + (" <b>relabelled</b>" if r["was_relabelled_by_owner"] else ""))
        for r in fix_f["result"]["per_candidate"]
    ], classes=("mono", "", "", "", ""))

    g_rows = rows([
        (f"<code>{cid[-2:]}</code>",
         f"<code>{fix_g['result']['as_generated_correctly_dropped'][cid]}</code>"
         " — <span class='ok'>dropped</span>",
         f"<code>{fix_g['result']['as_approved_pass'][cid]}</code>"
         " — <span class='ok'>exports</span>")
        for cid in sorted(fix_g["result"]["as_generated_correctly_dropped"])
    ], classes=("mono", "", ""))

    why_items = "".join(
        f"<li><b>{esc(w['finding'])}.</b> {ticks(w['evidence'])}</li>"
        for w in pilot["why"])

    threshold_rows = rows([
        (k.replace("_", " "), v["threshold"],
         "<span class='no'>not measured — pilot not run</span>")
        for k, v in pilot["thresholds_not_measurable"].items()
    ])

    files_items = "".join(f"<li><code>{esc(f)}</code> (new)</li>"
                          for f in record["invariants_held"]["files_added"])

    return f"""<title>Batch 007 E/F/G Fixes</title>
<style>{CSS}</style>
<h1>GOLD-001 — Batch 007 Fixes E/F/G,<br>and the Pilot That Could Not Run</h1>
<p class="subtitle">Production RAG v1 · {esc(record['written_at'])} · corpus snapshot
<code>{esc(record['corpus_snapshot'])}</code> · commit
<code>{esc(record['git_commit'][:12])}</code></p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">The finding</div>
<p><b>The calibration pilot did not run.</b> The three preregistered generator defects
are implemented and verified against the real candidates that revealed them. The pilot
the preregistration requires before the paraphrasing lane may scale could not be run:
the frozen evidence it must draw from is not present in this environment, and no
substitute for it is admissible. <b>The paraphrasing lane does not scale, and no
batch-007 candidate has been authored.</b></p>
</div>

<div class="grid4">
<div class="stat win"><div class="big">3 / 3</div>
<div class="cap">preregistered fixes implemented</div></div>
<div class="stat win"><div class="big">{esc(fix_f['result']['agreement_with_owner'])}</div>
<div class="cap">whole-sentence labels agreeing with the owner</div></div>
<div class="stat warn"><div class="big">0 / 10</div>
<div class="cap">pilot cases authored — input unobtainable</div></div>
<div class="stat"><div class="big">{state['holdout_eligible']}</div>
<div class="cap">project holdout-eligible, unchanged</div></div>
</div>

<h2>1. State verified before anything was written</h2>
<table><thead><tr><th>reads</th><th>value</th><th></th></tr></thead>
<tbody>{state_rows}</tbody></table>
<p>The closure hash was <b>recomputed</b> from the nine closed batch-006 records rather
than read off the closure, so the state is checked rather than quoted.</p>

<h2>2. E — cross-library duplicate facts</h2>
<p><code>{esc(fix_e['implemented_in'])}</code></p>
<p>{ticks(fix_e['behaviour'])}</p>
<p><b>The pair the owner caught is now visible.</b> <code>GOLD-B005-11</code> (OpenAI
Python library) and <code>GOLD-B006-06</code> (TypeScript/JavaScript library) share no
question text, no span offsets and no span text — which is exactly why the old
comparison could not see them. Both now normalise to the triple
<code>{esc(tuple(fix_e['result']['shared_triple']))}</code>, and the second is flagged.</p>
<blockquote>B005-11  Pass `base_url` to `bedrock(...)` or set `AWS_BEDROCK_BASE_URL` to override the derived `https://bedrock-mantle.&lt;region&gt;.api.aws/openai/v1` endpoint.
B006-06  … and `AWS_BEDROCK_BASE_URL` can override the endpoint.</blockquote>
<p>Batch 005 predates the triple fields, so its triple is <b>derived from its frozen
evidence</b> — never from its question, because the evidence is the part that cannot
drift. Within batch 006 the check raises
<b>{fix_e['result']['false_positives_within_batch_006']}</b> false positives. It
<b>flags and never drops</b>: two libraries genuinely differing in behaviour is a real
case, and only a reviewer can tell that apart from a restatement.</p>

<h2>3. F — reasoning type read from the whole sentence</h2>
<p><code>{esc(fix_f['implemented_in'])}</code></p>
<p>{ticks(fix_f['behaviour'])}</p>
<table class="long"><thead><tr><th>id</th><th>generated</th><th>owner</th>
<th>whole-sentence</th><th></th></tr></thead><tbody>{f_rows}</tbody></table>
<p><b>{esc(fix_f['result']['agreement_with_owner'])}</b> agreement with the owner's
labels, including all <b>{fix_f['result']['relabelled_cases_now_correct']}</b> the owner
had to relabel. Lifecycle is tested first, whatever the verb: a compatibility sentence
almost always also contains a lookup verb, and reading it as a lookup is precisely how
<code>GOLD-B006-03</code> was mislabelled.</p>

<h2 class="break">4. G — a scoped source needs a scoped question</h2>
<p><code>{esc(fix_g['implemented_in'])}</code></p>
<p>{ticks(fix_g['behaviour'])}</p>
<table><thead><tr><th>id</th><th>as generated</th><th>as owner-approved</th></tr></thead>
<tbody>{g_rows}</tbody></table>
<p>The second condition is the one with teeth. A qualifier that appears in the question
but in no critical string is decoration: nothing downstream reads it. Requiring it in the
critical strings is what turns this from a style rule into a gate.</p>

<div class="callout">
<div class="label">A finding the reviewer must decide — {esc(finding['id'])}</div>
<p>{ticks(finding['detail'])}</p>
<p><i>{esc(finding['status'])}.</i></p>
</div>

<div class="callout warn">
<div class="label">{esc(review['label'])}</div>
<p>{ticks(review['authority'])}</p>
<p class="dim">Recorded {esc(review['recorded_at'])} · concerns
{esc(review['concerns'])}</p>
</div>
{review_items}
<p><b>Consequence accepted.</b> {ticks(review['consequence_accepted'])}</p>
<p><b>What this changes in the code:</b>
{ticks(review['what_this_changes_in_the_code'])}
<b>Status of the finding:</b>
{ticks(review['status_of_finding_after_this_recommendation'])}</p>

<h2>5. The calibration pilot was not run</h2>
<div class="callout warn">
<div class="label">Blocked</div>
<p>{ticks(pilot['status'])}</p>
</div>
<p>The preregistration fixes the pilot's input exactly: <i>10 evidence spans that failed
batch 006 ONLY because no builder could express them — NO_BUILDER / UNBUILDABLE.</i>
That input cannot be obtained here, on four independent grounds.</p>
<ol>{why_items}</ol>
<p>{ticks(pilot['what_was_not_done_and_why'])}</p>

<h3>The four thresholds, unmeasured</h3>
<table><thead><tr><th>criterion</th><th>threshold</th><th>measured</th></tr></thead>
<tbody>{threshold_rows}</tbody></table>
<p><b>To unblock:</b> {ticks(pilot['to_unblock'])}</p>
<p>Until the pilot runs and is independently reviewed, the paraphrasing lane does not
scale. The preregistration is explicit that a failed pilot means revising the authoring
contract and re-piloting — not proceeding — and an <i>absent</i> pilot is not a weaker
condition than a failed one.</p>

<h3>Recovery checklist</h3>
<p>{ticks(checklist['purpose'])}</p>
<div class="callout warn">
<div class="label">Not admissible as a substitute for the frozen corpus</div>
<ul>{prohibition_items}</ul>
</div>
<table class="long"><thead><tr><th class="num">#</th><th>step</th>
<th>expected / done when</th></tr></thead><tbody>{step_rows}</tbody></table>

<h2 class="break">6. Recovery search — every path, and what was in it</h2>
<div class="callout warn">
<div class="label">{esc(search['conclusion'])}</div>
<p>{ticks(search['question'])}</p>
<p class="dim">Searched {esc(search['performed_at'])}</p>
</div>
<table class="long"><thead><tr><th>path searched</th><th>method</th><th>result</th>
</tr></thead><tbody>{search_rows}</tbody></table>
<p><b>Constraints observed throughout.</b></p>
<ul>{constraint_items}</ul>

<h2>7. Host-side recovery evidence</h2>
<div class="callout warn">
<div class="label">{esc(host['label'])}</div>
<p>{ticks(host['authority'])}</p>
<p class="dim">Recorded {esc(host['recorded_at'])} · {esc(host['scope'])}</p>
</div>
<p><b>Provenance.</b> {ticks(host['provenance'])}</p>
<p><b>Locations searched.</b> {host_locations}</p>
<p><b>Looked for:</b></p>
<ul>{host_wanted}</ul>
<table class="long"><thead><tr><th>area</th><th>result</th></tr></thead>
<tbody>{host_rows}</tbody></table>
<p><b>Conclusion.</b> {ticks(host['conclusion'])}</p>
<div class="callout">
<div class="label">What this does not establish</div>
<p>{ticks(host['what_this_does_not_establish'])}</p>
</div>

<h2 class="break">8. The ChatGPT-project archive lead, closed</h2>
<div class="callout warn">
<div class="label">{esc(archive['label'])}</div>
<p>{ticks(archive['authority'])}</p>
<p class="dim">Recorded {esc(archive['recorded_at'])} · lead:
{esc(archive['lead'])}</p>
</div>
<p><b>Provenance.</b> {ticks(archive['provenance'])}</p>
<p><b>Conclusion.</b> {ticks(archive['conclusion'])}</p>
<table><thead><tr><th>the archive</th><th></th></tr></thead>
<tbody>{archive_rows}</tbody></table>
<p><b>The audit found:</b></p>
<ul>{finding_items}</ul>
<p class="dim">Constraints: {esc('; '.join(archive['audit_constraints']))}.</p>
<h3>Corroborated inside this container</h3>
{corroboration_blocks}
<div class="callout">
<div class="label">The August 17 architecture packet</div>
<p>{ticks(archive['architecture_packet']['finding'])}
{ticks(archive['architecture_packet']['verdict'])}</p>
</div>
<div class="callout">
<div class="label">What this does not establish</div>
<p>{ticks(archive['what_this_does_not_establish'])}</p>
</div>

<h2 class="break">9. The 2026-08-17 published results, assessed</h2>
<div class="callout warn">
<div class="label">{esc(published['conclusion'].split(' — ')[0])}</div>
<p>{ticks(published['conclusion'])}</p>
<p class="dim">{esc(published['artifact'])} · assessed
{esc(published['assessed_at'])}</p>
</div>
<p><b>What it confirms.</b> Snapshot
<code>{esc(published['what_it_confirms']['snapshot_id'])}</code>;
<b>{published['what_it_confirms']['documents']}</b> documents;
<b>{published['what_it_confirms']['chunks']:,}</b> chunks; and
{published['what_it_confirms']['v1_evidence_spans']} evidence spans in the v1 run.
{ticks(published['what_it_confirms']['arithmetic_checked_here'])}</p>
<p><b>Why it cannot recover the corpus.</b>
{ticks(published['why_it_cannot_recover_the_corpus'])}</p>
<table class="long"><thead><tr><th>reference chased</th><th>found</th>
<th>what it carries</th></tr></thead><tbody>{ref_rows}</tbody></table>
<table><thead><tr><th>coverage measured here</th><th class="num"></th></tr></thead>
<tbody>{cov_rows}</tbody></table>
<p>{ticks(cov['verdict'])}</p>
<div class="callout win">
<div class="label">What it does make possible</div>
<p>{ticks(published['what_it_does_make_possible']['summary'])}</p>
<p><b>Implemented.</b> {ticks(published['what_it_does_make_possible']['implemented'])}</p>
<p><b>Not identity.</b>
{ticks(published['what_it_does_make_possible']['explicitly_not_identity'])}</p>
</div>

<h2>10. The narrowest remaining artifact</h2>
<p><b>Narrowed from</b> {ticks(narrow['narrowed_from'])} <b>to</b>
{ticks(narrow['narrowed_to'])}</p>
<p><b>Why this is enough.</b> {ticks(narrow['why_this_is_enough'])}</p>
<p><b>Why nothing narrower works.</b> {ticks(narrow['why_nothing_narrower_works'])}</p>
<p><b>Environment prerequisite.</b> {ticks(narrow['environment_prerequisite'])}</p>

<h2>11. The earlier statement of the required artifact</h2>
<p>{ticks(required['summary'])}</p>
{option_blocks}
<div class="callout warn">
<div class="label">Environment prerequisite</div>
<p>{ticks(required['environment_prerequisite'])}</p>
</div>
<p><b>Acceptance test.</b> {ticks(required['acceptance_test'])}</p>

<h2>12. Reproducibility safeguards added</h2>
<p>{ticks(safeguards['why'])}</p>
<p>Implemented in <code>{esc(safeguards['implemented_in'])}</code>, tested in
<code>{esc(safeguards['tested_in'])}</code>.</p>
<table class="long"><thead><tr><th class="num"></th><th>need</th><th>provides</th>
<th>verified by</th></tr></thead><tbody>{safeguard_rows}</tbody></table>
<p><b>Harness — <code>{esc(safeguards['harness']['script'])}</code>.</b>
{ticks(safeguards['harness']['purpose'])}</p>
<p><i>{ticks(safeguards['harness']['does_not_modify'])}</i></p>
<p>It refuses unless:</p>
<ul>{refuse_items}</ul>
<p>{ticks(safeguards['harness']['verified_now'])}</p>

<h2>13. Invariants</h2>
<ul>
<li><code>retrieval_was_not_run</code> is still <code>true</code> and
<code>systems_executed</code> is still <code>[]</code>. No retrieval system was run
against any candidate at any point; SYSTEM-A and SYSTEM-B remain frozen and unexecuted.</li>
<li>Closed batches modified: <b>{record['invariants_held']['closed_batches_modified']}</b>.
Dataset records modified:
<b>{record['invariants_held']['dataset_records_modified']}</b>. Eligibility state
modified: <b>{str(record['invariants_held']['eligibility_state_modified']).lower()}</b>.</li>
<li>Validation and holdout were neither inspected nor modified; no split is frozen.</li>
<li><code>human_verified</code> set by this work:
<b>{record['invariants_held']['human_verified_set_by_this_work']}</b>.
{esc(prereg['who_may_set_human_verified'])}</li>
<li>Files added, none modified:<ul>{files_items}</ul></li>
</ul>
<p><b>Next:</b> {ticks(record['next_step'])}</p>

<footer>Generated by <code>scripts/build_batch_007_efg_pdf.py</code> from the E/F/G
implementation record, the batch-007 preregistration, the project-wide eligibility status
and the closed batch-005 and batch-006 records. Every figure is read from those artifacts
at build time. The build refuses to run if the record's state disagrees with the
eligibility status, if the E/F/G checks re-run here disagree with the recorded results,
if a batch-007 candidate or pilot artifact exists, or if the page would claim the pilot
ran. Raw provider documentation is not redistributed; quoted spans are the short excerpts
under review.</footer>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",
                        default="docs/reports/GOLD-001-batch-007-efg-fixes.pdf")
    args = parser.parse_args()

    paths = {"record": RECORD, "prereg": PREREG, "status": STATUS,
             "batch_006": BATCH_006, "batch_006_gen": BATCH_006_GEN,
             "batch_005": BATCH_005}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}
    record, status = data["record"], data["status"]
    b006 = {r["candidate_id"]: r for r in data["batch_006"]["records"]}
    b005 = {r["candidate_id"]: r for r in data["batch_005"]["records"]}
    gen006 = {r["candidate_id"]: r for r in data["batch_006_gen"]["records"]}

    # 1. The record's starting state must still be the project's state.
    state = record["state_verified_before_any_change"]
    if (state["holdout_eligible"] != status["combined"]["holdout_eligible"]
            or state["human_rejected"] != status["combined"]["human_rejected"]
            or state["human_verified"] != status["combined"]["human_verified"]):
        raise SystemExit("refusing to build: the record's state disagrees with the "
                         "eligibility status")

    # 2. Retrieval must still not have been run. This page asserts it on every page.
    if status["retrieval_was_not_run"] is not True or status["systems_executed"] != []:
        raise SystemExit("refusing to build: retrieval state has changed")

    # 3. Fix F is re-run here, never trusted: the recorded agreement must reproduce.
    for row in record["fixes_implemented"][1]["result"]["per_candidate"]:
        derived = reasoningtype.evaluate(b006[row["candidate_id"]])["derived"]
        if derived != row["derived_label"]:
            raise SystemExit(f"refusing to build: fix F no longer derives "
                             f"{row['derived_label']} for {row['candidate_id']}")

    # 4. Fix G is re-run here too, on both the generated and the approved forms.
    result_g = record["fixes_implemented"][2]["result"]
    for cid, expected in result_g["as_generated_correctly_dropped"].items():
        if questionscope.evaluate(gen006[cid])["status"] != expected:
            raise SystemExit(f"refusing to build: fix G no longer drops {cid}")
    for cid, expected in result_g["as_approved_pass"].items():
        if questionscope.evaluate(b006[cid])["status"] != expected:
            raise SystemExit(f"refusing to build: fix G changed its verdict on {cid}")

    # 5. Fix E must still see the pair the owner caught.
    flags = duplicate_facts([b006["GOLD-B006-06"]], [b005["GOLD-B005-11"]])
    if not flags or flags[0]["status"] != "duplicate_fact":
        raise SystemExit("refusing to build: fix E no longer flags the pair it was "
                         "written for")

    # 6. The pilot must still be un-run, and no batch-007 candidate may exist. If either
    #    changed, this page describes a state the project has left.
    if record["calibration_pilot"]["run"] is not False:
        raise SystemExit("refusing to build: the record says the pilot ran")
    for path in (REPO_ROOT / "evals/review/gold_review_batch_007.json",
                 REPO_ROOT / "evals/review/gold_review_batch_007_pilot.json"):
        if path.exists():
            raise SystemExit(f"refusing to build: {path.name} exists, so this page "
                             "would describe a state the project has left")

    # 7. The independent automated review is a recommendation, and the page must never
    #    render it as anything else. Only the owner approves; a page that let a
    #    recommendation read as approval would be manufacturing an approval nobody gave.
    review = record["independent_automated_review"]
    if review["is_project_owner_approval"] is not False:
        raise SystemExit("refusing to build: the recommendation is marked as owner "
                         "approval, which no automated review can give")
    if "NOT PROJECT-OWNER APPROVAL" not in review["label"]:
        raise SystemExit("refusing to build: the recommendation's label does not "
                         "disclaim owner approval")
    if record["finding_for_reviewer"]["id"] not in review["concerns"]:
        raise SystemExit("refusing to build: the recommendation does not name the "
                         "finding it concerns")

    # 8. The page describes a failed recovery. If a corpus has since been restored and
    #    verified, this page is stale and must not be republished as current.
    if not record["recovery_search"]["conclusion"].startswith("NO"):
        raise SystemExit("refusing to build: the recovery search no longer concludes the "
                         "corpus is unavailable, so this page is stale")
    unbuildable = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-006-unbuildable.json"
    if unbuildable.exists():
        raise SystemExit("refusing to build: an unbuildable-span manifest exists, so the "
                         "blocker this page describes has been cleared")

    # 9. The host-side search is external evidence relayed to this session, not an
    #    approval and not something this session verified. The page must say both.
    host = record["host_side_recovery_evidence"]
    if host["is_project_owner_approval"] is not False:
        raise SystemExit("refusing to build: host-side evidence is marked as owner "
                         "approval, which a filesystem search cannot be")
    if "NOT PROJECT-OWNER APPROVAL" not in host["label"]:
        raise SystemExit("refusing to build: the host-side evidence label does not "
                         "disclaim owner approval")
    if "NOT performed or independently confirmed" not in host["provenance"]:
        raise SystemExit("refusing to build: the host-side evidence does not disclose "
                         "that this session did not verify it")
    if not host["conclusion"].startswith("NO"):
        raise SystemExit("refusing to build: the host-side search no longer concludes the "
                         "corpus is absent, so this page is stale")

    # 10. The published results are evidence about the corpus, not the corpus. If this
    #     record ever claims otherwise, the page would be describing a recovery that did
    #     not happen.
    published = record["published_results_evidence"]
    if not published["conclusion"].startswith("INSUFFICIENT FOR RECOVERY"):
        raise SystemExit("refusing to build: the published-results assessment no longer "
                         "concludes the attachment is insufficient for recovery")
    if published["coverage_measured_here"]["document_content_hashes_persisted"] != 0:
        raise SystemExit("refusing to build: the record claims persisted document content "
                         "hashes, which would change the recovery verdict — re-measure")

    # 11. The archive audit is relayed external evidence that closed a lead negatively.
    #     It is not approval, was not verified here, and must not read as a recovery.
    archive = record["chatgpt_project_archive_evidence"]
    if archive["is_project_owner_approval"] is not False:
        raise SystemExit("refusing to build: the archive audit is marked as owner "
                         "approval, which an archive listing cannot be")
    if "NOT PROJECT-OWNER APPROVAL" not in archive["label"]:
        raise SystemExit("refusing to build: the archive audit label does not disclaim "
                         "owner approval")
    if "NOT performed or independently confirmed" not in archive["provenance"]:
        raise SystemExit("refusing to build: the archive audit does not disclose that "
                         "this session did not verify it")
    if not archive["conclusion"].startswith("LEAD CLOSED"):
        raise SystemExit("refusing to build: the archive audit no longer closes the lead, "
                         "so this page is stale")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    document = build_html(data)
    if "NOT PROJECT-OWNER APPROVAL" not in document:
        raise SystemExit("refusing to build: the rendered page does not carry the "
                         "recommendation's disclaimer")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "efg007.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
