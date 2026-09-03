#!/usr/bin/env python3
"""Render one consolidated results PDF covering EXP-NULL through EXP-006.

Every figure is read from the experiment artifacts at build time, so the
consolidated report cannot drift from the per-experiment ones. Regenerate the
inputs first if anything changed:

    python scripts/analyze_experiments.py
    python scripts/analyze_exp005.py
    python scripts/run_exp006.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHROME_CANDIDATES = (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
)

CSS = """
@page { size: Letter; margin: 17mm 15mm 15mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.6pt;
  line-height: 1.48; color: #16181c; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-size: 22pt; line-height: 1.12; margin: 0 0 4pt; letter-spacing: -0.5pt; }
h2 { font-size: 12.5pt; margin: 18pt 0 6pt; padding-bottom: 4pt;
     border-bottom: 1.2pt solid #16181c; letter-spacing: -0.2pt; }
h3 { font-size: 10pt; margin: 11pt 0 3pt; }
p { margin: 0 0 6pt; }
code, .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 8.3pt; background: #eef0f3; padding: 0.5pt 3pt; border-radius: 2pt; }
.subtitle { font-size: 10.5pt; color: #52565d; margin: 0 0 11pt; }
.rule { height: 2.5pt; background: #16181c; margin: 0 0 13pt; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 11pt; font-size: 8.5pt; }
th { text-align: left; font-weight: 600; padding: 4.5pt 6pt; background: #16181c; color: #fff; }
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.b { font-weight: 700; }
.bad { color: #8a1c1c; font-weight: 700; }
.good { color: #14532d; font-weight: 700; }
.dim { color: #6f747b; }
.callout { border-left: 2.5pt solid #16181c; background: #f6f7f9; padding: 7pt 10pt; margin: 9pt 0 11pt; }
.callout.warn { border-left-color: #8a1c1c; background: #fdf5f5; }
.callout p:last-child { margin-bottom: 0; }
.callout .label { font-size: 7.3pt; letter-spacing: 0.7pt; text-transform: uppercase;
  color: #52565d; font-weight: 700; margin-bottom: 3pt; }
.callout.warn .label { color: #8a1c1c; }
ol, ul { margin: 0 0 7pt; padding-left: 14pt; } li { margin-bottom: 3.5pt; }
.q { margin-bottom: 7pt; break-inside: avoid; }
.q .t { display: block; font-weight: 700; margin-bottom: 1pt; }
.grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10pt; margin-bottom: 4pt; }
.stat { border: 0.8pt solid #dde0e4; padding: 7pt 9pt; border-radius: 3pt; }
.stat .big { font-size: 16pt; font-weight: 700; line-height: 1.1; letter-spacing: -0.5pt; }
.stat .cap { font-size: 7.6pt; color: #52565d; margin-top: 2pt; }
.arc { border: 0.8pt solid #dde0e4; border-radius: 3pt; padding: 8pt 10pt; margin: 8pt 0 10pt;
  font-size: 8.6pt; background: #fafbfc; }
.arc b { display: inline-block; min-width: 108pt; }
footer { margin-top: 15pt; padding-top: 7pt; border-top: 0.6pt solid #dde0e4;
  font-size: 7.8pt; color: #6f747b; }
.avoid { break-inside: avoid; page-break-inside: avoid; }
.pb { break-before: page; page-break-before: always; }
"""


def load(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def build_html() -> str:
    summary = load("experiments/summary.json")
    null = load("experiments/EXP-NULL/results.json")
    e5 = load("experiments/EXP-005/paired-analysis.json")
    dist = load("experiments/EXP-005/chunk-distribution.json")
    e6 = load("experiments/EXP-006/results.json")

    s = summary["experiments"]
    e5c = e5["configurations"]
    e6c = e6["configurations"]
    sets = {d["chunker"]: d for d in dist["chunk_sets"]}

    def v1_row(label, key, note=""):
        r = s[key]
        return (f"<tr><td>{label}{note}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
                f"<td class='num'>{r['cases_fully_recalled']}/{r['cases']}</td>"
                f"<td class='num'>{r['spans_found']}/{r['spans_expected']}</td>"
                f"<td class='num'>{r['document_level_recall']:.3f}</td></tr>")

    v1_rows = (
        "<tr class='bad'><td>EXP-000 lexical — <em>as shipped</em></td><td class='num'>0.000</td>"
        "<td class='num'>0/20</td><td class='num'>0/22</td><td class='num'>0.000</td></tr>"
        + v1_row("EXP-000 lexical — BM25 (fixed)", "EXP-000 lexical (BM25)")
        + v1_row("EXP-001 dense (LSA substitute)", "EXP-001 dense (LSA)")
        + v1_row("EXP-002 hybrid interleave", "EXP-002 hybrid interleave")
        + v1_row("EXP-003 RRF <span class='mono'>rrf_k=60</span>", "EXP-003 RRF rrf_k=60")
    )
    best = summary["exp003_sweep"]["pool100-rrfk60"]
    v1_rows += (f"<tr><td>EXP-003 RRF pool 100, <span class='mono'>rrf_k=60</span> "
                f"<span class='dim'>(tuned on eval set)</span></td>"
                f"<td class='num'>{best['macro_span_recall']:.3f}</td>"
                f"<td class='num'>{best['cases_fully_recalled']}/20</td>"
                f"<td class='num'>13/22</td><td class='num'>0.818</td></tr>")

    e5_rows = ""
    for label, key in (("EXP-000 control (v1 chunker)", "EXP-000_control"),
                       ("EXP-005A bounded (v2)", "EXP-005A_bounded"),
                       ("EXP-005B technical (v3)", "EXP-005B_technical")):
        r = e5c[key]
        comp = e5["paired_comparisons"].get(f"EXP-000_control -> {key}")
        moved = "—" if comp is None else f"{len(comp['rescued'])} / {len(comp['regressed'])}"
        e5_rows += (f"<tr><td>{label}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
                    f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                    f"<td class='num'>{r['document_recall']:.3f}</td><td class='num'>{moved}</td></tr>")

    e6_labels = {"EXP-006A": "A — control chunking, plain", "EXP-006B": "B — control chunking, enriched",
                 "EXP-006C": "C — bounded chunking, plain", "EXP-006D": "D — bounded chunking, enriched"}
    e6_rows = ""
    for key, label in e6_labels.items():
        r = e6c[key]
        a = r["spans_absent_from_top"]
        e6_rows += (f"<tr><td>{label}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
                    f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td>"
                    f"<td class='num'>{r['document_recall']:.3f}</td><td class='num'>{r['mrr']:.3f}</td>"
                    f"<td class='num'>{a['10']}</td><td class='num'>{a['300']}</td></tr>")

    e6_pairs = ""
    for name, c in e6["paired_results"].items():
        cls = " class='bad'" if name.startswith("A->B") else ""
        e6_pairs += (f"<tr><td>{name}</td><td class='num'{cls}>{c['macro_recall_delta']:+.3f}</td>"
                     f"<td>{', '.join(c['rescued']) or '—'}</td>"
                     f"<td>{', '.join(c['regressed']) or '—'}</td>"
                     f"<td class='num'>{c['net_rescued']:+d}</td></tr>")

    ctrl_dist = sets["chunker_v1_control"]
    v2_dist = sets["chunker_v2_bounded"]

    an003 = ""
    for key, label in e6_labels.items():
        sp = e6c[key]["cases"]["AN-003"]["spans"][0]
        rank = sp["rank"] if sp["rank"] else "—"
        cls = " class='good'" if sp["rank"] else ""
        an003 += (f"<tr><td>{label}</td><td class='num'{cls}>{rank}</td>"
                  f"<td>{'yes' if sp['within']['300'] else 'no'}</td>"
                  f"<td class='num'>{sp['doc_rank']}</td></tr>")

    expl = e6["exploratory_field_ablation"]["configurations"]
    ex_rows = "".join(
        f"<tr><td>{k}</td><td>{r['description']}</td><td class='num'>{r['macro_span_recall']:.3f}</td>"
        f"<td class='num'>{r['cases_fully_recalled']}/{r['cases_total']}</td></tr>"
        for k, r in expl.items()
    )

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Production RAG Results</title><style>{CSS}</style></head><body>

<h1>Production RAG — Complete Results</h1>
<p class="subtitle">An evaluation-first retrieval baseline over 202 official OpenAI and
Anthropic documentation pages. Every hypothesis tested, including the two that failed.</p>
<div class="rule"></div>

<div class="callout warn">
  <div class="label">What this project has actually established</div>
  <p>Two architectural hypotheses were diagnosed, then tested with controlled interventions,
  and <strong>both were falsified</strong>. Retrieval did not improve because the diagnoses
  were wrong — and the value here is that the measurements say so plainly.</p>
  <p>The closed-book control <strong>never ran</strong> (no generation credential, provider
  host egress-blocked), so the project's primary question — does retrieval beat what the
  model already knows? — remains <strong>unanswered</strong>.</p>
</div>

<div class="grid3 avoid">
  <div class="stat"><div class="big">0.000 &rarr; 0.475</div>
    <div class="cap">Lexical baseline, before and after diagnosing why it retrieved nothing</div></div>
  <div class="stat"><div class="big">0 rescued</div>
    <div class="cap">Questions recovered by bounding chunk size (EXP-005), despite a 16,096
    &rarr; 1,999 char cut</div></div>
  <div class="stat"><div class="big">&Delta; 0.000</div>
    <div class="cap">Macro recall change from contextual enrichment, isolated (EXP-006 A&rarr;B)</div></div>
</div>

<h3>The investigation, in order</h3>
<div class="arc">
<b>Initial belief</b> the shipped lexical baseline works &rarr; it returned <b>nothing at all</b><br>
<b>Fix</b> BM25 over the same index &rarr; 0.000 &rarr; 0.475<br>
<b>Diagnosis 1</b> oversized chunks hide evidence &rarr; <b>EXP-005: 0 rescued. Falsified.</b><br>
<b>Diagnosis 2</b> missing structural context &rarr; <b>EXP-006: &Delta;0.000. Falsified.</b><br>
<b>Surviving</b> BM25 cannot bridge the question/document vocabulary gap &rarr; untested
</div>

<h2>Setup</h2>
<table>
<tr><td style="width:34%">Corpus</td><td>202 documents / 14,209 chunks — Anthropic 139 docs
(12,028 chunks), OpenAI 63 docs (2,181 chunks)</td></tr>
<tr><td>Golden set</td><td>22 cases: 20 retrieval-scored + 2 abstain controls; 22 evidence spans</td></tr>
<tr><td>Evidence anchoring</td><td><span class="mono">(version_id, section_path, char_start, char_end)</span>
— never chunk IDs, so re-chunking cannot invalidate the benchmark</td></tr>
<tr><td>Retrieval</td><td>BM25, <span class="mono">k1={e6['bm25_config']['k1']}</span>,
<span class="mono">b={e6['bm25_config']['b']}</span>, <span class="mono">simple</span> config,
<span class="mono">top_k=10</span> throughout</td></tr>
<tr><td>Closed-book control</td><td class="bad">{null['status']} — {null['blocked_reason'][:90]}…</td></tr>
</table>

<h2>V1 — retrieval methods (EXP-000 … EXP-003)</h2>
<table>
<thead><tr><th>Experiment</th><th class="num">macro recall</th><th class="num">fully recalled</th>
<th class="num">spans</th><th class="num">doc recall</th></tr></thead>
<tbody>{v1_rows}</tbody></table>

<div class="q"><span class="t">The shipped lexical baseline retrieved nothing at all.</span>
<span class="mono">websearch_to_tsquery</span> ANDs every token, so a 16-word question required
all 16 tokens inside one chunk. Zero hits on all 20 questions. Replaced with BM25 over the
same TSVECTOR/GIN index.</div>

<div class="q"><span class="t">Lexical beat the available dense retriever, and hybrid interleave was worse than lexical alone.</span>
BM25 0.475 vs LSA 0.300; switching to dense regressed 5 of 20 questions. Interleave scored
0.450 — below lexical. <span class="dim">The dense retriever is an offline TF-IDF+SVD
substitute, not a pretrained model; this says nothing about dense retrieval generally.</span></div>

<div class="q"><span class="t">RRF's gain over lexical is partial credit, not a win.</span>
Per question it is 1 rescued / 1 regressed — a wash. It regressed OA-004, whose evidence sits
at lexical rank 5 and dense rank 61; fusion averaged it to rank 13, outside k.</div>

<div class="q"><span class="t">Every configuration hit the same ceiling.</span>
Document-level recall is 0.818 for lexical, interleave and RRF alike, against span recall of
0.455–0.500. Of 12 missed spans, 8 had the correct document in the top 10. That gap set up
the next two experiments.</div>

<h2 class="pb">EXP-005 — is chunk granularity the bottleneck?</h2>
<p><strong>Hypothesis:</strong> if oversized chunks hide evidence, bounding chunk size should
move span recall toward the 0.818 document ceiling.</p>

<table>
<thead><tr><th>Chunker</th><th class="num">chunks</th><th class="num">mean</th><th class="num">p90</th>
<th class="num">max</th><th class="num">&gt;2000 chars</th></tr></thead>
<tbody>
<tr><td>v1 control</td><td class="num">{ctrl_dist['total_chunks']:,}</td>
<td class="num">{ctrl_dist['mean_chars']:,}</td><td class="num">{ctrl_dist['p90_chars']:,}</td>
<td class="num b">{ctrl_dist['max_chars']:,}</td><td class="num">{ctrl_dist['over_2000']:,}</td></tr>
<tr><td>v2 bounded</td><td class="num">{v2_dist['total_chunks']:,}</td>
<td class="num">{v2_dist['mean_chars']:,}</td><td class="num">{v2_dist['p90_chars']:,}</td>
<td class="num b">{v2_dist['max_chars']:,}</td><td class="num good">{v2_dist['over_2000']}</td></tr>
</tbody></table>

<table>
<thead><tr><th>Configuration</th><th class="num">macro recall</th><th class="num">fully recalled</th>
<th class="num">doc recall</th><th class="num">rescued / regressed</th></tr></thead>
<tbody>{e5_rows}</tbody></table>

<div class="callout warn">
  <div class="label">Falsified</div>
  <p>The intervention was real — the corpus maximum fell from 16,096 to 1,999 characters and
  all 3,069 over-2,000 chunks disappeared — and it rescued <strong>zero</strong> questions.
  Across 22 spans it improved 8 ranks and worsened 9, and <strong>not one</strong> previously
  unreachable span became reachable.</p>
  <p>The case that motivated the hypothesis, AN-003, went from 1.65% to 4.79% of its chunk —
  a 2.9× improvement on exactly the diagnosed quantity — and remained unretrieved.</p>
</div>

<div class="q"><span class="t">Smaller chunks also cost real ranks.</span>
AN-002 fell from rank 27 to 172 when splitting cut query-term coverage in its chunk from
12/13 to 7/13. The control's oversized chunks were accidentally <em>helping</em> a
bag-of-words retriever by aggregating co-occurring terms.</div>

<div class="q"><span class="t">V3's +3 was confounded.</span>
It changed boundaries <em>and</em> prepended structural context to the indexed text, and its
document recall rose to 0.900 when a pure chunking change should have left it flat. That
confound is what EXP-006 was built to resolve.</div>

<h2>EXP-006 — is it the structural context?</h2>
<p>A 2×2. B and D are row-for-row copies of A and C — <strong>0</strong> boundary differences,
<strong>0</strong> body differences — so an A&rarr;B difference cannot be a chunking difference.
The canonical chunk body is never mutated; the header lives in a separate
<span class="mono">search_text</span> column, because a citation must quote real source text.</p>

<table>
<thead><tr><th>Configuration</th><th class="num">macro recall</th><th class="num">fully recalled</th>
<th class="num">doc recall</th><th class="num">MRR</th><th class="num">absent@10</th>
<th class="num">absent@300</th></tr></thead>
<tbody>{e6_rows}</tbody></table>

<table>
<thead><tr><th>Comparison</th><th class="num">&Delta; macro</th><th>rescued</th><th>regressed</th>
<th class="num">net</th></tr></thead>
<tbody>{e6_pairs}</tbody></table>

<div class="callout warn">
  <div class="label">Falsified</div>
  <p>A&rarr;B is the comparison that isolates enrichment, and it moved macro recall by
  <strong>exactly zero</strong>. Its single rescue (AN-004, rank 12&rarr;7) crossed the cutoff
  while its BM25 score <em>fell</em> — competitors merely lost more. Its regression (AN-005,
  4&rarr;18) is large.</p>
  <p><strong>Mechanism:</strong> enrichment inflates document frequency. Writing
  <span class="mono">Provider: anthropic</span> into all 12,028 Anthropic chunks took that term
  from df 3,289 to 12,028 (+266%); <span class="mono">OpenAI</span> 366 &rarr; 2,185 (+497%).
  BM25 weights by <span class="mono">ln(1+(N−df+0.5)/(df+0.5))</span>, so a constant field
  repeated everywhere attacks the very signal it adds. Across all 22 spans enrichment supplied
  a query term to only <strong>3</strong>, and in <strong>zero</strong> cases a discriminative one.</p>
</div>

<h3>Exploratory: which header fields matter <span class="dim">(dev-set selected, not held out)</span></h3>
<table>
<thead><tr><th>Variant</th><th>Header fields</th><th class="num">macro recall</th><th class="num">fully recalled</th></tr></thead>
<tbody>
<tr><td>A</td><td>none (baseline)</td><td class="num">0.475</td><td class="num">9/20</td></tr>
{ex_rows}
<tr><td>B</td><td>provider + document + section</td><td class="num">0.475</td><td class="num">9/20</td></tr>
</tbody></table>
<p>The ordering matches the mechanism exactly: the more constant the field, the more df
inflation and the worse the result. Only the section path — which actually varies chunk to
chunk — carries information, and it improves the baseline by <strong>one case</strong>.</p>

<h2 class="pb">AN-003 — the canonical failure, across every experiment</h2>
<p><strong>Query:</strong> "How many requests can a single Message Batches create request
contain at most?" &nbsp;<strong>Evidence:</strong> <em>"There is a limit of 100,000 messages in
a single request."</em></p>
<table>
<thead><tr><th>Configuration</th><th class="num">rank</th><th>reachable at depth 300?</th>
<th class="num">document rank</th></tr></thead>
<tbody>{an003}</tbody></table>
<p>Enrichment built a lexical bridge for the first time — rank 74 under D, having been absent
at depth 300 everywhere else — because the header supplied <span class="mono">Batches</span>.
Still nowhere near k=10. The terms that would actually identify this evidence appear nowhere
in the chunk that answers it: <span class="mono">contain</span> (df 111),
<span class="mono">most</span> (533), <span class="mono">many</span> (564), and
<span class="mono">requests</span>, which never matches the body's singular
<span class="mono">request</span> because the deliberately unstemmed
<span class="mono">simple</span> configuration cannot bridge it.</p>
<p>This is a <strong>vocabulary mismatch</strong>, and it is why both architectural
hypotheses failed.</p>

<h2>Limitations — read before quoting any number</h2>
<ol>
<li><strong>The closed-book control never ran.</strong> No generation credential and the
provider host is egress-blocked. Retrieval is uncalibrated against what the model already
knows — the project's primary question is still open.</li>
<li><strong>Dense retrieval has not been tested.</strong> The dense numbers use an offline
TF-IDF+SVD substitute; both the sentence-transformer host and the OpenAI embedding endpoint
are egress-blocked. All dense, hybrid and RRF figures are lower bounds, and nothing here
supports "BM25 beats dense retrieval".</li>
<li><strong>n = 20 is development scale.</strong> One case is 5 points of macro recall. Every
EXP-005/006 movement is 1–2 cases. Nothing is statistically significant; the paired per-case
tables are the trustworthy part.</li>
<li><strong>Some numbers are eval-set tuned</strong> — the RRF pool-100 configuration and the
EXP-006 field ablation. Both are labelled where they appear. BM25 <span class="mono">k1</span>
and <span class="mono">b</span> were never swept.</li>
<li><strong>V3's largest rescue is still unexplained.</strong> AN-010 (rank 49&rarr;1) is
reproduced by no EXP-006 configuration, so it likely came from V3's table row-group splitting,
which was never isolated.</li>
<li><strong>Corpus skew:</strong> 139 Anthropic documents to 63 OpenAI, because OpenAI's own
documentation hosts were unreachable and only its public repositories could be used.</li>
<li><strong>The golden set is single-author.</strong> Anchors were mechanically verified
against source, but no second annotator reviewed them.</li>
</ol>

<h2>What the data justifies next</h2>
<p><strong>A real pretrained embedding model.</strong> Both lexical hypotheses have been
tested and rejected by controlled intervention. The surviving diagnosis — vocabulary mismatch
— is exactly what semantic retrieval addresses, and AN-003 is its canonical test case: an
answer whose discriminative query terms appear nowhere in the text that answers it. Blocked
only on network egress.</p>
<p><strong>Secondary and cheap:</strong> isolate V3's table row-group mechanism, the last
unexplained rescue; and add stemming as a <em>third ranked list</em> rather than a
replacement, so identifier precision survives while plural/singular matching is recovered.</p>
<p><strong>Still not justified:</strong> a reranker — AN-003 is absent from depth 300 in three
of four configurations; reranking reorders candidates, it cannot retrieve missing evidence.
Nor freezing enrichment, nor a larger k, nor a confidence threshold.</p>
<p><strong>Baseline decision:</strong> control chunking, unenriched, BM25. Neither new chunker
nor enrichment earned promotion.</p>

<footer>
Generated from experiments/*.json by scripts/build_consolidated_pdf.py.
Git commit {(e6.get('git_commit') or 'unknown')[:12]}. EXP-006 config hash {e6['config_hash'][:16]}.
Corpus snapshot snap_689e3363…. Per-experiment reports: EXP-005-rechunking.pdf,
EXP-006-enrichment-ablation.pdf. Raw provider documentation is not redistributed; published
results carry evidence anchors, ranks and scores with retrieved text replaced by a content hash.
</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/production-rag-complete-results.pdf")
    args = parser.parse_args()
    html = build_html()
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "consolidated.html"
        src.write_text(html, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
