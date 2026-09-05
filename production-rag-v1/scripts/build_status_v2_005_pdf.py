#!/usr/bin/env python3
"""Render the SYSTEM-H blocker plus the BM25 control run as one shareable PDF.

The two halves must not be allowed to blur into each other. SYSTEM-H has no
result and is not failed; BM25 has a result and is not a release decision.
A reader who came away thinking 0.375 was SYSTEM-H's number, or that SYSTEM-H
had been measured and lost, would have the situation exactly backwards, so the
page states both negatives explicitly and a build gate enforces it.

Every figure is read from STATUS-V2-005.json at build time. Ten gates refuse
the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-005.json"
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
h3 { font-size: 9.6pt; margin: 10pt 0 4pt; }
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


def rows(items) -> str:
    return "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in items)


def build_html(d: dict) -> str:
    H, U, T, M, G = d["system_h"], d["unblock"], d["threshold"], d["bm25"], d["gates"]
    mx = M["metrics"]

    req_rows = rows([
        (f"<span class='num'>{r['n']}</span>", esc(r["item"]),
         " · ".join(f"<span class='{'hot' if c in ('PROVENANCE_GAP',) else ('ok' if c == 'AVAILABLE_LOCAL' else 'dim')}'>{esc(c)}</span>"
                    for c in r["cls"]))
        for r in U["requirements"]])

    slice_rows = rows([
        (esc(s), f"<span class='num'>{v['cases']}</span>", f"<span class='num'>{v['gold_spans']}</span>",
         f"<span class='num'>{v['case_hit_at_10']:.3f}</span>", f"<span class='num'>{v['micro_MRR']:.4f}</span>",
         f"<span class='num'>{v['span_recall_at_10']:.4f}</span>")
        for s, v in mx["per_slice"].items()])

    hash_rows = rows([(ticks(k.replace("_", " ")), f"<span class='mono'>{esc(v)}</span>")
                      for k, v in d["hashes"].items()])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>SYSTEM-H blocker and BM25 control</title><style>{CSS}</style></head><body>
<h1>SYSTEM-H blocker &amp; NATQ-002 BM25 control</h1>
<p class="subtitle">SYSTEM-H not executable &middot; 0 validation runs consumed &middot;
BM25 control scored on 40 validation cases &middot; {G['passed']}/{G['total']} integrity gates &middot;
head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout warn">
<p><strong>Two results here, and neither is what it might look like.</strong></p>
<p><strong>SYSTEM-H has no result and did not fail.</strong> Its status is
<code>{esc(H['status'])}</code> and <code>SUPPORTED</code> is <strong>null, not false</strong>. This is an
execution and provenance blocker. Nothing about SYSTEM-H's quality was measured, and
{H['runs_consumed']} of its preregistered validation runs were consumed.</p>
<p><strong>The {mx['case_hit_at_10']:.3f} below is BM25's number, not SYSTEM-H's.</strong> It is a control
measurement with no pass/fail threshold. The approved floors belong to SYSTEM-H and were deliberately not
applied to a comparator.</p>
</div>

<div class="grid">
<div class="card"><div class="big">{H['runs_consumed']}</div><div class="cap">SYSTEM-H runs consumed</div></div>
<div class="card"><div class="big">null</div><div class="cap">SYSTEM-H supported</div></div>
<div class="card"><div class="big">{mx['case_hit_at_10']:.3f}</div><div class="cap">BM25 case_hit@10</div></div>
<div class="card"><div class="big">{d['reserve_access_log_bytes']}</div><div class="cap">reserve log bytes</div></div>
<div class="card"><div class="big">{G['passed']}/{G['total']}</div><div class="cap">integrity gates</div></div>
</div>

<h2>1 &mdash; Why SYSTEM-H cannot be scored</h2>
<p>SYSTEM-H-V2-DEV-CANDIDATE is an architecture <em>record</em>, not runnable code. Nine requirements were
classified; eight are transfer problems, and one is not.</p>
<table><thead><tr><th class="num">#</th><th>Requirement</th><th>Classification</th></tr></thead>
<tbody>{req_rows}</tbody></table>
<div class="callout">
<p><strong>Item 4 is the one copying cannot fix.</strong> The EXP-019A retrieval prior is
<em>score-determining</em>, and its originals are absent from every fetched ref &mdash;
<code>PROVENANCE-GAP-001</code> holds them only as relayed conversation values. Its behaviour <em>is</em>
described well enough to re-implement, and that is precisely the trap: a re-implementation would run and
produce numbers that could never be verified against the thing they claim to reproduce, because that thing
does not exist.</p>
<p>The preregistration makes a run valid only if <code>score_determining_hash</code> equals
<code>{esc(H['hash_required'])}</code> at run time, and that hash covers fields that would be invented
rather than reproduced. Reproduction status: <strong>{esc(H['hash_reproduced'])}</strong>. No field was
invented to force a match, and no new configuration was given SYSTEM-H's identity.</p>
</div>
<p><strong>No requirement needs a CUDA host.</strong> SYSTEM-H is CPU-executable in principle &mdash; it is
provenance, not hardware, that blocks it. Two legitimate paths remain, and reconstruction is not one of
them: a rebuild from the written description takes a new identity and inherits none of SYSTEM-H's claims.</p>

<h2>2 &mdash; Threshold decision, recorded without touching the preregistration</h2>
<p>Decision <strong>{esc(T['decision'])}</strong> &middot; thresholds changed
<strong>{esc(T['changed'])}</strong> &middot; validation runs consumed before the decision
<strong>{T['runs_before']}</strong>.</p>
<table><thead><tr><th>Floor</th><th class="num">Value</th><th>Scope / definition / population</th></tr></thead>
<tbody>
<tr><td>case_hit@10 PASS</td><td class="num">{T['floors']['case_hit_at_10_pass_floor']}</td><td>unchanged</td></tr>
<tr><td>case_hit@10 FAIL</td><td class="num">{T['floors']['case_hit_at_10_fail_floor']}</td><td>unchanged</td></tr>
</tbody></table>
<p>{esc(T['rationale'])}</p>
<p>The decision is a <strong>separate artifact referencing the preregistration by SHA</strong>
(<code class="mono">{esc(T['prereg_sha'])}</code>) rather than an edit to it. That keeps the
preregistration's own hash and its &ldquo;written before any scoring&rdquo; claim independently checkable
&mdash; editing it to improve the rationale would have destroyed exactly the property that makes it
evidence. Preregistration unmodified: <strong>{esc(T['prereg_unmodified'])}</strong>.</p>

<h2>3 &mdash; BM25 control ({esc(M['system_id'])})</h2>
<p>Pure BM25 over <code>cs_v1_control</code>, k1={M['params']['k1']}, b={M['params']['b']}, depth
{M['params']['top_k']}, randomness: {esc(M['params']['randomness'])}. Scored on the
<strong>{esc(M['partition'])} partition only</strong> &mdash; {M['cases']} cases, {M['spans']} gold spans,
{M['ranked_rows']} ranked rows persisted.</p>
<p class="dim">Excluded by construction: {esc(', '.join(M['excluded']))}.</p>
<table><thead><tr><th>Metric</th><th class="num">Value</th></tr></thead><tbody>
<tr><td>case_hit@10</td><td class="num">{mx['case_hit_at_10']:.4f}</td></tr>
<tr><td>micro_MRR</td><td class="num">{mx['micro_MRR']:.4f}</td></tr>
<tr><td>case_full_coverage@10</td><td class="num">{mx['case_full_coverage_at_10']:.4f}</td></tr>
<tr><td>span_recall@10</td><td class="num">{mx['span_recall_at_10']:.4f}</td></tr>
<tr><td>case_hit@1</td><td class="num">{mx['case_hit_at_1']:.4f}</td></tr>
<tr><td>latency p50 / p95</td><td class="num">{mx['latency_p50_ms']:.0f} ms / {mx['latency_p95_ms']:.0f} ms</td></tr>
</tbody></table>
<h3>Per authoring slice</h3>
<table><thead><tr><th>Slice</th><th class="num">Cases</th><th class="num">Spans</th>
<th class="num">case_hit@10</th><th class="num">micro_MRR</th><th class="num">span_recall@10</th></tr></thead>
<tbody>{slice_rows}</tbody></table>
<div class="callout">
<p><strong>A weak floor is the useful outcome here.</strong> {mx['case_hit_at_10']:.3f} is the expected
shape for pure BM25 against conversational questions, and it matters for two reasons: it leaves the future
paired test real headroom to detect an effect, and it confirms the approved 0.80 floor is a demanding bar
rather than one a keyword baseline already clears. Decision recorded: <strong>{esc(M['decision'])}</strong>
&mdash; {esc(M['decision_note'])}</p>
</div>
<p>The per-case hit vector is persisted in fixed case-id order as the <strong>immutable comparator input</strong>
for a future SYSTEM-H paired bootstrap over cases.</p>

<h2>4 &mdash; Integrity</h2>
<p>{G['passed']} of {G['total']} post-run gates pass. The benchmark, split, lock and preregistration hashes
were verified <em>before</em> the run and re-verified <em>after</em> it, unchanged in both directions.</p>
<ul>{''.join(f'<li>{ticks(g)}</li>' for g in G['list'])}</ul>

<h3>Pinned hashes</h3>
<table><thead><tr><th>Artifact</th><th>SHA256</th></tr></thead><tbody>{hash_rows}</tbody></table>

<h2>5 &mdash; Constraints held</h2>
<table><thead><tr><th>Constraint</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='ok'>{esc(v)}</span>") for k, v in d['constraints'].items()])}
</tbody></table>

<div class="foot">Generated from STATUS-V2-005.json, itself assembled from the run records at
<code>{esc(d['head'])}</code>. Reserve access log: {d['reserve_access_log_bytes']} bytes, 0 entries. Ten
build gates refuse this page if a constraint is violated.</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-005.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    H, T, M, G = d["system_h"], d["threshold"], d["bm25"], d["gates"]

    # 1. Every forbidden action must still be false.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")
    # 2. SYSTEM-H must not be presented as measured or failed.
    if H["supported"] is not None:
        raise SystemExit("refusing to build: SYSTEM-H SUPPORTED is not null")
    if H["runs_consumed"] != 0 or H["scored"] or H["reserve_accessed"]:
        raise SystemExit("refusing to build: SYSTEM-H shows consumed runs, a score, or reserve access")
    # 3. The score-determining hash must not be claimed as reproduced.
    if H["hash_reproduced"] is not False:
        raise SystemExit("refusing to build: score_determining_hash is claimed reproduced")
    # 4. The threshold decision must be an approval that changed nothing.
    if T["decision"] != "APPROVED_PRE_RUN" or T["changed"] is not False or T["runs_before"] != 0:
        raise SystemExit("refusing to build: the threshold decision is not a clean pre-run approval")
    if T["prereg_unmodified"] is not True:
        raise SystemExit("refusing to build: the preregistration was modified")
    # 5. BM25 must carry no decision and must not be scored on reserve.
    if M["decision"] is not None:
        raise SystemExit("refusing to build: the BM25 control has been given a pass/fail decision")
    if M["partition"] != "validation":
        raise SystemExit("refusing to build: BM25 was scored on something other than validation")
    # 6. The reserve must be untouched.
    if d["reserve_access_log_bytes"] != 0:
        raise SystemExit("refusing to build: the reserve access log is not empty")
    # 7. Integrity must be complete.
    if not G["all_passed"] or G["passed"] != G["total"]:
        raise SystemExit("refusing to build: an integrity gate failed")
    # 8. Counts must reconcile.
    if M["ranked_rows"] != M["cases"] * M["params"]["top_k"]:
        raise SystemExit("refusing to build: ranked rows != cases x depth")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 9. Both negatives must be stated, or a reader will conflate the two halves.
    for phrase in ("has no result and did not fail", "is BM25's number, not SYSTEM-H's"):
        if phrase.lower() not in flat.lower():
            raise SystemExit(f"refusing to build: the page omits {phrase!r}")
    # 10. The provenance blocker must not be softened into a hardware excuse.
    if "provenance, not hardware" not in flat:
        raise SystemExit("refusing to build: the page does not identify provenance as the blocker")

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
