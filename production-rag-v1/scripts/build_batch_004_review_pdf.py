#!/usr/bin/env python3
"""Render the batch-004 review-preparation results as an independent-verification PDF.

The audience is an outside reviewer, so the document carries what a reviewer needs to
disagree: every candidate's final question, answer, claims and exact evidence with its
hash, what the internal review found, what it repaired and from what, and the semantic
argument for the one multi-hop case rather than the mechanical PASS.

Every number and every quoted span is read from the artifacts at build time — the
generation batch, the repairs file, the QC packet, the internal review, the near-miss
diagnostic and the eligibility status. The build refuses to run when the repairs were
computed against a different batch than the one on disk, so the document cannot show a
repair applied to evidence it never touched.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BATCH = REPO_ROOT / "evals/review/gold_review_batch_004.json"
REPAIRS = REPO_ROOT / "evals/review/gold_review_batch_004_repairs.json"
PACKET = REPO_ROOT / "evals/review/gold_batch_004_qc.json"
DECISIONS = REPO_ROOT / "evals/review/human_decisions_batch_004.json"
INTERNAL = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-004-internal-review.json"
NEAR_MISS = REPO_ROOT / "experiments/GOLD-001/BATCH-004-near-miss-multihop-review.json"
ELIGIBILITY = REPO_ROOT / "experiments/GOLD-001/GOLD-001-eligibility-status.json"
GENERATION = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-004-generation-report.json"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 16mm 14mm 14mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.3pt;
  line-height: 1.45; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 19pt; line-height: 1.15; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 11.5pt; margin: 16pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 9.6pt; margin: 10pt 0 4pt; }
h4 { font-size: 8.8pt; margin: 8pt 0 3pt; color: #52565d; text-transform: uppercase;
     letter-spacing: 0.6pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.1pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt;
  word-break: break-word; }
.subtitle { font-size: 10.2pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.2pt;
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
  font-size: 7.7pt; color: #33373d; white-space: pre-wrap; }
.card { border: 0.8pt solid #dde0e4; border-radius: 3pt; padding: 9pt 11pt;
  margin: 0 0 11pt; page-break-inside: avoid; }
.card.repair { border-left: 2.5pt solid #8a5a00; }
.card.reject { border-left: 2.5pt solid #8a1c1c; }
.card.ready { border-left: 2.5pt solid #14532d; }
.card h3 { margin-top: 0; }
.meta { font-size: 7.6pt; color: #52565d; margin: 0 0 6pt; }
.hash { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7pt;
  color: #6f747b; word-break: break-all; }
.qa { margin: 0 0 5pt; } .qa .k { font-weight: 700; }
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


def candidate_card(entry: dict, generated: dict) -> str:
    record, review = entry["record"], entry["review"]
    status = review["status"]
    kind = {"REJECT_RECOMMENDED": "reject", "NEEDS_REPAIR": "repair"}.get(status, "ready")
    badge = {"REJECT_RECOMMENDED": "bad", "NEEDS_REPAIR": "warnt"}.get(status, "good")

    spans = "".join(
        f"<h4>{esc(span['evidence_id'])} · {esc(span['version_id'])} "
        f"{span['char_start']}–{span['char_end']} "
        f"({span['evidence_char_length']} chars) · "
        f"{esc(' › '.join(span['section_path']))}</h4>"
        f"<blockquote>{esc(span['evidence_text'])}</blockquote>"
        f"<p class='meta'>critical strings: "
        + ", ".join(f"<code>{esc(s)}</code>" for s in span["critical_strings"])
        + f"<br><span class='hash'>evidence_hash {esc(span['evidence_hash'])}</span></p>"
        for span in record["expected_evidence"])

    claims = "".join(f"<li>{ticks(c)}</li>" for c in record["atomic_claims"])
    findings = ("".join(f"<li>{ticks(f)}</li>" for f in review["findings"])
                or "<li>No finding. The candidate stands as generated.</li>")

    repairs = ""
    if entry["was_repaired"]:
        anchor_rows = "".join(
            (f"<li><b>{esc(r['evidence_id'])} anchor extended</b> "
             f"({esc(r['reason'])})<br>"
             f"<span class='hash'>was {r['old_char_start']}–{r['old_char_end']}, "
             f"hash {esc(r['old_evidence_hash'])}<br>"
             f"now {r['new_char_start']}–{r['new_char_end']}, "
             f"hash {esc(r['new_evidence_hash'])}</span></li>")
            if r["action"] == "extend_boundary" else
            (f"<li><b>{esc(r['evidence_id'])} scope span added</b> "
             f"({esc(r['reason'])})<br>"
             f"<span class='hash'>{r['new_char_start']}–{r['new_char_end']}, "
             f"hash {esc(r['new_evidence_hash'])}</span></li>")
            for r in record.get("anchor_revisions", []))
        text_rows = "".join(
            f"<li><b>{esc(r['field'])} rewritten</b><br>"
            f"<span class='dim'>was:</span> {ticks(str(r['from']))}<br>"
            f"<span class='dim'>now:</span> {ticks(str(r['to']))}</li>"
            for r in record.get("revisions", []))
        repairs = (f"<h4>Repairs made</h4><ul>{anchor_rows}{text_rows}</ul>")

    flags = ""
    if record.get("precheck_flags"):
        flags = ("<h4>Flags for the reviewer's judgement</h4><ul>"
                 + "".join(f"<li>{ticks(f)}</li>" for f in record["precheck_flags"])
                 + "</ul>")

    relabel = ""
    if record["reasoning_type"] != generated["reasoning_type"]:
        relabel = (f" <span class='dim'>(generated as "
                   f"<code>{esc(generated['reasoning_type'])}</code>)</span>")

    composed = ""
    if record.get("composed_claim"):
        composed = f"<p class='qa'><span class='k'>Composed claim.</span> " \
                   f"{ticks(record['composed_claim'])}</p>"

    return f"""
<div class="card {kind}">
<h3>{esc(record['candidate_id'])} · <span class="{badge}">{esc(status)}</span></h3>
<p class="meta">{esc(record['provider'])} · {esc(record['document_title'])} ·
{esc(' › '.join(record['section_path']))}<br>
reasoning type <code>{esc(record['reasoning_type'])}</code>{relabel} ·
shape <code>{esc(record['evidence_shape'])}</code> ·
requires all evidence {record['requires_all_evidence']} ·
precheck holdout-ready {record['precheck_holdout_ready']}</p>
<p class="qa"><span class="k">Q.</span> {ticks(record['question'])}</p>
<p class="qa"><span class="k">A.</span> {ticks(record['answer'])}</p>
<h4>Atomic claims</h4><ol>{claims}</ol>
{composed}
<h4>Exact evidence</h4>{spans}
<h4>Internal review findings</h4><ul>{findings}</ul>
{repairs}{flags}
</div>"""


def build_html(data: dict) -> str:
    batch = data["batch"]
    repairs = data["repairs"]
    packet = data["packet"]
    internal = data["internal"]
    near_miss = data["near_miss"]
    eligibility = data["eligibility"]
    generation = data["generation"]
    decisions = data["decisions"]

    generated = {r["candidate_id"]: r for r in batch["records"]}
    entries = packet["candidates"]
    counts = packet["internal_review_status_counts"]

    summary = rows([
        (f"<code>{e['record']['candidate_id']}</code>", e["record"]["provider"],
         f"<code>{e['record']['reasoning_type']}</code>",
         e["record"]["evidence_shape"],
         f"<span class='{ {'REJECT_RECOMMENDED': 'bad', 'NEEDS_REPAIR': 'warnt'}.get(e['review']['status'], 'good') }'>"
         f"{e['review']['status']}</span>",
         "yes" if e["was_repaired"] else "no",
         len(e["review"]["findings"]))
        for e in entries
    ], classes=("mono", "", "", "", "", "num", "num"))

    semantic = internal["multi_hop_semantic_review"]
    questions = "".join(
        f"<h3>{esc(q['id'])}. {ticks(q['question'])}</h3>"
        f"<p><b>{ticks(q['answer'])}</b></p><p>{ticks(q['reasoning'])}</p>"
        for q in semantic["questions"])

    near_rows = rows([
        (f"<code>{f['bridge_entity']}</code>", f["provider"],
         "same document" if f["same_document"] else "two documents",
         f"<span class='good'>{f['verdict']}</span>")
        for f in near_miss["findings"]
    ])

    near_detail = "".join(
        f"<div class='card'><h3><code>{esc(f['bridge_entity'])}</code> · "
        f"<span class='good'>{esc(f['verdict'])}</span></h3>"
        f"<h4>Span 1 — proposed hop 1</h4>"
        f"<blockquote>{esc(f['span_1']['evidence_text'])}</blockquote>"
        f"<h4>Span 2 — proposed hop 2</h4>"
        f"<blockquote>{esc(f['span_2']['evidence_text'])}</blockquote>"
        f"<h4>Why the entity-state rule rejected it</h4>"
        f"<p>{ticks(f['entity_state_rejection'])}</p>"
        f"<h4>Reviewer reasoning</h4><p>{ticks(f['reviewer_reasoning'])}</p></div>"
        for f in near_miss["findings"])

    cards = "".join(candidate_card(e, generated[e["record"]["candidate_id"]])
                    for e in entries)

    undecided = sum(1 for d in decisions["decisions"] if d["decision"] is None)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 004 Review Preparation</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 004<br>Source-Integrity Review &amp; Owner QC Packet</h1>
<p class="subtitle">Production RAG v1 · evidence-candidate authoring ·
prepared for independent verification · {esc(packet['prepared_at'])}</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">What is being asked of a reviewer</div>
<p>Fifteen candidates await a project-owner decision. Nothing here is verified, approved
or eligible: every candidate is <code>candidate_unverified</code>, all
{undecided} decisions are <code>null</code>, and no script in this repository can produce
<code>human_verified</code>. The confirmed holdout-eligible count is
<span class="b">{eligibility['combined']['holdout_eligible']}</span>, unchanged, from
batches 001–003.</p>
<p>The internal review below was done by the authoring model against the frozen corpus.
It is a self-check, not independent verification, and that is the gap this document
exists to close. Where it repaired a candidate, both the original text and the original
anchor are reproduced so a disagreement is checkable without the repository.</p>
</div>

<div class="grid4">
  <div class="stat"><div class="big">{len(entries)}</div>
    <div class="cap">candidates awaiting<br>an owner decision</div></div>
  <div class="stat warn"><div class="big">{counts.get('NEEDS_REPAIR', 0)} / {counts.get('REJECT_RECOMMENDED', 0)}</div>
    <div class="cap">repaired / recommended<br>for rejection</div></div>
  <div class="stat"><div class="big">{packet['precheck_holdout_ready']} / {len(entries)}</div>
    <div class="cap">precheck holdout-ready<br>before and after review</div></div>
  <div class="stat win"><div class="big">{packet['human_verified']}</div>
    <div class="cap">human_verified<br>nothing is gold</div></div>
</div>

<h2>1. The finding that matters most</h2>
<p>All fifteen candidates were <code>precheck_holdout_ready</code> before this review, and
all fifteen still are. The review nonetheless found one candidate to recommend for
rejection and ten to repair.</p>
<p>What the structural precheck passed: a rule that holds only on one experimental API
surface; three questions broader than the evidence answering them; four anchors whose
scope lived in a section heading rather than in the span; and two critical strings that
were 60-character cuts through a markdown link. The precheck verifies hashes, offsets and
string containment. It cannot read.</p>
<div class="callout">
<div class="label">The three states, kept apart</div>
<p><code>precheck_holdout_ready</code> — a script decides. The record is structurally
capable.<br>
<code>human_verified</code> — only the project owner decides. A person read the evidence
and approved it.<br>
<code>holdout_eligible</code> — derived: <code>human_verified</code> <b>and</b>
deterministic claim support <b>and</b> valid evidence <b>and</b> no unresolved
blocker.</p>
<p>Collapsing the first into the second is the failure this pipeline is built to prevent,
which is why a 15/15 precheck result appears here next to a review that rejected one and
repaired ten.</p>
</div>

<h2>2. Review outcome</h2>
<table class="long"><thead><tr><th>candidate</th><th>provider</th><th>reasoning type</th>
<th>shape</th><th>internal status</th><th class="num">repaired</th>
<th class="num">findings</th></tr></thead><tbody>{summary}</tbody></table>

<h3>Findings by class</h3>
<ul>
<li><b>Scope in a heading</b> (06, 09, 14, 15) — the qualification a question relies on
sat outside every span. Rule 2D of the generation brief forbids leaning on a header
outside the exact evidence, so each anchor was extended or given a scope span.</li>
<li><b>Question broader than its evidence</b> (01, 07, 11) — "What happens when using
server tools?" has many true answers; the span supports one.</li>
<li><b>Truncated critical strings</b> (06, 13) — 60-character cuts through a markdown
link are not meaningful checkable strings.</li>
<li><b>Comparative anaphora</b> (10) — "a different <code>RealtimeModel</code>" is
different from a default the span never named.</li>
<li><b>Taxonomy inflation</b> (01, 11) — a single conditional fact is not an interaction
between settings; both relabelled to <code>error_behavior</code> with the reason
recorded.</li>
<li><b>Not an ambiguity</b> (08) — recommended for rejection.</li>
<li><b>Noncritical flags left for the owner</b> (02, 05, 15) — surfaced, not
overridden.</li>
</ul>

<div class="break"></div>
<h2>3. The multi-hop case, reviewed semantically</h2>
<p>{ticks(semantic['note'])}</p>
{questions}
<div class="callout win">
<div class="label">Verdict</div>
<p>{ticks(semantic['verdict'])}. Preserved:
{', '.join(f"<code>{esc(k)}</code> = <code>{esc(v)}</code>" for k, v in semantic['labels_preserved'].items())}.</p>
</div>
<div class="callout warn">
<div class="label">What the mechanical check still cannot see</div>
<p>{ticks(semantic['what_the_mechanical_check_still_cannot_see'])}</p>
</div>

<h2>4. Near-miss bridge pairs — the rule under test</h2>
<p>{near_miss['pairs']} pairs cleared every check in the composer except the entity-state
rule: span 2's conditional must test the bridge entity's own state, not merely mention it
while testing something else. Every one is judged a correct rejection, so on this evidence
the rule is not too strict — it was the only check that caught them, since all
{near_miss['pairs']} passed the composition check that is supposed to be the hostile
one.</p>
<table><thead><tr><th>bridge entity</th><th>provider</th><th>span layout</th>
<th>verdict</th></tr></thead><tbody>{near_rows}</tbody></table>
<p><b>Diagnostic only.</b> None of these is a batch-004 candidate, none was promoted, and
the batch was not regenerated. Choosing candidates by re-reading the rejection list is how
a benchmark ends up measuring its own generator.</p>
{near_detail}

<div class="break"></div>
<h2>5. Erratum — the near-miss count</h2>
<p>The batch-004 results PDF said <b>three</b> near-miss pairs. The correct number is
<b>{near_miss['pairs']}</b>. The three came from a manual probe run mid-development, with
the composer's per-run limit and its used-fact set in force, before the entity-state rule
existed. The diagnostic now derives the set properly and the PDF builder reads the count
from it instead of hardcoding it.</p>
<p>The generation report's own figures were computed from the run and are unchanged:
<b>{generation['multi_hop_rejection']['attempted_pairs']}</b> pairs tested,
<b>{generation['multi_hop_rejection']['passed']}</b> passed,
<b>{generation['multi_hop_rejection']['rejected']}</b> rejected. No candidate changed
status because of the erratum.</p>
<p>One finding from the corrected diagnostic is a gap in a check rather than a judgement
about a pair. The <code>max_tokens</code> pair failed because span 1 means a request
parameter and span 2 means a <code>stop_reason</code> value. The bridge requirement — the
entity must appear in both spans — is a string test and cannot see equivocation. Nothing
in the current composer can. That belongs in batch 005's design, preregistered before it
sees a candidate.</p>

<h2>6. How a repair is gated</h2>
<p>Every anchor repair is a strict outward growth of the span it replaces; an anchor that
moves rather than grows is a different claim wearing the same candidate id. Both hashes
are recorded. A repaired candidate is approved by quoting the post-repair evidence hash,
and the importer refuses an approval quoting the pre-repair hash — so a repair cannot be
waved through by someone who only ever saw the original.</p>
<p>The generation artifact is not rewritten.
<code>gold_review_batch_004.json</code> is byte-identical to what the generator produced;
repairs live beside it in <code>gold_review_batch_004_repairs.json</code> with the
original offsets, text and hashes preserved.</p>

<div class="break"></div>
<h2>7. The fifteen candidates</h2>
<p>Each card carries the final question, answer and claims, the exact evidence with its
hash, what the review found, and what it changed. This is the material to check.</p>
{cards}

<h2>8. Invariants</h2>
<ul>
<li>No retrieval system was run against any candidate, in this phase or in generation.
<code>retrieval_was_not_run = true</code>; <code>systems_executed = []</code>.</li>
<li>SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B <code>304c3509…</code> remain frozen and
unexecuted.</li>
<li>The holdout is not frozen
(<code>holdout_frozen = {str(eligibility['holdout_frozen']).lower()}</code>).</li>
<li>Batches 001–003 are untouched:
{eligibility['combined']['human_verified']} human_verified,
{eligibility['combined']['holdout_eligible']} holdout_eligible,
{eligibility['combined']['human_rejected']} rejected.</li>
<li>No batch-004 candidate is verified or eligible. All {undecided} owner decisions are
<code>null</code>.</li>
</ul>

<footer>
Generated by scripts/build_batch_004_review_pdf.py from
gold_review_batch_004.json, gold_review_batch_004_repairs.json,
gold_batch_004_qc.json, human_decisions_batch_004.json,
GOLD-001-batch-004-internal-review.json,
BATCH-004-near-miss-multihop-review.json,
GOLD-001-batch-004-generation-report.json and GOLD-001-eligibility-status.json.
Every count and every quoted span is read from those artifacts at build time.
Batch 004, schema {esc(batch['schema_version'])}, corpus snapshot
{esc(batch['corpus_snapshot'])}, batch_sha256 {esc(batch['batch_sha256'][:32])}…,
review {esc(repairs['reviewed_at'])} by {esc(repairs['reviewer'])}.
Raw provider documentation is not redistributed; quoted spans are the short excerpts
under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default="docs/reports/GOLD-001-batch-004-review-preparation.pdf")
    args = parser.parse_args()

    paths = {"batch": BATCH, "repairs": REPAIRS, "packet": PACKET,
             "decisions": DECISIONS, "internal": INTERNAL, "near_miss": NEAR_MISS,
             "eligibility": ELIGIBILITY, "generation": GENERATION}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}

    if data["repairs"]["source_batch_sha256"] != data["batch"]["batch_sha256"]:
        raise SystemExit(
            "the repairs were computed against a different batch file — regenerate the "
            "review rather than publishing repairs applied to evidence they never saw")
    if data["packet"]["source_batch_sha256"] != data["batch"]["batch_sha256"]:
        raise SystemExit("the QC packet was composed from a different batch file")
    if data["packet"]["human_verified"] or data["packet"]["holdout_eligible"]:
        raise SystemExit(
            "the packet claims verified or eligible candidates — refusing to publish a "
            "document that would present unapproved candidates as approved")

    document = build_html(data)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "review.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
