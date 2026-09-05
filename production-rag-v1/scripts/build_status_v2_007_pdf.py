#!/usr/bin/env python3
"""Render the SYSTEM-H recovery completion as one shareable PDF.

Everything here is green — CE verified, projection identity-exact, 33/33 gates,
replacement preregistration written — and that is exactly the risk. A page of
passes invites approval by momentum. The one fact a reader must not skim past
is that the approved PASS floor sits well above SYSTEM-H's own historical
result, so a failure is a live possibility rather than a surprise. That warning
is load-bearing and a build gate enforces it.

Every figure is read from STATUS-V2-007.json at build time. Ten gates refuse
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
DATA = REPO / "experiments/STATUS-V2-007.json"
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


def rows(items) -> str:
    return "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in items)


def build_html(d: dict) -> str:
    C, ID, CE, PR, G, P, T, ST = (d["closure"], d["identity"], d["ce"], d["projection"],
                                 d["gate"], d["prior"], d["thresholds"], d["state"])
    dif = PR["diff"]

    id_rows = rows([(esc(k), f"<span class='num'>{v}</span>") for k, v in dif["identity_fields"]])
    tim_rows = rows([(esc(k), f"<span class='num'>{a}</span>", f"<span class='num'>{b}</span>")
                     for k, a, b in dif["differing_detail"]])
    hash_rows = rows([(ticks(k.replace("_", " ")), f"<span class='mono'>{esc(v)}</span>")
                      for k, v in d["hashes"].items()])
    res = P["results"]

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>SYSTEM-H recovery completion</title><style>{CSS}</style></head><body>
<h1>SYSTEM-H &mdash; recovery completion &amp; preregistration repair</h1>
<p class="subtitle">{G['passed']}/{G['total']} runtime identity gates &middot; projection identity-exact
&middot; {ST['runs_consumed']} runs consumed &middot; reserve {ST['reserve_bytes']} bytes &middot;
head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout warn">
<p><strong>Everything below passes, and that is the reason to read the last section first.</strong>
The approved PASS floor is <strong>case_hit@10 &ge; {T['PASS_floor_case_hit_at_10']}</strong>. SYSTEM-H's own
recovered historical result on a comparable natural-query set is <strong>{esc(res['strict_recall_at_10'])}</strong>
&mdash; roughly 0.50 at case level. <strong>SYSTEM-H may well fail this run.</strong> The floor is retained
unchanged by coordinator ruling; this is recorded now so that outcome cannot later be presented as a surprise.</p>
</div>

<div class="grid">
<div class="card"><div class="big">{G['passed']}/{G['total']}</div><div class="cap">identity gates</div></div>
<div class="card"><div class="big">{PR['projection_count']:,}</div><div class="cap">projections, exact</div></div>
<div class="card"><div class="big">{dif['identical']}/{dif['fields']}</div><div class="cap">build fields identical</div></div>
<div class="card"><div class="big">{ST['runs_consumed']}</div><div class="cap">runs consumed</div></div>
<div class="card"><div class="big">{ST['reserve_bytes']}</div><div class="cap">reserve log bytes</div></div>
</div>

<h2>1 &mdash; The superseded preregistration is closed, not edited</h2>
<p>State <code>{esc(C['state'])}</code> &middot; old preregistration modified:
<strong>{esc(C['modified'])}</strong>.</p>
<ul>{''.join(f'<li>{ticks(r)}</li>' for r in C['reasons'])}</ul>
<p>Recorded as a separate closure artifact so the superseded document keeps its own hash and its
&ldquo;written before any scoring&rdquo; claim stays independently checkable. Editing it to fix its
rationale would have destroyed the property that makes it evidence.</p>

<h2>2 &mdash; Identity resolved</h2>
<table><thead><tr><th>Identity</th><th>Hash</th><th>Status</th></tr></thead><tbody>
<tr><td>Authoritative SYSTEM-H config hash</td>
    <td class="mono">{esc(ID['authoritative'])}</td><td><span class="ok">pinned</span></td></tr>
<tr><td>Local config hash</td><td class="mono dim">{esc(ID['local_rejected'][0])}</td>
    <td><span class="hot">rejected</span></td></tr>
<tr><td>Local score_determining_hash</td><td class="mono dim">{esc(ID['local_rejected'][1])}</td>
    <td><span class="hot">rejected</span></td></tr>
</tbody></table>
<p>Neither local hash was reproduced or force-matched, and neither was attached to the authoritative frozen
system. The recovered runner pins the authoritative hash in its own source, so the identity is self-verifying
rather than asserted.</p>

<h2>3 &mdash; Cross-encoder verified, and the decoy identified</h2>
<p>The exact original is present at revision <code>{esc(CE['revision'])}</code> with SHA256
<code class="mono">{esc(CE['sha'])}</code> &mdash; matching the frozen value. Verified:
<strong>{esc(CE['verified'])}</strong>.</p>
<div class="callout">
<p>The locally cached <code>data/cache/models/exp009/model.onnx</code> hashes to
<code class="mono">{esc(CE['local_decoy'])}</code>. It is <strong>not</strong> the cross-encoder &mdash; it is
the MiniLM <em>sentence encoder</em>. Earlier caution about it being unverified was warranted, and no
substitution was made.</p>
</div>

<h2>4 &mdash; Projection rematerialized, identity-exact</h2>
<p>Original rows were absent from every database, backup and cache. The index was rebuilt with the recovered
EXP-017 builder running against the recovered source tree, the same frozen corpus, and the same MiniLM bundle
(<code class="mono">{esc(PR['bundle_sha'][:32])}…</code>, matching the encoder's own pinned value).</p>
<p><strong>The config hash was computed and checked against the recorded value before any compute was
spent.</strong> Only then was the build run.</p>
<h3>Identity-determining fields &mdash; all identical to the recovered original</h3>
<table><thead><tr><th>Field</th><th class="num">Value</th></tr></thead><tbody>{id_rows}</tbody></table>
<h3>The only three differences</h3>
<table><thead><tr><th>Field</th><th class="num">Original</th><th class="num">Rebuilt</th></tr></thead>
<tbody>{tim_rows}</tbody></table>
<p>Wall-clock timings only. {dif['identical']} of {dif['fields']} fields identical; config hash
<code class="mono">{esc(PR['config_hash'][:32])}…</code>, count {PR['projection_count']:,}, fingerprint
<code>{esc(PR['fingerprint'])}</code> &mdash; all exact. The builder writes new tables only, and the scratch
worktree was restored to pristine afterwards.</p>

<h2>5 &mdash; Runtime identity gate: {G['passed']}/{G['total']}</h2>
<p>Twelve code artifacts hashed against the recovered ref, seven configuration artifacts recovered, the
upstream record's parent hashes cross-checked, the CE and embedding bundle verified, and the projection
identity confirmed against the corpus. A failed gate does not write a manifest &mdash; the builder exits
non-zero so a failure cannot be mistaken for a pass.</p>

<h2>6 &mdash; Replacement preregistration <code>EVAL-NATQ2-H-001</code></h2>
<p>A replacement, not an edit. It pins the authoritative config hash, the runtime manifest, every benchmark
and split hash, and the immutable BM25 comparator vector
(case_hit@10 {d['bm25']['case_hit_at_10']}, micro-MRR {d['bm25']['micro_MRR']}).</p>
<table><thead><tr><th>Threshold provenance</th><th>State</th></tr></thead><tbody>
<tr><td>PASS / FAIL floors</td>
    <td class="num">{T['PASS_floor_case_hit_at_10']} / {T['FAIL_floor_case_hit_at_10']}</td></tr>
<tr><td>Changed</td><td><span class="ok">{esc(T['changed'])}</span></td></tr>
<tr><td>Chosen before any SYSTEM-H NATQ-002 score existed</td>
    <td><span class="ok">{esc(T['chosen_before_any_SYSTEM_H_NATQ002_score_existed'])}</span></td></tr>
<tr><td>Empirically derived from NATQ-002</td>
    <td><span class="ok">{esc(T['not_empirically_derived_from_NATQ_002'])} (i.e. not derived)</span></td></tr>
<tr><td>Historical NATQ-001 result known when written</td>
    <td><span class="hot">{esc(T['historical_NATQ_001_result_was_known_when_this_replacement_was_written'])}</span></td></tr>
</tbody></table>
<p>{esc(T['these_are_not_statistical_priors'])}</p>

<h2>7 &mdash; Disclosed prior evidence, and what it implies</h2>
<p>{esc(P['statement'])} {esc(P['experiment'])} on {esc(P['benchmark'])}, n={P['n']},
{P['gold_spans']} gold spans, config hash verified.</p>
<table><thead><tr><th>Metric</th><th class="num">Result</th></tr></thead><tbody>
<tr><td>strict_recall@10</td><td class="num hot">{esc(res['strict_recall_at_10'])}</td></tr>
<tr><td>evidence_span_recall@10</td><td class="num">{esc(res['evidence_span_recall_at_10'])}</td></tr>
<tr><td>document_recall@10</td><td class="num">{esc(res['document_recall_at_10'])}</td></tr>
<tr><td>candidate_gold_span_recall@100</td><td class="num">{esc(res['candidate_gold_span_recall_at_100'])}</td></tr>
</tbody></table>
<div class="callout warn">
<p>{esc(P['implication_stated_plainly'])}</p>
<p class="dim">{esc(P['definition_caveat'])}</p>
</div>

<h2>8 &mdash; State and constraints</h2>
<table><thead><tr><th>Constraint</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='ok'>{esc(v)}</span>") for k, v in d['constraints'].items()])}
</tbody></table>
<h3>Pinned hashes</h3>
<table><thead><tr><th>Artifact</th><th>SHA256</th></tr></thead><tbody>{hash_rows}</tbody></table>
<p><strong>ready_for_first_SYSTEM_H_NATQ2_run: {esc(d['ready_for_first_run'])}</strong>, pending coordinator
approval. NATQ-002 has never been scored by SYSTEM-H; SYSTEM-H itself has been evaluated before, on
NATQ-001. Those are different statements and the preregistration keeps them apart.</p>

<div class="foot">Generated from STATUS-V2-007.json at <code>{esc(d['head'])}</code>. Reserve access log
{ST['reserve_bytes']} bytes across {ST['reserve_count']} sealed cases, verified before and after. Ten build
gates refuse this page if a constraint is violated.</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-007.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    G, P, T, ST, PR = d["gate"], d["prior"], d["thresholds"], d["state"], d["projection"]

    # 1. Every forbidden action must still be false.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")
    # 2. No run consumed, nothing scored, SUPPORTED still absent.
    if ST["runs_consumed"] != 0 or ST["h_natq002_scored"] or ST["supported"] is not None:
        raise SystemExit("refusing to build: SYSTEM-H shows a consumed run, a score, or a SUPPORTED value")
    # 3. Reserve untouched.
    if ST["reserve_bytes"] != 0 or ST["reserve_count"] != 60:
        raise SystemExit("refusing to build: the reserve is not intact and empty-logged")
    # 4. The identity gate must be complete.
    if not G["all"] or G["passed"] != G["total"]:
        raise SystemExit("refusing to build: a runtime identity gate failed")
    # 5. The projection must be identity-exact, and honest about its origin.
    if not PR["identity_exact"] or PR["projection_count"] != 18057 \
            or PR["fingerprint"] != "bd95feaeacf98559":
        raise SystemExit("refusing to build: the projection is not identity-exact")
    if PR["original_rows_recovered"] is not False:
        raise SystemExit("refusing to build: rematerialization is being presented as recovery")
    if PR["diff"]["identical"] + PR["diff"]["differing"] != PR["diff"]["fields"]:
        raise SystemExit("refusing to build: the build-record diff counts do not reconcile")
    # 6. Thresholds must be unchanged and not dressed up as priors.
    if T["changed"] is not False or T["PASS_floor_case_hit_at_10"] != 0.80 \
            or T["FAIL_floor_case_hit_at_10"] != 0.65:
        raise SystemExit("refusing to build: the thresholds are not the approved unchanged floors")
    if T["not_empirically_derived_from_NATQ_002"] is not True:
        raise SystemExit("refusing to build: the floors are presented as empirically derived")
    # 7. Prior evidence must be disclosed, not implied absent.
    if P["results"]["strict_recall_at_10"] != "20/40":
        raise SystemExit("refusing to build: the disclosed prior result has changed")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 8. The failure warning is load-bearing on a page of passes.
    if "may well fail this run" not in flat:
        raise SystemExit("refusing to build: the page does not warn that SYSTEM-H may fail the floor")
    # 9. The two "never scored" claims must stay distinguished.
    if "Those are different statements" not in flat:
        raise SystemExit("refusing to build: the page conflates 'NATQ-002 unscored' with 'SYSTEM-H unevaluated'")
    # 10. Rematerialization must not be sold as recovery.
    if "Original rows were absent" not in flat:
        raise SystemExit("refusing to build: the page does not state the original rows were absent")

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
