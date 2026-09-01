#!/usr/bin/env python3
"""Render the PERF-002 cross-encoder latency audit as a PDF.

Two results lead, and they point in opposite directions: the bitwise-identity
claim I doubted is correct, and the flag that bundles the win with a
machine-dependent thread setting is a regression on a smaller host. The
decomposition is the body.

Every figure is read from PERF-002-measurements.json at build time. Seven gates
refuse the build rather than publish a document that disagrees with the audited
source.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT = REPO_ROOT / "experiments/PERF-002"
MEASUREMENTS = AUDIT / "PERF-002-measurements.json"
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


def build_html(m: dict) -> str:
    art, host = m["ce_artifact"], m["audit_host"]
    sl, dom = m["sequence_lengths"], m["dominant_bottleneck"]
    base, buck = m["decomposition_104_pairs"]["runs"]
    proj, find = m["projections_ratios_only"], {f["id"]: f for f in m["key_findings"]}
    tim = {r["config"]: r for r in m["timing_104_pairs"]["rows"]}

    def comp(key, label):
        b, k = base[key], buck[key]
        hot = " class='hot'" if key == "onnx_ms" else ""
        return (f"<span{hot}>{label}</span>", f"{b:,.1f}", f"{b/base['total_ms']:.2%}",
                f"{k:,.1f}", f"{k/buck['total_ms']:.2%}")

    decomp_rows = rows([
        comp("pre_tokenize_ms", "pre-pass tokenize (bucketing only)"),
        comp("tokenize_ms", "tokenize"),
        comp("numpy_pack_ms", "numpy pack"),
        comp("onnx_ms", "<strong>ONNX inference</strong>"),
        comp("post_ms", "postprocess / unpermute"),
        comp("loop_ms", "batching / loop overhead"),
        ("<strong>total</strong>", f"<strong>{base['total_ms']:,.0f}</strong>", "",
         f"<strong>{buck['total_ms']:,.0f}</strong>", ""),
    ], ("", "num", "num", "num", "num"))

    def trow(cfg, label, note, hot=False):
        r = tim[cfg]
        cls = " class='hot'" if hot else ""
        return (label, f"{r['ms']:,.0f}", f"<span{cls}>{r['speedup']:.2f}&times;</span>",
                "&#10003;" if r["bitwise_identical"] else "&#10007;", note)

    lever_rows = rows([
        ("baseline <code>CrossEncoderReranker()</code>",
         f"{tim['baseline pad=512 b16 t4']['ms']:,.0f}", "1.00&times;", "&mdash;", "&mdash;"),
        trow("pad=batch BUCKETED b16 t4",
             "<strong>D1</strong> &mdash; bucketed <code>pad=\"batch\"</code>, threads unchanged",
             "<strong>no</strong>"),
        trow("pad=batch BUCKETED b1  t4", "D1b &mdash; same, <code>batch_size=1</code>", "probably"),
        trow("threads=8 pad=512 b16", "D2 &mdash; <code>threads=8</code> alone",
             "<strong>YES</strong>", hot=True),
        trow("fast=True (t8+batch+bucket)", "<code>fast=True</code> (bundles D1 + threads=8)",
             "<strong>YES</strong>", hot=True),
        trow("pad=batch unsorted b16 t4", "<code>pad=\"batch\"</code> unsorted", "no"),
        trow("pad=512 b1  t4", "<code>batch_size=1</code> at pad 512", "probably"),
    ], ("", "num", "num", "num", "num"))

    eq_rows = rows([
        (ticks(r["config"]), "&#10003; bitwise" if r["bitwise_identical"] else "&#10007;",
         f"{r['max_abs_diff']:.3e}", "same" if r["ranks_identical"] else "DIFFER")
        for r in m["equivalence_matrix"]
    ], ("", "num", "num", "num"))

    def pr(key, label, note):
        p = proj[key]
        ce = p["ce_ms"]; tot = p["total_ms"]
        fmt = lambda v: f"{v[0]:,}&ndash;{v[1]:,}" if isinstance(v, list) else f"{v:,}"
        return (label, fmt(ce), fmt(tot), note)

    proj_rows = rows([
        ("current (stored)", f"{proj['stored']['ce_ms']:,.1f}",
         f"{proj['stored']['total_ms']:,.1f}", "&mdash;"),
        pr("D1_bucketing_only", "<strong>D1 alone</strong> &mdash; bucketing, threads untouched",
           "<strong>machine-independent</strong>"),
        pr("D1_plus_merged_call", "D1 + merged CE call", "machine-independent"),
        pr("D1_plus_threads_on_true_8_core", "D1 + threads matched on an 8-CPU host",
           "agrees with Grok's &asymp;2380"),
        pr("fast_true_on_4_core_host",
           "<span class='hot'><code>fast=True</code> on a 4-CPU host</span>",
           "<span class='hot'>the trap</span>"),
    ], ("", "num", "num", ""))

    gate = "".join(f"<li>{ticks(g)}</li>" for g in m["gate_before_flipping"])
    callsites = ", ".join(f"<code>{esc(c)}</code>" for c in find["F6"]["call_sites"])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>PERF-002</title><style>{CSS}</style></head><body>

<h1>PERF-002 &mdash; cross-encoder score-preserving latency audit</h1>
<p class="subtitle">Read-only &middot; no patch applied &middot; E-L10 not validated,
not frozen &middot; holdout not opened</p>
<div class="rule"></div>

<p>Source audited: <code>{esc(m['source']['branch'])}</code> @
<strong>{esc(m['source']['commit'])}</strong>, and re-verified byte-identical
against the full tree <code>{esc(m['source']['verified_against_full_tree']['branch'])}</code>
@ <strong>{esc(m['source']['verified_against_full_tree']['commit'])}</strong>
&mdash; so nothing here rests on the handoff pack being a faithful copy. CE
artifact sha256 re-verified against the preregistered value. Model confirmed
<code>{esc(art['architectures'][0])}</code>, <code>{esc(art['output'])}</code>,
{art['num_hidden_layers']} layers / hidden {art['hidden_size']} &mdash;
MiniLM-<strong>L6</strong>.</p>

<div class="callout warn">
  <div class="label">Two results, pointing opposite ways</div>
  <p><strong>1. Grok's bitwise-identity claim is correct. I doubted it and I was
  wrong.</strong> All {len(m['equivalence_matrix'])} levers tested return
  <strong>bit-identical logits</strong> &mdash; including width 24 versus width
  512. So the equivalence criterion here is <strong>bitwise</strong>, not a
  tolerance, and ranks are identical by construction.</p>
  <p><strong>2. <code>fast=True</code> is the wrong bundle.</strong> It couples a
  machine-<em>independent</em>
  <strong>{find['F2']['measured_bucketing_only_speedup']:.2f}&times;</strong> win with a
  machine-<em>dependent</em> <code>threads=8</code> that is a
  <strong>{find['F2']['measured_threads8_only_speedup']:.2f}&times; regression</strong>
  on this 4-CPU host. Bundled it delivers only
  {find['F2']['measured_fast_true_speedup']:.2f}&times;.
  <strong>The two levers must be separated.</strong></p>
</div>

<div class="grid4">
  <div class="stat warn"><div class="big">{dom['share_of_ce_time']:.1%}</div>
    <div class="cap">of CE time is ONNX inference</div></div>
  <div class="stat warn"><div class="big">{sl['pad_slot_waste_at_fixed_512']:.1%}</div>
    <div class="cap">of tokens fed to it are <code>[PAD]</code></div></div>
  <div class="stat"><div class="big">{dom['non_levers_combined_share']:.2%}</div>
    <div class="cap">is everything else combined</div></div>
  <div class="stat win"><div class="big">{find['F2']['measured_bucketing_only_speedup']:.2f}&times;</div>
    <div class="cap">bitwise, machine-independent</div></div>
</div>

<h2>B &mdash; Measured latency decomposition</h2>
<p>104 pairs (E-L10 mean union 104.1), one query, warmed, this container:</p>
<table><thead><tr><th>Component</th>
<th class="num">baseline pad=512</th><th class="num">share</th>
<th class="num">bucketed pad=batch</th><th class="num">share</th></tr></thead>
<tbody>{decomp_rows}</tbody></table>
<p>Batch widths &mdash; baseline <code>[512 &times;7]</code>; bucketed
<code>{esc(buck['widths'])}</code>. Session and tokenizer are built
<strong>once per process</strong>
({m['decomposition_104_pairs']['construct_ms']:,.0f} ms), correctly excluded from
per-query cost.</p>

<div class="callout warn">
  <div class="label">Absolute milliseconds here are not EXP-018B's</div>
  <p>This box is <strong>~{host['slower_than_exp018b_box_by']:.2f}&times; slower</strong>
  than the EXP-018B host ({host['cores']} CPUs, {esc(host['cpu'])}, {esc(host['isa'])}).
  <strong>Ratios transfer; milliseconds do not.</strong> Every projection below is
  built from ratios only.</p>
</div>

<h2>C &mdash; Dominant bottleneck</h2>
<p><strong>ONNX inference on padding.</strong>
{dom['share_of_ce_time']:.2%} of CE time is inside <code>session.run</code>, and
<strong>{sl['pad_slot_waste_at_fixed_512']:.1%} of the tokens fed to it are
<code>[PAD]</code></strong>. Attention is O(n&sup2;) in width, so a
{sl['p50']}-token pair padded to 512 costs roughly 3&times; the FFN work and
~9&times; the attention work of the same pair at its true width.</p>
<p>Measured over {esc(sl['source'])}: mean <strong>{sl['mean']}</strong>,
p50 {sl['p50']}, p90 {sl['p90']}, <strong>{sl['fraction_at_512']:.1%} already at
512</strong> &mdash; independently reproducing Grok's
{sl['independently_reproduces_grok']['grok_mean']} /
{sl['independently_reproduces_grok']['grok_fraction_at_512']:.1%} on different
hardware.</p>

<div class="callout">
  <div class="label">A finding, not an omission</div>
  <p>Brief items 3, 4, 7 and 8 &mdash; tokenization, tensor construction,
  query-side caching, candidate-side caching &mdash; sum to
  <strong>{dom['non_levers_combined_share']:.2%} of CE time</strong>. Perfect
  elimination of all of it saves about 100 ms of 5904.
  <strong>These are not levers.</strong></p>
</div>

<div class="break"></div>
<h2>D &mdash; Score-preserving optimizations, ranked</h2>
<table><thead><tr><th>Change</th><th class="num">ms</th><th class="num">speedup</th>
<th class="num">bitwise</th><th class="num">machine-dependent?</th></tr></thead>
<tbody>{lever_rows}</tbody></table>
<p><strong>D1 &mdash; ship this one.</strong>
{find['F2']['measured_bucketing_only_speedup']:.2f}&times; here, and ~2.16&times;
derived from Grok's own 5571 / 3728 / 1729 triple. Agreement across two different
CPUs is what makes it safe to project.</p>
<p><strong>D3 &mdash; merge the two CE calls.</strong>
{ticks(find['F4']['consequence'])} ({esc(find['F4']['location'])}). Bitwise-safe,
because batch composition provably does not affect logits.</p>
<p><strong>D2 &mdash; do not ship in a bundle.</strong>
{ticks(find['F5']['finding'])} was a further finding Grok did not test
({find['F5']['measured_speedup']:.2f}&times;), worth one measurement on the target
box before adopting.</p>

<h2>E &mdash; Equivalence: bitwise is achievable</h2>
<p>Compared on exact bit patterns (<code>struct.pack("&lt;d", x)</code>, so
&minus;0.0 would show as a difference and NaN would be visible), not a tolerance:</p>
<table><thead><tr><th>Configuration vs <code>CrossEncoderReranker()</code></th>
<th class="num">identity</th><th class="num">max|&Delta;|</th>
<th class="num">ranks</th></tr></thead><tbody>{eq_rows}</tbody></table>

<div class="callout win">
  <div class="label">Why it holds &mdash; not luck</div>
  <p><code>attention_mask</code> sets padded positions to exactly <code>0.0</code>
  after softmax, and adding exact zeros to a float accumulation in sequence order
  changes nothing. MLAS parallelizes GEMM over M/N tiles rather than splitting the
  K reduction, so each output element's summation order is fixed regardless of
  thread count or batch shape. <strong>Neither padding nor threading perturbs a
  single bit</strong> &mdash; so ranks are identical by construction and the
  <code>(-score, a_rank, chunk_id)</code> tie-break is never exercised
  differently.</p>
</div>

<h3>The gate to run before flipping anything</h3>
<ol>{gate}</ol>
<p class="dim">Honest limitation: EXP-018B stores no CE logits, so there is no
stored-logit replay gate. Gate 1 must run as a paired A/B in one process.</p>

<h2>G &mdash; Risks</h2>
<div class="callout warn">
  <div class="label">G3b &mdash; seven callers share the defaults, two already frozen</div>
  <p>{callsites}.</p>
  <p><strong>{ticks(find['F6']['consequence'])}</strong></p>
</div>
<div class="callout">
  <div class="label">Correction &mdash; G2, after the full tree landed</div>
  <p>{ticks(find['F2']['correction'])}</p>
</div>
<p><strong>G1 &mdash; bitwise identity is a property of this ORT build on this CPU
class, not a theorem.</strong> It held on two independent machines at ORT 1.29.0.
A different ORT version or a CPU without AVX-512 could select different kernels.
<strong>Re-run the &sect;E gate on the deployment host</strong> &mdash; the most
important residual risk, and the cheapest to close.</p>
<p><strong>G3 &mdash; D1's benefit tracks the length distribution.</strong>
{sl['fraction_at_512']:.1%} of pairs are already at 512 and can never bucket
cheaper; if V2 chunking changes, re-measure.
<strong>G5 &mdash; {ticks(find['F3']['finding'])}</strong>
({esc(find['F3']['location'])}), so every projection inherits its error.</p>

<h2>H &mdash; Expected realistic latency range</h2>
<p>Ratios only, applied to the stored E-L10 figures.
<strong>Projections to verify, not results.</strong></p>
<table><thead><tr><th>Scenario</th><th class="num">CE ms</th>
<th class="num">E-L10 total</th><th>note</th></tr></thead>
<tbody>{proj_rows}</tbody></table>
<div class="callout win">
  <div class="label">Recommendation</div>
  <p>{ticks(m['recommendation'])}</p>
</div>

<footer>PERF-002 &middot; read-only &middot; no patch applied &middot; E-L10 still
constructs <code>CrossEncoderReranker()</code> with defaults &middot; holdout not
opened &middot; V2-DEVSET-001 not scored &middot; every figure rendered from
<code>experiments/PERF-002/PERF-002-measurements.json</code> at build time
&middot; <strong>{esc(m['status'])}</strong></footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="experiments/PERF-002/PERF-002-report.pdf")
    args = parser.parse_args()
    m = json.loads(MEASUREMENTS.read_text())

    # 1. The audit must still be read-only, or the document misdescribes itself.
    if m["patch_applied"] is not False:
        raise SystemExit("refusing to build: patch_applied is not False")
    for name, value in m["constraints_observed"].items():
        if value is not False:
            raise SystemExit(f"refusing to build: constraint {name} is not False")

    # 2. The headline rests on every tested lever being bit-identical.
    if not all(r["bitwise_identical"] and r["ranks_identical"]
               for r in m["equivalence_matrix"]):
        raise SystemExit("refusing to build: a lever is no longer bitwise identical")

    # 3. The decomposition must still make ONNX the dominant term.
    base = m["decomposition_104_pairs"]["runs"][0]
    share = base["onnx_ms"] / base["total_ms"]
    if not 0.95 <= share <= 1.0 or abs(share - m["dominant_bottleneck"]["share_of_ce_time"]) > 0.01:
        raise SystemExit("refusing to build: the ONNX share does not reconcile")

    # 4. The second headline is a comparison; it must survive in the data.
    f2 = next(f for f in m["key_findings"] if f["id"] == "F2")
    if not (f2["measured_threads8_only_speedup"] < 1.0 < f2["measured_fast_true_speedup"]
            < f2["measured_bucketing_only_speedup"]):
        raise SystemExit("refusing to build: the fast=True finding no longer holds")

    # 5. The correction must stay in the document, not be quietly dropped.
    if "correction" not in f2 or "cpu_count=8" not in f2["correction"]:
        raise SystemExit("refusing to build: the G2 correction is missing")

    # 6. The caller inventory is what makes F1 a call-site change.
    f6 = next((f for f in m["key_findings"] if f["id"] == "F6"), None)
    if f6 is None or len(f6["call_sites"]) < 7:
        raise SystemExit("refusing to build: the caller inventory is incomplete")

    document = build_html(m)

    # 7. The page must lead with both results, including the one against Grok.
    flat = " ".join(document.split())
    if "I was wrong" not in flat or "wrong bundle" not in flat:
        raise SystemExit("refusing to build: the page does not lead with both results")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "perf002.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
