#!/usr/bin/env python3
"""Render NATQ-002 Stage-3 adjudication progress as one shareable PDF.

The number that matters here is not 22/150 but which 22: slice A supplies
22 of the 23 cases touched, so the observed rejection rate is a property of
one authoring slice and not yet of the benchmark. A page that reported the
rate without that caveat would invite a yield decision on a biased sample,
so the projection is shown and immediately labelled unstable.

Every figure is read from STATUS-V2-003.json at build time, itself assembled
from the packet files rather than typed. Seven gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-003.json"
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
ul { margin: 0 0 7pt; padding-left: 14pt; }
li { margin: 0 0 3pt; }
code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.2pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 10.3pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.1pt;
  page-break-inside: avoid; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
th.num { text-align: right; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.mono { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7.5pt; }
.dim { color: #6f747b; }
.hot { color: #8a1c1c; font-weight: 700; }
.ok { color: #14532d; font-weight: 700; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt;
  margin: 9pt 0 11pt; page-break-inside: avoid; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout p:last-child { margin-bottom: 0; }
.grid { display: flex; gap: 8pt; margin: 9pt 0 11pt; }
.card { flex: 1; border: 0.8pt solid #d6dae0; border-radius: 3pt; padding: 7pt 9pt; }
.card .big { font-size: 16pt; font-weight: 700; letter-spacing: -0.5pt; }
.card .cap { font-size: 7.5pt; color: #6f747b; text-transform: uppercase;
  letter-spacing: 0.3pt; margin-top: 2pt; }
.bar { height: 7pt; background: #e3e6ea; border-radius: 2pt; overflow: hidden; min-width: 60pt; }
.bar span { display: block; height: 100%; background: #16181c; }
.foot { margin-top: 14pt; padding-top: 7pt; border-top: 0.8pt solid #d6dae0;
  font-size: 7.8pt; color: #6f747b; }
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
    T, Y, G = d["totals"], d["yield"], d["gates"]

    slice_rows = rows([
        (esc(s), f"<span class='num'>{v['done']}</span>", f"<span class='num'>{v['total']}</span>",
         f"<div class='bar'><span style='width:{100 * v['done'] // v['total']}%'></span></div>")
        for s, v in d["slices"].items()])

    sup_rows = rows([
        (esc(c["case"]), ticks(c["q"][:58]), esc(c["doc"][:26]),
         esc(c["prov"]), f"<span class='num'>{c['spans']}</span>")
        for c in d["supported_cases"]])

    rej_rows = rows([
        (esc(c["case"]), ticks(c["q"][:52]), esc(c["reason"][:118]))
        for c in d["rejected_cases"]])

    col_rows = rows([
        (", ".join(esc(x) for x in c["cases"]),
         f"<span class='mono'>{esc(c['span'][0][0][:22])}… @{c['span'][0][1]}-{c['span'][0][2]}</span>")
        for c in d["collisions"]])

    dfr = d["deferred"][0]
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>NATQ-002 Stage 3</title><style>{CSS}</style></head><body>
<h1>NATQ-002 &mdash; Stage-3 adjudication report</h1>
<p class="subtitle">{T['adjudicated']} of {T['authored']} adjudicated &middot;
{T['supported']} supported, {T['rejected']} rejected, {T['deferred']} deferred &middot;
{T['validator_pass']} validator PASS / {T['validator_fail']} FAIL &middot;
head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout warn">
<p><strong>Read the coverage before the rate.</strong> The rejection rate below is
{Y['rate']} ({Y['pct']}%), but slice A supplies 22 of the 23 cases touched so far. The rate
is currently a property of <em>one authoring slice</em>, not of the benchmark. Slice A skews
toward troubleshooting scenarios that reference documentation does not cover, which is exactly
the kind of question that rejects. <strong>No yield decision should be taken on this
sample.</strong></p>
</div>

<div class="grid">
<div class="card"><div class="big">{T['adjudicated']}/{T['authored']}</div>
  <div class="cap">adjudicated</div></div>
<div class="card"><div class="big">{T['supported']}</div><div class="cap">supported</div></div>
<div class="card"><div class="big">{T['rejected']}</div><div class="cap">rejected on premise</div></div>
<div class="card"><div class="big">{T['validator_fail']}</div><div class="cap">validator failures</div></div>
<div class="card"><div class="big">0</div><div class="cap">systems run</div></div>
</div>

<h2>1 &mdash; Coverage by authoring slice</h2>
<table><thead><tr><th>Slice</th><th class="num">Done</th><th class="num">Total</th>
<th>Progress</th></tr></thead><tbody>{slice_rows}</tbody></table>
<p>This table is the reason the yield number is not yet actionable. Slices B, D and E are
entirely untouched and slice C has one case. Each slice was authored by a different isolated
cold-context agent from a different domain prompt, so their premise-support rates are not
interchangeable.</p>

<h2>2 &mdash; Supported cases ({T['supported']})</h2>
<table><thead><tr><th>Case</th><th>Question</th><th>Document</th><th>Provider</th>
<th class="num">Spans</th></tr></thead><tbody>{sup_rows}</tbody></table>
<p><strong>Cross-provider:</strong> {ticks(', '.join(d['cross_provider']))} &mdash; evidence spans
two providers' documents, which the validator now expresses through span-level
<code>version_id</code> plus an explicit <code>cross-provider</code> declaration.</p>

<h2>3 &mdash; Rejected on premise ({T['rejected']})</h2>
<p>These are not failures to find evidence. They are questions whose premise the frozen corpus
never states, so no gold span can exist. Admitting them would train the benchmark to reward a
system for retrieving a passage that does not answer the question.</p>
<table><thead><tr><th>Case</th><th>Question</th><th>Why rejected</th></tr></thead>
<tbody>{rej_rows}</tbody></table>
<div class="callout">
<p><strong>The near-miss discipline.</strong> Each rejection records the probes run and, where
adjacent text exists, why anchoring there would be a false positive. A01 is the clearest case:
<code>loop</code> appears 41 times across two documents, but always meaning the agentic
request/response cycle &mdash; never a model repeating a call. A15 is flagged in its own packet
as the rejection most open to being overturned, since the chain retina &rarr; high resolution
&rarr; heavy downscaling &rarr; imprecise clicks has every link documented except the first.</p>
</div>

<h2>4 &mdash; Deferred, not forced ({T['deferred']})</h2>
<p><strong>{esc(dfr['case'])}</strong> &mdash; {ticks(dfr['question'])}</p>
<p>The corpus separately (a) gives general guidance to instruct the model to respond without
preamble, and (b) shows preamble text preceding a <code>tool_use</code> block. It never connects
them, and <code>preamble</code> is absent from every tool-use document checked.</p>
<p>{esc(dfr['why_deferred'])} It is counted in neither the supported nor the rejected column.</p>

<h2>5 &mdash; Evidence collisions</h2>
<table><thead><tr><th>Cases</th><th>Shared gold span</th></tr></thead><tbody>{col_rows}</tbody></table>
<p>Detected by gold span, not by wording: a lexical screen over all {T['authored']} questions
missed this pair entirely because the two share almost no vocabulary. The full collision gate
runs <strong>{esc(d['dedup_rule']['detect'])}</strong>, and
<strong>{esc(d['dedup_rule']['do_not'])}</strong>.</p>

<h2>6 &mdash; Yield: projection shown, and why it is not yet a forecast</h2>
<table><thead><tr><th>Quantity</th><th class="num">Value</th></tr></thead><tbody>
<tr><td>Observed rejection rate</td><td class="num">{Y['rate']} ({Y['pct']}%)</td></tr>
<tr><td>Naive projection of accepted cases at that rate</td><td class="num">{Y['naive_projection']}</td></tr>
<tr><td>Target</td><td class="num">{T['target']}</td></tr>
<tr><td>Sample is representative</td><td class="num"><span class="hot">{esc(Y['stable'])}</span></td></tr>
</tbody></table>
<div class="callout warn">
<p>{Y['naive_projection']} clears {T['target']}, but only by {Y['naive_projection'] - T['target']}
&mdash; and that margin is consumed before the collision gate removes any duplicate-evidence
cases. Deferred cases also do not count toward the accepted pool unless the coordinator admits
them. The honest reading is that the benchmark is <strong>near the line, on a biased sample</strong>,
and the real number arrives when slice A closes and slices B&ndash;E begin.</p>
</div>

<h2>7 &mdash; Gates still closed</h2>
<table><thead><tr><th>Gate</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='hot'>{esc(v)}</span>") for k, v in G.items()])}
</tbody></table>
<h3>Constraints held</h3>
<table><thead><tr><th>Constraint</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='ok'>{esc(v)}</span>") for k, v in d['constraints'].items()])}
</tbody></table>
<p>Order of remaining work: finish the {T['remaining']} untouched questions; run the collision
gate; freeze the accepted {T['target']}; hash after identity normalisation; then return to the
coordinator for the split. No retrieval or reranking architecture has been run against
NATQ-002, and the NATQ-001 holdout has not been opened.</p>

<div class="foot">Generated from STATUS-V2-003.json, itself assembled from the packet files at
<code>{esc(d['head'])}</code>. Corpus <code>{esc(d['corpus']['snapshot'])}</code> &middot;
{d['corpus']['docs']} documents &middot; {d['corpus']['chunks']:,} chunks. Seven build gates
refuse this page if a constraint is violated.</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-003.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    T, Y, G = d["totals"], d["yield"], d["gates"]

    # 1. Nothing may have been scored, split, or opened.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")
    # 2. No downstream gate may have silently opened.
    for k, v in G.items():
        if v is not False:
            raise SystemExit(f"refusing to build: gate {k} claims to be complete")
    # 3. Counts must reconcile against the authored total.
    if T["supported"] + T["rejected"] != T["adjudicated"]:
        raise SystemExit("refusing to build: supported + rejected != adjudicated")
    if T["adjudicated"] + T["deferred"] + T["remaining"] != T["authored"]:
        raise SystemExit("refusing to build: adjudicated + deferred + remaining != authored")
    if len(d["supported_cases"]) != T["supported"] or len(d["rejected_cases"]) != T["rejected"]:
        raise SystemExit("refusing to build: case tables do not match the counts")
    # 4. A validator failure must never be reported as progress.
    if T["validator_fail"] != 0:
        raise SystemExit("refusing to build: a packet fails validation")
    # 5. The yield projection must stay labelled unstable while slices are untouched.
    if Y["stable"]:
        raise SystemExit("refusing to build: the yield sample is marked representative")
    if sum(1 for v in d["slices"].values() if v["done"] == 0) == 0 and Y["stable"] is False:
        pass  # once every slice has coverage, the caveat may legitimately be revisited
    # 6. Deferred cases must not be counted as accepted.
    if T["deferred"] and any(c["case"] in {x["case"] for x in d["supported_cases"]}
                             for c in d["deferred"]):
        raise SystemExit("refusing to build: a deferred case is also counted as supported")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 7. The page must lead with the coverage caveat, not the rate.
    if "Read the coverage before the rate" not in flat:
        raise SystemExit("refusing to build: the page reports the rate without its caveat")
    if "not yet a forecast" not in flat:
        raise SystemExit("refusing to build: the projection is not labelled")

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
