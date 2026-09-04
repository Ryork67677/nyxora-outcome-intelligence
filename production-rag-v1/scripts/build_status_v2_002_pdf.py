#!/usr/bin/env python3
"""Render the NATQ-002 identity decision and Stage-3 status as one shareable PDF.

Three things happened and they have different evidential standing: the rename
is complete and byte-verified, Stage 3 is 8 of 150 and honest about the pace,
and EXP-029A cannot execute because its measurement artifact does not exist.
A page that flattened those into one confidence level would mislead the
coordinator, so the sections keep them apart.

Every figure is read from STATUS-V2-002.json at build time, itself assembled
from the artifacts rather than typed. Eight gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-002.json"
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
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.3pt;
  page-break-inside: avoid; }
tr { page-break-inside: avoid; }
th { text-align: left; font-weight: 600; padding: 5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.mono { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7.6pt; }
.dim { color: #6f747b; }
.hot { color: #8a1c1c; font-weight: 700; }
.ok { color: #14532d; font-weight: 700; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt;
  margin: 9pt 0 11pt; page-break-inside: avoid; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout p:last-child { margin-bottom: 0; }
.grid { display: flex; gap: 8pt; margin: 9pt 0 11pt; }
.card { flex: 1; border: 0.8pt solid #d6dae0; border-radius: 3pt; padding: 7pt 9pt; }
.card .big { font-size: 16pt; font-weight: 700; letter-spacing: -0.5pt; }
.card .cap { font-size: 7.6pt; color: #6f747b; text-transform: uppercase;
  letter-spacing: 0.3pt; margin-top: 2pt; }
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


def rows(items, classes=()) -> str:
    return "".join("<tr>" + "".join(
        f"<td class='{classes[i] if i < len(classes) else ''}'>{c}</td>"
        for i, c in enumerate(r)) + "</tr>" for r in items)


def build_html(d: dict) -> str:
    idy, ren, s3, dd, ex, ln = (d["identity"], d["rename"], d["stage3"],
                                d["dedup"], d["exp029a"], d["lineage"])
    n1, n2 = idy["natq001"], idy["natq002"]

    case_rows = rows([
        (esc(c["case"]), ticks(c["q"][:62]),
         f"<span class='{'ok' if c['status'] == 'SUPPORTED' else 'hot'}'>{esc(c['status'])}</span>",
         esc(c["shape"]), f"<span class='num'>{c['spans']}</span>")
        for c in s3["cases"]])

    keep_rows = rows([(f"<span class='mono'>{esc(k)}</span>",
                       f"<span class='mono'>{esc(v[:16])}…</span>", "<span class='ok'>identical</span>")
                      for k, v in ren["unchanged"].items()])
    chg_rows = rows([(f"<span class='mono'>{esc(k)}</span>",
                      f"<span class='mono dim'>{esc(v['old'][:16])}…</span>",
                      f"<span class='mono'>{esc(v['new'][:16])}…</span>")
                     for k, v in ren["changed"].items()])

    miss = dd["missed"]
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>NATQ-002 status</title><style>{CSS}</style></head><body>
<h1>NATQ-002 &mdash; benchmark identity and Stage-3 status</h1>
<p class="subtitle">Rename complete and byte-verified &middot; Stage 3 at
{s3['done']} of {s3['raw']} &middot; EXP-029A cannot execute &middot;
branch head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout">
<p><strong>Three findings, three different confidence levels.</strong> The rename is
<strong>done and proven</strong> &mdash; every content file is byte-identical before and after.
Stage 3 is <strong>in progress</strong> at {s3['done']}/{s3['raw']} and the pace is the
binding constraint. EXP-029A <strong>cannot execute</strong>: its measurement artifact does
not exist, so no result is available from anyone. Nothing in this document is a
measurement of NATQ-002 &mdash; it has not been scored by any system.</p>
</div>

<div class="grid">
<div class="card"><div class="big">{s3['done']}/{s3['raw']}</div>
  <div class="cap">Stage-3 adjudicated</div></div>
<div class="card"><div class="big">{s3['supported']}</div>
  <div class="cap">supported</div></div>
<div class="card"><div class="big">{s3['rejected']}</div>
  <div class="cap">rejected on premise</div></div>
<div class="card"><div class="big">0</div>
  <div class="cap">systems run vs NATQ-002</div></div>
</div>

<h2>1 &mdash; Benchmark identity</h2>
<p>The identifier <code>NATQ-001</code> already belongs to the frozen benchmark. Two distinct
objects cannot share it, so the benchmark under construction here is now
<strong>NATQ-002</strong>. They are <strong>not merged</strong>.</p>
<table><thead><tr><th>&nbsp;</th><th>NATQ-001 (frozen, upstream)</th>
<th>NATQ-002 (under construction, here)</th></tr></thead><tbody>
<tr><td>Cases</td><td>{n1['total']} accepted</td>
    <td>{n2['authored']} authored &rarr; target {n2['target']}</td></tr>
<tr><td>Validation</td><td>{n1['validation']} &mdash; <span class="hot">{esc(n1['validation_status'])}</span></td>
    <td class="dim">not yet split</td></tr>
<tr><td>Holdout</td><td>{n1['holdout']} &mdash; <span class="ok">{esc(n1['holdout_status'])}</span></td>
    <td class="dim">not yet split</td></tr>
<tr><td>Case-ID shape</td><td><code>{esc(n1['id_shape'])}</code></td>
    <td><code>{esc(n2['id_shape'])}</code></td></tr>
<tr><td>Scored by any system</td><td>yes &mdash; validation slice</td>
    <td><span class="ok">no</span></td></tr>
</tbody></table>
<p><strong>No case-ID collision.</strong> The namespaces are disjoint, so no ID was renamed and
no migration map was required. The qualified citation form
<code>{esc(idy['citation_form'])}</code> is recorded for cross-benchmark tables; the stored
<code>case</code> field is deliberately unchanged, because rewriting adjudicated packets to fix
a citation convention would be a content revision.</p>

<h2>2 &mdash; The rename is provenance-only, and that is verifiable</h2>
<p>Change class <code>{esc(ren['class'])}</code>. Benchmark content revision:
<strong>{esc(ren['content_revision'])}</strong>. Question text altered:
<strong>{esc(ren['question_text_altered'])}</strong>. Adjudicated evidence altered:
<strong>{esc(ren['evidence_altered'])}</strong>.</p>
<h3>Content files &mdash; byte-identical before and after</h3>
<table><thead><tr><th>File</th><th>SHA256</th><th>State</th></tr></thead>
<tbody>{keep_rows}</tbody></table>
<h3>Identity files &mdash; the only two that changed</h3>
<table><thead><tr><th>File</th><th>Superseded</th><th>Current</th></tr></thead>
<tbody>{chg_rows}</tbody></table>
<div class="callout">
<p><strong>Historical records were left alone.</strong> {ticks(', '.join(ren['historical_left_alone']))}
still carry their NATQ-001 wording. They are dated, circulated documents describing this
benchmark under its former name; rewriting them would falsify what was reported at the time.
The rename provenance record is the pointer that disambiguates them.</p>
</div>

<h2>3 &mdash; Stage 3: {s3['done']} of {s3['raw']} adjudicated</h2>
<table><thead><tr><th>Case</th><th>Question</th><th>Status</th><th>Evidence shape</th>
<th class="num">Spans</th></tr></thead><tbody>{case_rows}</tbody></table>
<p><strong>A02 forced a validator change.</strong> No single document defines both
<code>required</code> (OpenAI Agents SDK) and <code>any</code> (Anthropic Messages) &mdash; they are
different vendors' names for forcing a tool call. The validator assumed one
<code>version_id</code> per packet, so spans now carry their own and a packet whose evidence
crosses providers must declare <code>cross-provider</code> and list them, rather than claim one
provider while citing another. Batch 01 re-validates unchanged.</p>
<p><strong>Two rejections, both on undocumented premises.</strong> A08 asks about a
&ldquo;schema root must be an object&rdquo; error; the corpus enumerates every schema constraint
and states no root-type rule. The phrase <code>must be an object</code> does occur &mdash; but only
about input <em>messages</em>, a different subject, so anchoring there would have been a false
positive that taught the benchmark to reward a wrong retrieval.</p>
<div class="callout warn">
<p><strong>Two risks the coordinator should price in now.</strong></p>
<p><strong>Pace.</strong> {s3['remaining']} cases remain. The token-coverage locator ranks poorly on
conversational questions, so most cases need literal probes and direct document reads &mdash;
roughly two to four tool calls each. This is several sessions of work, not one.</p>
<p><strong>Yield.</strong> {s3['rejected']} of {s3['done']} adjudicated cases were rejected because the
corpus never states their premise. If that rate holds, {n2['authored']} authored questions
will not yield {n2['target']} accepted cases, and topping up means another cold-context
authoring round. A rate on the full slice A will follow.</p>
</div>

<h2>4 &mdash; Duplicates must be detected by evidence, not wording</h2>
<p>A lexical screen over all {n2['authored']} questions at Jaccard
&ge; {dd['threshold']} found {dd['lexical_pairs']} pairs &mdash; and
<strong>missed the one that matters</strong>.</p>
<table><thead><tr><th>Case</th><th>Question</th><th>Gold span</th></tr></thead><tbody>
<tr><td>{esc(miss['pair'][0])}</td><td>{ticks(miss['A09'])}</td>
    <td class="mono">{esc(miss['gold_span_A09'])}</td></tr>
<tr><td>{esc(miss['pair'][1])}</td><td>{ticks(miss['A10'])}</td>
    <td class="mono">{esc(miss['gold_span_A10'])}</td></tr>
</tbody></table>
<p>The two share almost no vocabulary yet resolve to a
<strong>{esc(miss['relationship']).lower()}</strong>. {esc(miss['why_it_matters'])}</p>
<div class="callout">
<p><strong>Rule adopted.</strong> {esc(dd['rule']['detect'])}. Each collision gets an explicit
ruling before the accepted {n2['target']} are frozen. Critically:
<strong>{esc(dd['rule']['do_not'])}</strong>. Evidence-collision detection cannot run before
adjudication, because the gold span being compared does not exist until a case is
adjudicated &mdash; so dedup is a gate <em>between</em> adjudication and selection, not a
pre-screen. Both A09 and A10 are individually valid, recorded PASS, and flagged; nothing
is deleted.</p>
</div>

<h2>5 &mdash; EXP-029A cannot execute</h2>
<div class="callout warn">
<p><strong>Status <code>{esc(ex['status'])}</code>. Scores emitted: none, and none estimated.</strong>
The blocker is not a missing file this session failed to find &mdash; the operator confirmed
<code>EXP-029A-raw-outputs.jsonl</code> exists nowhere, so the generation half has never been
run by anyone.</p>
</div>
<p>This container cannot run it either: <code>cuda_available</code>
{esc(ex['env']['cuda_available'])}, <code>torch_installed</code> {esc(ex['env']['torch_installed'])},
<code>transformers_installed</code> {esc(ex['env']['transformers_installed'])},
huggingface.co unreachable (<code>{esc(ex['env']['huggingface_failure_mode'])}</code>). The same
two blockers stopped EXP-025A.</p>
<h3>The analysis half is ready and unblocked</h3>
<ul>{''.join(f'<li>{ticks(r)}</li>' for r in ex['ready'])}</ul>
<p><strong>Unblock condition.</strong> {ticks(ex['unblock'])}</p>

<h2>6 &mdash; Relayed lineage: indexed, not verified</h2>
<p>The upstream artifacts pasted into chat are recorded as a receipt with
<code>verified_here={esc(ln['verified_here'])}</code> and
<code>byte_verified={esc(ln['byte_verified'])}</code>. Their bytes were <strong>not</strong>
reconstructed into this repository &mdash; doing so would create a second authority for
artifacts this session never saw computed.</p>
<p><strong>What is verified here:</strong></p>
<ul>{''.join(f'<li>{ticks(c)}</li>' for c in ln['corroborated'])}</ul>
<p><strong>Closed-state chain as relayed</strong> (directions unambiguous; counts transcribed,
not verified): {esc(' &rarr; '.join(x.split(' (')[0] for x in ln['chain']))}.</p>
<div class="callout warn">
<p><strong>If EXP-029A analysis is assigned here, those artifacts must be pushed to a branch,
not pasted.</strong> The analysis compares against locked span sets and hash-identified
populations; working from retyped numbers would fail the provenance bar this program has
held everywhere else.</p>
</div>

<h2>7 &mdash; Constraints honoured</h2>
<table><thead><tr><th>Constraint</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='ok'>{esc(v)}</span>")
       for k, v in d['constraints'].items()])}
</tbody></table>
<p>Still gated, in order: finish authoring and adjudication; run the dedup gate; freeze the
accepted {n2['target']}; hash after identity normalisation; <em>then</em> return to the
coordinator for the split and preregistration. The split must not be chosen by looking at
system results, and no retrieval or reranking architecture has been run against NATQ-002.</p>

<div class="foot">Generated from STATUS-V2-002.json, itself assembled from the artifacts at
<code>{esc(d['head'])}</code>. Corpus <code>{esc(d['corpus']['snapshot'])}</code> &middot;
{d['corpus']['docs']} documents &middot; {d['corpus']['chunks']:,} chunks, re-verified this
session. Eight build gates refuse this page if a constraint is violated.</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-002.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())

    # 1. Nothing may have been scored, split, or opened.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")

    # 2. The rename must still be provenance-only.
    r = d["rename"]
    if r["content_revision"] or r["question_text_altered"] or r["evidence_altered"]:
        raise SystemExit("refusing to build: the rename claims to be content-preserving "
                         "but a content field is marked altered")
    if len(r["unchanged"]) < 8:
        raise SystemExit("refusing to build: fewer than 8 byte-identical content files")

    # 3. EXP-029A must emit no scores.
    if d["exp029a"]["scores_emitted"] is not None:
        raise SystemExit("refusing to build: EXP-029A emits scores; none can exist")
    if d["exp029a"]["status"] != "CANNOT_EXECUTE":
        raise SystemExit("refusing to build: EXP-029A is not CANNOT_EXECUTE")

    # 4. Relayed values must still be labelled relayed.
    if d["lineage"]["verified_here"] or d["lineage"]["byte_verified"]:
        raise SystemExit("refusing to build: relayed lineage is marked verified")

    # 5. Stage-3 counts must reconcile.
    s = d["stage3"]
    if s["done"] + s["remaining"] != s["raw"]:
        raise SystemExit("refusing to build: the Stage-3 counts do not reconcile")
    if s["supported"] + s["rejected"] != s["done"]:
        raise SystemExit("refusing to build: the adjudication counts do not reconcile")

    # 6. The dedup finding must keep its ordering rule, which is the whole point.
    if "after all 150 are adjudicated" not in d["dedup"]["rule"]["detect"]:
        raise SystemExit("refusing to build: the dedup rule no longer runs after adjudication")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 7. The page must keep the three confidence levels apart, not average them.
    for phrase in ("done and proven", "in progress", "cannot execute"):
        if phrase not in flat:
            raise SystemExit(f"refusing to build: the page flattens {phrase!r}")
    # 8. The two benchmarks must never be described as merged.
    if "not merged" not in flat:
        raise SystemExit("refusing to build: the page does not state the benchmarks are separate")

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
