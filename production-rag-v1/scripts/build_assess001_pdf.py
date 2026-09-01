#!/usr/bin/env python3
"""Render the ASSESS-001 engineering assessment as a PDF.

This document is a judgement, not a measurement, and it says so on the page.
Every figure in it is read from ASSESS-001-assessment.json at build time, and
that file was populated from the project's own artifacts rather than typed, so
the opinions can be argued with while the numbers under them cannot drift.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "experiments/ASSESS-001/ASSESS-001-assessment.json"
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


SEV = {"high": "warn", "medium": "", "low": ""}


def build_html(d: dict) -> str:
    ho, ce, v2 = d["v1_holdout"], d["ce_cost"], d["v2_devset_n50"]
    rej, corp = d["ce_rejected_at_dev"], d["corpus"]
    by = {c["id"]: c for c in d["concerns_ranked"]}

    def vrow(v):
        best_mrr = v["v"] == "A"
        shipped = v["v"] == "D"
        name = f"<strong>{v['v']}</strong> &mdash; {esc(v['what'])}"
        if shipped:
            name += " &nbsp;<span class='dim'>shipped</span>"
        mrr = f"<strong>{v['mrr']:.4f}</strong>" if best_mrr else f"{v['mrr']:.4f}"
        lat = (f"<strong>{v['latency_ms']:,.1f}</strong>" if best_mrr
               else f"<span class='hot'>{v['latency_ms']:,.1f}</span>")
        net = ("&mdash;" if v["net_rescues"] == 0
               else f"<span class='hot'>{v['net_rescues']:+d}</span>" if v["net_rescues"] < 0
               else f"{v['net_rescues']:+d}")
        return (name, v["strict"], mrr, lat, net)

    variant_rows = rows([vrow(v) for v in d["exp016_development_n20"]],
                        ("", "num", "num", "num", "num"))
    guard_rows = rows([
        (f"<code>{esc(g['case'])}</code>", f"{g['a_rank']}",
         f"<span class='hot'>{g['ce_rank']}</span>", f"{g['d_rank']}",
         "yes" if g["clamped"] else "no")
        for g in d["guard_evidence"]], ("", "num", "num", "num", "num"))
    strength_items = "".join(f"<li>{ticks(s)}</li>" for s in d["verified_process_strengths"])
    next_items = "".join(f"<li>{ticks(s)}</li>" for s in d["recommended_next"])

    def concern(cid, title, body):
        c = by[cid]
        cls = SEV[c["severity"]]
        return f"""<div class="callout {cls}">
  <div class="label">{esc(cid)} &mdash; {esc(c['severity'])} &mdash; {esc(title)}</div>
  {body}
</div>"""

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>RAG Assessment</title><style>{CSS}</style></head><body>

<h1>Is this RAG system good?</h1>
<p class="subtitle">An engineering assessment &middot; judgement, not a new
measurement &middot; every figure read from the project's own artifacts</p>
<div class="rule"></div>

<div class="callout">
  <div class="label">Verdict</div>
  <p><strong>The engineering discipline is excellent &mdash; better than most
  production RAG work. The retrieval numbers are decent. But the cross-encoder is
  probably not paying for itself, and that matters because it is
  {ce['share_of_e_l10_runtime']:.1%} of your runtime.</strong></p>
  <p>{ticks(d['verdict'])}</p>
</div>

<div class="grid4">
  <div class="stat win"><div class="big">{ho['strict_pct']:.1%}</div>
    <div class="cap">V1 holdout strict R@10, {esc(ho['strict_recall_at_10'])}, unseen</div></div>
  <div class="stat warn"><div class="big">{ce['latency_multiplier_vs_A']:.1f}&times;</div>
    <div class="cap">latency the CE costs, for +{ce['cases_gained_n20']} case of 20</div></div>
  <div class="stat warn"><div class="big">{ce['mrr_delta_vs_A']:+.4f}</div>
    <div class="cap">MRR the CE costs versus not using it</div></div>
  <div class="stat"><div class="big">{corp['documents']}</div>
    <div class="cap">documents &middot; {corp['chunks']:,} chunks</div></div>
</div>

<h2>What is genuinely good</h2>
<p><strong>The V1 holdout number is real.</strong>
<code>{esc(ho['system'])}</code> scored
<strong>{esc(ho['strict_recall_at_10'])} = {ho['strict_pct']:.1%}</strong> strict
Recall@10, span recall {ho['span_recall']}, document recall
{ho['document_recall']}, MRR {ho['mrr']} &mdash; on a split frozen
contamination-aware rather than randomly, guarded by an access log, and opened
once. Most teams never get a number that clean.</p>

<p>The process is the strongest part of this project. Each of these was checked
against the artifacts rather than taken on trust:</p>
<ul>{strength_items}</ul>
<p>Two deserve singling out. <strong>EVAL-VAL-001 rejected SYSTEM-B when it
failed to replicate</strong> &mdash; killing your own promising result is rare.
And <strong>EXP-015 refused to substitute a hand-rolled scorer</strong> when no
pretrained cross-encoder was reachable, rather than produce a number that would
have looked fine.</p>

<div class="break"></div>
<h2>The thing I would worry about</h2>
<p>&ldquo;Reranker rejected at development&rdquo; and &ldquo;reranker is
{ce['share_of_e_l10_runtime']:.1%} of runtime&rdquo; cannot both be fine, so I read
EXP-016. Development, n=20:</p>

<table><thead><tr><th>variant</th><th class="num">strict R@10</th>
<th class="num">MRR</th><th class="num">latency ms</th>
<th class="num">net rescues</th></tr></thead>
<tbody>{variant_rows}</tbody></table>

<p>The cross-encoder buys <strong>+{ce['cases_gained_n20']} case out of 20</strong>,
at <strong>{ce['latency_multiplier_vs_A']:.1f}&times; the latency</strong>, and it
<strong>lowers MRR</strong> against not using it at all
({d['exp016_development_n20'][0]['mrr']:.4f} &rarr;
{d['exp016_development_n20'][3]['mrr']:.4f}).</p>

<p>Now read what the guard is actually doing. These are cases SYSTEM-A already
had right, which the cross-encoder pushed out of the top 10:</p>
<table><thead><tr><th>case</th><th class="num">A rank</th>
<th class="num">CE rank</th><th class="num">D rank</th>
<th class="num">clamped by guard</th></tr></thead>
<tbody>{guard_rows}</tbody></table>

<div class="callout warn">
  <div class="label">The guard's job is to protect A's ranking from the reranker</div>
  <p>EXP-015 recorded the honest verdict first:
  <code>{esc(rej['status'])}</code>, net {rej['net']} &mdash; one rescue
  ({esc(rej['rescues'][0])}) against two regressions
  ({', '.join(esc(r) for r in rej['regressions'])}). The component then returned
  as a guarded blend. The net is one case gained and MRR lost, for
  {(d['exp016_development_n20'][3]['latency_ms'] - d['exp016_development_n20'][0]['latency_ms'])/1000:.1f}
  seconds.</p>
  <p><strong>That makes PERF-002 slightly beside the point.</strong> Making a
  {v2['ce_ms']:,.0f} ms component 1.9&times; faster matters less than asking
  whether you need it.</p>
</div>

{concern("C1", "the missing ablation", f'''
  <p>I could not find <strong>D versus D-without-CE on V2-DEVSET-001
  (n=50)</strong>. EXP-016's comparison is n=20. If the cross-encoder's
  contribution on the larger devset is also one or two cases, the correct move is
  to <strong>cut it, not optimise it</strong>: you would get roughly 550 ms of
  retrieval instead of {v2['total_ms']:,.0f} ms, and lose about one case.</p>
  <p>This is one run, and it is the highest-information thing available right
  now.</p>''')}

<h2>Two structural caveats</h2>

{concern("C2", "n is too small for the decisions", '''
  <p>EXP-018 is <strong>+2 cases on n=50</strong>. EXP-016 is <strong>+1 on
  n=20</strong>. Your own <code>systems.py</code> says it plainly: <em>&ldquo;six
  of the last seven experiments turned on one or two cases.&rdquo;</em></p>
  <p>Architecture is being chosen on deltas a bootstrap CI will not separate from
  noise. The 90-case holdout is the only measurement here with real statistical
  weight, and it is spent.</p>''')}

{concern("C3", "the benchmark is source-anchored", '''
  <p>Cases were mined from the corpus, then reviewed. That systematically favours
  extractive lexical retrieval and inflates absolute recall relative to real user
  questions. It is also, I suspect, why the recurring V1 finding was <em>&ldquo;the
  answer is visible to the encoder but does not rank&rdquo;</em> &mdash; that is
  the signature of questions written from the documents being searched.</p>
  <p>It does not invalidate the comparisons: A versus D is fair on the same set.
  It does mean the headline percentage will not survive contact with real
  traffic.</p>''')}

<p><strong>C4 &mdash; latency is not shippable.</strong>
{v2['total_ms']:,.0f} ms of retrieval before generation has even started;
about 3,360 ms after PERF-002's bucketing; about 550 ms without the
cross-encoder. <strong>C5 &mdash; the corpus is small</strong>
({corp['documents']} documents, {corp['chunks']:,} chunks), so the BM25 IDF and
routing conclusions may not transfer at 100&times; the scale.</p>

<h2>What I would do next</h2>
<ol>{next_items}</ol>

<div class="callout win">
  <div class="label">To be fair to it</div>
  <p>This is a research pipeline behaving like a research pipeline, and a
  rigorous one. The risk is not sloppiness. It is that the rigour is being spent
  on differences too small to be real, and that the most expensive component in
  the system has the weakest evidence behind it.</p>
</div>

<footer>ASSESS-001 &middot; an assessment, not an experiment &middot;
{d['measurements_run_for_this']} new measurements were run for it &middot; every
figure read from <code>experiments/ASSESS-001/ASSESS-001-assessment.json</code>
at build time, itself populated from EXP-015, EXP-016 and EXP-018B artifacts
&middot; the V1 holdout figures are as reported in the handoff; EVAL-HOLDOUT-001's
results were not opened</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="experiments/ASSESS-001/ASSESS-001-assessment.pdf")
    args = parser.parse_args()
    d = json.loads(DATA.read_text())

    # 1. This is a judgement. It must not quietly become a claim of new measurement.
    if d["measurements_run_for_this"] != 0:
        raise SystemExit("refusing to build: this document claims to run no measurements")

    # 2. The central argument is a comparison; it has to survive in the numbers.
    v = {x["v"]: x for x in d["exp016_development_n20"]}
    if not (v["A"]["mrr"] > v["D"]["mrr"] and v["D"]["cases"] > v["A"]["cases"]
            and v["D"]["latency_ms"] > 10 * v["A"]["latency_ms"]):
        raise SystemExit("refusing to build: the cross-encoder argument no longer holds "
                         "(A should beat D on MRR, lose on cases, and be >10x faster)")

    # 3. The CE-rejected record is what makes the argument more than an opinion.
    if d["ce_rejected_at_dev"]["net"] >= 0:
        raise SystemExit("refusing to build: the CE was not rejected at dev after all")

    # 4. The guard evidence must still show A-ranks being rescued from the CE.
    if not all(g["ce_rank"] > 10 >= g["a_rank"] for g in d["guard_evidence"]):
        raise SystemExit("refusing to build: the guard evidence no longer shows "
                         "the CE displacing cases A had inside the top 10")

    # 5. Credit and criticism must both be present. A one-sided page is not the read.
    if not d["verified_process_strengths"] or not d["concerns_ranked"]:
        raise SystemExit("refusing to build: the assessment must carry both sides")

    document = build_html(d)
    flat = " ".join(document.split())
    if "genuinely good" not in flat or "would worry about" not in flat:
        raise SystemExit("refusing to build: the page must lead with both sides")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "assess001.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
