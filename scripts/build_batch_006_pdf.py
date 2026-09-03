#!/usr/bin/env python3
"""Render the batch-006 generation result as a PDF.

The headline is the shortfall. Batch 006 was commissioned as the final coverage push —
25 to 28 candidates, to carry the project from 82 confirmed holdout-eligible cases past
100 — and it exported nine. That is the finding, and it leads the document rather than
sitting under the composition tables.

Every figure is read from the batch, the generation report, the heading-parser audit and
the project-wide eligibility status at build time. Seven gates refuse the build rather
than publish something false, including the one that matters most here: a page claiming
the project reaches 100 when the arithmetic says it does not.
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
from rag_v1.gold.normalisation import has_markdown_link

BATCH = REPO_ROOT / "evals/review/gold_review_batch_006.json"
REPORT = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-006-generation-report.json"
AUDIT = REPO_ROOT / "experiments/GOLD-001/GOLD-001-heading-parser-audit.json"
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
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.2pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
td.mono { white-space: nowrap; width: 1%; }
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
  font-size: 7.6pt; color: #33373d; white-space: pre-wrap; }
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
    batch = data["batch"]
    report = data["report"]
    audit = data["audit"]
    status = data["status"]

    records = batch["records"]
    review = batch["internal_review"]
    removed = batch["removed"]
    length = batch["evidence_length"]
    combined = status["combined"]
    census = batch["corpus_census"]
    exported = batch["candidates"]
    target = batch["target_size"]
    confirmed = combined["holdout_eligible"]
    best = confirmed + exported
    rates = [b["human_verified"] / (b["human_verified"] + b["human_rejected"])
             for b in batch["starting_state"]["by_batch"]
             if b["human_verified"] + b["human_rejected"]]
    worst = min(rates)
    low = confirmed + int(exported * worst)

    fix_rows = rows([
        (f"<b>{f['id']}</b>", ticks(f["fix"]), f"<code>{esc(f['from_case'])}</code>",
         f"<code>{esc(f['module'])}</code>")
        for f in batch["preregistered_fixes_applied"]
    ], classes=("num", "", "mono", ""))

    gate_rows = rows([
        (f"<code>{esc(gate)}</code>", count)
        for gate, count in review["gate_counts"].items()
    ], classes=("", "num"))

    removed_rows = rows([
        (reason.replace("_", " "), count)
        for reason, count in sorted(removed.items(), key=lambda kv: -kv[1])
    ], classes=("", "num"))

    candidate_rows = rows([
        (f"<code>{r['candidate_id'][-2:]}</code>", r["provider"],
         f"<code>{r['reasoning_type']}</code>", ticks(r["question"]),
         r["evidence_char_length"])
        for r in records
    ], classes=("mono", "", "", "", "num"))

    triple_rows = rows([
        (f"<code>{r['candidate_id'][-2:]}</code>",
         ticks((r["source_subject"] or "")[:56]),
         f"<code>{esc(r['source_relation'])}</code>",
         ticks((r["source_object"] or "")[:56]),
         ticks((r["question_subject"] or "")[:40]))
        for r in records
    ], classes=("mono", "", "", "", ""))

    dropped_rows = rows([
        (f"<code>{esc(d['findings'][0].split(':', 1)[0])}</code>",
         d["reasoning_type"].replace("_", " "),
         ticks(d["question"][:78] + ("…" if len(d["question"]) > 78 else "")))
        for d in review["dropped"][:22]
    ])

    batch_rows = rows([
        (f"{b['batch']:03d}", b["candidates"], b["human_verified"],
         b["human_rejected"], f"<b>{b['holdout_eligible']}</b>")
        for b in status["batches"]
    ], classes=("mono", "num", "num", "num", "num"))

    detail = "".join(
        f"<h3>{esc(r['candidate_id'])} · {esc(r['provider'])} · "
        f"<code>{esc(r['reasoning_type'])}</code></h3>"
        f"<p><b>Q.</b> {ticks(r['question'])}<br>"
        f"<b>A.</b> {ticks(r['answer'])}</p>"
        f"<p class='dim' style='font-size:7.8pt'>"
        f"{esc(r['document_title'])} · <code>{esc(r['version_id'][:16])}…</code> · "
        f"{r['expected_evidence'][0]['char_start']}–"
        f"{r['expected_evidence'][0]['char_end']} · "
        f"{r['evidence_char_length']} chars · triple read by "
        f"{esc(r['source_triple_derivation'])}</p>"
        f"<blockquote>{esc(r['expected_evidence'][0]['evidence_text'])}</blockquote>"
        f"<p class='dim' style='font-size:7.8pt'>critical strings: "
        + ", ".join(f"<code>{esc(s)}</code>"
                    for s in r["expected_evidence"][0]["critical_strings"])
        + "</p>"
        for r in records)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — Batch 006 Generation</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — Batch 006<br>The Coverage Push That Came Back Short</h1>
<p class="subtitle">Production RAG v1 · generated {esc(batch['generated_at'])} ·
corpus snapshot <code>{esc(batch['corpus_snapshot'])}</code> · nothing here is gold</p>
<div class="rule"></div>

<div class="callout warn">
<div class="label">The finding: {exported} of {target}, and 100 is out of reach</div>
<p>Batch 006 was commissioned as the final coverage push — {target} candidates, to carry
the project from <b>{confirmed}</b> confirmed holdout-eligible cases past <b>100</b>. It
exported <b>{exported}</b>.</p>
<p>Even if an independent review and the owner approved <i>every one</i>, the project
would reach <b>{best}</b> — still <b>{100 - best} short</b>. At the {worst:.0%}
acceptance rate of the weakest closed batch it reaches {low}. <b>This batch does not get
GOLD-001 to its minimum</b>, and no approval decision should be taken as though it
might.</p>
<p>Nothing was padded to close the gap. Every one of the {exported} cleared the
structural precheck and the semantic self-review; {review['counts'].get('DROP', 0)} more
were dropped and are listed below with the gate that caught each.</p>
</div>

<div class="grid4">
  <div class="stat warn"><div class="big">{exported} / {target}</div>
    <div class="cap">exported against target</div></div>
  <div class="stat warn"><div class="big">{best} / 100</div>
    <div class="cap">best case if all were<br>approved</div></div>
  <div class="stat"><div class="big">{review['counts'].get('DROP', 0)}</div>
    <div class="cap">dropped by the<br>self-review</div></div>
  <div class="stat win"><div class="big">4 / 4</div>
    <div class="cap">preregistered fixes<br>implemented first</div></div>
</div>

<h2>1. Why it came back short</h2>
<p>Not the corpus. A census of the frozen snapshot found
<b>{census['unspent_distinct_texts']} distinct evidence spans that no closed batch has
spent</b>, out of {census['distinct_evidence_texts']} distinct spans the miners reach.
The shortage is in <i>authoring</i>: of
{report['candidate_pool_size']} mined facts, <b>{removed.get('unbuildable', 0)}</b>
reached no builder that could turn them into a question without paraphrasing. The
material in this corpus is long, multi-clause prose, and a template that fits it is a
template that invents wording.</p>
<p>A new predicate lane was added for this batch — one question frame per verb the
corpus actually uses, with the question built from the sentence's own subject — and it
is what produced most of the {exported}. Pushing further meant either loosening a gate
that exists because a real defect got through a previous batch, or inventing question
templates that paraphrase. Neither was done.</p>

<table><thead><tr><th>where candidates were lost</th><th class="num">count</th>
</tr></thead><tbody>{removed_rows}</tbody></table>

<h2>2. The four preregistered fixes, implemented before anything was authored</h2>
<table><thead><tr><th></th><th>fix</th><th>from</th><th>implemented in</th>
</tr></thead><tbody>{fix_rows}</tbody></table>
<p>Each was recorded in batch 005's closure as a preregistration input, and each has a
regression test built from the candidate that motivated it. Batch 005's artifacts are
unchanged: the fixes are forward-looking, which is the point of recording them rather
than patching a closed batch.</p>

<div class="callout">
<div class="label">What the fixes actually caught in this batch</div>
<p>A gate that never fires is indistinguishable from a gate that was never wired in, so
the counts are reported rather than the intention.
<b>{review['gate_counts'].get('BARE_DEFINITION_SCOPE', 0)}</b> candidates were dropped
for bare definition bullets (Fix A — the rule batch 005 applied only to single-span
records), <b>{review['gate_counts'].get('NO_TRIPLE', 0)}</b> because they could not state
their own subject and relation (Fix D), and
<b>{review['gate_counts'].get('SUBJECT_MISMATCH', 0)}</b> for asking about the wrong
subject.</p>
</div>

<table><thead><tr><th>gate that fired</th><th class="num">candidates</th>
</tr></thead><tbody>{gate_rows}</tbody></table>

<div class="break"></div>
<h2>3. What was dropped</h2>
<table class="long"><thead><tr><th>gate</th><th>reasoning type</th><th>question</th>
</tr></thead><tbody>{dropped_rows}</tbody></table>
<p class="dim">{len(review['dropped'])} drops in total; the first
{min(22, len(review['dropped']))} are shown. They are recorded rather than regenerated
away — what the miner gets wrong is part of what this batch measures.</p>

<h2>4. The {exported} candidates</h2>
<table class="long"><thead><tr><th>id</th><th>provider</th><th>reasoning type</th>
<th>question</th><th class="num">chars</th></tr></thead>
<tbody>{candidate_rows}</tbody></table>
<p>Provider {esc(batch['by_provider'])} · {batch['unique_documents']} distinct documents
· evidence mean {length['mean']}, median {length['median']}, max {length['max']}
characters, {length['over_soft_cap']} over the 1000-character soft cap.
{batch['precheck_holdout_ready']} of {exported} are <code>precheck_holdout_ready</code>,
which means <b>structurally checkable and nothing more</b>.</p>

<h3>Subject and relation, on every record</h3>
<p>Fix D's contract: a candidate states what its source says and what its question asks,
and export compares them. A question that reverses its source cannot leave.</p>
<table class="long"><thead><tr><th>id</th><th>source subject</th><th>relation</th>
<th>source object</th><th>question subject</th></tr></thead>
<tbody>{triple_rows}</tbody></table>

<div class="break"></div>
<h2>5. Every candidate in full</h2>
{detail}

<div class="break"></div>
<h2>6. Heading parser audit (Fix C)</h2>
<p><b>{audit['likely_prose']} of {audit['headings_parsed']} parsed headings
({audit['likely_prose_share']:.2%})</b> read as prose rather than as a label, across
{audit['documents_with_prose_headings']} of {audit['documents']} documents —
<code>GOLD-B005-11</code>'s <i>"configured through AWS_REGION, AWS_DEFAULT_REGION, or
your AWS profile."</i> among them.</p>
<p>{esc(audit['verdict']['finding'])}</p>
<p><b>Nothing was rewritten.</b> {esc(audit['not_done'][0])}
{esc(audit['not_done'][1])} What changed is a rule, not a record:
{esc(audit['rule_for_batch_006'])}</p>

<h2>7. Multi-hop: no search was run</h2>
<p>{ticks(batch['multi_hop_search']['reason'])} Exported chains:
<b>{batch['multi_hop_search']['exported_chains']}</b>. The project's genuine multi-hop
count stays at <b>{combined['genuine_multi_hop']}</b>.</p>

<h2>8. Project state — batch 006 counts for nothing yet</h2>
<table><thead><tr><th>batch</th><th class="num">candidates</th>
<th class="num">human_verified</th><th class="num">rejected</th>
<th class="num">holdout_eligible</th></tr></thead><tbody>{batch_rows}</tbody>
<tfoot><tr><td>confirmed</td><td class="num">{combined['candidates']}</td>
<td class="num">{combined['human_verified']}</td>
<td class="num">{combined['human_rejected']}</td>
<td class="num">{combined['holdout_eligible']}</td></tr>
<tr><td>006 (unverified)</td><td class="num">{exported}</td><td class="num">0</td>
<td class="num">0</td><td class="num">0</td></tr></tfoot></table>
<p>No batch-006 candidate is <code>human_verified</code>, and none is counted as
confirmed anywhere in this project's records. The next step is independent review.</p>

<h2>9. Invariants</h2>
<ul>
<li>No retrieval system was run against any candidate at any point.
<code>retrieval_was_not_run = true</code>; <code>systems_executed = []</code>. No
question was selected, ordered or worded because of retrieval difficulty.</li>
<li>SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B <code>304c3509…</code> were verified
frozen before generation began and were not executed.</li>
<li>The corpus snapshot, chunks, embeddings and retrieval architecture are unchanged.
This was evaluation-authoring work only.</li>
<li>Batches 001–005 are untouched; their closure hashes still cover their records.</li>
<li>No holdout and no validation split is frozen.</li>
<li>The semantic self-review is Claude reading its own output. It is not independent
verification, and nothing in this document treats it as such.</li>
</ul>

<footer>
Generated by scripts/build_batch_006_pdf.py from gold_review_batch_006.json,
GOLD-001-batch-006-generation-report.json, GOLD-001-heading-parser-audit.json and
GOLD-001-eligibility-status.json. Every figure is read from those artifacts at build
time. The build refuses to run if any record claims a verification it does not have, if
the batch records a retrieval run, if a multi-hop search ran, if any exported record
fails the scope, link or relation-direction checks, if the report disagrees with the
batch, or if the page would claim the project reaches 100 when the arithmetic says
otherwise. Raw provider documentation is not redistributed; quoted spans are the short
excerpts under review.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/GOLD-001-batch-006.pdf")
    args = parser.parse_args()

    paths = {"batch": BATCH, "report": REPORT, "audit": AUDIT, "status": STATUS}
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"{path} is missing — cannot build the {name} section")
    data = {name: json.loads(path.read_text()) for name, path in paths.items()}
    batch, report, status = data["batch"], data["report"], data["status"]

    # 1. Nothing may claim a verification it does not have.
    bad = [r["candidate_id"] for r in batch["records"]
           if r["verification_status"] != "candidate_unverified"]
    if bad:
        raise SystemExit("refusing to build: these claim verification — "
                         + ", ".join(bad))

    # 2. Retrieval, and 3. the multi-hop search, must both not have run.
    if not batch["retrieval_was_not_run"] or batch["systems_executed"]:
        raise SystemExit("refusing to build: the batch records a retrieval run")
    if batch["multi_hop_search"]["ran"]:
        raise SystemExit("refusing to build: §7 forbids a multi-hop search here")

    # 4. The three fixes that act on output are re-checked here, not trusted.
    for check, message in (
        (lambda r: scoping.evaluate(r)["status"] == scoping.NEEDS_SCOPE,
         "a bare-definition-bullet span survived (Fix A)"),
        (lambda r: has_markdown_link(r["question"]) or has_markdown_link(r["answer"]),
         "markdown link plumbing survived (Fix B)"),
        (lambda r: relations.evaluate(r)["status"] in (relations.REVERSED,
                                                       relations.SUBJECT_MISMATCH),
         "a question does not match its source's direction (Fix D)"),
    ):
        failing = [r["candidate_id"] for r in batch["records"] if check(r)]
        if failing:
            raise SystemExit(f"refusing to build: {message} — "
                             + ", ".join(failing))

    # 5. The report has to describe this batch.
    if (report["candidates"] != len(batch["records"])
            or report["by_provider"] != batch["by_provider"]):
        raise SystemExit("refusing to build: the report disagrees with the batch")

    # 6. Batch 006 must not already be counted as confirmed.
    if any(b["batch"] == 6 for b in status["batches"]):
        raise SystemExit("refusing to build: batch 006 is in the confirmed status")

    # 7. The page must not claim the project reaches 100 when it does not.
    best = status["combined"]["holdout_eligible"] + batch["candidates"]
    document = build_html(data)
    if best < 100 and "short</b>" not in document:
        raise SystemExit(
            "refusing to build: the project cannot reach 100 from this batch and the "
            "document does not say so")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "batch006.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
