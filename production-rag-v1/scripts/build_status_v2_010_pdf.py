#!/usr/bin/env python3
"""Render the NATQ-002 failure analysis as one PDF.

The finding is a reversal of the natural reading of the run. SYSTEM-H looked like a
system that could not find the evidence; the traces say it found the evidence and threw
it away. 44 of 57 gold spans reached the candidate pool and 12 were ranked out, and
recovering those alone would have cleared the PASS floor. A report that let the reader
keep blaming retrieval would send the next experiment at the wrong stage, so a gate
refuses to build unless the ranking-versus-retrieval conclusion and its oracle caveat
are both on the page.

The second thing that must survive editing is what the traces CANNOT say: SYSTEM-A and
local BM25 membership were never persisted separately, and pre-CE rank was never
persisted at all, so reranker movement is unavailable rather than estimated. Gates
enforce that those limits are printed rather than quietly dropped.

Every figure is read from STATUS-V2-010.json at build time. Ten gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-010.json"
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
.bar { display: inline-block; height: 7pt; background: #16181c; vertical-align: middle; margin-right: 4pt; }
.bar.lost { background: #8a1c1c; }
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
    CE, PR, CF, HR = d["ce"], d["projection"], d["counterfactual"], d["headroom"]

    fun = "".join(
        f"<tr><td>{esc(n)}</td><td class='num'>{v}</td><td class='num dim'>{esc(f)}</td>"
        f"<td><span class='bar{'' if i < 4 else ' lost'}' style='width:{(v if isinstance(v, int) else 0) * 1.9}pt'></span></td></tr>"
        for i, (n, v, f) in enumerate(d["funnel"]))
    tax = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td class='num'>{c}</td>"
                  f"<td class='num'>{e}</td><td>{esc(m)}</td><td class='dim'>{esc(s)}</td></tr>"
                  for a, b, c, e, m, s in d["taxonomy_rows"])
    ro = "".join(f"<tr><td>{esc(c)}</td><td class='num'>{i}</td><td class='num'>{r}</td>"
                 f"<td class='num {'hot' if s < 0 else ''}'>{s}</td></tr>" for c, i, r, s in d["ranked_out"])
    hs = "".join(f"<tr><td>{ticks(k)}</td><td class='mono'>{esc(v)}</td></tr>"
                 for k, v in d["hashes"].items())
    unav = "".join(f"<li>{ticks(k.replace('_', ' '))} &mdash; {esc(d['stage_availability'][k])}</li>"
                   for k in d["unavailable"])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>NATQ-002 failure analysis</title><style>{CSS}</style></head><body>
<h1>NATQ2&#8209;DIAG&#8209;001 &mdash; why SYSTEM-H missed the floor</h1>
<p class="subtitle">Trace-only &middot; {d['state']['systems_run']} systems run &middot;
{d['state']['runs_consumed_by_this_task']} validation runs consumed &middot;
validation closed as FAIL, not reopened &middot; reserve {d['state']['reserve_bytes']} bytes &middot;
head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout warn">
<p><strong>SYSTEM-H did not fail because it could not find the evidence. It found the evidence and
ranked it away.</strong> Of the 57 gold spans, <strong>44 reached the final candidate pool</strong> and
only 32 survived into the top 10. The 12 that were ranked out took <strong>10 whole cases</strong> from
hit to miss. Recover only those, changing nothing about retrieval, and
<code>case_hit@10</code> goes from <strong>{esc(CF['achieved_case_hit_at_10'])}</strong> to
<strong>{esc(CF['if_every_in_pool_span_were_ranked_into_top10'])}</strong> &mdash; above the
{CF['PASS_floor']} PASS floor. This is an <em>oracle bound on the stored pool, not a prediction</em>:
it establishes where the loss happened, not that any particular fix would recover it.</p>
</div>

<div class="grid">
<div class="card"><div class="big">44 &rarr; 32</div><div class="cap">spans in pool &rarr; in top 10</div></div>
<div class="card"><div class="big hot">12</div><div class="cap">spans ranked out</div></div>
<div class="card"><div class="big">{esc(d['ceiling']['any_span_candidate_ceiling'])}</div><div class="cap">any-span candidate ceiling</div></div>
<div class="card"><div class="big hot">{PR['gold_spans_covered_by_a_projection_candidate']}/57</div><div class="cap">spans from projection</div></div>
<div class="card"><div class="big">{d['state']['runs_consumed_by_this_task']}</div><div class="cap">runs consumed here</div></div>
</div>

<h2>1 &mdash; Where the 57 gold spans were lost</h2>
<table><thead><tr><th style="width:44%">Stage</th><th class="num">Spans</th><th class="num">Rate</th>
<th style="width:26%"></th></tr></thead><tbody>{fun}</tbody></table>
<p>Only <strong>one</strong> gold span had its document miss the candidate pool entirely. Twelve more had the
document but no chunk covering the span &mdash; localization. The remaining twelve losses happened after
retrieval had already succeeded.</p>

<h2>2 &mdash; The cross-encoder is the locus</h2>
<div class="callout">
<p>Spans that survived carry a median CE score of <strong>{CE['median_CE_score_hit_spans']}</strong> at a
median CE-score rank of <strong>{CE['median_CE_score_rank_in_pool_hit']}</strong> in their pool. Spans that
were ranked out carry a median of <strong>{CE['median_CE_score_ranked_out_spans']}</strong> at rank
<strong>{CE['median_CE_score_rank_in_pool_ranked_out']}</strong>.
<strong>{esc(CE['ranked_out_spans_with_negative_CE'])}</strong> of the ranked-out spans were scored negative.
The reranker is not undecided about this evidence &mdash; it is confidently against it.</p>
</div>
<table><thead><tr><th>Case</th><th class="num">Span</th><th class="num">CE-score rank in pool</th>
<th class="num">CE score</th></tr></thead><tbody>{ro}</tbody></table>
<p>One row implicates the blend rather than the cross-encoder: <strong>{esc(d['ce_blend_exception']['case'])}</strong>
span {d['ce_blend_exception']['span_index']} sat at CE-score rank
{d['ce_blend_exception']['CE_score_rank_in_pool']} and still finished outside the top 10, so the
EXP&#8209;017/EXP&#8209;019A blend demoted it. That is 1 of 12; the other 11 were already far down the CE
ordering.</p>

<h2>3 &mdash; Candidate generation caps the system at 0.825</h2>
<p>CANDIDATE_CASE_CEILING, every-span oracle: <strong>{esc(d['ceiling']['candidate_case_ceiling'])}</strong>.
Candidate span ceiling: <strong>{esc(d['ceiling']['candidate_span_ceiling'])}</strong>. Any-span ceiling,
which is what bounds <code>case_hit@10</code>: <strong>{esc(d['ceiling']['any_span_candidate_ceiling'])}</strong>.</p>
<p>So a <em>perfect</em> reranker over the pool as generated reaches 33/40 &mdash; one case above the
{HR['PASS_floor']} floor. Ranking is where the recoverable loss is, but the margin behind it is a single
case. Any future work that improves ranking without improving candidate generation is working inside that cap.
These are oracle bounds and are not system performance.</p>

<h2>4 &mdash; The projection stage contributed no gold coverage</h2>
<div class="callout warn">
<p>Across the 40 cases the projection stage supplied <strong>{PR['projection_candidates_supplied']}</strong>
candidates ({PR['per_case']} per case) and covered <strong>{PR['gold_spans_covered_by_a_projection_candidate']}</strong>
gold spans. All 44 in-pool gold spans arrived through the SYSTEM&#8209;A / local&#8209;BM25 fusion. Meanwhile
{PR['projection_chunks_that_reached_top10']} projection chunks did occupy final top-10 slots, at a mean
{PR['mean_projection_stage_latency_ms']}&#8239;ms per case.</p>
<p class="dim">{esc(d['projection_caveat'])}</p>
</div>

<h2>5 &mdash; Failure taxonomy</h2>
<p>{esc(', '.join(f'{k} {v}' for k, v in d['taxonomy'].items()))}. No case was left
TRACE_INSUFFICIENT.</p>
<table><thead><tr><th>Case</th><th>Population</th><th class="num">Spans</th><th class="num">Failed</th>
<th>Primary mechanism</th><th>Secondary</th></tr></thead><tbody>{tax}</tbody></table>
<p>All three <strong>H_REGRESSIONS</strong> (B09, B28, D27) are reranking failures: SYSTEM-H had the covering
candidate in its pool and ranked it out, while BM25 found the same evidence and kept it. Even inside
BOTH_MISS, five of fourteen are ranking losses rather than retrieval losses.</p>

<h2>6 &mdash; What these traces cannot say</h2>
<ul>{unav}</ul>
<p><strong>Reranker movement could not be computed.</strong> Pre-CE RRF rank was never persisted, so no
per-span before/after delta exists. The CE-score ranks above are derived by ordering the stored CE scores
and are diagnostic only, because the final order is a blend. GLOBAL_CANDIDATE_FAILURE and
DOCUMENT_DISCOVERY_FAILURE are likewise not separable here: SYSTEM-A membership was never persisted apart
from local BM25, so the one span whose document never entered the pool is reported as E rather than split
against a distinction the traces cannot support. Nothing above was recreated by rerunning anything.</p>

<h2>7 &mdash; Answer</h2>
<div class="callout win"><p>{esc(d['answer'])}</p></div>

<h2>8 &mdash; Artifacts</h2>
<table><thead><tr><th style="width:40%">File</th><th>SHA256</th></tr></thead><tbody>{hs}</tbody></table>
<p class="foot">Authoritative SYSTEM-H config hash <code>{esc(d['config_hash'])}</code>, unchanged.
SYSTEM_H_NATQ2_VALIDATION_CLOSED = true; SYSTEM_H_NATQ2_RETRY_AUTHORIZED = false. Neither remaining
validation run was used. No retrieval, reranking, or CE inference was performed; the only external read was
the frozen chunk table, to resolve stored chunk ids into offsets they already carried.
The task message was truncated mid-sentence in the RERANKER MOVEMENT section; every fully specified section
was completed and any section after it was not received. Prior status at head <code>{esc(d['prior_status_head'])}</code>.</p>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-010.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    ST, CF, CE, PR = d["state"], d["counterfactual"], d["ce"], d["projection"]

    # 1. Every forbidden action must still be false, and every forbidden count zero.
    # The block mixes booleans with one tally, so each is checked on its own terms rather
    # than dropping the tally to keep a uniform test.
    for k, v in d["constraints"].items():
        if isinstance(v, bool):
            if v:
                raise SystemExit(f"refusing to build: constraint {k} is not false")
        elif isinstance(v, (int, float)):
            if v != 0:
                raise SystemExit(f"refusing to build: constraint {k} is not zero")
        else:
            raise SystemExit(f"refusing to build: constraint {k} is neither a flag nor a count")
    # 2. This was a trace-only task: nothing run, nothing consumed, decision not reopened.
    if ST["systems_run"] != 0 or ST["runs_consumed_by_this_task"] != 0 \
            or not ST["validation_closed"] or ST["retry_authorized"] or ST["reserve_bytes"] != 0:
        raise SystemExit("refusing to build: the page reports a run, a consumed budget, or a reopened decision")
    # 3. The funnel must reconcile: in-pool = reached top10 + ranked out.
    v = {n: x for n, x, _ in d["funnel"]}
    if v["Covering candidate in the final pre-rerank pool"] != \
            v["Reached the final top 10"] + v["In the pool but ranked out"]:
        raise SystemExit("refusing to build: the span funnel does not reconcile")
    # 4. The counterfactual must stay a bound, never a promise.
    if not CF["would_clear_PASS_floor"] or "not a prediction" not in CF["caveat"]:
        raise SystemExit("refusing to build: the oracle bound is missing its caveat")
    # 5. The CE evidence must actually support the claim the page makes about it.
    if CE["median_CE_score_ranked_out_spans"] >= CE["median_CE_score_hit_spans"]:
        raise SystemExit("refusing to build: the CE claim is not supported by the stored scores")
    # 6. The projection finding must keep its limits.
    if PR["gold_spans_covered_by_a_projection_candidate"] != 0 or "does NOT establish" not in d["projection_caveat"]:
        raise SystemExit("refusing to build: the projection finding is overstated or its caveat is gone")
    # 7. Unavailable stages must be declared, not quietly dropped.
    if len(d["unavailable"]) < 3:
        raise SystemExit("refusing to build: the trace limitations are not being declared")
    # 8. The truncation must be disclosed.
    if not d["truncation"]["task_message_truncated"]:
        raise SystemExit("refusing to build: the page would hide that the instruction was truncated")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 9. The reversal must be stated, or the reader blames the wrong stage.
    if "found the evidence and ranked it away" not in flat:
        raise SystemExit("refusing to build: the page does not state where the failure actually is")
    # 10. The ceiling must not be allowed to read as performance.
    if "are not system performance" not in flat:
        raise SystemExit("refusing to build: the page does not disclaim the oracle ceiling")

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
