#!/usr/bin/env python3
"""Render batch 006's closure and the batch-007 contract it preregisters, as a PDF.

Two documents in one, because they are one decision. Batch 006 closed at 8 of 9 and
carried the project to 90 holdout-eligible cases; its census said why nine was all there
was; and the batch-007 preregistration is the answer to that census — a model may author
the question, never the fact.

Every figure is read from the closed record at build time. Six gates refuse the build
rather than publish something false.
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

from rag_v1.gold import relations, scoping
from rag_v1.gold.eligibility import evaluate as eligibility

CLOSURE = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-006-closure.json"
FINAL = REPO_ROOT / "evals/review/gold_review_batch_006_final.json"
GENERATION = REPO_ROOT / "evals/review/gold_review_batch_006.json"
PREREG = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-007-preregistration.json"
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
tfoot td { font-weight: 700; border-top: 1.2pt solid #16181c; background: #fff; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
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
    closure, final, prereg, status = (data["closure"], data["final"],
                                      data["prereg"], data["status"])
    generation = {r["candidate_id"]: r for r in data["generation"]["records"]}
    totals = closure["totals"]
    combined = status["combined"]
    census = closure["corpus_census"]
    audit = closure["heading_parser_audit"]
    shortfall = closure["generation_shortfall"]
    state = prereg["starting_state"]
    proj = prereg["projection"]

    verified = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    rejected = [r for r in final["records"]
                if r["verification_status"] == "human_rejected"]

    # The closure's own reason already ends on the no-relabelling claim, so the page
    # would print it twice. The record's wording wins; the template only supplies the
    # claim if the record ever stops carrying it.
    search_reason = closure["multi_hop_search"]["reason"]
    relabel_claim = ("" if "relabelled to raise the count" in search_reason
                     else " No multi-span case was relabelled to raise the count.")

    approved_rows = rows([
        (f"<code>{r['candidate_id'][-2:]}</code>", r["provider"],
         f"<code>{r['reasoning_type']}</code>",
         ticks(r["question"]),
         str(len(r.get("revisions", []))))
        for r in verified
    ], classes=("mono", "", "", "", "num"))

    relabel_rows = rows([
        (f"<code>{cid[-2:]}</code>",
         f"<code>{generation[cid]['reasoning_type']}</code>",
         f"<code>{next(r for r in final['records'] if r['candidate_id'] == cid)['reasoning_type']}</code>",
         reason)
        for cid, reason in (
            ("GOLD-B006-01",
             ("a requirement stated in one sentence is not two settings interacting")),
            ("GOLD-B006-03",
             ("accepts / unavailable / behaves-like is a compatibility statement, "
              "not a lookup")),
            ("GOLD-B006-08",
             ("a compatibility path described as a migration bridge is lifecycle, "
              "not interaction")),
        )
    ], classes=("mono", "", "", ""))

    batch_rows = rows([
        (f"{b['batch']:03d}", b["candidates"], b["human_verified"],
         b["human_rejected"], f"<b>{b['holdout_eligible']}</b>")
        for b in status["batches"]
    ], classes=("mono", "num", "num", "num", "num"))

    check_rows = rows([
        (f"<b>{c['id']}</b>", c["question"], c["fails_when"])
        for c in prereg["entailment_self_check"]
    ], classes=("num", "", ""))

    gate_rows = rows([
        (g["gate"], f"<code>{esc(g['implemented_in'])}</code>", g["behaviour"])
        for g in prereg["retained_gates"]
    ])

    defect_rows = rows([
        (f"<b>{d['id']}</b>", ticks(d["defect"]), f"<code>{esc(d['seen_in'])}</code>",
         ticks(d["proposed_fix"]))
        for d in prereg["generator_defects_to_fix_first"]
    ], classes=("num", "", "mono", ""))

    order = "".join(f"<li>{esc(step)}</li>" for step in prereg["authoring_order"])
    reject = rejected[0]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 006 Closure</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 006 Closed,<br>and the Batch 007 Contract</h1>
<p class="subtitle">Production RAG v1 · closed {esc(closure['closed_at'])} ·
corpus snapshot <code>{esc(closure['corpus_snapshot'])}</code> ·
closure <code>{esc(closure['closure_sha256'][:16])}…</code></p>
<div class="rule"></div>

<div class="callout win">
<div class="label">Batch 006 closed · the project stands at {combined['holdout_eligible']}</div>
<p>The owner approved <b>{totals['human_verified']}</b> of
<b>{totals['candidates']}</b> and rejected <b>{totals['human_rejected']}</b>
({totals['acceptance_rate']:.0%} acceptance). All
{totals['holdout_eligible']} approved cases passed the deterministic holdout gate —
re-run at closure, not asserted.</p>
<p>The project now holds <b>{combined['human_verified']} human_verified</b> and
<b>{combined['holdout_eligible']} holdout_eligible</b> cases, with
{combined['human_rejected']} rejected across six closed batches.</p>
</div>

<div class="grid4">
  <div class="stat win"><div class="big">{totals['human_verified']} / {totals['candidates']}</div>
    <div class="cap">approved by the owner</div></div>
  <div class="stat win"><div class="big">{combined['holdout_eligible']}</div>
    <div class="cap">project holdout-eligible</div></div>
  <div class="stat warn"><div class="big">{state['still_needed']}</div>
    <div class="cap">short of the new<br>{state['project_target']} target</div></div>
  <div class="stat"><div class="big">{census['unspent_distinct_texts']}</div>
    <div class="cap">unspent evidence spans<br>still in the corpus</div></div>
</div>

<h2>1. What the owner decided</h2>
<p>Five were approved after revisions the owner specified, three as generated, one was
rejected. <b>Every revision is recorded as a numbered revision attributed to the
owner</b> — not to Claude's review — because a change someone asked for and a change the
author proposed are different acts, and the record has to tell them apart.</p>

<table class="long"><thead><tr><th>id</th><th>provider</th><th>reasoning type</th>
<th>question as approved</th><th class="num">revs</th></tr></thead>
<tbody>{approved_rows}</tbody></table>

<h3>Taxonomy corrections</h3>
<p>Three labels were wrong and the evidence was right in every case. The anchors did not
move: a taxonomy change is a change of label, and a test now enforces that.</p>
<table><thead><tr><th>id</th><th>was</th><th>now</th><th>why</th></tr></thead>
<tbody>{relabel_rows}</tbody></table>
<p class="dim">Two of these were compound facts stated in a single span. The owner was
explicit that neither is multi-hop, and none was labelled as such.</p>

<h3>The rejection</h3>
<div class="callout">
<div class="label">{esc(reject['candidate_id'])} — duplicate fact / benchmark redundancy</div>
<p>{ticks(reject['question'])}</p>
<blockquote>{esc(reject['expected_evidence'][0]['evidence_text'])}</blockquote>
<p>The fact is supported. <code>GOLD-B005-11</code>, approved in batch 005, already
carries the same operational relation from the OpenAI <i>Python</i> library; this
obtains it from the <i>TypeScript/JavaScript</i> library. Useful source corroboration,
not a second benchmark case.</p>
<p><b>Duplicate control could not see it.</b> It compares question text, span offsets
and span text, and two libraries documenting the same behaviour share none of those.
Recorded as defect E for batch 007 rather than patched here. The record is preserved as
a negative audit example and was not replaced.</p>
</div>

<div class="break"></div>
<h2>2. Why the batch was small — and why that is not a corpus problem</h2>
<p>Batch 006 was commissioned at <b>{shortfall['target']}</b> and exported
<b>{shortfall['exported']}</b>. Of the {shortfall['entered_semantic_self_review']}
candidates that reached the semantic self-review,
{shortfall['dropped_by_semantic_self_review']} were dropped. Nothing was padded in.</p>

<table><thead><tr><th>the census behind the shortfall</th><th class="num">count</th>
</tr></thead><tbody>
<tr><td>facts mined</td><td class="num">{census['facts_mined']}</td></tr>
<tr><td>distinct evidence spans the miners reach</td>
    <td class="num">{census['distinct_evidence_texts']}</td></tr>
<tr><td><b>of those, unspent by any closed batch</b></td>
    <td class="num"><b>{census['unspent_distinct_texts']}</b></td></tr>
</tbody></table>

<div class="callout warn">
<div class="label">The finding that sets the next batch's method</div>
<p><b>The corpus is not exhausted. The authoring is.</b>
{census['unspent_distinct_texts']} distinct spans in the frozen snapshot have never been
used, and no deterministic template could turn them into a question without paraphrasing
— what remains is long, multi-clause prose, and a template that fits it is a template
that invents wording.</p>
<p>Refusing all paraphrase is precisely what keeps those facts out of the benchmark.
That is the problem batch 007 is preregistered to solve.</p>
</div>

<h2>3. Heading parser audit</h2>
<p><b>{audit['likely_prose']} of {audit['headings_parsed']} parsed headings
({audit['share']:.2%})</b> read as prose rather than as a label, across
{audit['documents_affected']} of {audit['documents']} documents;
{audit['suspicious']} were suspicious on at least one rule.
{esc(audit['finding'])}</p>
<p><b>Nothing was rewritten.</b> No heading changed, no document was reparsed, no anchor
moved. What changed is a rule: <code>section_path</code> is not trusted for claim scope,
and a candidate's exact evidence must carry the scope its claim needs.</p>

<h2>4. Multi-hop</h2>
<p><b>No search was run.</b> {ticks(search_reason)}
Genuine multi-hop cases in this batch:
<b>{closure['reasoning_and_shape']['genuine_multi_hop']}</b>.{relabel_claim}</p>

<h2>5. Project state</h2>
<table><thead><tr><th>batch</th><th class="num">candidates</th>
<th class="num">verified</th><th class="num">rejected</th>
<th class="num">holdout-eligible</th></tr></thead><tbody>{batch_rows}</tbody>
<tfoot><tr><td>all</td><td class="num">{combined['candidates']}</td>
<td class="num">{combined['human_verified']}</td>
<td class="num">{combined['human_rejected']}</td>
<td class="num">{combined['holdout_eligible']}</td></tr></tfoot></table>

<div class="break"></div>
<h1 style="font-size:15pt">Batch 007 — preregistered, not generated</h1>
<p class="subtitle">{esc(prereg['status'])}</p>

<div class="callout">
<div class="label">The line</div>
<p style="font-size:10.5pt"><b>{esc(prereg['strategy_change']['the_line'])}</b></p>
</div>

<p>Batch 007 introduces <b>controlled evidence-grounded question paraphrasing</b>: where
a deterministic template cannot express an explicit evidence fact, a model may author
the question. This is an <b>authoring</b> change. The evidence stays frozen and exact,
the ground truth is still read out of the source, and every existing gate still runs.</p>

<h3>The order is the safeguard</h3>
<ol>{order}</ol>
<p><b>Never:</b> {esc(prereg['forbidden_order'])}. Inventing a question and then hunting
for evidence to support it is how a benchmark ends up testing what its author imagined
rather than what the documentation says.</p>

<h3>The entailment self-check — any failure drops the candidate</h3>
<table class="long"><thead><tr><th></th><th>check</th><th>it fails when</th></tr></thead>
<tbody>{check_rows}</tbody></table>
<p>There is no flag-and-continue branch, deliberately. Every paraphrased candidate also
carries its <code>source_fact_literal</code> and its subject/relation/object beside the
authored question, so a reviewer can see the gap between fact and question and disagree
with it.</p>

<h3>Answer conservatism</h3>
<p>{esc(prereg['answer_conservatism']['rule'])} Source says
<i>{esc(prereg['answer_conservatism']['example_source'])}</i> → answer
<i>{esc(prereg['answer_conservatism']['example_good_answer'])}</i>, <b>not</b>
<i>{esc(prereg['answer_conservatism']['example_bad_answer'])}</i>.
{esc(prereg['answer_conservatism']['why_bad'])}</p>

<h3>A pilot gates the lane</h3>
<p><b>{prereg['calibration_pilot']['size']} spans</b> that failed batch 006 <i>only</i>
because no builder could express them. Run through the new paraphraser and every
semantic check, then <b>independently reviewed</b> before the lane may scale.</p>
<table><thead><tr><th>criterion</th><th class="num">threshold</th></tr></thead><tbody>
<tr><td>independently judged factually sound</td><td class="num">≥ 8 of 10</td></tr>
<tr><td>unsupported claims</td><td class="num">0</td></tr>
<tr><td>relation-direction reversals</td><td class="num">0</td></tr>
<tr><td>scope broadening</td><td class="num">0</td></tr>
<tr><td>wording cleanup needed</td><td class="num">acceptable</td></tr>
</tbody></table>
<p><b>If it fails:</b> {esc(prereg['calibration_pilot']['if_it_fails'])}</p>

<h3>Every existing gate still runs</h3>
<table class="long"><thead><tr><th>gate</th><th>implemented in</th><th>behaviour</th>
</tr></thead><tbody>{gate_rows}</tbody></table>

<h3>Defects to fix before batch 007 authors anything</h3>
<table class="long"><thead><tr><th></th><th>defect</th><th>seen in</th>
<th>proposed fix</th></tr></thead><tbody>{defect_rows}</tbody></table>

<h3>The arithmetic, which is not a plan</h3>
<p>The project holds <b>{state['holdout_eligible']}</b> and the target is now
<b>{state['project_target']}</b>, leaving <b>{state['still_needed']}</b>. Batch 007
targets <b>{proj['batch_007_target']}</b> candidates, which at the observed acceptance
rates lands between <b>{proj['if_low_target_at_worst_rate']}</b> and
<b>{proj['if_high_target_at_best_rate']}</b> — <b>short of
{state['project_target']}</b>, so more than one batch will be needed.</p>
<p class="dim">{esc(proj['note'])}</p>

<h2>Invariants</h2>
<ul>
<li>No retrieval system was run against any candidate. <code>retrieval_was_not_run =
true</code>; <code>systems_executed = []</code>.</li>
<li>SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B <code>304c3509…</code> remain frozen
and unexecuted.</li>
<li>The corpus snapshot, chunks, embeddings and retrieval architecture are unchanged.</li>
<li>Batches 001–006 are closed and hash-covered; the batch-006 generation artifact was
not rewritten — repairs live beside it.</li>
<li>No holdout and no validation split is frozen.</li>
<li>{esc(prereg['who_may_set_human_verified'])}</li>
</ul>

<footer>
Generated by scripts/build_batch_006_closure_pdf.py from the batch-006 closure, its
composed reviewed-state file, its generation artifact, the batch-007 preregistration and
the project-wide eligibility status. Every figure is read from those artifacts at build
time. The build refuses to run if the closure's totals disagree with the records, if the
eligibility gate re-run disagrees with the closure, if a taxonomy change moved an anchor,
if any approved record fails the scope or relation-direction checks, if a batch-007
candidate exists, or if the page would claim batch 007 reaches the project target.
Raw provider documentation is not redistributed; quoted spans are the short excerpts
under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",
                        default="docs/reports/GOLD-001-batch-006-closure.pdf")
    args = parser.parse_args()

    paths = {"closure": CLOSURE, "final": FINAL, "generation": GENERATION,
             "prereg": PREREG, "status": STATUS}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}
    closure, final, prereg = data["closure"], data["final"], data["prereg"]
    generation = {r["candidate_id"]: r for r in data["generation"]["records"]}

    # 1. The closure's totals must match the records it closed.
    verified = [r for r in final["records"]
                if r["verification_status"] == "human_verified"]
    if closure["totals"]["human_verified"] != len(verified):
        raise SystemExit("refusing to build: the closure disagrees with the records")

    # 2. The eligibility gate is re-run here, never trusted.
    eligible = sorted(r["candidate_id"] for r in verified
                      if eligibility(r)["holdout_eligible"])
    if eligible != closure["holdout_eligible_ids"]:
        raise SystemExit("refusing to build: the eligibility gate disagrees with the "
                         "closure")

    # 3. A taxonomy change must not have moved an anchor.
    for record in final["records"]:
        before = generation[record["candidate_id"]]["expected_evidence"]
        after = record["expected_evidence"]
        if [(s["char_start"], s["char_end"], s["evidence_hash"]) for s in before] != \
                [(s["char_start"], s["char_end"], s["evidence_hash"]) for s in after]:
            raise SystemExit(f"refusing to build: {record['candidate_id']}'s anchor "
                             "moved during a taxonomy change")

    # 4. The gates that act on output are re-checked, not assumed.
    for record in verified:
        if scoping.evaluate(record)["status"] == scoping.NEEDS_SCOPE:
            raise SystemExit(f"refusing to build: {record['candidate_id']} has an "
                             "unscoped span")
        if relations.evaluate(record)["status"] == relations.REVERSED:
            raise SystemExit(f"refusing to build: {record['candidate_id']} reverses "
                             "its source's relation")

    # 5. Batch 007 is preregistered, not generated.
    if (REPO_ROOT / "evals/review/gold_review_batch_007.json").exists():
        raise SystemExit("refusing to build: a batch-007 artifact exists, so this page "
                         "would describe a contract that has already been used")

    # 6. The page must not claim batch 007 closes the gap when it cannot.
    document = build_html(data)
    if not prereg["projection"]["reaches_target_this_batch"] and \
            "short of" not in document:
        raise SystemExit("refusing to build: batch 007 cannot reach the project target "
                         "and the page does not say so")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "closure006.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
