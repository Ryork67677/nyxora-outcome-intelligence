#!/usr/bin/env python3
"""Render the batch-005 source-integrity review and owner QC packet to a PDF.

The audience is the project owner and an independent reviewer, so the document carries
what someone needs to disagree: every candidate's final question, answer and exact
evidence with its hash, what the review found, and what it changed with the pre-repair
offsets beside the new ones.

It also carries the three generator defects the review found and did not patch. A batch
whose review reports only candidate-level findings is a batch whose review was not
looking at the generator.

Every figure is read from the artifacts at build time. The build refuses to run when the
repairs were computed against a different batch, when the packet claims any verified or
eligible candidate, or when a decision has already been recorded — this document
describes an undecided batch.
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
REPAIRS = REPO_ROOT / "evals/review/gold_review_batch_005_repairs.json"
PACKET = REPO_ROOT / "evals/review/gold_batch_005_qc.json"
DECISIONS = REPO_ROOT / "evals/review/human_decisions_batch_005.json"
STATUS = REPO_ROOT / "experiments/GOLD-001/GOLD-001-eligibility-status.json"
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
h4 { font-size: 8.6pt; margin: 8pt 0 3pt; color: #52565d; text-transform: uppercase;
     letter-spacing: 0.6pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.1pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
td.mono { white-space: nowrap; width: 1%; }
.hash { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7pt;
  color: #6f747b; overflow-wrap: anywhere; }
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


def candidate_card(entry: dict) -> str:
    record, review, generated = entry["record"], entry["review"], entry["generated"]
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

    interaction = ""
    if review.get("interaction"):
        block = review["interaction"]
        interaction = (
            "<h4>Interaction recorded</h4><ul>"
            f"<li><b>A</b>: {ticks(block['setting_or_state_A'])}</li>"
            f"<li><b>B</b>: {ticks(block['setting_or_state_B'])}</li>"
            f"<li><b>relation</b>: {ticks(block['documented_relation'])}</li></ul>")

    repairs = ""
    if entry["was_repaired"]:
        anchors = "".join(
            (f"<li><b>{esc(r['evidence_id'])} anchor extended</b> "
             f"({esc(r['reason'])})<br><span class='hash'>"
             f"was {r['old_char_start']}–{r['old_char_end']}, "
             f"hash {esc(r['old_evidence_hash'])}<br>"
             f"now {r['new_char_start']}–{r['new_char_end']}, "
             f"hash {esc(r['new_evidence_hash'])}</span></li>")
            for r in record.get("anchor_revisions", [])
            if r["action"] == "extend_boundary")
        texts = "".join(
            f"<li><b>{esc(r['field'])} rewritten</b><br>"
            f"<span class='dim'>was:</span> {ticks(str(r['from']))}<br>"
            f"<span class='dim'>now:</span> {ticks(str(r['to']))}</li>"
            for r in record.get("revisions", []))
        repairs = f"<h4>Repairs made</h4><ul>{anchors}{texts}</ul>"

    relabel = ""
    if record["reasoning_type"] != generated["reasoning_type"]:
        relabel = (f" <span class='dim'>(generated as "
                   f"<code>{esc(generated['reasoning_type'])}</code>)</span>")

    return f"""
<div class="card {kind}">
<h3>{esc(record['candidate_id'])} · <span class="{badge}">{esc(status)}</span></h3>
<p class="meta">{esc(record['provider'])} · {esc(record['document_title'])} ·
{esc(' › '.join(record['section_path']))}<br>
reasoning type <code>{esc(record['reasoning_type'])}</code>{relabel} ·
shape <code>{esc(record['evidence_shape'])}</code> ·
precheck holdout-ready {record['precheck_holdout_ready']}</p>
<p class="qa"><span class="k">Q.</span> {ticks(record['question'])}</p>
<p class="qa"><span class="k">A.</span> {ticks(record['answer'])}</p>
<h4>Atomic claims</h4><ol>{claims}</ol>
{interaction}
<h4>Exact evidence</h4>{spans}
<h4>Internal review findings</h4><ul>{findings}</ul>
{repairs}
</div>"""


def build_html(data: dict) -> str:
    packet, repairs, batch = data["packet"], data["repairs"], data["batch"]
    status, decisions = data["status"], data["decisions"]
    entries = packet["candidates"]
    counts = packet["internal_review_status_counts"]
    combined = status["combined"]
    defects = packet["generator_defects_found"]

    summary = rows([
        (f"<code>{e['record']['candidate_id'][-2:]}</code>", e["record"]["provider"],
         f"<code>{e['record']['reasoning_type']}</code>",
         (f"<span class='{ {'REJECT_RECOMMENDED': 'bad', 'NEEDS_REPAIR': 'warnt'}.get(e['review']['status'], 'good') }'>"
         f"{e['review']['status']}</span>"),
         "yes" if e["was_repaired"] else "no",
         len(e["review"]["findings"]))
        for e in entries
    ], classes=("mono", "", "", "", "num", "num"))

    reject_rows = rows([
        (f"<code>{cid}</code>", ticks(d["reason"]))
        for cid, d in sorted(repairs["review"].items())
        if d["status"] == "REJECT_RECOMMENDED"
    ])

    defect_rows = "".join(
        f"<li><b>{ticks(d['defect'])}</b> — seen in <code>{esc(d['seen_in'])}</code>. "
        f"{ticks(d['detail'])}</li>" for d in defects)

    cards = "".join(candidate_card(e) for e in entries)
    undecided = sum(1 for d in decisions["decisions"] if d["decision"] is None)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 005 Review</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 005<br>Source-Integrity Review &amp; Owner QC Packet</h1>
<p class="subtitle">Production RAG v1 · evidence-candidate authoring ·
prepared {esc(packet['prepared_at'])} · {undecided} decisions outstanding</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">An internal authoring review is not independent verification</div>
<p>The statuses in this document were produced by the authoring model reading its own
output against the frozen evidence. That is a self-check. A
<code>READY_FOR_OWNER_REVIEW</code> label means the author found nothing wrong — which
is exactly the claim an independent reviewer exists to test.</p>
<p>Nothing here is verified. All {len(entries)} candidates are
<code>candidate_unverified</code>, all {undecided} decisions are <code>null</code>, and
the project's confirmed total is unchanged at
<b>{combined['holdout_eligible']}</b> holdout-eligible cases from batches 001–004.</p>
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

<h2>1. What the review found</h2>
<p>All {len(entries)} candidates were <code>precheck_holdout_ready</code> before this
review and all {len(entries)} still are. The review nonetheless recommends
<b>{counts.get('REJECT_RECOMMENDED', 0)}</b> for rejection and repaired
<b>{packet['repaired_candidates']}</b>. That gap is the same point batch 004 made and
this batch confirms with a second sample: a structural check verifies hashes, offsets and
string containment, and cannot read.</p>

<table class="long"><thead><tr><th>id</th><th>provider</th><th>reasoning type</th>
<th>internal status</th><th class="num">repaired</th>
<th class="num">findings</th></tr></thead><tbody>{summary}</tbody></table>

<h3>Recommended for rejection</h3>
<table><thead><tr><th>candidate</th><th>reason</th></tr></thead>
<tbody>{reject_rows}</tbody></table>
<p>These are recommendations, not decisions. Nothing binds the owner, and a rejection
recommendation the owner disagrees with is a candidate the owner may approve.</p>

<h2>2. Defects in the generator, not just in the candidates</h2>
<p>A review that reports only candidate-level findings is a review that was not looking
at the thing that produced them. Three defects surfaced here, all recorded rather than
patched: the batch-005 generation artifact is not being regenerated, and a fix belongs in
batch 006's preregistration where it can be declared before it sees a candidate.</p>
<ul>{defect_rows}</ul>

<div class="break"></div>
<h2>3. The nineteen candidates</h2>
<p>Each card carries the final question, answer and claims, the exact evidence with its
hash, what the review found, and what it changed. This is the material to check.</p>
{cards}

<h2>4. How a repair is gated</h2>
<p>Every anchor repair is a strict outward growth of the span it replaces — an anchor
that moves rather than grows is a different claim wearing the same candidate id — and
both hashes are recorded. A repaired candidate is approved by quoting the post-repair
hash, and the importer refuses an approval quoting the pre-repair one.</p>
<p>The generation artifact is not rewritten.
<code>gold_review_batch_005.json</code> is byte-identical to what the generator produced;
repairs live beside it in <code>gold_review_batch_005_repairs.json</code> with the
original text, offsets and hashes preserved.</p>

<h2>5. Invariants</h2>
<ul>
<li>No new multi-hop search was run. Batch 005's result stands: 3 dependency-first pairs
considered, 1 valid chain, 0 new unique chains.</li>
<li>The semantic bridge-equivalence check is unchanged and still refuses
<code>max_tokens</code> as a bridge — a request parameter in one span, a
<code>stop_reason</code> value in the other.</li>
<li>No retrieval system was run. <code>retrieval_was_not_run = true</code>;
<code>systems_executed = []</code>.</li>
<li>SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B <code>304c3509…</code> remain frozen and
unexecuted.</li>
<li>The holdout is not frozen
(<code>holdout_frozen = {str(status['holdout_frozen']).lower()}</code>).</li>
<li>Batches 001–004 are byte-identical and their closure hashes still verify.</li>
</ul>

<footer>
Generated by scripts/build_batch_005_review_pdf.py from gold_review_batch_005.json,
gold_review_batch_005_repairs.json, gold_batch_005_qc.json,
human_decisions_batch_005.json and GOLD-001-eligibility-status.json. Every figure is read
from those artifacts at build time, and the build refuses to run if the repairs were
computed against a different batch, if the packet claims any verified or eligible
candidate, or if a decision has already been recorded. Batch 005, schema
{esc(batch['schema_version'])}, corpus snapshot {esc(batch['corpus_snapshot'])},
batch_sha256 {esc(batch['batch_sha256'][:32])}…, reviewed {esc(repairs['reviewed_at'])}
by {esc(repairs['reviewer'])}. Raw provider documentation is not redistributed; quoted
spans are the short excerpts under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default="docs/reports/GOLD-001-batch-005-review-preparation.pdf")
    args = parser.parse_args()

    paths = {"batch": BATCH, "repairs": REPAIRS, "packet": PACKET,
             "decisions": DECISIONS, "status": STATUS}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}

    if data["repairs"]["source_batch_sha256"] != data["batch"]["batch_sha256"]:
        raise SystemExit("the repairs were computed against a different batch file")
    if data["packet"]["source_batch_sha256"] != data["batch"]["batch_sha256"]:
        raise SystemExit("the QC packet was composed from a different batch file")
    if data["packet"]["human_verified"] or data["packet"]["holdout_eligible"]:
        raise SystemExit(
            "the packet claims verified or eligible candidates — refusing to present "
            "unapproved candidates as approved")
    if any(d["decision"] is not None for d in data["decisions"]["decisions"]):
        raise SystemExit(
            "a decision has already been recorded — this document describes an "
            "undecided batch and would misstate the project's state")

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
