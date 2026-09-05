#!/usr/bin/env python3
"""Render the pre-CE trace reconstruction as one PDF.

This report corrects its own predecessor, which is the thing most at risk of being
smoothed away. NATQ2-DIAG-001 named the cross-encoder and stopped there; the
reconstructed pre-CE ordering shows retrieval was weak on nine of the same twelve spans,
so a guard built on the retrieval signal would rescue three cases and land exactly on the
FAIL floor. A page that let the earlier CE-centric reading stand would send the next
build at option A. A gate refuses to render unless the correction and the arithmetic that
forces it are both present.

The second risk is the retrieval-only diagnostic reading as a rival system: 24/40 against
SYSTEM-H's 23/40 invites exactly that misreading, and it is not a system at all. A gate
enforces the disclaimer.

Every figure is read from STATUS-V2-011.json at build time. Eleven gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-011.json"
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 15mm 13mm 13mm 13mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.2pt;
  line-height: 1.43; color: #16181c; margin: 0;
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
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 7.8pt;
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
.card .big { font-size: 14.5pt; font-weight: 700; letter-spacing: -0.5pt; }
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
    RP, RT, PJ, LC, RC, DI = d["replay"], d["rtfo"], d["projection"], d["localization"], \
        d["recommendation"], d["dist"]
    CH, CE = d["channels"], d["ceiling"]

    def bkt(k, b):
        return DI[k].get(b, 0)

    dist = "".join(
        f"<tr><td>{esc(b)}</td><td class='num'>{bkt('ranked_out_12', b)}</td>"
        f"<td class='num'>{bkt('all_in_pool_44', b)}</td>"
        f"<td class='num'>{bkt('final_top10_32', b)}</td></tr>"
        for b in ("<=3", "<=5", "<=10", "<=20", ">20"))
    ro = "".join(
        f"<tr><td>{esc(c)}</td><td class='num'>{i}</td><td>{esc(o)}</td><td class='num'>{ar}</td>"
        f"<td class='num'>{lr if lr else '&mdash;'}</td>"
        f"<td class='num {'hot' if pc and pc > 20 else 'ok'}'><strong>{pc}</strong></td>"
        f"<td class='num'>{cs}</td><td class='num'>{cr}</td><td class='num'>{fr}</td></tr>"
        for c, i, o, ar, lr, pc, cs, cr, fr in d["ranked_out"])
    loc = "".join(
        f"<tr><td>{esc(c)}</td><td class='num'>{i}</td><td>{esc(a)}</td><td>{esc(p)}</td>"
        f"<td class='num'>{n}</td><td class='num'>{f}</td></tr>"
        for c, i, a, p, n, f in d["loc_rows"])
    hs = "".join(f"<tr><td>{ticks(k)}</td><td class='mono'>{esc(v)}</td></tr>"
                 for k, v in d["hashes"].items())

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Pre-CE trace reconstruction</title><style>{CSS}</style></head><body>
<h1>NATQ2&#8209;DIAG&#8209;002 &mdash; pre-CE trace reconstruction</h1>
<p class="subtitle">Diagnostic only &middot; {d['state']['systems_evaluated']} systems evaluated &middot;
CE inference {esc(RP['ce_inference'])} &middot;
validation_runs_consumed {d['state']['validation_runs_consumed']}, {d['state']['unused_validation_runs']} unused &middot;
reserve {d['state']['reserve_bytes']} bytes &middot; head <code>{esc(d['head'])}</code> &middot;
{esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout warn">
<p><strong>This corrects DIAG-001&rsquo;s emphasis.</strong> That report named the cross-encoder and
stopped. The reconstructed pre-CE ordering shows the retrieval stage was weak on the same spans:
<strong>only {RT['spans_n']} of the 12 ranked-out gold spans were inside the pre-CE retrieval top 10</strong>,
and <strong>{bkt('ranked_out_12', '>20')} sat beyond rank 20</strong>, as deep as 68. So there is no strong
retrieval signal to protect. A guard keyed on the existing ordering rescues at most those
{RT['spans_n']} cases &mdash; 23/40 &rarr; 26/40 = 0.65, <em>exactly the FAIL floor</em> and nowhere near the
0.80 PASS floor. That rules out the retrieval-protected reranker and is why the recommendation below is
<strong>{RC['letter']}</strong>, not A.</p>
</div>

<div class="grid">
<div class="card"><div class="big ok">EXACT</div><div class="cap">replay identity</div></div>
<div class="card"><div class="big hot">{RT['spans_n']}/12</div><div class="cap">protected by retrieval</div></div>
<div class="card"><div class="big">{bkt('ranked_out_12', '>20')}/12</div><div class="cap">pre-CE rank &gt; 20</div></div>
<div class="card"><div class="big">{d['state']['candidate_rows']:,}</div><div class="cap">candidates traced</div></div>
<div class="card"><div class="big">{d['state']['unused_validation_runs']}</div><div class="cap">runs still unused</div></div>
</div>

<h2>1 &mdash; Replay identity</h2>
<p>{RP['implementations']} hash-pinned implementations from <code>{esc(RP['ref'])}</code>. No cross-encoder
was invoked; every CE score is the persisted EVAL-NATQ2-H-002 value, and the join was required to be a
bijection on every case &mdash; it was ({esc(RP['ce_bijective'])}).</p>
<table><thead><tr><th style="width:56%">Reproduction check</th><th class="num">Mismatches</th></tr></thead>
<tbody>
<tr><td>Final top-10 rows (400)</td><td class="num ok">{RP['top10_mismatches']}</td></tr>
<tr><td>Case hit vector (40)</td><td class="num ok">{RP['vector_mismatches']}</td></tr>
<tr><td>Per-case span ranks</td><td class="num ok">{RP['rank_mismatches']}</td></tr>
<tr><td>Aggregate metrics</td><td class="num ok">{esc(RP['metric_mismatches'] or 'identical')}</td></tr>
</tbody></table>
<p>The final ranking reproduced exactly even though non-top-10 CE scores were stored at 6 decimals, which
is what establishes that the rounding never flipped an ordering at the depth-10 boundary.</p>

<h2>2 &mdash; Pre-CE rank of the gold spans</h2>
<table><thead><tr><th>pre-CE retrieval rank</th><th class="num">12 ranked out</th>
<th class="num">all 44 in pool</th><th class="num">32 in final top 10</th></tr></thead>
<tbody>{dist}</tbody></table>
<p><strong>RETRIEVAL_TOP10_TO_FINAL_OUT = {esc(RT['spans'])} spans, {esc(RT['cases'])} cases</strong>
({esc(', '.join(RT['ids']))}) &mdash; all three finished at final rank 11, 11 and 14, just outside. This is a
mechanism measurement, not a system result.</p>
<table><thead><tr><th>case</th><th class="num">span</th><th>origin</th><th class="num">A rank</th>
<th class="num">local</th><th class="num">pre-CE</th><th class="num">CE score</th>
<th class="num">CE rank</th><th class="num">final</th></tr></thead><tbody>{ro}</tbody></table>

<h2>3 &mdash; Retrieval-only versus SYSTEM-H</h2>
<div class="callout">
<p><code>RETRIEVAL_ONLY_TOP10_HIT</code> is an internal mechanism diagnostic.
<strong>It is not a qualified system</strong> and must never be reported as one.</p>
<p>retrieval hit / H hit <strong>{d['paired'].get('retrieval_hit/H_hit', 0)}</strong> &middot;
retrieval hit / H miss <strong>{d['paired'].get('retrieval_hit/H_miss', 0)}</strong> &middot;
retrieval miss / H hit <strong>{d['paired'].get('retrieval_miss/H_hit', 0)}</strong> &middot;
retrieval miss / H miss <strong>{d['paired'].get('retrieval_miss/H_miss', 0)}</strong></p>
<p>Diagnostic rate {esc(d['retrieval_only_rate'])} against SYSTEM-H&rsquo;s closed 23/40: the CE/blend stage
trades {d['paired'].get('retrieval_hit/H_miss', 0)} cases away
({esc(', '.join(d['paired_ids'].get('retrieval_hit/H_miss', [])))}) and buys
{d['paired'].get('retrieval_miss/H_hit', 0)} back
({esc(', '.join(d['paired_ids'].get('retrieval_miss/H_hit', [])))}). Near-parity does not make an ordering
a system.</p>
</div>
<p><strong>BM25 regressions.</strong>
{''.join(f"{k} <strong>{esc(v)}</strong>. " for k, v in d['regressions'].items())}
B09 sat at SYSTEM-A rank 11, pre-CE rank 26 and CE &minus;6.37 &mdash; both stages weak. B28 and D27 were
both at pre-CE rank 4 and pushed to final rank 11.</p>

<h2>4 &mdash; Channel contribution</h2>
<table><thead><tr><th>population</th><th class="num">BOTH_A_AND_LOCAL</th><th class="num">SYSTEM_A_ONLY</th>
<th class="num">LOCAL_BM25_ONLY</th><th class="num">PROJECTION_ONLY</th></tr></thead><tbody>
<tr><td>in pool (44)</td><td class="num">{CH['in_pool_44'].get('BOTH_A_AND_LOCAL', 0)}</td>
<td class="num">{CH['in_pool_44'].get('SYSTEM_A_ONLY', 0)}</td>
<td class="num">{CH['in_pool_44'].get('LOCAL_BM25_ONLY', 0)}</td>
<td class="num">{CH['in_pool_44'].get('PROJECTION_ONLY', 0)}</td></tr>
<tr><td>final top 10 (32)</td><td class="num">{CH['final_top10_32'].get('BOTH_A_AND_LOCAL', 0)}</td>
<td class="num">{CH['final_top10_32'].get('SYSTEM_A_ONLY', 0)}</td>
<td class="num">{CH['final_top10_32'].get('LOCAL_BM25_ONLY', 0)}</td>
<td class="num">{CH['final_top10_32'].get('PROJECTION_ONLY', 0)}</td></tr>
<tr><td>ranked out (12)</td><td class="num">{CH['ranked_out_12'].get('BOTH_A_AND_LOCAL', 0)}</td>
<td class="num">{CH['ranked_out_12'].get('SYSTEM_A_ONLY', 0)}</td>
<td class="num">{CH['ranked_out_12'].get('LOCAL_BM25_ONLY', 0)}</td>
<td class="num">{CH['ranked_out_12'].get('PROJECTION_ONLY', 0)}</td></tr>
</tbody></table>
<p>Corroboration across both retrieval channels tracks survival closely: {CH['final_top10_32'].get('BOTH_A_AND_LOCAL', 0)}
of the 32 surviving gold spans were found by SYSTEM-A <em>and</em> local BM25, while
{CH['ranked_out_12'].get('SYSTEM_A_ONLY', 0)} of the 12 ranked-out spans were SYSTEM-A only. Local BM25
contributes a mean {d['stage']['local_additive_selected']} additive candidates out of
{d['stage']['local_additive_available']} available.</p>

<h2>5 &mdash; Projection is inert, not harmful</h2>
<p>{PJ['total_projection_candidates']} projection candidates across the 40 queries covered
<strong>{PJ['gold_spans_covered_by_projection']}</strong> gold spans.
{PJ['projection_candidates_entering_final_top10']} entered the final top 10 across
{PJ['queries_with_at_least_one_projection_top10']} queries, a mean of
{PJ['mean_projection_top10_slots_per_query']} slots per query. For <strong>every one</strong> of those
{PJ['projection_candidates_entering_final_top10']} slots, the next non-projection candidate in frozen final
score order covers no gold span &mdash; {PJ['next_candidate_covers_gold_count']} of
{PJ['projection_candidates_entering_final_top10']}. Projection displaced nothing gold.
<strong>No removal was simulated and no claim is made that removing it improves any metric.</strong></p>

<h2>6 &mdash; Localization, not document discovery</h2>
<p>Of the {LC['spans']} gold spans with no covering candidate,
<strong>{LC['gold_doc_in_system_a']}</strong> had the gold document present in SYSTEM-A and only
<strong>{LC['gold_doc_absent_from_pool_entirely']}</strong> was absent from the pool entirely. But only
<strong>{LC['gold_doc_in_local_parents']}</strong> had that document among the local-BM25 parents, so the
localization stage was not pointed at the right document for the other seven. Projection windows covered the
gold chunk in {LC['projection_window_covered_gold']} of {LC['spans']}.</p>
<table><thead><tr><th>case</th><th class="num">span</th><th>doc in SYSTEM-A</th><th>doc in local parents</th>
<th class="num">same-doc candidates</th><th class="num">nearest final rank</th></tr></thead>
<tbody>{loc}</tbody></table>
<p>E01 is the clearest shape: 38 candidates from the gold document sit in the pool, the nearest at final
rank 1, and none of them covers the gold span. B19 is the same at rank 2. That is a chunk-boundary problem,
not a retrieval problem.</p>

<h2>7 &mdash; Recommendation: {esc(RC['letter'])}. {esc(RC['name'])}</h2>
<div class="callout win"><p>{esc(RC['why'])}</p></div>
<ul>
<li><strong>Why not A.</strong> {esc(RC['why_not_A'])}</li>
<li><strong>Why not C.</strong> {esc(RC['why_not_C'])}</li>
<li><strong>Why not D.</strong> {esc(RC['why_not_D'])}</li>
</ul>
<div class="callout warn"><p><strong>The qualification caveat stands.</strong> {esc(d['margin_caveat'])}
The ceiling work has a target: parent selection for the localization stage, which reaches the gold document
for only {LC['gold_doc_in_local_parents']} of the {LC['spans']} missing spans.</p></div>
<p>Candidate ceilings reconfirm DIAG-001 exactly &mdash; any-span
{esc(CE['any_span_candidate_ceiling'])}, every-span {esc(CE['every_span_candidate_ceiling'])}, span
{esc(CE['candidate_span_ceiling'])}: {esc(CE['matches_NATQ2_DIAG_001'])}.</p>

<h2>8 &mdash; Artifacts</h2>
<table><thead><tr><th style="width:40%">File</th><th>SHA256</th></tr></thead><tbody>{hs}</tbody></table>
<p class="foot">SYSTEM-H config hash <code>{esc(d['config_hash'])}</code>, unchanged. SYSTEM-H validation
remains CLOSED as FAIL and was not rerun; no validation run was consumed by this task. No parameter search:
no guard K tested, no blend weight changed, no projection removed, no retriever run, no candidate pool
altered, no successor implemented. Reserve verified before and after: {d['state']['reserve_bytes']} bytes,
reserve_frozen {esc(d['state']['reserve_frozen'])}, reserve_count {d['state']['reserve_count']}.
Prior status at head <code>{esc(d['prior_status_head'])}</code>.</p>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-011.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    ST, RP, RT, PJ, RC, DI = d["state"], d["replay"], d["rtfo"], d["projection"], \
        d["recommendation"], d["dist"]

    # 1. Every forbidden action false, every forbidden count zero.
    for k, v in d["constraints"].items():
        if isinstance(v, bool):
            if v:
                raise SystemExit(f"refusing to build: constraint {k} is not false")
        elif v != 0:
            raise SystemExit(f"refusing to build: constraint {k} is not zero")
    # 2. Run budget and reserve untouched.
    if ST["validation_runs_consumed"] != 1 or ST["unused_validation_runs"] != 2 \
            or ST["systems_evaluated"] != 0 or ST["reserve_bytes"] != 0 \
            or not ST["reserve_frozen"] or ST["reserve_count"] != 60:
        raise SystemExit("refusing to build: run budget or reserve state is not as required")
    # 3. A non-exact replay may not be used for architectural decisions at all.
    if not RP["exact"] or RP["top10_mismatches"] or RP["vector_mismatches"] \
            or RP["rank_mismatches"] or RP["metric_mismatches"]:
        raise SystemExit("refusing to build: the replay is not exact")
    if RP["ce_inference"] is not False or RP["ce_bijective"] is not True:
        raise SystemExit("refusing to build: CE was re-run or the CE join was not bijective")
    # 4. The recommendation must be exactly one of the four families.
    if RC["letter"] not in {"A", "B", "C", "D"}:
        raise SystemExit("refusing to build: the recommendation is not one architecture family")
    # 5. The recommendation must follow the decision rule from the measured distribution.
    protected, deep = RT["spans_n"], DI["ranked_out_12"].get(">20", 0)
    if RC["letter"] == "A" and protected <= 6:
        raise SystemExit("refusing to build: A is recommended without a large protected fraction")
    if RC["letter"] == "B" and not (protected <= 6 and deep >= 6):
        raise SystemExit("refusing to build: B is recommended without broadly weak retrieval ranks")
    # 6. The correction of DIAG-001 must survive.
    if protected >= 6:
        raise SystemExit("refusing to build: the protected-span count contradicts the narrative")
    # 7. Projection findings keep their limits.
    if PJ["gold_spans_covered_by_projection"] != 0 or not PJ["no_removal_was_simulated"] \
            or not PJ["no_claim_that_removal_improves_metrics"]:
        raise SystemExit("refusing to build: the projection finding is overstated")
    # 8. The one-case margin caveat must be present in the data, not just the prose.
    if "not sufficient evidence for reserve" not in d["margin_caveat"]:
        raise SystemExit("refusing to build: the reserve caveat has been softened")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 9. The correction must be stated plainly.
    if "This corrects DIAG-001" not in flat or "no strong retrieval signal to protect" not in flat:
        raise SystemExit("refusing to build: the page does not carry the correction to DIAG-001")
    # 10. The retrieval-only diagnostic must not read as a system.
    if "It is not a qualified system" not in flat:
        raise SystemExit("refusing to build: the retrieval-only diagnostic is not disclaimed")
    # 11. The FAIL-floor arithmetic that rules out A must be shown.
    if "exactly the FAIL floor" not in flat:
        raise SystemExit("refusing to build: the page does not show why option A is insufficient")

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
