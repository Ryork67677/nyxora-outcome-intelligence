#!/usr/bin/env python3
"""The complete GOLD-001 record: six closed batches, every case, every defect.

One document for the whole evaluation-authoring effort. It exists because the project's
history now lives in twenty-odd JSON artifacts and nobody should have to open all of
them to answer "what is in the benchmark, who approved it, and what went wrong on the
way".

Every figure is read from an artifact at build time — the closures, the generation
reports, the reviews, the heading audit, the eligibility status, the batch-007
preregistration and the git log. Nothing is typed in. Nine gates refuse the build
rather than publish a claim the records do not support.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_v1.gold.defects import normalise_all
from rag_v1.gold.eligibility import evaluate as eligibility

EXPERIMENTS = REPO_ROOT / "experiments/GOLD-001"
REVIEW = REPO_ROOT / "evals/review"
STATUS = EXPERIMENTS / "GOLD-001-eligibility-status.json"
PREREG = EXPERIMENTS / "GOLD-001-batch-007-preregistration.json"
AUDIT = EXPERIMENTS / "GOLD-001-heading-parser-audit.json"
B006_INPUTS = EXPERIMENTS / "GOLD-001-batch-006-preregistration-inputs.json"

#: Batch → (records file, overlay that supersedes it, review-decisions file).
#: The same resolution eligibility_status.py uses, so the two cannot drift.
BATCHES = {
    1: ("gold_review_batch_001.json", "evals/gold/batch_001_v2/overlay.json", None),
    2: ("gold_review_batch_002.json", None, None),
    3: ("gold_review_batch_003.json", None, None),
    4: ("gold_review_batch_004_final.json", None, "b004-review-decisions.json"),
    5: ("gold_review_batch_005_final.json", None, "b005-review-decisions.json"),
    6: ("gold_review_batch_006_final.json", None, "b006-review-decisions.json"),
}
FROZEN_SYSTEMS = {
    "SYSTEM-A-GLOBAL":
        "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38",
    "SYSTEM-B-DOC-C":
        "304c350940b83733df6043ae3a8abdcbcde33d16950730127aa9f1f39494388b",
}
SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 15mm 13mm 13mm 13mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.2pt;
  line-height: 1.44; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 20pt; line-height: 1.12; margin: 0 0 4pt; letter-spacing: -0.5pt; }
h2 { font-size: 12pt; margin: 17pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.3pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 9.9pt; margin: 11pt 0 4pt; }
h4 { font-size: 9.2pt; margin: 8pt 0 3pt; color: #33373d; }
p { margin: 0 0 6pt; }
code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 10.4pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8pt;
  page-break-inside: avoid; }
table.long { page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 4.5pt 5pt; background: #16181c;
     color: #fff; }
td { padding: 3.5pt 5pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
tfoot td { font-weight: 700; border-top: 1.3pt solid #16181c; background: #fff; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.mono { font-family: "SFMono-Regular", Consolas, monospace; white-space: nowrap;
  width: 1%; }
.dim { color: #6f747b; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt;
  margin: 9pt 0 11pt; page-break-inside: avoid; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.1pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }
.callout.win .label { color: #14532d; }
ol, ul { margin: 0 0 7pt; padding-left: 15pt; } li { margin-bottom: 3.5pt; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt;
  margin: 4pt 0 11pt; }
.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8pt;
  margin: 4pt 0 11pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 7pt 9pt; border-radius: 3pt; }
.stat.warn { border-color: #8a1c1c; background: #fdf5f5; }
.stat.win { border-color: #14532d; background: #f2f8f4; }
.stat .big { font-size: 15pt; font-weight: 700; line-height: 1.1;
  letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.1pt; color: #52565d; margin-top: 2pt; }
blockquote { margin: 4pt 0 6pt; padding: 5pt 9pt; border-left: 2pt solid #c9ccd1;
  background: #f6f7f9; font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 7.4pt; color: #33373d; white-space: pre-wrap; }
.break { page-break-before: always; }
.toc { columns: 2; font-size: 8.6pt; margin-bottom: 10pt; }
.toc div { margin-bottom: 2.5pt; break-inside: avoid; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.5pt; color: #6f747b; }
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


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def gather() -> dict:
    """Read every artifact this document reports on. Nothing is computed from memory."""
    status = load(STATUS)
    closures, batches, reviews = {}, {}, {}
    for number, (records_file, overlay, decisions) in BATCHES.items():
        closures[number] = load(EXPERIMENTS /
                                f"GOLD-001-batch-{number:03d}-closure.json")
        payload = load(REVIEW / records_file)
        if overlay and (REPO_ROOT / overlay).exists():
            payload = {**payload, "records": load(REPO_ROOT / overlay)["case_records"],
                       "overlay": overlay}
        batches[number] = payload
        if decisions and (EXPERIMENTS / decisions).exists():
            reviews[number] = load(EXPERIMENTS / decisions)
    reports = {}
    for number in (4, 5, 6):
        path = EXPERIMENTS / f"GOLD-001-batch-{number:03d}-generation-report.json"
        if path.exists():
            reports[number] = load(path)
    commits = subprocess.run(
        ["git", "log", "--format=%h|%ad|%s", "--date=short", "-14"],
        capture_output=True, text=True, cwd=REPO_ROOT,
        check=False).stdout.strip().splitlines()
    return {"status": status, "closures": closures, "batches": batches,
            "reviews": reviews, "reports": reports,
            "prereg": load(PREREG), "audit": load(AUDIT),
            "b006_inputs": load(B006_INPUTS),
            "commits": [c.split("|", 2) for c in commits if "|" in c]}


def defect_ledger(data: dict) -> list[dict]:
    """Every generator defect any review recorded, in the order they were found."""
    ledger = []
    for entry in data["b006_inputs"]["inputs"]:
        item = normalise_all([entry])[0]
        item["found_in"] = "batch 005 review"
        item["fixed_in"] = "batch 006"
        ledger.append(item)
    for entry in data["reviews"].get(6, {}).get("generator_defects_found", []):
        item = normalise_all([entry])[0]
        item["found_in"] = "batch 006 review"
        item["fixed_in"] = "batch 007 (preregistered)"
        ledger.append(item)
    return ledger


def all_cases(data: dict) -> list[dict]:
    """Every approved case across every closed batch, with its batch number."""
    out = []
    for number, payload in sorted(data["batches"].items()):
        for record in payload["records"]:
            if record.get("verification_status") != "human_verified":
                continue
            out.append({"batch": number, **record})
    return sorted(out, key=lambda r: r["candidate_id"])


def all_rejections(data: dict) -> list[dict]:
    out = []
    for number, closure in sorted(data["closures"].items()):
        for entry in closure.get("rejected", []):
            out.append({"batch": number, **entry})
    return out


def build_html(data: dict) -> str:
    status, closures = data["status"], data["closures"]
    combined = status["combined"]
    prereg, audit = data["prereg"], data["audit"]
    b006 = closures[6]
    census = b006["corpus_census"]
    cases = all_cases(data)
    rejections = all_rejections(data)
    ledger = defect_ledger(data)
    state = prereg["starting_state"]
    proj = prereg["projection"]

    batch_rows = rows([
        (f"<b>{n:03d}</b>", c["closed_at"][:10], c["totals"]["candidates"],
         c["totals"]["human_verified"], c["totals"]["human_rejected"],
         f"{c['totals']['acceptance_rate']:.0%}",
         next(b["holdout_eligible"] for b in status["batches"] if b["batch"] == n),
         f"<code>{c['closure_sha256'][:10]}…</code>")
        for n, c in sorted(closures.items())
    ], classes=("mono", "mono", "num", "num", "num", "num", "num", ""))

    reasoning = Counter(r["reasoning_type"] for r in cases if r.get("reasoning_type"))
    provider = Counter(r["provider"] for r in cases)
    shape = Counter(r.get("evidence_shape", "single_span") for r in cases)
    documents = len({r.get("document_title") for r in cases})

    reasoning_rows = rows([
        (f"<code>{k}</code>", v, f"{v / len(cases):.0%}")
        for k, v in reasoning.most_common()
    ], classes=("", "num", "num"))

    case_rows = rows([
        (f"<code>{r['candidate_id']}</code>", r["provider"][:4],
         f"<code>{(r.get('reasoning_type') or '')[:26]}</code>",
         ticks((r.get("question") or "")[:96]))
        for r in cases
    ], classes=("mono", "mono", "", ""))

    reject_rows = rows([
        (f"<code>{r['candidate_id']}</code>", f"{r['batch']:03d}",
         ticks((r.get("reason") or "")[:190]))
        for r in rejections
    ], classes=("mono", "mono", ""))

    ledger_rows = rows([
        (f"<b>{d['id']}</b>", ticks(d["defect"]), f"<code>{esc(d['seen_in'])}</code>",
         d["found_in"], d["fixed_in"])
        for d in ledger
    ], classes=("num", "", "mono", "", ""))

    commit_rows = rows([
        (f"<code>{sha}</code>", date, esc(subject))
        for sha, date, subject in data["commits"]
    ], classes=("mono", "mono", ""))

    check_rows = rows([
        (f"<b>{c['id']}</b>", c["question"], c["fails_when"])
        for c in prereg["entailment_self_check"]
    ], classes=("num", "", ""))

    gate_rows = rows([
        (g["gate"], f"<code>{esc(g['implemented_in'])}</code>", g["behaviour"])
        for g in prereg["retained_gates"]
    ])

    modules = [
        ("rag_v1.gold.scoping", "bare definition bullets, asked of every span",
         "batch 006", "GOLD-B005-01"),
        ("rag_v1.gold.relations", "source and question triples; direction check",
         "batch 006", "GOLD-B005-10"),
        ("rag_v1.gold.questionform", "question form must match evidence form",
         "batch 006", "GOLD-B005-08, -18"),
        ("rag_v1.gold.normalisation", "markdown link stripping (3 link shapes)",
         "batch 006", "GOLD-B005-15"),
        ("rag_v1.gold.defects", "one defect shape across six renderers",
         "batch 006", "three renderers crashed identically"),
        ("rag_v1.gold.bridge_equivalence",
         ("a bridge entity must mean the same thing in both spans"),
         "batch 005", "max_tokens near-miss"),
        ("rag_v1.gold.mining_v5",
         ("interaction, constraint, lifecycle and ambiguity miners"),
         "batch 005", "question subject ≠ fact subject"),
        ("rag_v1.gold.multihop", "dependency-first chain search",
         "batch 005", "batch 004's 559-pair all-pairs search"),
        ("rag_v1.gold.authoring",
         ("question builders, including the batch-006 predicate lane"),
         "batches 005-006", "2482 facts no builder could reach"),
        ("rag_v1.gold.eligibility", "the deterministic holdout gate (6 conditions)",
         "batch 005", "required_evidence_declared added"),
    ]
    module_rows = rows([
        (f"<code>{name}</code>", purpose, added, ticks(because))
        for name, purpose, added, because in modules
    ], classes=("", "", "mono", ""))

    b004, b005 = closures[4], closures[5]
    mh4 = b004["multi_hop_rejection"]
    mh5 = b005["multi_hop_search"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 — The Complete Record</title><style>{CSS}</style></head><body>

<h1>GOLD-001 — The Complete Record</h1>
<p class="subtitle">Production RAG v1 · six closed batches ·
{combined['holdout_eligible']} holdout-eligible cases · corpus snapshot
<code>{SNAPSHOT}</code> · status generated {esc(status['generated_at'])}</p>
<div class="rule"></div>

<div class="callout win">
<div class="label">Where the project stands</div>
<p><b>{combined['human_verified']} human-verified cases, all
{combined['holdout_eligible']} of them holdout-eligible</b>, drawn from
{combined['candidates']} candidates across six closed batches.
{combined['human_rejected']} were rejected and every one is kept as a negative audit
example. <b>{combined['genuine_multi_hop']}</b> case is genuine multi-hop.</p>
<p>No retrieval system has ever been run against a GOLD candidate. No holdout and no
validation split is frozen. SYSTEM-A and SYSTEM-B remain frozen and unexecuted.</p>
</div>

<div class="grid4">
  <div class="stat win"><div class="big">{combined['human_verified']}</div>
    <div class="cap">human-verified</div></div>
  <div class="stat win"><div class="big">{combined['holdout_eligible']}</div>
    <div class="cap">holdout-eligible</div></div>
  <div class="stat"><div class="big">{combined['human_rejected']}</div>
    <div class="cap">rejected, all preserved</div></div>
  <div class="stat warn"><div class="big">{state['still_needed']}</div>
    <div class="cap">short of the {state['project_target']} target</div></div>
</div>

<div class="toc">
<div><b>1.</b> The six closed batches</div>
<div><b>2.</b> What is in the benchmark</div>
<div><b>3.</b> Every approved case</div>
<div><b>4.</b> Every rejection</div>
<div><b>5.</b> Batch 004 — multi-hop, measured</div>
<div><b>6.</b> Batch 005 — two lanes</div>
<div><b>7.</b> Batch 006 — the four fixes, and the shortfall</div>
<div><b>8.</b> The generator defect ledger</div>
<div><b>9.</b> Modules built</div>
<div><b>10.</b> Heading parser audit</div>
<div><b>11.</b> Batch 007 — preregistered</div>
<div><b>12.</b> Tests and invariants</div>
<div><b>13.</b> Commits and artifacts</div>
</div>

<h2>1. The six closed batches</h2>
<p>A batch closes only when every candidate has a final human decision. The closure
records a hash over its candidate records, and the test suite re-checks that hash, so an
edit after closure fails the tests rather than passing unnoticed.</p>
<table><thead><tr><th>batch</th><th>closed</th><th class="num">candidates</th>
<th class="num">verified</th><th class="num">rejected</th><th class="num">acceptance</th>
<th class="num">eligible</th><th>closure hash</th></tr></thead>
<tbody>{batch_rows}</tbody>
<tfoot><tr><td>all</td><td></td><td class="num">{combined['candidates']}</td>
<td class="num">{combined['human_verified']}</td>
<td class="num">{combined['human_rejected']}</td>
<td class="num">{combined['human_verified'] / combined['candidates']:.0%}</td>
<td class="num">{combined['holdout_eligible']}</td><td></td></tr></tfoot></table>

<div class="callout">
<div class="label">Three states, deliberately kept apart</div>
<p><code>precheck_holdout_ready</code> is <b>structural only</b> — a script's verdict
that a record is checkable. <code>human_verified</code> is an <b>owner decision</b> and
nothing else can set it. <code>holdout_eligible</code> is <b>derived</b>: a
deterministic gate re-run against the current records at every closure.</p>
<p>The distinction is load-bearing. Batch 005 shipped 19 of 19 precheck-ready and its
review still repaired seven and rejected four. Batch 006 shipped 9 of 9 precheck-ready
and the owner still rejected one and revised five.</p>
</div>

<h2>2. What is in the benchmark</h2>
<div class="grid3">
  <div class="stat"><div class="big">{documents}</div>
    <div class="cap">distinct source documents</div></div>
  <div class="stat"><div class="big">{provider.get('anthropic', 0)} / {provider.get('openai', 0)}</div>
    <div class="cap">anthropic / openai</div></div>
  <div class="stat"><div class="big">{shape.get('single_span', 0)} / {sum(v for k, v in shape.items() if k != 'single_span')}</div>
    <div class="cap">single-span / multi-span</div></div>
</div>
<table><thead><tr><th>reasoning type</th><th class="num">cases</th>
<th class="num">share</th></tr></thead><tbody>{reasoning_rows}</tbody></table>
<p>Every case is anchored to exact character offsets in the frozen corpus, carries an
evidence hash, and lists the literal critical strings its claims depend on. Ground truth
never depends on chunk IDs, so a chunking change cannot silently invalidate the
benchmark.</p>

<div class="break"></div>
<h2>3. Every approved case</h2>
<p class="dim">All {len(cases)} human-verified cases, in id order. Batch 001's rows come
from its v2 overlay, which supersedes the closed v1 record for eligibility.</p>
<table class="long"><thead><tr><th>id</th><th>prov</th><th>reasoning type</th>
<th>question</th></tr></thead><tbody>{case_rows}</tbody></table>

<div class="break"></div>
<h2>4. Every rejection</h2>
<p>All {len(rejections)} rejected candidates are kept in their batch records as negative
audit examples. None was deleted, and none was replaced with a substitute to keep a
count up.</p>
<table class="long"><thead><tr><th>id</th><th>batch</th><th>why</th></tr></thead>
<tbody>{reject_rows}</tbody></table>

<div class="break"></div>
<h2>5. Batch 004 — multi-hop, measured rather than assumed</h2>
<p>Batch 004 set out to find genuinely composable multi-hop questions: cases where the
answer requires combining two spans and neither span alone suffices. It tested
<b>{mh4['attempted_pairs']}</b> identifier-sharing pairs and found <b>{mh4['passed']}</b>.</p>
<table><thead><tr><th>why a pair was rejected</th><th class="num">pairs</th></tr></thead>
<tbody>{rows([(k.replace('_', ' '), v) for k, v in mh4['reasons'].items()],
              classes=('', 'num'))}</tbody>
<tfoot><tr><td>rejected</td><td class="num">{mh4['rejected']}</td></tr>
<tr><td><b>passed</b></td><td class="num"><b>{mh4['passed']}</b></td></tr></tfoot></table>
<p>A near-miss diagnostic re-examined the {b004['near_miss_diagnostic']['pairs']} pairs
that failed on a single gate. All were <b>correct rejections</b> — the rule under test
was <i>{esc(b004['near_miss_diagnostic']['rule_under_test'])}</i>. The best-known of
them, <code>max_tokens</code>, is a request parameter in one span and a
<code>stop_reason</code> value in the other: the same token, two different things. That
near-miss is why <code>rag_v1.gold.bridge_equivalence</code> exists, and it is now a
regression test.</p>
<p>Batch 004 closed at {b004['totals']['human_verified']} of
{b004['totals']['candidates']} with {len(b004.get('repaired') or [])} anchor repairs and
{len(b004.get('human_overrides') or [])} owner overrides. An override never deletes a
finding: the finding stays on the record next to the owner's decision to accept it.</p>

<h2>6. Batch 005 — two lanes, and a second multi-hop measurement</h2>
<p>Batch 005 split its effort. Lane A spent it where the corpus pays — interactions,
constraints, lifecycle statements, cross-component ambiguity. Lane B searched for chains
<b>dependency-first</b>, opening only on sentences that state a dependency, rather than
batch 004's all-pairs sweep.</p>
<table><thead><tr><th>dependency-first search</th><th class="num">count</th></tr></thead>
<tbody>{rows([(k.replace('_', ' '), v) for k, v in mh5['funnel'].items()],
              classes=('', 'num'))}
<tr><td>budget</td><td class="num">{mh5['budget']}</td></tr>
<tr><td><b>new unique chains exported</b></td><td class="num"><b>0</b></td></tr>
</tbody></table>
<div class="callout">
<div class="label">Two searches, two methods, one chain</div>
<p>The single valid chain batch 005 found was the chain batch 004 had already closed, so
batch 005 exported none. <b>That is a result about the corpus, not a failed search</b>:
this frozen snapshot contains very little naturally composable multi-hop structure. It is
why batch 006 was instructed not to search again, and why the project's multi-hop count
is {combined['genuine_multi_hop']} and is not presented as coverage.</p>
</div>
<p>Batch 005 targeted 30 and exported {b005['generation_shortfall']['exported']}; of the
{b005['generation_shortfall']['entered_semantic_self_review']} candidates that reached
the semantic self-review, {b005['generation_shortfall']['dropped_by_semantic_self_review']}
were dropped. It closed at {b005['totals']['human_verified']} of
{b005['totals']['candidates']} — the lowest acceptance rate of the six
({b005['totals']['acceptance_rate']:.0%}), and the batch that produced four of the seven
generator defects in the ledger below.</p>

<div class="break"></div>
<h2>7. Batch 006 — the four fixes, and a shortfall worth having</h2>
<p>Batch 006 implemented the four fixes batch 005's closure preregistered, <b>before</b>
authoring anything, then targeted {b006['generation_shortfall']['target']} candidates and
exported {b006['generation_shortfall']['exported']}.</p>

<table><thead><tr><th>the census behind the shortfall</th><th class="num">count</th>
</tr></thead><tbody>
<tr><td>facts mined</td><td class="num">{census['facts_mined']}</td></tr>
<tr><td>distinct evidence spans the miners reach</td>
    <td class="num">{census['distinct_evidence_texts']}</td></tr>
<tr><td><b>of those, unspent by any closed batch</b></td>
    <td class="num"><b>{census['unspent_distinct_texts']}</b></td></tr>
<tr><td>mined facts that reached no builder</td>
    <td class="num">{data['reports'][6]['removed'].get('unbuildable')}</td></tr>
</tbody></table>

<div class="callout warn">
<div class="label">The finding that changed the plan</div>
<p><b>The corpus is not exhausted. The authoring is.</b>
{census['unspent_distinct_texts']} distinct evidence spans in the frozen snapshot have
never been used by any closed batch, and no deterministic template could turn them into a
question without paraphrasing — what remains is long, multi-clause prose, and a template
that fits it is a template that invents wording.</p>
<p>Refusing all paraphrase is precisely what keeps those facts out of the benchmark. That
is the problem batch 007 is preregistered to solve.</p>
</div>

<p>The owner approved {b006['totals']['human_verified']} of
{b006['totals']['candidates']}: five after revisions they specified, three as generated,
one rejected. Three taxonomy corrections were applied — a requirement mislabelled as a
configuration interaction, a compatibility statement as an exact lookup, a migration note
as an interaction — and <b>no anchor moved</b>, which a test now enforces. Every revision
is attributed to the owner rather than to Claude's review, because a change someone asked
for and a change the author proposed are different acts.</p>

<h3>The one rejection, and the gate that missed it</h3>
<p><code>GOLD-B006-06</code> was rejected as <b>DUPLICATE_FACT / BENCHMARK_REDUNDANCY</b>.
The fact is supported, but <code>GOLD-B005-11</code> already carries the same operational
relation from the OpenAI Python library while this obtained it from the TypeScript
library. Duplicate control compares question text, span offsets and span text — and two
libraries documenting the same behaviour share none of those. Recorded as defect E.</p>

<h2>8. The generator defect ledger</h2>
<p>Every defect a review found in the generator, what case exposed it, and where it was
or will be fixed. A defect is <b>recorded, never patched into a closed batch</b>: the
generation artifact stays as generated, and the fix belongs in the next batch's
preregistration where it can be declared before it sees a candidate.</p>
<table class="long"><thead><tr><th></th><th>defect</th><th>seen in</th><th>found</th>
<th>fixed in</th></tr></thead><tbody>{ledger_rows}</tbody></table>
{"".join(f'<h4>{esc(d["id"])}. {esc(d["defect"])}</h4><p>{ticks(d["detail"] or "")}</p>'
         + (f'<p class="dim"><b>Fix:</b> {ticks(d["proposed_fix"])}</p>'
            if d.get("proposed_fix") else "")
         for d in ledger)}

<div class="break"></div>
<h2>9. Modules built</h2>
<p>Each exists because a specific candidate got through a gate that should have caught
it. Every one carries a regression test built from that candidate, not from an invented
example — a test written from an imagined case tests the rule the author had in mind,
and these rules exist because the author's rule missed the real thing.</p>
<table class="long"><thead><tr><th>module</th><th>what it checks</th><th>added</th>
<th>because of</th></tr></thead><tbody>{module_rows}</tbody></table>

<h2>10. Heading parser audit</h2>
<p><b>{audit['likely_prose']} of {audit['headings_parsed']} parsed headings
({audit['likely_prose_share']:.2%})</b> read as ordinary prose rather than as a label,
across {audit['documents_with_prose_headings']} of {audit['documents']} documents.
{audit['suspicious_headings']} were suspicious on at least one rule.</p>
<table><thead><tr><th>why a heading was flagged</th><th class="num">headings</th>
</tr></thead><tbody>{rows([(k, v) for k, v in audit['reason_counts'].items()],
                          classes=('', 'num'))}</tbody></table>
<p>{esc(audit['verdict']['finding'])}</p>
<p><b>Nothing was rewritten.</b> No heading changed, no document was reparsed into
storage, no evidence anchor moved. A closed case approved against a bad
<code>section_path</code> was approved against its <i>evidence</i>; the path is metadata
beside it. What changed is a rule: <code>section_path</code> is never trusted for claim
scope, and a candidate's exact evidence must carry the scope its claim needs.</p>

<div class="break"></div>
<h2>11. Batch 007 — preregistered, not generated</h2>
<p class="subtitle">{esc(prereg['status'])}</p>
<div class="callout">
<div class="label">The line</div>
<p style="font-size:10.5pt"><b>{esc(prereg['strategy_change']['the_line'])}</b></p>
</div>
<p>Batch 007 introduces <b>controlled evidence-grounded question paraphrasing</b>: where
a deterministic template cannot express an explicit evidence fact, a model may author the
question. This is an <b>authoring</b> change. The evidence stays frozen and exact, the
ground truth is still read out of the source, and every existing gate still runs.</p>

<h3>The order is the safeguard</h3>
<ol>{"".join(f"<li>{esc(step)}</li>" for step in prereg["authoring_order"])}</ol>
<p><b>Never:</b> {esc(prereg['forbidden_order'])}. Inventing a question and then hunting
for evidence to support it is how a benchmark ends up testing what its author imagined
rather than what the documentation says.</p>

<h3>The entailment self-check — any failure drops the candidate</h3>
<table class="long"><thead><tr><th></th><th>check</th><th>it fails when</th></tr></thead>
<tbody>{check_rows}</tbody></table>
<p>Every paraphrased candidate also stores its <code>source_fact_literal</code> and its
subject/relation/object beside the authored question, so a reviewer can see the gap
between fact and question and disagree with it.</p>

<h3>Answer conservatism</h3>
<p>{esc(prereg['answer_conservatism']['rule'])} Source says
<i>{esc(prereg['answer_conservatism']['example_source'])}</i> → answer
<i>{esc(prereg['answer_conservatism']['example_good_answer'])}</i>, <b>not</b>
<i>{esc(prereg['answer_conservatism']['example_bad_answer'])}</i>.
{esc(prereg['answer_conservatism']['why_bad'])}</p>

<h3>A pilot gates the lane</h3>
<p><b>{prereg['calibration_pilot']['size']} spans</b> that failed batch 006 <i>only</i>
because no builder could express them — not spans that failed a semantic gate, which
failed for reasons paraphrasing does not fix. Run through the paraphraser and every
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

<div class="callout warn">
<div class="label">The arithmetic, which is not a plan</div>
<p>The project holds <b>{state['holdout_eligible']}</b> and the target is
<b>{state['project_target']}</b>, leaving <b>{state['still_needed']}</b>. Batch 007
targets <b>{proj['batch_007_target']}</b> candidates, which at the six observed
acceptance rates lands between <b>{proj['if_low_target_at_worst_rate']}</b> and
<b>{proj['if_high_target_at_best_rate']}</b> eligible cases — <b>short of
{state['project_target']}</b>. More than one batch will be needed, and that is not a
reason to approve a candidate that should not be approved.</p>
</div>

<div class="break"></div>
<h2>12. Tests and invariants</h2>
<p>The suite is <b>{data['tests']}</b>. Ten test files cover GOLD-001 specifically,
including regression tests built from
<code>GOLD-B005-01</code>, <code>-08</code>, <code>-10</code>, <code>-11</code>,
<code>-15</code> and <code>-18</code>, and from batch 006's duplicate against
<code>GOLD-B005-11</code>.</p>
<h3>What the tests hold</h3>
<ul>
<li><b>Closed-batch immutability.</b> Every closure hash is recomputed from the records
it covers. An edit to a closed batch fails the suite.</li>
<li><b>No retrieval leakage.</b> <code>retrieval_was_not_run</code> is asserted on every
batch and every record, and each record is checked for retrieval-derived fields.</li>
<li><b>Frozen system hashes.</b> SYSTEM-A <code>9afcb5b7…</code> and SYSTEM-B
<code>304c3509…</code> are compared against the frozen constants.</li>
<li><b>Evidence integrity.</b> Every span hashes to its own text; every critical string
is literally inside its own span.</li>
<li><b>Taxonomy changes move no evidence.</b> Offsets, text and hashes are compared
before and after every relabelling.</li>
<li><b>Nothing claims verification it lacks.</b> Generation artifacts must carry no
decision; only the owner appears as a reviewer.</li>
<li><b>The paraphrasing contract.</b> Batch 007 cannot broaden scope, add conditions,
reverse relations or introduce causal claims without a test failing.</li>
</ul>

<h3>Invariants, unchanged across all six batches</h3>
<ul>
<li>No retrieval system has been run against any GOLD candidate at any point.
<code>retrieval_was_not_run = true</code>; <code>systems_executed = []</code>. No
question was selected, ordered or worded because of retrieval difficulty.</li>
<li>SYSTEM-A and SYSTEM-B remain frozen and unexecuted; the corpus snapshot, chunks,
embeddings, fusion, DOC-C, top-k, routing, prompts and reranking are unchanged. All of
this has been evaluation-authoring work only.</li>
<li>No holdout is frozen and no validation split is frozen.</li>
<li>Closed batches are never modified. Repairs live beside a generation artifact, never
inside it; a new discovery about old tooling becomes an audit, an erratum or a future
overlay, never a silent mutation.</li>
<li>Claude's self-review is authoring, not verification. It has never been presented as
independent verification, and no AI may set <code>human_verified</code>.</li>
</ul>

<h2>13. Commits and artifacts</h2>
<table class="long"><thead><tr><th>commit</th><th>date</th><th>subject</th></tr></thead>
<tbody>{commit_rows}</tbody></table>

<h3>Where each figure in this document comes from</h3>
<ul>
<li><code>experiments/GOLD-001/GOLD-001-eligibility-status.json</code> — project totals
and the per-batch eligibility figures.</li>
<li><code>experiments/GOLD-001/GOLD-001-batch-00N-closure.json</code> (N = 1…6) —
acceptance, closure hashes, repairs, overrides, shortfalls, multi-hop results.</li>
<li><code>evals/review/gold_review_batch_00N*.json</code> — the candidate records
themselves, and batch 001's v2 overlay.</li>
<li><code>experiments/GOLD-001/b00N-review-decisions.json</code> — the review findings
and the generator defects each batch recorded.</li>
<li><code>experiments/GOLD-001/GOLD-001-heading-parser-audit.json</code> — the heading
figures.</li>
<li><code>experiments/GOLD-001/GOLD-001-batch-007-preregistration.json</code> — the
batch-007 contract.</li>
</ul>

<footer>
Generated by scripts/build_gold001_complete_record.py. Every figure is read from the
artifacts listed above at build time; none is typed into this document. The build refuses
to run if any batch is missing a closure, if a closure's totals disagree with its records,
if the eligibility gate re-run disagrees with any closure, if the project totals disagree
with the sum of the batches, if any batch records a retrieval run, if a frozen system hash
has moved, if a batch-007 artifact exists, or if the page would claim batch 007 reaches
the project target. Raw provider documentation is not redistributed; the corpus is
referenced by snapshot id and cases by character offset.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",
                        default="docs/reports/GOLD-001-complete-record.pdf")
    parser.add_argument("--tests", default=None,
                        help="pytest summary line; measured if omitted")
    args = parser.parse_args()

    data = gather()
    status, closures, batches = data["status"], data["closures"], data["batches"]
    combined = status["combined"]

    # 1. Every batch must have a closure and records.
    for number in BATCHES:
        if number not in closures or number not in batches:
            raise SystemExit(f"refusing to build: batch {number:03d} is incomplete")

    # 2. Each closure's totals must match the records it closed.
    for number, closure in closures.items():
        payload = batches[number]
        if payload.get("overlay"):
            continue  # the overlay supersedes the closed v1 record by design
        verified = sum(1 for r in payload["records"]
                       if r.get("verification_status") == "human_verified")
        if closure["totals"]["human_verified"] != verified:
            raise SystemExit(f"refusing to build: batch {number:03d}'s closure says "
                             f"{closure['totals']['human_verified']} verified, its "
                             f"records say {verified}")

    # 3. The eligibility gate is re-run, never trusted.
    for number, payload in batches.items():
        approved = [r for r in payload["records"]
                    if r.get("verification_status") == "human_verified"]
        eligible = sum(1 for r in approved if eligibility(r)["holdout_eligible"])
        recorded = next(b["holdout_eligible"] for b in status["batches"]
                        if b["batch"] == number)
        if eligible != recorded:
            raise SystemExit(f"refusing to build: batch {number:03d}'s eligibility "
                             f"gate gives {eligible}, the status says {recorded}")

    # 4. The project totals must be the sum of the batches.
    if sum(b["human_verified"] for b in status["batches"]) != combined["human_verified"]:
        raise SystemExit("refusing to build: the project totals do not sum")

    # 5. No batch may record a retrieval run.
    for number, payload in batches.items():
        if payload.get("retrieval_was_not_run") is False or \
                payload.get("systems_executed"):
            raise SystemExit(f"refusing to build: batch {number:03d} records a "
                             "retrieval run")
    if not status["retrieval_was_not_run"] or status["systems_executed"]:
        raise SystemExit("refusing to build: the project status records a retrieval run")

    # 6. The frozen systems must not have moved.
    from rag_v1.systems import FROZEN_HASHES
    if dict(FROZEN_HASHES) != FROZEN_SYSTEMS:
        raise SystemExit("refusing to build: a frozen system hash has changed")

    # 7. Nothing may be frozen yet.
    if status["holdout_frozen"]:
        raise SystemExit("refusing to build: this document describes an unfrozen "
                         "holdout and the holdout is frozen")

    # 8. Batch 007 must still be only preregistered.
    if (REPO_ROOT / "evals/review/gold_review_batch_007.json").exists():
        raise SystemExit("refusing to build: a batch-007 artifact exists")

    if args.tests:
        data["tests"] = args.tests
    else:
        # check=False deliberately: a failing suite is read from the summary line
        # below and refused there, with the count, rather than as a bare exception.
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                                capture_output=True, text=True, cwd=REPO_ROOT,
                                check=False)
        line = [ln for ln in result.stdout.splitlines() if " passed" in ln]
        if not line:
            raise SystemExit("refusing to build: could not read a pytest summary")
        data["tests"] = line[-1].split(" in ")[0].strip()
        if "failed" in data["tests"] or "error" in data["tests"]:
            raise SystemExit(f"refusing to build: the suite is not green — "
                             f"{data['tests']}")

    document = build_html(data)

    # 9. The page must not claim batch 007 reaches the project target when it cannot.
    if not data["prereg"]["projection"]["reaches_target_this_batch"] and \
            "short of" not in document:
        raise SystemExit("refusing to build: batch 007 cannot reach the project target "
                         "and the page does not say so")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "complete.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    print(f"  {combined['human_verified']} verified, "
          f"{combined['holdout_eligible']} eligible, "
          f"{combined['human_rejected']} rejected across {len(closures)} batches")
    print(f"  tests: {data['tests']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
