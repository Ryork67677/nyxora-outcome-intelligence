#!/usr/bin/env python3
"""Render the SYSTEM-H provenance recovery as one shareable PDF.

The recovery is good news that must not read as an unblock. Two separate facts
have to survive contact with a reader in a hurry: the artifacts were found and
were never actually lost, AND the run is still blocked for reasons the recovery
does not touch. A page that led with "RECOVERED" and buried the identity
discrepancy would invite exactly the run this report exists to prevent.

Every figure is read from STATUS-V2-006.json at build time. Ten gates refuse
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
DATA = REPO / "experiments/STATUS-V2-006.json"
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
    D, S2, I, SC, ST = d["discrepancy"], d["second"], d["identity"], d["scope"], d["state"]
    res = S2["recorded_results"]

    art_rows = rows([(esc(k.replace("_", " ")), f"<span class='num'>{v}</span>")
                     for k, v in d["artifact_counts"].items()])
    key_rows = rows([(esc(a["name"]), f"<span class='mono'>{esc(a['sha'][:40])}…</span>",
                      f"<span class='num'>{a['bytes']:,}</span>") for a in d["key_artifacts"]])
    miss_rows = rows([(esc(m["item"]), esc(m["state"])) for m in d["still_missing"]])
    rec_rows = rows([(ticks(k.replace("_", " ")), ticks(str(v)[:150])) for k, v in d["recoverable"].items()])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>SYSTEM-H provenance recovery</title><style>{CSS}</style></head><body>
<h1>SYSTEM-H &mdash; provenance recovery</h1>
<p class="subtitle">Outcome <strong>{esc(d['outcome'])}</strong> &middot; {d['artifacts_total']} original
artifacts &middot; {ST['system_h_runs_consumed']} runs consumed &middot; reserve
{ST['reserve_log_bytes']} bytes &middot; head <code>{esc(d['head'])}</code> &middot;
{esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout win">
<p><strong>The EXP-019A lineage was found, complete, as original git blobs.</strong> It was never lost.
{d['artifacts_total']} artifacts on <code>{esc(d['found_on_ref'])}</code>, each with a verified SHA256, and a
second independent copy already checked out in a worktree at <code>37adc2c</code>.</p>
</div>

<div class="callout warn">
<p><strong>Recovery does not unblock the run.</strong> Two findings block it for reasons the recovered
artifacts do not touch: the NATQ-002 preregistration <em>names the wrong system identity</em>, and it rests
on a <em>false premise about prior scoring</em>. Both need a ruling before SYSTEM-H is executed. Nothing was
reconstructed, modified, run or scored, and the repository was not mutated.</p>
</div>

<div class="grid">
<div class="card"><div class="big">{d['artifacts_total']}</div><div class="cap">artifacts recovered</div></div>
<div class="card"><div class="big">{SC['refs_searched'].__len__()}</div><div class="cap">refs searched</div></div>
<div class="card"><div class="big">{ST['system_h_runs_consumed']}</div><div class="cap">runs consumed</div></div>
<div class="card"><div class="big">null</div><div class="cap">SYSTEM-H supported</div></div>
<div class="card"><div class="big">{ST['reserve_log_bytes']}</div><div class="cap">reserve log bytes</div></div>
</div>

<h2>1 &mdash; Where it was, and why two searches missed it</h2>
<p>{esc(d['why_missed'])}</p>
<div class="callout">
<p><strong>The artifacts were reachable from <code>origin</code> the whole time.</strong> This was a search
failure, not an absence. Two of my own records said otherwise and both are corrected here:
<code>PROVENANCE-GAP-001</code> is superseded but deliberately <em>not</em> rewritten &mdash; it remains an
accurate account of what was known at commit <code>9dc0899</code>.</p>
</div>

<h2>2 &mdash; What was recovered</h2>
<table><thead><tr><th>Lineage</th><th class="num">Artifacts</th></tr></thead><tbody>{art_rows}</tbody></table>
<h3>Selected artifacts</h3>
<table><thead><tr><th>File</th><th>SHA256</th><th class="num">Bytes</th></tr></thead>
<tbody>{key_rows}</tbody></table>
<h3>Identity cross-checks &mdash; all pass</h3>
<table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>
<tr><td>EXP-019A preregistration SHA256</td>
    <td><span class="mono">{esc(I['EXP-019A_preregistration_sha256'])}</span></td></tr>
<tr><td>&hellip; matches the value relayed in PROVENANCE-GAP-001</td>
    <td><span class="ok">{esc(I['matches_value_relayed_in_PROVENANCE_GAP_001'])}</span></td></tr>
<tr><td>&hellip; matches its own <code>.sha256</code> sidecar</td>
    <td><span class="ok">{esc(I['matches_its_own_sidecar_file'])}</span></td></tr>
<tr><td>SYSTEM-G config hash matches coordinator value</td>
    <td><span class="ok">{esc(I['SYSTEM_G_matches_coordinator_value'])}</span></td></tr>
<tr><td>PERF-003 CE-D1 config hash matches coordinator value</td>
    <td><span class="ok">{esc(I['PERF_003_matches_coordinator_value'])}</span></td></tr>
<tr><td>PERF-003 prereg SHA matches value cited inside the upstream SYSTEM-H record</td>
    <td><span class="ok">{esc(I['PERF_003_prereg_matches_value_cited_inside_upstream_SYSTEM_H_record'])}</span></td></tr>
<tr><td>Projection config hash matches the SYSTEM-H record</td>
    <td><span class="ok">{esc(I['projection_matches_SYSTEM_H_record'])}</span></td></tr>
</tbody></table>
<p>The preregistration hashing to exactly the value that was previously only a <em>relayed</em> number is
the strongest evidence available that this is the original artifact rather than a reconstruction.</p>

<h2>3 &mdash; Blocking finding 1: the preregistration names the wrong system</h2>
<table><thead><tr><th>Identity</th><th>Hash</th></tr></thead><tbody>
<tr><td><strong>Authoritative</strong> SYSTEM-H config hash</td>
    <td><span class="mono ok">{esc(D['authoritative_SYSTEM_H_config_hash'])}</span></td></tr>
<tr><td>My local record config hash</td>
    <td><span class="mono">{esc(D['local_record_config_hash'])}</span></td></tr>
<tr><td>My local <code>score_determining_hash</code> &mdash; pinned by the NATQ-002 preregistration</td>
    <td><span class="mono hot">{esc(D['local_record_score_determining_hash'])}</span></td></tr>
<tr><td>That hash found on any Grok ref</td>
    <td><span class="hot">{esc(D['hash_3fade96a_found_on_any_grok_ref'])}</span></td></tr>
</tbody></table>
<p>{esc(D['finding'])}</p>
<p><strong>{esc(D['consequence'])}</strong></p>

<h2>4 &mdash; Blocking finding 2: SYSTEM-H has already been scored</h2>
<p>My preregistration claims SYSTEM-H has never been scored on any benchmark. That is
<strong>{esc(S2['status'])}</strong>. {esc(S2['evidence'])}</p>
<table><thead><tr><th>Metric (EVAL-NATQ-VAL-001, NATQ-001 validation)</th><th class="num">Result</th></tr></thead>
<tbody>
<tr><td>PRIMARY strict_recall@10</td><td class="num hot">{esc(res['PRIMARY_strict_recall_at_10'])}</td></tr>
<tr><td>evidence_span_recall@10</td><td class="num">{res['SECONDARY_evidence_span_recall_at_10']}
    ({esc(res['SECONDARY_evidence_span_found'])})</td></tr>
<tr><td>document_recall@10</td><td class="num">{esc(res['SECONDARY_document_recall_at_10'])}</td></tr>
<tr><td>candidate_gold_span_recall@100</td><td class="num">{esc(res['SECONDARY_candidate_gold_span_recall_at_100'])}</td></tr>
</tbody></table>
<div class="callout warn">
<p>{esc(S2['why_this_matters'])}</p>
<p class="dim">{esc(S2['metric_caveat'])}</p>
</div>

<h2>5 &mdash; Score-determining coverage, and what is still missing</h2>
<table><thead><tr><th>Field</th><th>State</th></tr></thead><tbody>{rec_rows}</tbody></table>
<table><thead><tr><th>Still missing</th><th>State</th></tr></thead><tbody>{miss_rows}</tbody></table>
<p>A rebuild of the projection index would be <strong>reproduction, not recovery</strong>, and is not
proposed here.</p>

<h2>6 &mdash; Search scope</h2>
<p>{len(SC['refs_searched'])} refs &middot; {SC['tags']} tags &middot; {SC['stashes']} stashes &middot;
{SC['worktrees']} worktrees &middot; {SC['reflog_entries']} reflog entries &middot;
{SC['unreachable_objects']} unreachable objects, {SC['unreachable_relevant']} relevant
({esc(SC['unreachable_detail'])}).</p>
<p>Filesystem roots: {ticks(', '.join(SC['filesystem_roots']))}. Archives listed read-only, never extracted:
{esc('; '.join(SC['archives_listed_not_extracted']))}. {esc(SC['windows_paths'])}</p>
<p>Database: {esc(SC['database'])}</p>

<h2>7 &mdash; Recommendation</h2>
<div class="callout">
<p><strong>Do not move SYSTEM-H to {esc(d['lifecycle']['rejected'])}</strong> &mdash;
{esc(d['lifecycle']['why_rejected'])}. Recommended state: <strong>{esc(d['lifecycle']['recommended'])}</strong>.</p>
<p>{esc(d['recommendation'])}</p>
</div>
<h3>Constraints held</h3>
<table><thead><tr><th>Constraint</th><th>State</th></tr></thead><tbody>
{rows([(ticks(k.replace('_', ' ')), f"<span class='ok'>{esc(v)}</span>") for k, v in d['constraints'].items()])}
</tbody></table>

<div class="foot">Generated from STATUS-V2-006.json at <code>{esc(d['head'])}</code>. Recovery record
<code class="mono">{esc(d['hashes']['recovery_record'])}</code>. Reserve access log
{ST['reserve_log_bytes']} bytes, verified before and after the search. Ten build gates refuse this page if a
constraint is violated.</div>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-006.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    D, S2, ST = d["discrepancy"], d["second"], d["state"]

    # 1. Every forbidden action must still be false.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")
    # 2. SYSTEM-H must remain unscored and unjudged.
    if ST["system_h_runs_consumed"] != 0 or ST["system_h_supported"] is not None:
        raise SystemExit("refusing to build: SYSTEM-H shows consumed runs or a SUPPORTED value")
    # 3. The recovery must not be presented as reproducing the pinned hash.
    if ST["score_determining_hash_reproduced"] is not False:
        raise SystemExit("refusing to build: score_determining_hash is claimed reproduced")
    # 4. The reserve must be untouched.
    if ST["reserve_log_bytes"] != 0:
        raise SystemExit("refusing to build: the reserve access log is not empty")
    # 5. The outcome must actually be a recovery for this page to be honest.
    if d["outcome"] != "RECOVERED" or d["artifacts_total"] < 20:
        raise SystemExit("refusing to build: the outcome is not a recovery with recorded artifacts")
    # 6. The lifecycle recommendation must reject the provenance-loss state.
    if d["lifecycle"]["rejected"] != "UNEVALUABLE_PROVENANCE_LOSS":
        raise SystemExit("refusing to build: the page no longer rejects UNEVALUABLE_PROVENANCE_LOSS")
    # 7. The identity discrepancy must remain a discrepancy.
    if D["hash_3fade96a_found_on_any_grok_ref"] is not False:
        raise SystemExit("refusing to build: the identity discrepancy has silently resolved")
    # 8. The false-premise finding must stay marked false.
    if S2["status"] != "FALSE":
        raise SystemExit("refusing to build: the prior-scoring finding is no longer marked FALSE")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 9. Good news must not be allowed to read as an unblock.
    for phrase in ("Recovery does not unblock the run", "never lost"):
        if phrase.lower() not in flat.lower():
            raise SystemExit(f"refusing to build: the page omits {phrase!r}")
    # 10. The self-correction must be visible, not buried.
    if "search failure, not an absence" not in flat:
        raise SystemExit("refusing to build: the page does not own the search failure")

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
