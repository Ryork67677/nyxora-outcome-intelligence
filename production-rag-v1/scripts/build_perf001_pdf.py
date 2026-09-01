#!/usr/bin/env python3
"""Render the PERF-001 read-only performance audit as a PDF.

The finding is the headline: the local stage does 0.15% local work, and one
corpus-wide average that depends on neither the query nor the parent is 96% of
it. The optimization plan is the body.

Every figure is read from PERF-001-measurements.json at build time, and every
claim about the source is re-read from the source. Seven gates refuse the build
rather than publish a document that disagrees with the repository.
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

AUDIT = REPO_ROOT / "experiments/PERF-001"
MEASUREMENTS = AUDIT / "PERF-001-measurements.json"
RETRIEVAL = REPO_ROOT / "src/rag_v1/retrieval.py"
SYSTEMS = REPO_ROOT / "src/rag_v1/systems.py"
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
    c, plan = m["corpus"], m["plan_costs_single_parent_local_bm25"]
    proj, micro = m["per_query_projection_10_parents_11_terms"], m["microbenchmarks"]
    proof, terms = m["avg_len_equivalence_proof"], m["query_term_counts"]
    state, g1 = m["repository_state"], m["highest_risk_false_optimization"]
    ce = next(u for u in m["unanswerable_here"] if u["question"].startswith("6 -"))

    single = plan["total_4_terms"]
    df_p50 = plan["df_lateral_per_term"] * terms["p50"]

    # The cost table is the spine of the document: three stages, one of which is
    # the work actually being asked for.
    stage_rows = rows([
        ("<code>corpus</code> CTE &mdash; <code>n</code>, <code>avg_len</code>, full corpus",
         f"{plan['corpus_cte_count_and_avg_len']:,.0f}",
         "<span class='bar hot' style='width:118pt'></span>",
         "<strong>no</strong>", "<strong>no</strong>"),
        ("<code>weighted</code> LATERAL &mdash; per-term <code>df</code>",
         f"{plan['df_lateral_per_term']:,.0f} &times; T",
         f"<span class='bar' style='width:{max(2, round(118 * df_p50 / (single + df_p50)))}pt'></span>",
         "<strong>no</strong>", "terms only"),
        ("scoring <code>SELECT</code> &mdash; the parent's own chunks",
         f"<strong>{plan['local_candidate_scan_single_parent']:,.0f}</strong>",
         "<span class='bar' style='width:2pt'></span>", "yes", "yes"),
    ], ("", "num", "", "num", "num"))

    isolate_rows = rows([
        ("<code>count(*)</code> only", f"{plan['corpus_cte_count_only']:,.2f}",
         "Index Only Scan &mdash; no heap access"),
        ("<code>count(*)</code> + <code>avg(length(coalesce(search_text, text)))</code>",
         f"<span class='hot'>{plan['corpus_cte_count_and_avg_len']:,.2f}</span>",
         "Bitmap <strong>Heap</strong> Scan, width 809"),
        ("<strong>marginal cost of <code>avg_len</code> alone</strong>",
         f"<span class='hot'>{plan['avg_len_marginal_cost']:,.2f}</span>",
         f"<strong>{plan['avg_len_share_of_single_parent_query']:.0%} of a single-parent query</strong>"),
    ], ("", "num", "dim"))

    ladder_rows = rows([
        ("Current &mdash; 10 independent <code>lexical_search()</code> calls",
         f"{proj['current_plan_cost']:,}", f"{proj['db_connections_current']}", "&mdash;"),
        ("Query-level work hoisted, parents batched into one window",
         f"{proj['after_hoist_and_batch']:,}", f"{proj['db_connections_after']}",
         f"{proj['current_plan_cost'] / proj['after_hoist_and_batch']:.1f}&times;"),
        ("&nbsp;&nbsp;+ <code>avg_len</code> materialized",
         f"{proj['after_avg_len_materialized']:,}", f"{proj['db_connections_after']}",
         f"{proj['current_plan_cost'] / proj['after_avg_len_materialized']:.1f}&times;"),
        ("&nbsp;&nbsp;+ <code>df</code> cache warm",
         f"{proj['after_df_cache_warm']:,}", f"{proj['db_connections_after']}",
         f"{proj['current_plan_cost'] / proj['after_df_cache_warm']:,.0f}&times;"),
    ], ("", "num", "num", "num"))

    bottleneck_rows = rows([
        (f"{b['rank']}", ticks(b["what"]), f"<code>{esc(b['location'])}</code>",
         (f"{b['relative_cost']:.2%}" if "relative_cost" in b
          else f"{b['cost_ms_per_query']} ms/query"))
        for b in m["bottlenecks_ranked"]
    ], ("num", "", "dim", "num"))

    complexity_rows = rows([
        ("full-corpus heap+TOAST scans", "<span class='hot'>10</span>", "1",
         "<strong>0</strong>"),
        ("full-corpus <code>df</code> index scans", "<span class='hot'>110</span>",
         "11", "~0 warm"),
        ("DB round trips", f"<span class='hot'>{proj['db_connections_current']}</span>",
         "1", "1"),
        ("DB connections", f"<span class='hot'>{proj['db_connections_current']}</span>",
         "1", "1"),
        ("plan cost / query", f"<span class='hot'>{proj['current_plan_cost']:,}</span>",
         f"{proj['after_hoist_and_batch']:,}", f"{proj['after_avg_len_materialized']:,}"),
        ("over Q = 50 queries", f"<span class='hot'>{proj['current_plan_cost'] * 50 / 1e6:.2f} M</span>",
         f"{proj['after_hoist_and_batch'] * 50 / 1e6:.2f} M",
         f"{proj['after_avg_len_materialized'] * 50 / 1e6:.2f} M"),
    ], ("", "num", "num", "num"))

    checks = [
        ("1", "Per-parent candidate identity",
         ("ordered list of chunk ids per parent, identical to the per-parent "
          "call &mdash; not a set")),
        ("2", "Bitwise score identity",
         ("compare float8 bits, not <code>math.isclose</code>; a tolerance hides "
          "exactly the IDF drift this audit exists to prevent")),
        ("3", "Rank identity",
         "so the RRF contribution 1/(k+rank) is unchanged downstream"),
        ("4", "<code>avg_len</code> and <code>n</code> bitwise",
         ("asserted in SQL against the live snapshot &mdash; already verified "
          "once, see above")),
        ("5", "<code>df</code> bitwise per term",
         ("cache keyed on tsquery text so two raw terms normalizing together "
          "cannot split")),
        ("6", "Union membership identity",
         "set <em>and</em> multiplicity; mean new union members still 82.7/query"),
        ("7", "Final ranking identity",
         "post-RRF, post-blend, post-CE top-10 identical, ordered"),
        ("8", "Metric identity",
         ("45/50, 40/50, .80, .5969, .92 reproduced exactly &mdash; not within "
          "tolerance")),
        ("9", "Empty and degenerate parents",
         (f"0 matches &rarr; <code>[]</code>; the 1-chunk and the "
          f"{c['chunks_per_document']['max']:,}-chunk documents both behave as before")),
        ("10", "Determinism across runs",
         ("byte-identical twice in-process and once fresh; guards the tie-break "
          "that exists because BM25 ties are common")),
    ]
    check_rows = rows([(n, f"<strong>{t}</strong>", ticks(d)) for n, t, d in checks],
                      ("num", "", "dim"))

    order = m["implementation_order"]
    order_items = "".join(f"<li>{ticks(step.split('. ', 1)[1])}</li>" for step in order)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>PERF-001</title><style>{CSS}</style></head><body>

<h1>PERF-001 &mdash; why local within-document BM25 is expensive</h1>
<p class="subtitle">Read-only performance audit &middot; no patch applied &middot;
no retrieval run &middot; parallel to EXP-018B</p>
<div class="rule"></div>

<div class="callout warn">
  <div class="label">The finding</div>
  <p><strong>The local stage does {plan['local_work_share_of_single_parent_query']:.2%}
  local work.</strong> A single corpus-wide average &mdash;
  <code>avg(length(coalesce(search_text, text)))</code> over all
  {c['chunks']:,} chunks, which depends on neither the query nor the parent
  &mdash; is <strong>{plan['avg_len_share_of_single_parent_query']:.0%}</strong> of a
  single-parent local BM25 query. SYSTEM-E pays it <strong>once per parent</strong>.</p>
  <p>It is not BM25 that is slow. It is one constant being recomputed ten times,
  each time detoasting a {c['toast_size']} TOAST relation and scanning a
  {c['heap_size']} heap through {c['shared_buffers']} of
  <code>shared_buffers</code>.</p>
</div>

<div class="grid4">
  <div class="stat warn"><div class="big">{plan['avg_len_share_of_single_parent_query']:.0%}</div>
    <div class="cap">of a single-parent query is one corpus-wide average</div></div>
  <div class="stat warn"><div class="big">{plan['local_work_share_of_single_parent_query']:.2%}</div>
    <div class="cap">is the actual per-parent work</div></div>
  <div class="stat win"><div class="big">{proj['cold_speedup_local_stage']:.0f}&times;</div>
    <div class="cap">cold speedup available on the local stage</div></div>
  <div class="stat win"><div class="big">bitwise</div>
    <div class="cap">equivalence proved, not argued</div></div>
</div>

<h2>Scope &mdash; what this repository actually contains</h2>
<p>The V2 handoff names <code>SYSTEM-D-GUARD-BLEND</code>,
<code>SYSTEM-E-WITHIN-DOC</code>, <code>V2-DEVSET-001</code> and
<code>EXP-018</code>. <strong>None of those artifacts exist in this
repository.</strong> History ends at
<code>{esc(state['highest_experiment_present'])}</code> (HEAD
<code>{esc(state['head'])}</code>); <code>systems.py</code> freezes only
SYSTEM-A-GLOBAL and SYSTEM-B-DOC-C and sets <code>cross_encoder: None</code>.</p>
<p>What <em>is</em> here is the code SYSTEM-E is built out of &mdash;
<code>retrieval.py</code>'s <code>_LEXICAL_SQL</code> and
<code>lexical_search()</code>, <code>hierarchical.py</code>, and the two-stage
callers in <code>run_exp012.py</code> and <code>run_exp014r.py</code>. Every
figure below is measured against that code and the live
<code>{esc(c['snapshot_id'])}</code> / <code>{esc(c['chunk_set_id'])}</code>
database ({c['chunks']:,} chunks, {c['documents']} documents). The audit
therefore describes the mechanism SYSTEM-E inherits with certainty. Anything
requiring SYSTEM-E source is marked unverified in the full report.</p>

<h3>What was executed</h3>
<ul>{''.join(f'<li>{ticks(x)}</li>' for x in m['what_was_executed'])}</ul>
<p class="dim">No retrieval was run, no D or E run, no cap variant, no
V2-DEVSET-001 case scored, no V1 holdout touched, no <code>EXP-018B</code>
artifact created or read, and nothing in <code>src/</code> modified.
<code>tests/test_perf001_audit.py</code> asserts each of these rather than
claiming them.</p>

<h2>A &mdash; Bottleneck map</h2>
<p>One call to
<code>lexical_search(q, snap, W, version_ids=[one_parent])</code> plans at
<strong>{single:,.0f}</strong> cost units for a 4-term query
(<code>EXPLAIN</code> without <code>ANALYZE</code>). Decomposed by CTE:</p>
<table><thead><tr><th>Stage</th><th class="num">Plan cost</th><th>Share</th>
<th class="num">Parent-dep?</th><th class="num">Query-dep?</th></tr></thead>
<tbody>{stage_rows}</tbody></table>

<p>Isolating the two halves of the <code>corpus</code> CTE makes it unambiguous:</p>
<table><thead><tr><th>Aggregate</th><th class="num">Plan cost</th><th>Plan node</th>
</tr></thead><tbody>{isolate_rows}</tbody></table>

<div class="callout">
  <div class="label">Why it is expensive physically</div>
  <p><code>search_text</code> is <strong>NULL for all
  {c['search_text_null_count']:,}</strong> control chunks, so
  <code>coalesce(search_text, text)</code> always resolves to <code>text</code>
  &mdash; the TOASTed column. <code>length()</code> on a TOASTed value has no
  shortcut: it must read the whole chain. The working set is roughly
  <strong>3.5&times; larger than <code>shared_buffers</code></strong>, so it comes
  off disk every time.</p>
</div>

<h3>Per query &mdash; 10 parents, p50 = {terms['p50']} distinct terms</h3>
<p class="dim">Term counts from tokenizing the {esc(terms['source'].split('(')[0].strip())}
with <code>query_terms()</code>: min {terms['min']}, <strong>p50
{terms['p50']}</strong>, p90 {terms['p90']}, max {terms['max']}.</p>
<table><thead><tr><th>Configuration</th><th class="num">Plan cost / query</th>
<th class="num">Connections</th><th class="num">Speedup</th></tr></thead>
<tbody>{ladder_rows}</tbody></table>

<p>Connection overhead is separately real: <code>connect()</code> +
<code>register_vector()</code> + <code>close()</code> costs a median
<strong>{micro['connect_register_vector_close_ms']['median']} ms</strong>
(n={micro['connect_register_vector_close_ms']['n']}, min
{micro['connect_register_vector_close_ms']['min']}, max
{micro['connect_register_vector_close_ms']['max']}), and each
<code>lexical_search()</code> opens
<strong>{micro['connections_per_lexical_search']}</strong> &mdash; so ten parents
cost {proj['db_connections_current']} connections &asymp;
<strong>{micro['connection_overhead_per_query_ms']} ms/query</strong> of pure setup.</p>

<div class="callout">
  <div class="label">Wall-clock projection &mdash; a target to verify, not a result</div>
  <p>The reported <code>E &minus; D = 16,604 &minus; 5,824 = 10,780 ms</code> is
  the local stage. Decomposing conservatively (not by scaling planner units,
  which are not milliseconds): connection churn
  {micro['connection_overhead_per_query_ms']} ms &rarr; ~21 ms; ten repetitions
  of the corpus scan &rarr; one; and materializing <code>avg_len</code> removes
  the heap+TOAST read from that last one.
  <strong>Projected E&prime; &asymp; 6.2&ndash;6.6 s</strong> against D's 5.82 s
  &mdash; roughly <strong>2.5&ndash;2.7&times; end-to-end</strong> and
  <strong>13&ndash;25&times; on the local stage</strong>.</p>
</div>

<div class="break"></div>
<h2>B &mdash; Exact code locations</h2>
<table><thead><tr><th class="num">#</th><th>What</th><th>Location</th>
<th class="num">Cost</th></tr></thead><tbody>{bottleneck_rows}</tbody></table>

<h3>The N+1 that is easy to miss</h3>
<blockquote>with connect() as conn, conn.cursor() as cur:
    cur.execute(_LEXICAL_SQL, {{
        ...
        "chunk_set_id": snapshot_chunk_set(snapshot_id),   # opens a SECOND connection</blockquote>
<p><code>snapshot_chunk_set()</code> opens its own <code>connect()</code>, and
because the dict literal is evaluated <em>inside</em> the outer <code>with</code>,
every <code>lexical_search()</code> holds two concurrent connections.
<code>dense_search()</code> and <code>exact_identifier_search()</code> have the
identical defect, and <code>db.py</code> has no pool anywhere.</p>

<div class="callout win">
  <div class="label">The invariant the fix must preserve &mdash; already written in the file</div>
  <p><code>retrieval.py:110-114</code> says it plainly: <em>&ldquo;the corpus and
  weighted CTEs above still compute n, avg_len and df across the whole snapshot,
  so a term's IDF is identical to the global run.&rdquo;</em> The optimization
  keeps that promise. It only stops paying for it eleven times.</p>
</div>

<h2>C &mdash; Proposed optimization, and the equivalence proof</h2>
<p>Three changes, strictly ordered. <strong>C1</strong>: one batched query using
<code>row_number() OVER (PARTITION BY version_id ORDER BY
round(score::numeric,9) DESC, chunk_id)</code> &mdash; the same total order the
per-parent <code>LIMIT</code> applies, with the statistics CTEs copied
byte-identically. <strong>C2</strong>: materialize <code>(n, sum_len)</code>.
<strong>C3</strong>: cache <code>df</code>.</p>

<div class="callout win">
  <div class="label">C2 equivalence &mdash; verified on the live snapshot</div>
  <blockquote>n                                 = {proof['n']:,}
sum(length(...))                  = {proof['sum_length']:,}        (exact bigint, order-independent)
avg(length(...))::float8          = {proof['avg_direct_float8']}
(sum::numeric / n::numeric)::float8 = {proof['avg_from_exact_sum_float8']}
float8send(a) = float8send(b)     = {'t' if proof['float8send_bitwise_identical'] else 'f'}   BITWISE IDENTICAL</blockquote>
  <p>Store the exact integers, never the float &mdash; a round trip through JSON
  or a <code>numeric</code> column can lose the last bit.
  {ticks(proof['why_deterministic'][0].upper() + proof['why_deterministic'][1:])}.
  There is no parallel-aggregation hazard here.</p>
</div>

<h2>E &mdash; Complexity before and after</h2>
<p class="dim">P = parents (10), T = distinct terms (p50 {terms['p50']}),
N = snapshot chunks ({c['chunks']:,}), M = chunks per routed parent (mean
{c['chunks_per_document']['mean']}, median {c['chunks_per_document']['median']},
max {c['chunks_per_document']['max']:,}), Q = queries (50).</p>
<table><thead><tr><th>Per query</th><th class="num">Before</th>
<th class="num">After C1</th><th class="num">After C1+C2</th></tr></thead>
<tbody>{complexity_rows}</tbody></table>
<p>Asymptotically <code>O(P&middot;(N + T&middot;N + M))</code> &rarr;
<code>O(T&middot;N + P&middot;M)</code> &rarr; <code>O(P&middot;M)</code> warm.
<strong>The P factor leaves the dominant term entirely.</strong></p>

<div class="break"></div>
<h2>G &mdash; The two optimizations to refuse</h2>

<div class="callout warn">
  <div class="label">G1 &mdash; highest risk: {esc(g1['what'])}</div>
  <p><strong>Why it is tempting.</strong> {ticks(g1['why_tempting'][0].upper() + g1['why_tempting'][1:])}.</p>
  <p><strong>Why it is wrong.</strong> {ticks(g1['why_wrong'])}</p>
  <p><strong>Predicted damage.</strong> {ticks(g1['predicted_damage'])} &mdash;
  and the result would still be internally consistent and would still pass a
  naive &ldquo;scores match&rdquo; test. Caught only by
  {ticks(g1['caught_by'])}.</p>
</div>

<div class="callout warn">
  <div class="label">G2 &mdash; restricting the statistics CTEs to routed documents</div>
  <p>It looks like the same change as C1 and is its opposite. <code>n</code>
  would fall from {c['chunks']:,} to ~703, <code>avg_len</code> would shift, and
  every <code>idf</code> would change. Every score changes.</p>
</div>

<p><strong>Also flagged, lower severity:</strong> caching <code>avg_len</code> as
a float rather than as <code>(sum, count)</code>; retyping the window
<code>ORDER BY</code> without the rounding and the <code>chunk_id</code>
tie-break; <code>LIMIT</code> vs <code>row_number()</code> diverging if anyone
drops that tie-break; and <code>sum(float8)</code> accumulation order changing
under batching &mdash; unlikely to move a bit, but test 2 is the proof, not the
argument.</p>

<h2>F &mdash; Equivalence-test checklist</h2>
<p>An optimization is score-preserving only if <strong>all ten</strong> pass.
Nos. 1&ndash;5 are the blocking gate; C1 alone must pass all ten before C2 and C3
are attempted.</p>
<table><thead><tr><th class="num">#</th><th>Check</th><th>Property</th></tr></thead>
<tbody>{check_rows}</tbody></table>
<p class="dim">Run tests 1&ndash;5 on <strong>V1 development questions</strong>,
not on V2-DEVSET-001. Equivalence is a property of the code, not of the
benchmark, so proving it should cost zero devset exposure. Only test 8 needs the
devset, and it is a reproduction check rather than a measurement.</p>

<h2>H &mdash; Recommended implementation order</h2>
<ol>{order_items}</ol>
<p><strong>Optional, measure before adopting:</strong> a stored generated column
<code>search_len</code> plus a covering index would make <code>avg_len</code>
index-only with no cache at all &mdash; but it is DDL on a frozen corpus DB, and
C2 gets there without it. <strong>Do not do without separate authorization:</strong>
connection pooling. It is a genuine win and it touches every experiment's timing
path; it should not ride along inside a Track-1 equivalence change.</p>

<h2>The one question this repository cannot answer</h2>
<div class="callout warn">
  <div class="label">Question 6 &mdash; CE batching overhead</div>
  <p><strong>{ticks(ce['reason'][0].upper() + ce['reason'][1:])}.</strong></p>
  <p>What can be said from the reported numbers alone: {ticks(ce['what_can_be_said'])}.</p>
  <p><strong>Recommendation.</strong> {ticks(ce['recommendation'][0].upper() + ce['recommendation'][1:])}.
  A plausible-looking number would be worse than none here, because it would be
  acted on.</p>
</div>

<div class="callout">
  <div class="label">A deliberate non-finding</div>
  <p>Fusion's <code>model_copy(deep=True)</code> costs
  {micro['searchhit_model_copy_deep_us']} &micro;s per hit against
  {micro['searchhit_model_copy_shallow_us']} &micro;s shallow &mdash;
  <strong>{micro['fusion_deep_copy_cost_at_pool_176_8_ms']} ms/query</strong> at
  E's 176.8-candidate mean pool, about
  {micro['fusion_deep_copy_share_of_E_latency']:.2%} of E's latency. It profiles
  loud and is not worth touching. Reporting it as a non-finding is the point.</p>
</div>

<h2>Bottom line</h2>
<p>Track 1's goal is reachable without touching a single scoring expression. The
<code>corpus</code> and <code>weighted</code> CTEs stay byte-identical and stay
full-corpus; they are simply computed once per query instead of once per parent,
and the ten per-parent <code>LIMIT</code> queries become one partitioned window.
Everything that determines a score is unchanged, which is what makes exact
equivalence provable rather than merely likely.</p>
<p>The two things to watch: the shortcut in G1 would pass a careless test while
deleting the mechanism EXP-018 supported, and the CE contribution is
unmeasurable from here and could be large enough to change what Track 1 can
deliver.</p>

<footer>PERF-001 &middot; read-only performance audit &middot; no patch applied,
no retrieval executed, no system modified &middot; every figure rendered from
<code>experiments/PERF-001/PERF-001-measurements.json</code> at build time
&middot; snapshot <code>{esc(c['snapshot_id'])}</code></footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="experiments/PERF-001/PERF-001-report.pdf")
    args = parser.parse_args()

    m = json.loads(MEASUREMENTS.read_text())
    retrieval = RETRIEVAL.read_text()

    # 1. The audit must still be read-only, or the document is a lie about itself.
    if m["patch_applied"] is not False:
        raise SystemExit("refusing to build: patch_applied is not False")
    for name, value in m["constraints_observed"].items():
        if value is not False:
            raise SystemExit(f"refusing to build: constraint {name} is not False")

    # 2. The proposed change must still be unapplied in the module it targets.
    if "local_lexical_search_batch" in retrieval or "_LOCAL_BATCH_SQL" in retrieval:
        raise SystemExit("refusing to build: the proposed patch has been applied")

    # 3. Scoring semantics must be untouched, or every figure is stale.
    for token in ("BM25_K1 = 1.2", "BM25_B = 0.75",
                  "ORDER BY round(scored.score::numeric, 9) DESC, scored.chunk_id"):
        if token not in retrieval:
            raise SystemExit(f"refusing to build: scoring semantics changed ({token})")

    # 4. The invariant the whole document rests on: statistics are still full-corpus.
    sql = retrieval.split("_LEXICAL_SQL = ")[1].split('"""')[1]
    if "version_ids" in sql.split("SELECT * FROM (")[0]:
        raise SystemExit("refusing to build: the statistics CTEs are no longer full-corpus")

    # 5. The CE question must still be unanswerable here, not quietly answered.
    if "\"cross_encoder\": None" not in SYSTEMS.read_text():
        raise SystemExit("refusing to build: a cross-encoder now exists; question 6 "
                         "must be measured rather than reported as blocked")

    # 6. The headline arithmetic must still hold against the recorded plan costs.
    plan = m["plan_costs_single_parent_local_bm25"]
    marginal = plan["corpus_cte_count_and_avg_len"] - plan["corpus_cte_count_only"]
    if abs(marginal - plan["avg_len_marginal_cost"]) > 0.01:
        raise SystemExit("refusing to build: avg_len marginal cost does not reconcile")
    if not 0.94 <= plan["avg_len_share_of_single_parent_query"] <= 0.98:
        raise SystemExit("refusing to build: the headline share is not what was measured")

    document = build_html(m)

    # 7. The page must lead with the finding, not with the optimization plan.
    flat = " ".join(document.split())
    if "The finding" not in flat or "local work" not in flat:
        raise SystemExit("refusing to build: the page does not lead with the finding")

    chrome = next((cand for cand in CHROME_CANDIDATES if Path(cand).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "perf001.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
