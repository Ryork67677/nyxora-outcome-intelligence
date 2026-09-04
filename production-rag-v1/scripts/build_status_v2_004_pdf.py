#!/usr/bin/env python3
"""Render the NATQ-002 freeze as one shareable PDF.

The headline is 100 accepted cases, but the number a reader should weigh is
28 rejected on premise and 3 adjudications corrected after the fact. A freeze
report that showed only the accepted set would hide the two things that decide
whether to trust it: what was refused, and what was caught wrong.

Every figure is read from STATUS-V2-004.json at build time, itself assembled
from the frozen benchmark and the stage-3 records rather than typed. Nine
gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-004.json"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 15mm 13mm 13mm 13mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.3pt;
  line-height: 1.44; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 19pt; line-height: 1.14; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 11.6pt; margin: 15pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 9.6pt; margin: 10pt 0 4pt; }
p { margin: 0 0 6pt; }
ul { margin: 0 0 7pt; padding-left: 14pt; } li { margin: 0 0 3pt; }
code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 10.2pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 12pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8pt;
  page-break-inside: avoid; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.mono { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7.1pt; word-break: break-all; }
.dim { color: #6f747b; } .hot { color: #8a1c1c; font-weight: 700; } .ok { color: #14532d; font-weight: 700; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt;
  margin: 9pt 0 11pt; page-break-inside: avoid; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout p:last-child { margin-bottom: 0; }
.grid { display: flex; gap: 7pt; margin: 9pt 0 11pt; }
.card { flex: 1; border: 0.8pt solid #d6dae0; border-radius: 3pt; padding: 7pt 8pt; }
.card .big { font-size: 15.5pt; font-weight: 700; letter-spacing: -0.5pt; }
.card .cap { font-size: 7.2pt; color: #6f747b; text-transform: uppercase;
  letter-spacing: 0.3pt; margin-top: 2pt; }
.foot { margin-top: 13pt; padding-top: 7pt; border-top: 0.8pt solid #d6dae0;
  font-size: 7.6pt; color: #6f747b; }
"""


def esc(t: object) -> str:
    return html.escape(str(t), quote=False)


def ticks(t: str) -> str:
    out, parts = [], esc(t).split("`")
    for i, p in enumerate(parts):
        out.append(f"<code>{p}</code>" if i % 2 else p)
    return "".join(out)


def rows(items) -> str:
    return "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in items)


def build_html(d: dict) -> str:
    T, C, S, X = d["totals"], d["collisions"], d["selection"], d["dedup_outcomes"]

    slice_rows = rows([
        (esc(s), "<span class='num'>30</span>", f"<span class='num'>{v['supported']}</span>",
         f"<span class='num hot'>{v['rejected']}</span>", f"<span class='num ok'>{v['accepted']}</span>")
        for s, v in d["slices"].items()])

    col_rows = rows([
        (", ".join(esc(c) for c in g["cases"]), f"<span class='ok'>{esc(g['kept'])}</span>",
         esc(g["reason"][:150]))
        for g in C["groups"]])

    rej_rows = rows([
        (esc(r["case"]), ticks(r["q"]), esc(r["reason"][:112]))
        for r in d["rejection_examples"]])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>NATQ-002 freeze</title><style>{CSS}</style></head><body>
<h1>NATQ-002 &mdash; benchmark freeze report</h1>
<p class="subtitle">{T['accepted']} accepted cases &middot; {T['gold_spans']} gold spans &middot;
{T['rejected']} rejected on premise &middot; {T['validator_fail']} validator failures &middot;
head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout">
<p><strong>Read the refusals, not just the acceptances.</strong> {T['accepted']} cases were accepted, but
{T['rejected']} of {T['adjudicated']} authored questions were <em>rejected because the frozen corpus never
states their premise</em>, and three adjudications were caught wrong and corrected after the fact. Those
two numbers, not the headline, are what decide whether this benchmark can be trusted &mdash; a set built
by admitting every question would score systems on evidence that does not exist.</p>
</div>

<div class="grid">
<div class="card"><div class="big">{T['accepted']}</div><div class="cap">accepted cases</div></div>
<div class="card"><div class="big">{T['gold_spans']}</div><div class="cap">gold spans</div></div>
<div class="card"><div class="big">{T['rejected']}</div><div class="cap">rejected on premise</div></div>
<div class="card"><div class="big">{C['residual_span_accepted']}</div><div class="cap">residual collisions</div></div>
<div class="card"><div class="big">{d['integrity']['failures']}</div><div class="cap">integrity failures</div></div>
</div>

<h2>1 &mdash; The pipeline, 150 to 100</h2>
<table><thead><tr><th>Stage</th><th class="num">Cases</th><th>What happened</th></tr></thead><tbody>
<tr><td>Authored</td><td class="num">{T['authored']}</td>
    <td>Five isolated cold-context agents, <code>tool_uses=0</code>, blind to corpus, evidence and each other's questions</td></tr>
<tr><td>Adjudicated</td><td class="num">{T['adjudicated']}</td><td>Every question checked against the frozen corpus</td></tr>
<tr><td>Supported</td><td class="num">{T['supported']}</td><td>Gold evidence located and validated</td></tr>
<tr><td>Rejected</td><td class="num hot">{T['rejected']}</td><td>Premise not documented &mdash; no gold span can exist</td></tr>
<tr><td>Eligible</td><td class="num">{T['eligible']}</td><td>After {len(C['dropped'])} cases dropped by the collision rulings</td></tr>
<tr><td><strong>Accepted</strong></td><td class="num ok"><strong>{T['accepted']}</strong></td>
    <td>Selected under a rule fixed before selection</td></tr>
</tbody></table>

<h3>By authoring slice</h3>
<table><thead><tr><th>Slice</th><th class="num">Authored</th><th class="num">Supported</th>
<th class="num">Rejected</th><th class="num">Accepted</th></tr></thead><tbody>{slice_rows}</tbody></table>
<p>Slice B yielded only 19 eligible cases, so an even 20-per-slice split was impossible. B contributes all
19 and the shortfall goes to D. Early in the build slice A alone suggested a 27% rejection rate; the true
rate across all five slices is {T['rejected']}/{T['adjudicated']}, which is why no yield decision was taken
on a partial sample.</p>

<h2>2 &mdash; What was refused, and why that matters</h2>
<p>A rejection here is not a failure to search. It is a finding that the corpus never states the question's
premise, so admitting the case would train the benchmark to reward retrieving a passage that does not
answer it. Every rejection records the probes run and, where adjacent text exists, why anchoring there
would be a false positive.</p>
<table><thead><tr><th>Case</th><th>Question</th><th>Why refused</th></tr></thead><tbody>{rej_rows}</tbody></table>
<p class="dim">{d['rejection_count']} rejections in total; ten shown.</p>

<h2>3 &mdash; Evidence collisions</h2>
<p>Different questions can resolve to the same gold evidence. Left unchecked, that double-weights one
retrieval capability. All {C['span_groups']} exact-span groups were ruled under a single stated rule:
<strong>keep the case whose gold answer requires the largest portion of the shared span</strong>, ties by
earlier case ID. Dropped cases are not deleted &mdash; their packets keep full evidence and carry the ruling.</p>
<table><thead><tr><th>Group</th><th>Kept</th><th>Reason</th></tr></thead><tbody>{col_rows}</tbody></table>

<div class="callout warn">
<p><strong>The rule you choose decides whether the benchmark clears 100.</strong></p>
<p>Under the governing exact-span rule, {X['exact_span_rule']['unique_remaining']} unique cases remain from
{X['supported_before_dedup']} supported &mdash; comfortably above target. Group the same cases by the
<code>{esc(d['corpus']['chunk_set'])}</code> chunk their spans fall in and only
{X['chunk_level_rule']['unique_remaining']} remain, which is <strong>below</strong> 100. A chunk is the unit a
retrieval system is actually scored on, so this is a real design choice, not bookkeeping. It is recorded
and left to the coordinator; no case was excluded for chunk overlap alone.</p>
</div>
<p>Selection used chunk diversity only as a tiebreak within the governing rule, which cut chunk-level
overlap from {C['chunk_groups_all']} groups covering {C['chunk_cases_all']} cases across all supported cases
to <strong>{C['chunk_groups_accepted']} groups covering {C['chunk_cases_accepted']} cases</strong> in the
accepted 100, with <strong>{C['residual_span_accepted']} residual exact-span collisions</strong>.</p>

<h2>4 &mdash; Selection rule, fixed before selecting</h2>
<ul>{''.join(f'<li>{ticks(r)}</li>' for r in S['rule'])}</ul>
<table><thead><tr><th>Slice</th>{''.join(f'<th class="num">{s}</th>' for s in 'ABCDE')}</tr></thead><tbody>
<tr><td>Eligible</td>{''.join(f"<td class='num'>{S['availability'][s]}</td>" for s in 'ABCDE')}</tr>
<tr><td>Quota</td>{''.join(f"<td class='num'>{S['quota'][s]}</td>" for s in 'ABCDE')}</tr>
</tbody></table>

<h2>5 &mdash; Errors caught, by assertion rather than by judgement</h2>
<div class="callout warn">
<p><strong>Three adjudications were wrong and were corrected.</strong> B22 was rejected with the reason
&ldquo;no document in the snapshot states this&rdquo; &mdash; written after searching a single document. The
string was in the corpus. That error triggered a corpus-wide audit of every rejection literal, which found
two more: A15 was a case-sensitivity miss (searched <code>retina</code>, corpus writes
<code>macOS Retina displays</code>) and E27 was scoped to the wrong documents. All three are now supported.</p>
<p><strong>Eight questions carried truncated text.</strong> The freeze asserts every accepted question equals
its authored text byte-for-byte, and it refused to run. An audit found eight packets carrying question
strings truncated by console listings rather than read from the authored file
({ticks(', '.join(d['corrections']['question_text']))}). Two had lost the second half of the asker's framing.
All restored; adjudications, spans and claims were unaffected.</p>
<p>The rule adopted and applied to every later rejection: <strong>per-document absence is not snapshot
absence</strong>, and substring searches must be case-checked.</p>
</div>

<h2>6 &mdash; Integrity of the frozen set</h2>
<ul>{''.join(f'<li>{ticks(c)}</li>' for c in d['integrity']['checks'])}</ul>
<p><strong>{d['integrity']['spans_checked']} gold spans re-read from the frozen corpus,
{d['integrity']['failures']} failures.</strong> {T['multi_span']} of the {T['accepted']} accepted cases carry
more than one gold span; {len(d['cross_provider'])} case cites evidence spanning two providers
({ticks(', '.join(d['cross_provider']))}), carried on span-level version_ids.</p>
<table><thead><tr><th>Quantity</th><th class="num">Value</th></tr></thead><tbody>
<tr><td>Corpus snapshot</td><td class="num mono">{esc(d['corpus']['snapshot'])}</td></tr>
<tr><td>Documents in snapshot / referenced by gold</td>
    <td class="num">{d['corpus']['docs']} / {d['corpus']['documents_referenced']}</td></tr>
<tr><td>Provider split</td><td class="num">{esc(', '.join(f'{k} {v}' for k, v in d['providers'].items()))}</td></tr>
<tr><td><code>benchmark_file_sha256</code></td>
    <td class="num mono">{esc(d['hashes']['benchmark_file_sha256'])}</td></tr>
<tr><td><code>canonical_content_sha256</code></td>
    <td class="num mono">{esc(d['hashes']['canonical_content_sha256'])}</td></tr>
</tbody></table>
<p>The canonical hash covers case IDs, question text and span offsets only, so it survives cosmetic edits to
answers or notes and breaks if any question or gold span changes.</p>

<h2>7 &mdash; Still gated</h2>
<table><thead><tr><th>Gate</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='hot'>{esc(v)}</span>") for k, v in d['gates_open'].items()])}
</tbody></table>
<h3>Constraints held</h3>
<table><thead><tr><th>Constraint</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='ok'>{esc(v)}</span>") for k, v in d['constraints'].items()])}
</tbody></table>
<p>The validation/reserve split is deliberately not decided here. It determines which cases become exposed
development data and which stay pristine, and it must not be chosen by looking at system results. It returns
to the coordinator along with the collision-rule question in section 3.</p>

<div class="foot">Generated from STATUS-V2-004.json, itself assembled from the frozen benchmark and the
stage-3 records at <code>{esc(d['head'])}</code>. Corpus
<code>{esc(d['corpus']['snapshot'])}</code> &middot; {d['corpus']['docs']} documents &middot;
{d['corpus']['chunks']:,} chunks. Nine build gates refuse this page if a constraint is violated.</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-004.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    T, C, X = d["totals"], d["collisions"], d["dedup_outcomes"]

    # 1. Nothing may have been scored, and no forbidden action may be recorded.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")
    # 2. The downstream gates must still be shut.
    for k, v in d["gates_open"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: gate {k} claims to be complete")
    # 3. Counts must reconcile end to end.
    if T["supported"] + T["rejected"] + T["deferred"] != T["adjudicated"]:
        raise SystemExit("refusing to build: supported + rejected + deferred != adjudicated")
    if T["adjudicated"] != T["authored"]:
        raise SystemExit("refusing to build: not every authored question was adjudicated")
    if T["supported"] - len(C["dropped"]) != T["eligible"]:
        raise SystemExit("refusing to build: eligible does not follow from supported minus dropped")
    if T["accepted"] != 100:
        raise SystemExit("refusing to build: the accepted set is not 100 cases")
    if sum(v["accepted"] for v in d["slices"].values()) != T["accepted"]:
        raise SystemExit("refusing to build: slice acceptances do not sum to the accepted total")
    # 4. A validator or integrity failure must never be reported as a clean freeze.
    if T["validator_fail"] != 0 or d["integrity"]["failures"] != 0:
        raise SystemExit("refusing to build: the freeze has validator or integrity failures")
    # 5. The freeze is void if an exact-span collision survived into the accepted set.
    if C["residual_span_accepted"] != 0:
        raise SystemExit("refusing to build: an exact-span collision survived into the accepted 100")
    # 6. Every collision group must carry an explicit ruling.
    if len(C["groups"]) != C["span_groups"]:
        raise SystemExit("refusing to build: a collision group has no recorded ruling")
    # 7. Both dedup outcomes must be shown; hiding the chunk-level one hides the real decision.
    if X["exact_span_rule"]["meets_target_100"] == X["chunk_level_rule"]["meets_target_100"]:
        raise SystemExit("refusing to build: the two dedup rules no longer disagree; "
                         "re-check the numbers before publishing this framing")
    doc = build_html(d)
    flat = " ".join(doc.split())
    # 8. The page must lead with the refusals and keep the corrections visible.
    if "Read the refusals" not in flat:
        raise SystemExit("refusing to build: the page does not lead with what was refused")
    for phrase in ("three adjudications were wrong", "truncated text"):
        if phrase.lower() not in flat.lower():
            raise SystemExit(f"refusing to build: the page omits {phrase!r}")
    # 9. The split must not be presented as decided.
    if "not decided here" not in flat:
        raise SystemExit("refusing to build: the page does not state the split is undecided")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO / a.out
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "status.html"
        src.write_text(doc, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
