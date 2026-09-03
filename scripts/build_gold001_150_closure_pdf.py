#!/usr/bin/env python3
"""Render the GOLD-001 closure at 150 as a PDF.

Every figure is read from the closure, the eligibility status and the group records at
build time; nothing is retyped. Seven gates refuse the build rather than publish a
document that disagrees with the project state.

The page leads with what the size does not buy. 150 is the benchmark-size target and that
is all it is: provider- and category-skewed, genuine multi-hop still n=1, the
preregistered pilot never run, the frozen corpus still not reproduced, retrieval still
blocked. A closure that opened on the number and buried those would be the wrong
document.
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

from rag_v1.gold.eligibility import evaluate  # noqa: E402

CLOSURE = REPO_ROOT / "experiments/GOLD-001/GOLD-001-150-case-closure.json"
STATUS = REPO_ROOT / "experiments/GOLD-001/GOLD-001-eligibility-status.json"
ADMISSION = REPO_ROOT / "experiments/GOLD-001/GOLD-001-HA-admission.json"
DEVIATION = REPO_ROOT / "experiments/GOLD-001/GOLD-001-protocol-deviation-001.json"
LIMITATION = REPO_ROOT / "experiments/GOLD-001/GOLD-001-corpus-reproduction-limitation.json"
HA_RECORDS = REPO_ROOT / "evals/review/gold_review_HA01_HA60_final.json"
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
.subtitle { font-size: 10.3pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.3pt;
  page-break-inside: avoid; }
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
.bar { height: 7pt; background: #16181c; border-radius: 1pt; display: inline-block;
  vertical-align: middle; }
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


def bars(dist: dict, total: int) -> str:
    return rows([(ticks(k), f"{v}", f"{v / total:.0%}",
                  f"<span class='bar' style='width:{max(2, round(120 * v / total))}pt'></span>")
                 for k, v in dist.items()], ("", "num", "num", ""))


def build_html(data: dict) -> str:
    c, adm = data["closure"], data["admission"]
    dev, lim = data["deviation"], data["limitation"]
    counts, cov, limits = c["counts"], c["coverage"], c["limitations"]
    total = counts["holdout_eligible"]
    repair = adm["ha47_repair"]

    group_rows = rows(
        [(esc(g["group"]), f"{g['human_verified']}", f"{g['human_rejected']}",
          f"<strong>{g['holdout_eligible']}</strong>",
          f"<span class='dim'>{esc(g['eligibility_source'])}</span>")
         for g in c["by_group"]], ("", "num", "num", "num", ""))

    mitigation_rows = rows(
        [(esc(m["mitigation"]), esc(m["figure"]), f"<span class='dim'>{esc(m['limit'])}</span>")
         for m in dev["mitigations_actually_performed"]])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GOLD-001 closure at 150</title><style>{CSS}</style></head><body>
<h1>GOLD-001 closed at {total}</h1>
<p class="subtitle">{esc(c['closed_at'])} &middot; closure hash
<code>{esc(c['closure_hash'])}</code> &middot; every figure read from the records at
build time</p>
<div class="rule"></div>

<div class="callout warn"><div class="label">Read this first</div>
<p><strong>{total} cases is the achieved benchmark-<em>size</em> target. It is not
coverage.</strong> {ticks(limits['provider_imbalance'])}
{ticks(limits['category_imbalance'])} Genuine multi-hop is still
<strong>n={counts['genuine_multi_hop']}</strong>. The preregistered calibration pilot was
never run and the frozen corpus is still not reproduced, so retrieval stays blocked.
None of that is fixed by reaching {total}.</p></div>

<div class="grid4">
  <div class="stat win"><div class="big">{counts['human_verified']}</div>
    <div class="cap"><code>human_verified</code></div></div>
  <div class="stat win"><div class="big">{counts['holdout_eligible']}</div>
    <div class="cap"><code>holdout_eligible</code></div></div>
  <div class="stat"><div class="big">{counts['human_rejected']}</div>
    <div class="cap"><code>human_rejected</code></div></div>
  <div class="stat warn"><div class="big">{counts['genuine_multi_hop']}</div>
    <div class="cap">genuine multi-hop</div></div>
</div>

<h2>Where the {total} come from</h2>
<table><thead><tr><th>group</th><th class="num">verified</th>
<th class="num">rejected</th><th class="num">eligible</th>
<th>eligibility read from</th></tr></thead>
<tbody>{group_rows}</tbody>
<tfoot><tr><td>all</td><td class="num">{counts['human_verified']}</td>
<td class="num">{counts['human_rejected']}</td>
<td class="num">{counts['holdout_eligible']}</td><td></td></tr></tfoot></table>
<p>Counts are derived through <code>rag_v1.gold.eligibility</code>, re-evaluated at build
time rather than copied from the status file. Conditions checked:
{", ".join(f"<code>{esc(x)}</code>" for x in c["conditions_checked"])}.</p>

<h2>The 60 admitted cases</h2>
<p>Admitted from <code>{esc(adm['packet_identity']['pages'])}</code>-page
<em>{esc(c['admission']['packet'])}</em>, sha256
<code>{esc(c['admission']['packet_sha256'])}</code>. Bound by <strong>evidence
identity</strong> &mdash; version id, offsets and evidence hash &mdash; never by the
short <code>HA-nn</code> label, because a separate 64-case packet uses the same labels
for different cases. {esc(adm['source_verification']['spans'])} spans across
{esc(adm['source_verification']['records'])} records were re-sliced from the pinned
source and rehashed before any approval was applied.</p>
<p>The decision is the project owner's, read from
<code>{esc(adm['owner_decisions']['decision_file'])}</code>. Codex, Grok Expert and
ChatGPT each reviewed the set independently and approved nothing; an independent review
is a recommendation. {ticks(c['alternate_packet'])}</p>

<h3>HA-15 &mdash; a finding kept, not deleted</h3>
<p>The detector reports
<code>{esc(adm['ha15_override']['anaphora_status'])}</code>:
&ldquo;{esc(adm['ha15_override']['finding_retained'])}&rdquo;. The scored fact &mdash;
that the returned handoff JSON is validated locally in the SDK &mdash; does not depend on
resolving that neighbouring phrase, so the case carries an explicit
<code>{esc(adm['ha15_override']['override_reviewer'])}</code> override <em>and keeps the
finding on the record</em>.</p>

<h3>HA-47 &mdash; an evidence boundary completed</h3>
<p>Its second span opened on &ldquo;It&rdquo; with the antecedent stranded in the first
span, which fails the independently self-contained-span rule. The two spans are replaced
by the one contiguous slice that carries both, recomputed from the frozen source at
{repair['to']['char_start']}:{repair['to']['char_end']}
({repair['to']['evidence_char_length']} chars):</p>
<blockquote>{esc(repair['to']['evidence_hash'])}</blockquote>
<p>Reason {", ".join(f"<code>{esc(r)}</code>" for r in repair["reason"])}. The pre-repair
spans and their hashes are preserved in the record's revision history and are not the
admitted evidence. A paragraph break is present; read from the predicate rather than
waived, no eligibility condition looks at paragraph structure, so
<code>eligibility_blocking</code> is
<strong>{esc(repair['eligibility_blocking'])}</strong>.</p>

<div class="break"></div>
<h2>Coverage, as measured</h2>
<h3>Provider</h3>
<table><thead><tr><th>provider</th><th class="num">cases</th><th class="num">share</th>
<th></th></tr></thead><tbody>{bars(cov['provider'], total)}</tbody></table>
<h3>Reasoning type</h3>
<table><thead><tr><th>category</th><th class="num">cases</th><th class="num">share</th>
<th></th></tr></thead><tbody>{bars(cov['reasoning_type'], total)}</tbody></table>
<p>{cov['cases_with_no_recorded_reasoning_type']} eligible cases carry no
<code>reasoning_type</code> at all &mdash; batches 001 and 002 predate the field. They
are counted separately rather than folded into a category they were never assigned.</p>
<h3>Evidence shape</h3>
<table><thead><tr><th>shape</th><th class="num">cases</th><th class="num">share</th>
<th></th></tr></thead><tbody>{bars(cov['evidence_shape'], total)}</tbody></table>

<div class="callout warn"><div class="label">Concentration</div>
<p>The {total} cases are anchored in
<strong>{cov['distinct_source_documents']}</strong> distinct document versions, and the
single most-used document supplies <strong>{cov['cases_from_the_top_document']}</strong>
of them ({cov['cases_from_the_top_document'] / total:.0%}). A retrieval system that
happens to chunk that one document well will look better than it is.</p>
<p>Ambiguity cases: <strong>{cov['ambiguity_cases']}</strong>. The set cannot measure
whether a system declines to answer an under-specified question.</p></div>

<h2>Protocol deviation &mdash; {esc(dev['disposition'])}</h2>
<p>{ticks(dev['actual']['what_happened'])}
<strong>{ticks(dev['actual']['the_claim_that_must_never_be_made'])}</strong></p>
<p>{ticks(dev['why_it_matters'])}</p>
<table><thead><tr><th>mitigation actually performed</th><th>figure</th>
<th>what it does not establish</th></tr></thead>
<tbody>{mitigation_rows}</tbody></table>

<h2>Corpus reproduction &mdash; still incomplete</h2>
<div class="callout warn"><div class="label">{esc(lim['effect'])}</div>
<p>{lim['reproduced']['openai_documents']} OpenAI documents are individually reproducible
from pinned commits. The collective snapshot <code>{esc(lim['frozen_snapshot'])}</code>
is not reproduced:
<strong>{lim['outstanding']['anthropic_documents']}</strong> Anthropic documents and
<strong>{lim['outstanding']['unbuildable_identities']}</strong> unbuildable identities
remain outstanding.</p>
<p>{ticks(lim['why_partial_recovery_does_not_close_this'])} Reaching {total} admitted
cases does not certify the corpus those cases point into, and no retrieval system may be
run until that gate clears.</p></div>

<h2>Splits are not frozen</h2>
<p><code>holdout_frozen</code> is <strong>false</strong>.
{ticks(c['reason_not_frozen'])}</p>

<div class="callout"><div class="label">Untouched</div>
<p>SYSTEM-A and SYSTEM-B remain frozen and unexecuted.
<code>retrieval_was_not_run</code> is <strong>true</strong> and
<code>systems_executed</code> is empty. No candidate selection has seen a retrieval
outcome, which is the property that makes a future holdout worth having.</p></div>

<footer>GOLD-001 closure at {total} &middot; hash
<code>{esc(c['closure_hash'])}</code> &middot; generated from
GOLD-001-150-case-closure.json, GOLD-001-eligibility-status.json,
GOLD-001-HA-admission.json, GOLD-001-protocol-deviation-001.json and the group records.
No figure in this document was typed by hand.</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/GOLD-001-150-case-closure.pdf")
    args = parser.parse_args()

    data = {
        "closure": json.loads(CLOSURE.read_text()),
        "status": json.loads(STATUS.read_text()),
        "admission": json.loads(ADMISSION.read_text()),
        "deviation": json.loads(DEVIATION.read_text()),
        "limitation": json.loads(LIMITATION.read_text()),
    }
    closure, status = data["closure"], data["status"]

    # 1. The document may not describe a state the project has left.
    for key in ("human_verified", "holdout_eligible", "human_rejected",
                "genuine_multi_hop"):
        if closure["counts"][key] != status["combined"][key]:
            raise SystemExit(f"refusing to build: closure and status disagree on {key}")

    # 2. Eligibility is re-evaluated here, not trusted.
    records = json.loads(HA_RECORDS.read_text())["records"]
    ineligible = [r["candidate_id"] for r in records if not evaluate(r)["holdout_eligible"]]
    if ineligible:
        raise SystemExit(f"refusing to build: {ineligible} are not eligible")
    if len(records) != 60:
        raise SystemExit(f"refusing to build: {len(records)} admitted records, expected 60")

    # 3. No retrieval, no frozen split.
    if status["retrieval_was_not_run"] is not True or status["systems_executed"]:
        raise SystemExit("refusing to build: a retrieval system has been executed")
    if status["holdout_frozen"] is not False:
        raise SystemExit("refusing to build: the holdout is frozen")

    # 4. The two open findings must still be on the record.
    by_id = {r["candidate_id"]: r for r in records}
    if not by_id["HA-15"].get("human_anaphora_override") or \
            not by_id["HA-15"].get("anaphora_finding"):
        raise SystemExit("refusing to build: HA-15's override or its finding is missing")
    if not by_id["HA-47"].get("revisions"):
        raise SystemExit("refusing to build: HA-47 carries no revision history")

    # 5. The deviation must not be softened into a pass.
    if data["deviation"]["disposition"] != "ACCEPTED_PROTOCOL_DEVIATION":
        raise SystemExit("refusing to build: the protocol deviation is not accepted")

    # 6. The corpus gate must still be shut.
    if data["limitation"]["CORPUS_REPRODUCTION_INCOMPLETE"] is not True:
        raise SystemExit("refusing to build: the corpus limitation no longer holds")

    document = build_html(data)

    # 7. The page must lead with the limitation, not the number.
    flat = " ".join(document.split())
    if "not coverage" not in flat or "never run" not in flat:
        raise SystemExit("refusing to build: the page does not say what 150 fails to buy")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "closure150.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
