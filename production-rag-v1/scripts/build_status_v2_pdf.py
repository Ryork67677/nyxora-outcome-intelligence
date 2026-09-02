#!/usr/bin/env python3
"""Render the V2 phase status as one shareable PDF.

Four things happened in this phase and they have different evidential
standing: SYSTEM-H is frozen and mostly verified, PERF-003 is recorded but
not reproduced, four upstream artifacts are missing entirely, and NATQ-001 is
three cases into a hundred-and-fifty-case verification. A status document that
flattened those into one confidence level would be worse than none, so the
page keeps them apart.

Every figure is read from STATUS-V2-001.json at build time, itself assembled
from the artifacts rather than typed. Six gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-001.json"
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
th.num { text-align: right; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.dim { color: #6f747b; }
.hot { color: #8a1c1c; font-weight: 700; }
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
.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8pt;
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
.bar.hot { background: #8a1c1c; }
.break { page-break-before: always; }
footer { margin-top: 14pt; padding-top: 8pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.6pt; color: #6f747b; }
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
    sh, pf, gp, nq = d["system_h"], d["perf003"], d["gap"], d["natq"]
    tri, st = nq["triage"], sh["status"]

    status_rows = rows([
        (k.replace("_", " "), "<strong>true</strong>" if v else "false")
        for k, v in st.items()], ("", "num"))
    tri_rows = rows([(k, f"{tri[k]}") for k in
                     ("STRONG", "PROBABLE", "REVIEW", "LIKELY_UNSUPPORTED")], ("", "num"))
    pkt_rows = rows([
        (f"<code>{esc(p['case'])}</code>", ticks(p["q"]),
         f"{esc(p['provider'])} &middot; {esc(p['doc'])}",
         f"{p['spans']}", f"{p['claims']}", "<strong>PASS</strong>")
        for p in nq["packets"]], ("", "", "dim", "num", "num", "num"))
    hash_rows = rows([(ticks(k), f"<code>{v[:32]}&hellip;</code>")
                      for k, v in d["artifact_hashes"].items()])
    gap_rows = rows([(f"<code>{esc(m)}</code>", "<span class='hot'>absent from every ref</span>",
                      "<code>verified_here = false</code>") for m in gp["missing"]])
    con_rows = rows([(k.replace("_", " "), f"<strong>{esc(v)}</strong>" if not isinstance(v, bool)
                      else ("<span class='hot'>true</span>" if v else "false"))
                     for k, v in d["constraints"].items()], ("", "num"))

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>V2 Phase Status</title><style>{CSS}</style></head><body>

<h1>V2 phase status</h1>
<p class="subtitle">SYSTEM-H freeze &middot; PERF-003 closure &middot; provenance gap
&middot; NATQ-001 stages 1&ndash;3 &middot; branch head <code>{esc(d['head'])}</code></p>
<div class="rule"></div>

<div class="callout">
  <div class="label">Four things, three different confidence levels</div>
  <p><strong>SYSTEM-H is frozen</strong> and {sh['verified_fields']} of its supplied
  values were checked against a preregistration written before the scores existed.
  <strong>PERF-003 is recorded, not reproduced.</strong> <strong>Four upstream
  artifacts are missing entirely.</strong> And <strong>NATQ-001 is
  {nq['stage3_done']} cases into {nq['raw']}</strong>. Those are deliberately not
  averaged into one number.</p>
</div>

<div class="grid4">
  <div class="stat win"><div class="big">FROZEN</div>
    <div class="cap">SYSTEM-H development architecture</div></div>
  <div class="stat"><div class="big">{sh['verified_fields']}</div>
    <div class="cap">fields verified against EXP-017 prereg</div></div>
  <div class="stat warn"><div class="big">{len(gp['missing'])}</div>
    <div class="cap">upstream artifacts absent from every ref</div></div>
  <div class="stat warn"><div class="big">{nq['stage3_done']}/{nq['raw']}</div>
    <div class="cap">NATQ evidence packets complete</div></div>
</div>

<h2>1 &mdash; SYSTEM-H-V2-DEV-CANDIDATE, frozen</h2>
<blockquote>config_hash             {esc(sh['config_hash'])}
score_determining_hash  {esc(sh['score_determining_hash'])}
file_sha256             {esc(sh['file_sha256'])}
file_sha256 superseded  {esc(sh['file_sha256_superseded'])}</blockquote>
<table><thead><tr><th>flag</th><th class="num">value</th></tr></thead>
<tbody>{status_rows}</tbody></table>
<p>Computed with <code>rag_v1.ids.config_hash</code>, verified in the same run to
reproduce <code>SYSTEM-A-GLOBAL</code>'s frozen identity exactly, so it is
comparable in kind to the existing systems. <strong>Two hashes because they
answer different questions:</strong> <code>config_hash</code> covers every field
including the PERF-003 D1 performance path and identifies the build;
<code>score_determining_hash</code> excludes that path alone, since it is
bitwise score-preserving, and answers whether two runs are comparable.</p>

<div class="callout win">
  <div class="label">The EXP-017 a_norm conflict &mdash; resolved, freeze kept</div>
  <p>EXP-017 preregistered projection-only <code>a_norm = 0.0</code>.
  <strong>EXP-019A formally superseded it</strong> with min-max over the query's P
  projection-only fused scores, degenerate 0.5, E-L10 members keeping their
  <code>a_norm</code> exactly.</p>
  <p><strong>Effect on the freeze: none.</strong> The value frozen was already the
  EXP-019A behaviour. Twelve content checks confirm it and both hashes recompute
  from the file, so <code>config_hash</code> is unchanged; only
  <code>file_sha256</code> moved, because the annotation lives outside the hashed
  configuration.</p>
</div>

<p><strong>Not verified here:</strong>
{", ".join(f"<code>{esc(x)}</code>" for x in sh['unverified_fields'])}. Recorded as
supplied.</p>

<h2>2 &mdash; PERF-003, recorded not reproduced</h2>
<p>Status <code>{esc(pf['status'])}</code>, <code>verified_here =
{str(pf['verified_here']).lower()}</code>. Preserved metrics as reported:
candidate R@100 {esc(pf['metrics']['candidate_recall_at_100'])}, strict R@10
{esc(pf['metrics']['strict_recall_at_10'])}, span {pf['metrics']['span_recall_at_10']},
MRR {pf['metrics']['mrr']}, doc recall {pf['metrics']['document_recall']}, with
{pf['equivalence']['bitwise_identical']}/{pf['equivalence']['raw_ce_logits_compared']}
CE logits bitwise identical and a {pf['timing']['speedup']}&times; CE speedup
&mdash; <strong>same-host only, not valid across hosts</strong>.</p>
<p class="dim">Recording a number is not reproducing it. PERF-003's own artifacts
are not reachable from this session, so every figure here is relayed.</p>

<div class="break"></div>
<h2>3 &mdash; Provenance gap</h2>
<p>As of reconciliation commit <code>{esc(gp['as_of'])}</code>, these are absent
from <strong>every</strong> fetched ref
({", ".join(f"<code>{esc(k.split('/')[-1])}</code>" for k in gp['refs'])}):</p>
<table><thead><tr><th>artifact</th><th>presence</th><th>flag</th></tr></thead>
<tbody>{gap_rows}</tbody></table>
<div class="callout warn">
  <div class="label">One conflation to avoid</div>
  <p><code>experiments/PERF-003/PERF-003-closure.json</code> on this branch is
  <strong>my closure record of relayed values</strong>, not Grok's
  <code>PERF-003-report.md</code>. They are different documents with different
  standing. None of these four may be reconstructed from conversation or marked
  verified until the originals are pushed.</p>
</div>

<h2>4 &mdash; NATQ-001</h2>
<p><strong>Stage 1 complete.</strong> {nq['raw']} questions authored by five
isolated cold-context agents, each given only a domain slice.
<strong>Verifiable, not asserted: every agent reported
<code>tool_uses = 0</code></strong> &mdash; none read a file, queried the
database, or reached the network. {nq['ambiguous']} were flagged ambiguous by
their own author.</p>
<p>This mattered because <strong>I could not author them</strong>: earlier in the
same session I loaded 400 corpus chunks for the PERF-002 microbenchmark and
tokenized 53 existing gold questions. Authoring them myself would have destroyed
the one property the benchmark exists to have.</p>

<p><strong>Stage 2 complete</strong> &mdash; triage by literal per-document token
coverage, run only after every question existed. No BM25, no dense, no CE, no
ranking that could sort questions by difficulty.</p>
<table><thead><tr><th>triage</th><th class="num">count</th></tr></thead>
<tbody>{tri_rows}</tbody></table>
<p class="dim">Best-document provider: anthropic {nq['provider'].get('anthropic')},
openai {nq['provider'].get('openai')} &mdash; recorded, not forced. Read the table
conservatively: coverage means a document holds the vocabulary, not that it
answers the question.</p>

<h3>Stage 3 &mdash; in progress, {nq['stage3_done']} of {nq['raw']}</h3>
<table><thead><tr><th>case</th><th>question</th><th>source</th>
<th class="num">spans</th><th class="num">claims</th><th class="num">verdict</th>
</tr></thead><tbody>{pkt_rows}</tbody></table>

<div class="callout">
  <div class="label">The validator earned its keep on its first run</div>
  <p><code>A09</code> was written with a span reading &ldquo;Whether to disable
  parallel tool use.&rdquo; and a critical string of
  <code>disable_parallel_tool_use</code> &mdash; the prose form, not the
  snake_case identifier. The check returned <code>FIX_REQUIRED</code>; the span
  was extended back to the parameter declaration and it now passes. That is
  exactly the defect that produces a case whose critical string cannot be found
  in its own evidence.</p>
  <p>Two of the three carry provenance the triage could not have supplied.
  <code>A04</code>'s author guessed OpenAI while the frozen corpus answers it for
  Anthropic, so provider is recorded from evidence rather than from the guess.
  <code>A09</code>'s block repeats at four offsets and the first canonical one is
  anchored, with the corpus distinction between &ldquo;at most one&rdquo; under
  <code>auto</code> and &ldquo;exactly one&rdquo; under <code>any</code>/
  <code>tool</code> preserved rather than flattened.</p>
</div>

<p><strong>{nq['stage3_remaining']} candidates remain.</strong> Each needs targeted
probing where the locator misses, reading, exact offsets, and claims scoped to
what the span actually supports. Stage 4 &mdash; the 40/60 cluster-safe split,
the hashes, the NATQ holdout lock &mdash; has not started.</p>

<h2>Artifact hashes</h2>
<table><thead><tr><th>artifact</th><th>sha256</th></tr></thead>
<tbody>{hash_rows}</tbody></table>

<h2>Constraints observed</h2>
<table><thead><tr><th>constraint</th><th class="num">value</th></tr></thead>
<tbody>{con_rows}</tbody></table>

<footer>STATUS-V2-001 &middot; every figure read from
<code>experiments/STATUS-V2-001.json</code> at build time, itself assembled from
the artifacts &middot; SYSTEM-H frozen; PERF-003 relayed; four upstream artifacts
missing; NATQ-001 Stage 3 in progress &middot; nothing scored, nothing split,
no holdout opened</footer>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-001.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())

    # 1. Nothing may have been scored, split, or opened.
    for k, v in d["constraints"].items():
        if isinstance(v, bool) and v:
            raise SystemExit(f"refusing to build: constraint {k} is true")
    # The V1 holdout log is a two-part fact and one number cannot carry it: this
    # branch forked before EVAL-HOLDOUT-001, so its copy is empty while the
    # authoritative log holds the single legitimate access. Report both.
    if d["constraints"].get("v1_holdout_new_accesses_this_phase") != 0:
        raise SystemExit("refusing to build: a new V1 holdout access was recorded this phase")
    if d["constraints"].get("v1_holdout_log_modified_here") is not False:
        raise SystemExit("refusing to build: the historical V1 holdout log was modified")
    if "v1_holdout_log_entries" in d["constraints"]:
        raise SystemExit("refusing to build: the ambiguous v1_holdout_log_entries field is back")

    # 2. SYSTEM-H must still be frozen, and only as a development architecture.
    st = d["system_h"]["status"]
    if not st["DEVELOPMENT_ARCHITECTURE_FROZEN"]:
        raise SystemExit("refusing to build: SYSTEM-H is not frozen")
    if st["RELEASE_FROZEN"] or st["VALIDATION_RUN"] or st["NEW_HOLDOUT_RUN"]:
        raise SystemExit("refusing to build: SYSTEM-H claims release/validation/holdout state")

    # 3. Relayed values must still be labelled relayed.
    if d["perf003"]["verified_here"] is not False:
        raise SystemExit("refusing to build: PERF-003 is marked verified without its artifacts")
    if not d["gap"]["missing"]:
        raise SystemExit("refusing to build: the provenance gap is empty but PERF-003 is relayed")

    # 4. The blind-authoring claim is the benchmark's whole value.
    au = d["natq"]["authoring"]
    if au["tool_uses_per_agent"] != 0 or au["author_saw_corpus"]:
        raise SystemExit("refusing to build: the authoring isolation claim no longer holds")

    # 5. Stage 3 must not be overstated.
    if d["natq"]["stage3_done"] + d["natq"]["stage3_remaining"] != d["natq"]["raw"]:
        raise SystemExit("refusing to build: the Stage-3 counts do not reconcile")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 6. The page must keep the confidence levels apart, not average them.
    if "recorded, not reproduced" not in flat or "in progress" not in flat:
        raise SystemExit("refusing to build: the page flattens the confidence levels")

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
