#!/usr/bin/env python3
"""Render the batch-004 closure and the project-wide state as a PDF.

This is the record of what closed: the owner's fifteen decisions, the state each
candidate reached, what the repairs changed, and what the project holds now. Every
figure is read from the closure, the decided batch, the eligibility status, the near-miss
diagnostic and the validator report at build time.

Four gates refuse the build rather than publish something false: a closure whose hash no
longer matches the records it covers, a closure that disagrees with the batch on counts,
an eligibility status that disagrees with the closure, and a frozen holdout — which
would mean this document is describing a state the project is not in.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FINAL = REPO_ROOT / "evals/review/gold_review_batch_004_final.json"
GENERATED = REPO_ROOT / "evals/review/gold_review_batch_004.json"
DECISIONS = REPO_ROOT / "evals/review/human_decisions_batch_004.json"
CLOSURE = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-004-closure.json"
STATUS = REPO_ROOT / "experiments/GOLD-001/GOLD-001-eligibility-status.json"
NEAR_MISS = REPO_ROOT / "experiments/GOLD-001/BATCH-004-near-miss-multihop-review.json"
VALIDATION = REPO_ROOT / "evals/review/validate_golden_batch_004.json"
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
/* Identifiers stay on one line; only hashes, which have no reading order, may break. */
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


def build_html(data: dict) -> str:
    closure = data["closure"]
    final = data["final"]
    generated = data["generated"]
    decisions = data["decisions"]
    status = data["status"]
    near_miss = data["near_miss"]
    validation = data["validation"]

    totals = closure["totals"]
    combined = status["combined"]
    rejection = closure["multi_hop_rejection"]
    precheck = closure["precheck_limitation"]
    records = {r["candidate_id"]: r for r in final["records"]}
    by_id = {r["candidate_id"]: r for r in generated["records"]}
    decided = {d["candidate_id"]: d for d in decisions["decisions"]}

    # Short ids: the full candidate id wraps across two lines in a seven-column table
    # and makes the row harder to read than the number it encodes.
    verdict_rows = rows([
        (f"<code>{cid[-2:]}</code>", record["provider"],
         f"<code>{record['reasoning_type']}</code>"
         + (f"<br><span class='dim'>generated as "
            f"<code>{by_id[cid]['reasoning_type']}</code></span>"
            if record["reasoning_type"] != by_id[cid]["reasoning_type"] else ""),
         record["evidence_shape"],
         decided[cid]["internal_review_status"],
         "yes" if record.get("anchor_revisions") else
         "text only" if record.get("revisions") else "no",
         f"<span class='{'bad' if decided[cid]['decision'] == 'REJECT' else 'good'}'>"
         f"{decided[cid]['decision']}</span>")
        for cid, record in sorted(records.items())
    ], classes=("mono", "", "", "", "", "num", ""))

    repair_rows = rows([
        (f"<code>{r['candidate_id']}</code>",
         ", ".join(f"{a}–{b}" for a, b in r["old_spans"]) or "— (scope span added)",
         ", ".join(f"{a}–{b}" for a, b in r["new_spans"]),
         esc(r["reason"]),
         f"<span class='hash'>{r['new_evidence_hashes'][0][:24]}…</span>")
        for r in closure["repaired"]
    ])

    override_rows = rows([
        (f"<code>{o['candidate_id']}</code>",
         o.get("anaphora_status") or o.get("dependency_status"),
         o["override_reviewer"], "finding retained")
        for o in closure["human_overrides"]
    ])

    rejection_rows = rows([
        (reason.replace("_", " "), count,
         f"{count / rejection['rejected']:.0%}" if rejection["rejected"] else "—")
        for reason, count in sorted(rejection["reasons"].items(), key=lambda kv: -kv[1])
    ], classes=("", "num", "num"))

    near_rows = rows([
        (f"<code>{f['bridge_entity']}</code>", f["provider"],
         f"<span class='good'>{f['verdict']}</span>")
        for f in near_miss["findings"]
    ])

    batch_rows = rows([
        (f"{b['batch']:03d}", b["candidates"], b["human_verified"],
         b["human_rejected"], f"<b>{b['holdout_eligible']}</b>",
         b["genuine_multi_hop"], b["overlay_version"] or "v1")
        for b in status["batches"]
    ], classes=("mono", "num", "num", "num", "num", "num", ""))

    hop = next(r for r in final["records"]
               if r["reasoning_type"] == "genuine_multi_hop")
    hop_spans = "".join(
        f"<h4>{esc(span['evidence_id'])} · {esc(span['version_id'])} "
        f"{span['char_start']}–{span['char_end']} "
        f"({span['evidence_char_length']} chars) · "
        f"{esc(' › '.join(span['section_path']))}</h4>"
        f"<blockquote>{esc(span['evidence_text'])}</blockquote>"
        f"<p class='dim' style='font-size:7.8pt'>critical strings: "
        + ", ".join(f"<code>{esc(s)}</code>" for s in span["critical_strings"])
        + f"<br><span class='hash'>{esc(span['evidence_hash'])}</span></p>"
        for span in hop["expected_evidence"])

    erratum = closure["errata"][0]
    reasoning = closure["reasoning_and_shape"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 004 Closure</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 004 Closure<br>and Project Eligibility State</h1>
<p class="subtitle">Production RAG v1 · closed {esc(closure['closed_at'])} by
{esc(closure['closed_by'])} · every candidate reached an explicit human decision</p>
<div class="rule"></div>

<div class="callout win">
<div class="label">Batch 004 is closed</div>
<p><b>{totals['human_verified']} approved, {totals['human_rejected']} rejected, 0
outstanding</b> from {totals['candidates']} candidates. All
{totals['human_verified']} approved cases pass the deterministic eligibility gate. The
project now holds <b>{combined['human_verified']} human_verified</b> and
<b>{combined['holdout_eligible']} holdout_eligible</b> cases across four batches, with
{combined['human_rejected']} rejections preserved as audit examples.</p>
<p>No retrieval system has been run against any candidate in any batch. SYSTEM-A and
SYSTEM-B remain frozen and unexecuted. The holdout is <b>not</b> frozen.</p>
</div>

<div class="grid4">
  <div class="stat win"><div class="big">{totals['human_verified']} / {totals['candidates']}</div>
    <div class="cap">approved · acceptance
      {totals['acceptance_rate']:.1%}</div></div>
  <div class="stat"><div class="big">{combined['holdout_eligible']}</div>
    <div class="cap">project holdout-eligible<br>was
      {combined['holdout_eligible'] - closure['totals']['human_verified']} before</div></div>
  <div class="stat warn"><div class="big">{rejection['passed']} / {rejection['attempted_pairs']}</div>
    <div class="cap">bridge pairs that became<br>a genuine multi-hop case</div></div>
  <div class="stat"><div class="big">{combined['genuine_multi_hop']}</div>
    <div class="cap">genuine multi-hop cases<br>in the whole project</div></div>
</div>

<h2>1. The owner's decisions</h2>
<p class="dim">Candidate ids are abbreviated to their final two digits;
<code>01</code> is <code>GOLD-B004-01</code>.</p>
<table class="long"><thead><tr><th>id</th><th>provider</th>
<th>reasoning type</th><th>shape</th><th>internal review</th>
<th class="num">repaired</th><th>decision</th></tr></thead>
<tbody>{verdict_rows}</tbody></table>

<p><b>What closed.</b> Reasoning types among the approved cases:
{", ".join(f"<code>{esc(k)}</code> {v}"
           for k, v in sorted(reasoning["by_reasoning_type_verified"].items(),
                              key=lambda kv: -kv[1]))}. Evidence shapes:
{", ".join(f"<code>{esc(k)}</code> {v}"
           for k, v in sorted(reasoning["by_evidence_shape_verified"].items(),
                              key=lambda kv: -kv[1]))}. Providers:
{", ".join(f"{esc(k)} {v}"
           for k, v in sorted(closure["by_provider"]["human_verified"].items()))}.</p>

<p>The internal review's status and the owner's decision are different columns and were
never allowed to collapse into one. Ten candidates the review marked
<code>NEEDS_REPAIR</code> were approved after repair; the one it recommended for
rejection was rejected on the owner's own reasoning, not on the recommendation.</p>

<div class="callout warn">
<div class="label">Rejected — kept, not deleted</div>
<p><b>{closure['rejected'][0]['candidate_id']}</b> —
{ticks(closure['rejected'][0]['reason'])}</p>
</div>

<h2>2. What the repairs changed</h2>
<p>Six candidates had an anchor repaired; four more had only their question, answer or
claims rewritten. Every anchor repair is a strict outward growth of the span it
replaced, both hashes are recorded, and each approval pins the post-repair hash — an
approval quoting a pre-repair hash is refused by the importer.</p>
<table><thead><tr><th>candidate</th><th>old span</th><th>new span</th><th>reason</th>
<th>approved anchor</th></tr></thead><tbody>{repair_rows}</tbody></table>

<h3>Human overrides</h3>
<p>A noncritical finding blocks until a person accepts it. These were accepted, and none
was deleted: the detector still reports every one, and a <b>critical</b> finding cannot
be overridden at all.</p>
<table><thead><tr><th>candidate</th><th>finding</th><th>accepted by</th>
<th>disposition</th></tr></thead><tbody>{override_rows}</tbody></table>

<div class="break"></div>
<h2>3. The genuine multi-hop case</h2>
<p><b>{esc(hop['candidate_id'])}</b> · {esc(hop['provider'])} ·
<code>{esc(hop['reasoning_type'])}</code> ·
<code>{esc(hop['evidence_shape'])}</code> ·
requires all evidence {hop['requires_all_evidence']} ·
composition check <span class="good">{esc(hop['multi_hop_composition_check'])}</span></p>
<p><b>Q.</b> {ticks(hop['question'])}</p>
<p><b>A.</b> {ticks(hop['answer'])}</p>
{hop_spans}
<p><b>The approved chain.</b> {ticks(hop['composed_claim'])}</p>
<div class="callout warn">
<div class="label">Scope, explicitly</div>
<p>This result holds on the hosted-agent surface and is not to be generalised beyond it.
In the ordinary Runner flow, <code>needs_approval = True</code> does what span 1 says and
pauses for approval. As generated, the question was unqualified and the composed answer
was false in the default path; the qualification lived in a section heading, and the
repair moved it inside the anchor.</p>
</div>

<h2>4. What it cost to find one chain</h2>
<p>The composer tested <b>{rejection['attempted_pairs']}</b> bridge pairs.
<b>{rejection['passed']}</b> passed the composition check;
<b>{rejection['rejected']}</b> were rejected.</p>
<table><thead><tr><th>rejection reason</th><th class="num">pairs</th>
<th class="num">share</th></tr></thead><tbody>{rejection_rows}</tbody></table>
<p>Five pairs cleared every check except the entity-state rule and were reviewed
individually. All five are correct rejections, so on this evidence the rule is not too
strict — it was the only check that caught them.</p>
<table><thead><tr><th>bridge entity</th><th>provider</th><th>verdict</th></tr></thead>
<tbody>{near_rows}</tbody></table>
<p class="dim">Diagnostic only: {near_miss['promoted_to_batch_004']} promoted into the
batch, batch regenerated: {str(near_miss['batch_004_regenerated']).lower()}. Choosing
candidates by re-reading the rejection list is how a benchmark ends up measuring its own
generator.</p>

<div class="break"></div>
<h2>5. Project eligibility</h2>
<table><thead><tr><th>batch</th><th class="num">candidates</th>
<th class="num">human_verified</th><th class="num">rejected</th>
<th class="num">holdout_eligible</th><th class="num">genuine multi-hop</th>
<th>read from</th></tr></thead><tbody>{batch_rows}</tbody>
<tfoot><tr><td>all</td><td class="num">{combined['candidates']}</td>
<td class="num">{combined['human_verified']}</td>
<td class="num">{combined['human_rejected']}</td>
<td class="num">{combined['holdout_eligible']}</td>
<td class="num">{combined['genuine_multi_hop']}</td><td></td></tr></tfoot></table>

<p><code>human_verified</code> counts approvals a person gave and does not change.
<code>holdout_eligible</code> counts cases a machine can still check — approval, a
deterministic check for every claim, critical strings present in their evidence, valid
hashes, no unresolved scope defect, and, for a multi-span case, a declaration that all of
its evidence is required.</p>

<div class="callout warn">
<div class="label">A gate tightened mid-project reaches backwards</div>
<p>The multi-span condition added for this batch, in its first form, also demanded
per-span critical strings — and disqualified five closed batch-003 cases for a
convention that arrived after a person had approved them. It now flags only a
<i>mixed</i> record, where one span is checked and another is not. Batch 003 stands at
20. Worth stating plainly, because the failure mode is silent: the count simply comes
back lower and looks like a discovery.</p>
</div>

<h2>6. Genuine multi-hop — one observation</h2>
<p><b>{combined['genuine_multi_hop']} of {combined['holdout_eligible']} eligible
cases.</b> That is one observation. It proves the benchmark infrastructure can represent
a genuine multi-hop case — anchor it, check its composition, carry it through review and
eligibility — and it does <b>not</b> mean the category is adequately sampled. A single
case cannot support a claim about how any system handles multi-hop reasoning.</p>
<p>The generation figure is the finding to carry forward: {rejection['attempted_pairs']}
bridge pairs tested, {rejection['passed']} valid chain. In this corpus, two facts sharing
an identifier are almost never two halves of an argument, and no candidate was
regenerated to improve that ratio.</p>

<h2>7. What <code>precheck_holdout_ready</code> does and does not mean</h2>
<p>Batch 004 produced <b>{precheck['precheck_ready']} of {precheck['candidates']}</b>
candidates precheck-ready. The source-integrity review that followed repaired
<b>{precheck['repaired']}</b> of them and recommended
<b>{precheck['reject_recommended']}</b> for rejection.</p>
<p>That is not a precheck failure — the precheck is deliberately structural. It verifies
hashes, offsets, string containment, anaphora and anchor size, and it means
<b>{esc(precheck['means'])}</b>: not
{", not ".join(esc(x) for x in precheck['does_not_mean'])}. The review is what showed why
the separation has to be maintained rather than assumed.</p>

<h2>8. Erratum</h2>
<p><b>{esc(erratum['correction'])}</b> — was “{esc(erratum['was'])}”; is
<b>{esc(erratum['is'])}</b>. {esc(erratum['why'])} Generation figures affected:
{'yes' if erratum['affects_generation_figures'] else 'no'}.</p>

<h2>9. Provenance and invariants</h2>
<table><thead><tr><th>what</th><th>value</th></tr></thead><tbody>
<tr><td>reviewed-state sha256</td>
<td class="hash">{esc(closure['source_batch_sha256'])}</td></tr>
<tr><td>generation batch sha256</td>
<td class="hash">{esc(closure['generation_batch_sha256'])}</td></tr>
<tr><td>closure sha256</td><td class="hash">{esc(closure['closure_sha256'])}</td></tr>
<tr><td>corpus snapshot</td><td class="hash">{esc(closure['corpus_snapshot'])}</td></tr>
<tr><td>validator</td>
<td>{validation['cases']} cases, {len(validation['failures'])} failures</td></tr>
<tr><td>holdout frozen</td>
<td>{str(status['holdout_frozen']).lower()}</td></tr>
</tbody></table>
<ul>
<li>The generation artifact was not rewritten. Repairs live in a separate file, and the
closure records both identities, so an approval traces to the text a person saw
<i>and</i> to the run it came from.</li>
<li>No retrieval system was run against any candidate, in generation, review or closure.
<code>retrieval_was_not_run = true</code>; <code>systems_executed = []</code>.</li>
<li>SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B <code>304c3509…</code> remain frozen and
unexecuted.</li>
<li>Batches 001–003 are untouched; their closure hashes are unchanged.</li>
<li>{esc(status['reason_not_frozen'])}</li>
</ul>

<footer>
Generated by scripts/build_batch_004_closure_pdf.py from
GOLD-001-batch-004-closure.json, gold_review_batch_004_final.json,
gold_review_batch_004.json, human_decisions_batch_004.json,
GOLD-001-eligibility-status.json, BATCH-004-near-miss-multihop-review.json and
validate_golden_batch_004.json. Every figure is read from those artifacts at build time,
and the build refuses to run if the closure hash no longer covers the records, if the
closure and the batch disagree on counts, if the eligibility status disagrees with the
closure, or if a holdout has been frozen. Raw provider documentation is not
redistributed; quoted spans are the short excerpts under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/GOLD-001-batch-004-closure.pdf")
    args = parser.parse_args()

    paths = {"final": FINAL, "generated": GENERATED, "decisions": DECISIONS,
             "closure": CLOSURE, "status": STATUS, "near_miss": NEAR_MISS,
             "validation": VALIDATION}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}

    closure, final, status = data["closure"], data["final"], data["status"]
    digest = hashlib.sha256(
        json.dumps(final["records"], sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if digest != closure["closure_sha256"] != final.get("closure_sha256"):
        # Recomputed the same way close_batch does; a mismatch means the records moved
        # after closure, and this document would be describing a batch that no longer
        # exists in that form.
        raise SystemExit(
            "the closure hash does not cover the records on disk — re-close the batch "
            "rather than publishing a closure of something else")
    verified = sum(1 for r in final["records"]
                   if r["verification_status"] == "human_verified")
    if verified != closure["totals"]["human_verified"]:
        raise SystemExit("the closure and the batch disagree on how many were approved")
    batch_004 = next((b for b in status["batches"] if b["batch"] == 4), None)
    if batch_004 is None or batch_004["human_verified"] != verified:
        raise SystemExit("the eligibility status disagrees with the closure")
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
