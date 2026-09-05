#!/usr/bin/env python3
"""Render the single preregistered SYSTEM-H NATQ-002 run as one PDF.

The result is genuinely two-sided and the two sides pull in opposite directions:
SYSTEM-H beat the lexical control decisively on the preregistered paired test, and it
still FAILED the run, because case_hit@10 = 0.575 sits below the 0.65 floor. A report
that leads with the delta would read as a win; one that leads with FAIL and buries the
delta would read as a system that does nothing. Both framings are available from the
same numbers, so gates force the page to carry both, plus the fact that this FAIL owes
nothing to the rule repair -- it would have failed identically under the old rule.

Every figure is read from STATUS-V2-009.json at build time. Eleven gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-009.json"
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
h1 { font-size: 18.5pt; line-height: 1.14; margin: 0 0 4pt; letter-spacing: -0.4pt; }
h2 { font-size: 11.6pt; margin: 15pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
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
.mono { font-family: "SFMono-Regular", Consolas, monospace; font-size: 7pt; word-break: break-all; }
.dim { color: #6f747b; } .hot { color: #8a1c1c; font-weight: 700; } .ok { color: #14532d; font-weight: 700; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 8pt 11pt;
  margin: 9pt 0 11pt; page-break-inside: avoid; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout.win { border-left-color: #14532d; background: #f2f8f4; }
.callout p:last-child { margin-bottom: 0; }
.grid { display: flex; gap: 7pt; margin: 9pt 0 11pt; }
.card { flex: 1; border: 0.8pt solid #d6dae0; border-radius: 3pt; padding: 7pt 8pt; }
.card .big { font-size: 15pt; font-weight: 700; letter-spacing: -0.5pt; }
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


def build_html(d: dict) -> str:
    P, R, SC, RU, PC = d["paired"], d["rule"], d["scorer"], d["run"], d["paired_cases"]
    DD = d["decision_detail"]

    met = "".join(
        f"<tr><td>{ticks(n)}</td><td class='num'>{h}</td><td class='num dim'>{b}</td>"
        f"<td class='num'>{'+' if h - b > 0 else ''}{round(h - b, 4)}</td></tr>"
        for n, h, b in d["metrics_table"])
    sl = "".join(
        f"<tr><td>{esc(s)}</td><td class='num'>{n}</td><td class='num'>{sp}</td>"
        f"<td class='num'>{hh}</td><td class='num dim'>{bb}</td><td class='num'>{cov}</td>"
        f"<td class='num'>{sr}</td><td class='num'>{mrr}</td></tr>"
        for s, n, sp, hh, bb, cov, sr, mrr in d["per_slice"])
    scs = "".join(f"<tr><td>{ticks(m)}</td><td class='num'>{g}</td><td class='num'>{w}</td>"
                  f"<td class='ok'>match</td></tr>" for m, g, w in SC["checks"])
    hs = "".join(f"<tr><td>{ticks(k)}</td><td class='mono'>{esc(v)}</td></tr>"
                 for k, v in d["hashes"].items())

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>SYSTEM-H on NATQ-002</title><style>{CSS}</style></head><body>
<h1>SYSTEM-H on NATQ-002 validation &mdash; the single preregistered run</h1>
<p class="subtitle">Decision <strong>{esc(d['decision'])}</strong> &middot;
{RU['gate']} identity gates &middot; {RU['consumed']} of 3 validation runs consumed &middot;
{RU['retries']} retries &middot; reserve {RU['reserve_bytes']} bytes &middot;
head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout warn">
<p><strong>SYSTEM-H beat the lexical control decisively and still failed the run.</strong>
Both halves of that sentence are load-bearing. The preregistered paired test came back
<strong>+{P['bootstrap_mean_delta']:.4f} micro-MRR</strong> with a 95% interval of
<strong>[{P['ci95_low']:.4f}, {P['ci95_high']:.4f}]</strong>, which excludes zero &mdash; the improvement
over BM25 is real and not a resampling artefact. But the decision also requires an absolute floor,
and <code>case_hit@10 = {DD['case_hit_at_10']}</code> is below the <strong>{DD['FAIL_floor']}</strong> FAIL
threshold, well short of the {DD['PASS_floor']} PASS floor. Relative progress, absolute
non&#8209;qualification. Neither half cancels the other.</p>
</div>

<div class="grid">
<div class="card"><div class="big hot">{esc(d['decision'])}</div><div class="cap">decision</div></div>
<div class="card"><div class="big">{DD['case_hit_at_10']}</div><div class="cap">case_hit@10 &middot; floor {DD['FAIL_floor']}</div></div>
<div class="card"><div class="big ok">+{P['bootstrap_mean_delta']:.3f}</div><div class="cap">paired micro-MRR delta</div></div>
<div class="card"><div class="big">{RU['gate']}</div><div class="cap">identity gates</div></div>
<div class="card"><div class="big">{RU['consumed']}</div><div class="cap">runs consumed</div></div>
</div>

<h2>1 &mdash; Decision under the replacement rule</h2>
<p>PASS clause satisfied: <strong>{esc(DD['PASS_clause'])}</strong> &middot;
FAIL clause satisfied: <strong>{esc(DD['FAIL_clause'])}</strong> &middot;
interval excludes zero: {esc(DD['interval_excludes_zero'])} &middot;
mean delta sign: {esc(DD['mean_delta_sign'])}.</p>
<div class="callout">
<p><strong>This FAIL owes nothing to the rule repair.</strong> {esc(d['decision_rule_note'])}
The regression disjunct added in EVAL-NATQ2-H-002 changes {R['changed']} states of the rule's
{R['states']}&#8209;state space, and this run is in none of them &mdash; its delta is positive.
The repair was still worth making before the run rather than after, but it is not what produced
this outcome, and presenting it as though it were would misstate the record.</p>
</div>

<h2>2 &mdash; SYSTEM-H versus the frozen BM25 comparator</h2>
<table><thead><tr><th style="width:46%">Metric</th><th class="num">SYSTEM-H</th>
<th class="num">BM25 control</th><th class="num">Delta</th></tr></thead><tbody>{met}</tbody></table>
<p><strong>Any-evidence and complete-evidence are different numbers and must not be conflated.</strong>
<code>case_hit@10 = {DD['case_hit_at_10']}</code> is the fraction of cases where <em>at least one</em>
gold span was retrieved. <code>case_full_coverage@10 =
{d['metrics_table'][2][1]}</code> is the fraction where <em>every gold span</em> was. The qualification
floors are defined against the former, which is the more forgiving of the two.</p>

<h2>3 &mdash; The preregistered paired test</h2>
<p>Paired bootstrap over <strong>cases</strong>, {P['resamples']:,} resamples, seed {P['seed']},
exactly as preregistered. Cases are the resampling unit because spans within a case are not
independent.</p>
<table><thead><tr><th>Quantity</th><th class="num">Value</th></tr></thead><tbody>
<tr><td>Observed micro-MRR delta (H &minus; BM25)</td><td class="num">{P['observed_delta']:.6f}</td></tr>
<tr><td>Bootstrap mean delta</td><td class="num">{P['bootstrap_mean_delta']:.6f}</td></tr>
<tr><td>95% percentile interval</td><td class="num">[{P['ci95_low']:.6f}, {P['ci95_high']:.6f}]</td></tr>
<tr><td>Interval excludes zero</td><td class="num ok">{esc(P['interval_excludes_zero'])}</td></tr>
</tbody></table>
<p>Case-level movement: <strong>{len(PC['h_only'])}</strong> cases SYSTEM-H hits that BM25 misses
({esc(', '.join(PC['h_only']))}); <strong>{len(PC['bm25_only'])}</strong> the other way
({esc(', '.join(PC['bm25_only']))}); {PC['both_hit']} hit by both; <strong>{PC['both_miss']} missed by
both</strong>. That last figure is the ceiling problem &mdash; more than a third of the partition is
out of reach of either system at depth 10.</p>

<h2>4 &mdash; Per authoring slice</h2>
<table><thead><tr><th>Slice</th><th class="num">n</th><th class="num">spans</th>
<th class="num">H hit@10</th><th class="num">BM25</th><th class="num">H full cov</th>
<th class="num">H span rec</th><th class="num">H MRR</th></tr></thead><tbody>{sl}</tbody></table>
<p>Eight cases per slice, so a single case moves a slice rate by 0.125. These are reported because
they were preregistered, not because any one of them supports a conclusion at this sample size.</p>

<h2>5 &mdash; One scorer, verified before the run</h2>
<div class="callout win">
<p>Both systems were scored by the same module. Before SYSTEM-H was run, that scorer was made to
reproduce the frozen comparator from its <strong>stored {SC['input_rows']}-row ranked output</strong>,
offline: BM25 retrieval rerun <strong>{esc(SC['bm25_rerun'])}</strong>, database queried
<strong>{esc(SC['db_queried'])}</strong>. It matched on every metric, on the stored 40-case pass/fail
vector ({SC['vector_mismatches']} mismatches) and on every stored per-case span rank
({SC['rank_mismatches']} mismatches).</p>
</div>
<table><thead><tr><th style="width:46%">Metric recomputed from stored traces</th>
<th class="num">Recomputed</th><th class="num">Frozen</th><th>Status</th></tr></thead>
<tbody>{scs}</tbody></table>
<p>This matters because METRIC-AUDIT-001 found NATQ-001&rsquo;s <code>strict_recall@10</code> and
NATQ-002&rsquo;s <code>case_hit@10</code> NOT_EQUIVALENT. Scoring SYSTEM-H with the NATQ-001 helpers
would have measured a stricter metric and made the comparison against 0.375 meaningless. The shared
scorer never consults <code>section_path</code>.</p>

<h2>6 &mdash; What this result does not say</h2>
<ul>{''.join(f'<li>{ticks(c)}</li>' for c in d['prohibited_claims'])}</ul>
<p>The historical NATQ-001 figure is not a baseline this run improved on: the metrics are
NOT_EQUIVALENT and the two benchmarks share no cases, so no comparison between them exists to win
or lose.</p>

<h2>7 &mdash; Run accounting</h2>
<ul>
<li>{RU['cases']} cases, {RU['spans']} gold spans, depth 10, one pass, {RU['retries']} retries.</li>
<li>Traces persisted: {esc(', '.join(f"{k} {v} rows" for k, v in RU['logs'].items()))}.</li>
<li>Validation runs: {RU['consumed']} consumed, {RU['remaining']} remaining under the preregistered cap of 3.</li>
<li>Mean stage latency (ms): {esc(', '.join(f"{k} {v}" for k, v in d['stage_latency'].items()))}.</li>
<li>Reserve opened: {esc(RU['reserve_opened'])}; access log {RU['reserve_bytes']} bytes, hash unchanged before and after.</li>
</ul>
<table><thead><tr><th style="width:40%">Artifact</th><th>SHA256</th></tr></thead><tbody>{hs}</tbody></table>
<p class="foot">Authoritative SYSTEM-H config hash <code>{esc(d['config_hash'])}</code>, preserved and
gate-checked. SYSTEM-H was not redesigned &mdash; the wrapper imports the recovered pipeline verbatim
and changes only the input partition and the scorer. No BM25 retrieval rerun, no tuning, no reserve or
holdout access, no release promotion. Prior status at head <code>{esc(d['prior_status_head'])}</code>.</p>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-009.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    DD, P, RU, SC, R = d["decision_detail"], d["paired"], d["run"], d["scorer"], d["rule"]

    # 1. Every forbidden action must still be false.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")
    # 2. Exactly one scored run, no retries, reserve untouched.
    if RU["consumed"] != 1 or RU["retries"] != 0 or RU["reserve_bytes"] != 0 or RU["reserve_opened"]:
        raise SystemExit("refusing to build: run accounting or reserve state is not as authorised")
    # 3. The decision must follow from the numbers, recomputed here rather than trusted.
    p = DD["interval_excludes_zero"] and P["bootstrap_mean_delta"] > 0 and DD["case_hit_at_10"] >= 0.80
    f = ((not DD["interval_excludes_zero"])
         or (DD["interval_excludes_zero"] and P["bootstrap_mean_delta"] < 0)
         or DD["case_hit_at_10"] < 0.65)
    expect = "PASS" if p and not f else ("FAIL" if f and not p else "INCONCLUSIVE")
    if d["decision"] != expect:
        raise SystemExit(f"refusing to build: reported decision {d['decision']} != recomputed {expect}")
    # 4. The rule repair must not be credited with this outcome.
    if not d["same_under_old_rule"]:
        raise SystemExit("refusing to build: the page would credit the rule repair for the verdict")
    # 5. The scorer must have been verified, offline, against the frozen comparator.
    if not SC["verified"] or SC["vector_mismatches"] or SC["rank_mismatches"] \
            or SC["bm25_rerun"] is not False or SC["db_queried"] is not False:
        raise SystemExit("refusing to build: the shared scorer was not verified offline and exactly")
    # 6. The comparator column must be the frozen values, not a re-measurement.
    if d["metrics_table"][1][2] != 0.375 or d["metrics_table"][0][2] != 0.1425:
        raise SystemExit("refusing to build: the comparator column is not the frozen BM25 result")
    # 7. The identity gate must be complete.
    if RU["gate"] != "33/33":
        raise SystemExit("refusing to build: the runtime identity gate is not complete")
    # 8. The rule must still be exhaustive and exclusive.
    if not (R["exclusive"] and R["exhaustive"] and R["regressions_fail"]):
        raise SystemExit("refusing to build: the decision rule no longer verifies")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 9. Both halves of the result must be on the page.
    if "beat the lexical control decisively and still failed" not in flat:
        raise SystemExit("refusing to build: the page does not carry both halves of the result")
    # 10. Any-evidence must not be allowed to read as complete-evidence.
    if "must not be conflated" not in flat or "at least one" not in flat or "every gold span" not in flat:
        raise SystemExit("refusing to build: the page does not distinguish any-evidence from coverage")
    # 11. The forbidden comparison must be explicitly disclaimed.
    if "no comparison between them exists" not in flat:
        raise SystemExit("refusing to build: the page does not disclaim the NATQ-001 comparison")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO / a.out if not Path(a.out).is_absolute() else Path(a.out)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "r.html"
        src.write_text(doc)
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                        f"--print-to-pdf={out}", "--no-pdf-header-footer",
                        f"--user-data-dir={td}/u", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
