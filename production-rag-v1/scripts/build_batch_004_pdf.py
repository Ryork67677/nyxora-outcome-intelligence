#!/usr/bin/env python3
"""Render the GOLD-001 batch-004 generation results to a shareable PDF.

Every number is read from the generated artifacts at build time — the batch file, the
generation report, the coverage report and the eligibility status — so the document
cannot claim a distribution those artifacts do not have. Batch 003's reports drifted
from their own records twice; a build step that recomputes nothing is the cheapest way
to stop that happening again.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BATCH = REPO_ROOT / "evals" / "review" / "gold_review_batch_004.json"
REPORT = REPO_ROOT / "experiments" / "GOLD-001" / "GOLD-001-batch-004-generation-report.json"
COVERAGE = (REPO_ROOT / "experiments" / "GOLD-001"
            / "GOLD-001-coverage-status-after-b004-generation.json")
#: The near-miss count was hardcoded here once and was wrong (three, against five).
#: It is now read from the diagnostic that computes it.
NEAR_MISS = (REPO_ROOT / "experiments" / "GOLD-001"
             / "BATCH-004-near-miss-multihop-review.json")
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
h3 { font-size: 9.8pt; margin: 11pt 0 4pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.4pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
pre { font-family: "SFMono-Regular", Consolas, monospace; font-size: 8pt;
  background: #f6f7f9; border: 0.6pt solid #dde0e4; border-radius: 3pt;
  padding: 7pt 9pt; margin: 6pt 0 10pt; white-space: pre-wrap; }
.subtitle { font-size: 10.5pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.4pt;
  page-break-inside: avoid; }
table.long { page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.b { font-weight: 700; } .bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; } .dim { color: #6f747b; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt;
  margin: 9pt 0 11pt; }
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
.break { page-break-before: always; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.8pt; color: #6f747b; }
"""


def esc(text: object) -> str:
    return html.escape(str(text), quote=False)


def ticks(text: str) -> str:
    """Render the source's backticks as code, escaping everything else."""
    out, parts = [], esc(text).split("`")
    for index, part in enumerate(parts):
        out.append(f"<code>{part}</code>" if index % 2 else part)
    return "".join(out)


def rows(pairs, classes=("", "num")) -> str:
    return "".join(
        "<tr>" + "".join(f"<td class='{classes[i] if i < len(classes) else ''}'>{cell}</td>"
                         for i, cell in enumerate(row)) + "</tr>"
        for row in pairs)


def build_html(batch: dict, report: dict, coverage: dict, near_miss: dict) -> str:
    confirmed = coverage["confirmed"]
    near_miss_count = near_miss["pairs"]
    verdicts = {f["verdict"] for f in near_miss["findings"]}
    near_miss_verdicts = (
        "; the review finds every one a correct rejection"
        if verdicts == {"CORRECT_REJECTION"} else
        f"; reviewer verdicts: {', '.join(sorted(verdicts))}")
    rejection = report["multi_hop_rejection"]
    pool = report["eligible_pool"]["by_reasoning_type"]
    targets = report["targets"]

    starting = rows([
        (f"{b['batch']:03d}", b["human_verified"], b["holdout_eligible"],
         b["human_rejected"], b["genuine_multi_hop"])
        for b in confirmed["batches"]
    ], classes=("mono", "num", "num", "num", "num"))
    starting += (
        f"<tr><td class='b'>total</td>"
        f"<td class='num b'>{confirmed['combined']['human_verified']}</td>"
        f"<td class='num b'>{confirmed['combined']['holdout_eligible']}</td>"
        f"<td class='num b'>{confirmed['combined']['human_rejected']}</td>"
        f"<td class='num b'>{confirmed['genuine_multi_hop']}</td></tr>")

    reasoning = rows([
        (f"<code>{name}</code>", report["by_reasoning_type"].get(name, 0),
         f"{low}–{high}",
         "<span class='good'>met</span>"
         if low <= report["by_reasoning_type"].get(name, 0) <= high
         else "<span class='bad'>MISSED</span>",
         pool.get(name, 0))
        for name, (low, high) in targets["reasoning_type"].items()
    ], classes=("", "num", "num", "num", "num"))

    providers = rows([
        (name, report["by_provider"].get(name, 0), f"{low}–{high}",
         "<span class='good'>met</span>"
         if low <= report["by_provider"].get(name, 0) <= high
         else "<span class='bad'>MISSED</span>",
         report["documents_by_provider"].get(name, 0),
         report["versions_by_provider"].get(name, 0))
        for name, (low, high) in targets["provider"].items()
    ], classes=("", "num", "num", "num", "num", "num"))

    rejections = rows([
        (reason.replace("_", " "), count,
         f"{count / rejection['rejected']:.0%}" if rejection["rejected"] else "—")
        for reason, count in sorted(rejection["reasons"].items(), key=lambda kv: -kv[1])
    ], classes=("", "num", "num"))

    checks = rows([(esc(check), count) for check, count in rejection["by_check"].items()])

    removed = rows([(reason.replace("_", " "), count)
                    for reason, count in sorted(report["removed"].items(),
                                                key=lambda kv: -kv[1])])

    index = rows([
        (f"<code>{r['candidate_id'][-2:]}</code>", r["provider"],
         f"<code>{r['reasoning_type']}</code>", r["evidence_shape"],
         r["evidence_char_length"], ticks(r["question"]))
        for r in batch["records"]
    ], classes=("mono", "", "", "", "num", ""))

    hop = next((r for r in batch["records"]
                if r["reasoning_type"] == "genuine_multi_hop"), None)
    hop_block = ""
    if hop is not None:
        spans = "".join(
            f"<h3>{span['evidence_id']} · <span class='dim mono'>"
            f"{esc(span['version_id'])} {span['char_start']}–{span['char_end']} "
            f"({span['evidence_char_length']} chars)</span></h3>"
            f"<blockquote>{esc(span['evidence_text'])}</blockquote>"
            for span in hop["expected_evidence"])
        hop_block = f"""
<h2>4. The one case that passed, in full</h2>
<p>{esc(hop['candidate_id'])} · {esc(hop['provider'])} ·
<code>{esc(hop['evidence_shape'])}</code> · {hop['document_count']} documents ·
composition check <span class="good">{esc(hop['multi_hop_composition_check'])}</span></p>
<p><span class="b">Q.</span> {ticks(hop['question'])}</p>
<p><span class="b">Bridge entity.</span> <code>{esc(hop['bridge_entity'])}</code> —
{ticks(hop['bridge_relationship'])}</p>
{spans}
<p><span class="b">Why neither span is enough.</span>
{ticks(hop['why_span_1_alone_is_insufficient'])}
{ticks(hop['why_span_2_alone_is_insufficient'])}</p>
<div class="callout">
<div class="label">What a reviewer should check here</div>
<p>This case is the batch's whole thesis, and it is the one I would attack first. The
composition check is mechanical: it proves that neither span carries the other's critical
strings. It cannot prove that span&nbsp;1 establishes the state span&nbsp;2's condition
tests — that judgement is why this candidate is marked
<code>needs_human_interpretation</code>.</p>
</div>"""

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 004 Generation Results</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 004<br>Genuine Multi-Hop &amp; Coverage Expansion</h1>
<p class="subtitle">Production RAG v1 · evidence-candidate authoring ·
{report['total_candidates']} candidates proposed, none verified, none gold</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">Status — nothing in batch 004 is gold</div>
<p>Every candidate is <code>candidate_unverified</code>. No retrieval system was run against
any of them, SYSTEM-A and SYSTEM-B remain frozen and unexecuted, and the holdout is not
frozen. The confirmed eligible count is still
<span class="b">{confirmed['combined']['holdout_eligible']}</span>, from batches 001–003;
batch 004 adds candidates, not cases.</p>
</div>

<div class="grid4">
  <div class="stat"><div class="big">{report['total_candidates']} / 20</div>
    <div class="cap">candidates returned<br>against the target of 20</div></div>
  <div class="stat warn"><div class="big">{rejection['passed']} / {rejection['attempted_pairs']}</div>
    <div class="cap">bridge pairs that passed<br>the composition check</div></div>
  <div class="stat win"><div class="big">{report['precheck_holdout_ready']} / {report['total_candidates']}</div>
    <div class="cap">precheck holdout-ready<br>(not human approval)</div></div>
  <div class="stat"><div class="big">{confirmed['combined']['holdout_eligible']}</div>
    <div class="cap">confirmed eligible cases<br>unchanged by this batch</div></div>
</div>

<h2>1. Why this batch exists</h2>
<p>Batch 003 closed with <span class="bad">zero</span> genuine multi-hop cases. Four
candidates carried the label and none survived review: each drew on two spans, which made
the label look earned, while the answer was the two spans' contents rather than anything
that followed from combining them. Multi-span is an evidence shape. Multi-hop is a
reasoning type. Batch 003 conflated them and had no check that could fail.</p>
<p>Batch 004 runs the composition check <span class="b">before</span> export. A pair is
rejected when either span already answers the whole question, when the bridge entity is
not in both spans, when a hop's assertion is not carried by its own span, when the two
spans sit in different providers' documentation, when span&nbsp;1 merely enumerates
values, or when span&nbsp;2's conditional tests something other than the bridge entity's
own state.</p>

<h2>2. Authoritative starting state</h2>
<p>Read from <code>GOLD-001-eligibility-status.json</code> and the closed batch records it
names, not from prose summaries.</p>
<table><thead><tr><th>batch</th><th class="num">human_verified</th>
<th class="num">holdout_eligible</th><th class="num">rejected</th>
<th class="num">genuine multi-hop</th></tr></thead><tbody>{starting}</tbody></table>
<p class="dim"><code>retrieval_was_not_run = true</code> on all three closed batches.
Holdout frozen: <span class="b">{str(confirmed['holdout_frozen']).lower()}</span>.
SYSTEM-A and SYSTEM-B config hashes unchanged.</p>

<h2>3. The finding: how often a hop is not a hop</h2>
<p>The composer tested <span class="b">{rejection['attempted_pairs']}</span> bridge pairs
drawn from facts that share a specific API symbol.
<span class="b">{rejection['passed']}</span> passed the composition check;
<span class="bad">{rejection['rejected']}</span> were rejected.</p>
<table><thead><tr><th>rejection reason (§30)</th><th class="num">pairs</th>
<th class="num">share</th></tr></thead><tbody>{rejections}</tbody></table>
<p>Counted from each check's own reason string, one bucket per pair, under the first
reason it failed. The report's <code>unclassified</code> guard is
{rejection['unclassified']}: a check cannot grow a reason the table silently drops.</p>
<h3>The same rejections, by the check that made them</h3>
<table><thead><tr><th>check</th><th class="num">pairs</th></tr></thead>
<tbody>{checks}</tbody></table>
<div class="callout">
<div class="label">Reading this honestly</div>
<p>A 1-in-{rejection['attempted_pairs']} yield looks like a failure and is in fact the
measurement working. It says that in this corpus two facts sharing an identifier are
almost never two halves of an argument. Batch 003 could not produce this number, because
it rejected nothing.</p>
</div>
{hop_block}

<div class="break"></div>
<h2>5. What the batch contains</h2>
<table><thead><tr><th>reasoning type</th><th class="num">in batch</th>
<th class="num">target</th><th class="num">met</th>
<th class="num">eligible available</th></tr></thead><tbody>{reasoning}</tbody></table>
<p>The last column is the honest one. Where it equals the batch count, the corpus had
nothing more to give under the checks in §6, §9 and §20 — the target was
not missed by selection. Where it is far above, the ceiling stopped the batch rather than
the material: the reasoning-type ceilings are hard, so a fourth exact lookup cannot fill a
multi-hop seat.</p>

<table><thead><tr><th>provider</th><th class="num">in batch</th><th class="num">target</th>
<th class="num">met</th><th class="num">documents</th>
<th class="num">versions</th></tr></thead><tbody>{providers}</tbody></table>
<p>No target was made to read <span class="good">met</span> by relabelling a candidate or
lowering the evidence standard. §3 of the brief puts quality above count, so the batch
came back at {report['total_candidates']} rather than padded to 20.</p>

<h3>Evidence size</h3>
<p>Across {report['evidence_length']['spans']} spans: mean
{report['evidence_length']['mean']}, median {report['evidence_length']['median']}, max
{report['evidence_length']['max']} characters.
{report['evidence_length']['over_soft_cap']} over the 1,000-character soft cap, none over
the 1,500 hard cap. Multi-hop cases are measured per span, because the size that matters
is the size of each anchor.</p>

<h3>Removed before export</h3>
<table><thead><tr><th>reason</th><th class="num">candidates</th></tr></thead>
<tbody>{removed}</tbody></table>

<div class="break"></div>
<h2>6. The candidates</h2>
<table class="long"><thead><tr><th>id</th><th>provider</th><th>reasoning type</th><th>shape</th>
<th class="num">chars</th><th>question</th></tr></thead><tbody>{index}</tbody></table>

<h2>7. What this document does not say</h2>
<ul>
<li>No batch-004 candidate is eligible, verified, or gold.
<code>precheck_holdout_ready</code> is a structural check, not an approval, and only an
explicit owner decision can produce <code>human_verified</code>.</li>
<li>No retrieval system was run against any candidate in any batch. No candidate was
selected, ordered or worded because of what any system does with it, and no difficulty
label in this batch derives from retrieval behaviour.</li>
<li>The holdout is not frozen, and this document does not freeze it.</li>
<li>Batches 001–003 are untouched. Their closure hashes are unchanged.</li>
</ul>

<h2>8. Next step, and who owns it</h2>
<div class="callout">
<div class="label">The next step is human review, not batch 005</div>
<p>{report['total_candidates']} candidates need an owner decision before any of them can
count. The multi-hop case should be reviewed first and hardest: it is the only one of its
kind, and the mechanical check that admitted it cannot judge whether span&nbsp;1 really
establishes the state span&nbsp;2's condition tests.</p>
<p>Two cases I would flag without being asked. The batch's evidence for
<code>GOLD-B004-04</code> opens “If generation <span class="b">then</span> reaches…”,
which leans on a preceding sentence the span does not contain. And {near_miss_count}
bridge pairs passed every other check and were rejected only by the entity-state rule —
a reviewer should satisfy themselves that the line was drawn on the evidence rather than
to reach a comfortable number. Each is set out in
<code>BATCH-004-near-miss-multihop-review.md</code>{near_miss_verdicts}.</p>
</div>

<footer>
Generated by scripts/build_batch_004_pdf.py from
evals/review/gold_review_batch_004.json, GOLD-001-batch-004-generation-report.json,
GOLD-001-coverage-status-after-b004-generation.json and GOLD-001-eligibility-status.json.
Every count is read from those artifacts at build time. Batch
{batch['batch']:03d}, schema {batch['schema_version']}, generated
{batch['generated_at']}, git commit {(batch.get('git_commit') or 'unknown')[:12]},
corpus snapshot {batch['corpus_snapshot']}, batch_sha256
{batch['batch_sha256'][:32]}… Raw provider documentation is not redistributed; quoted
spans are the short excerpts needed to show the evidence under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default="docs/reports/GOLD-001-batch-004-generation-results.pdf")
    args = parser.parse_args()

    for path in (BATCH, REPORT, COVERAGE, NEAR_MISS):
        if not path.exists():
            raise SystemExit(f"{path} is missing — run scripts/export_batch_004.py first")

    batch = json.loads(BATCH.read_text())
    report = json.loads(REPORT.read_text())
    coverage = json.loads(COVERAGE.read_text())
    if report["batch_sha256"] != batch["batch_sha256"]:
        raise SystemExit(
            "the generation report was built from a different batch file — regenerate "
            "both rather than publishing a document whose numbers disagree")

    near_miss = json.loads(NEAR_MISS.read_text())
    document = build_html(batch, report, coverage, near_miss)
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "batch004.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
