#!/usr/bin/env python3
"""Render the metric-definition audit and threshold-provenance correction as one PDF.

The finding this document exists to carry is negative: the historical 20/40 is not a
NATQ-002 baseline, because strict_recall@10 and case_hit@10 are different functions of
the same retrieval. A report that let a reader keep treating 0.50 as "SYSTEM-H's score
to beat" would be worse than no report, so a build gate refuses to render unless the
NOT_EQUIVALENT verdict and the reason for it are both on the page.

The second finding is smaller and easier to bury: the delivered STATUS-V2-007 table
prints a row that asserts the opposite of the field it renders. It is presentation-only,
and saying so is not the same as hiding it.

Every figure is read from STATUS-V2-008.json at build time. Nine gates refuse the build.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "experiments/STATUS-V2-008.json"
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
th.num, td.num { text-align: center; font-variant-numeric: tabular-nums; white-space: nowrap; }
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
.card .big { font-size: 14pt; font-weight: 700; letter-spacing: -0.5pt; }
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


def yn(b: bool) -> str:
    return "<span class='ok'>yes</span>" if b else "<span class='hot'>no</span>"


def build_html(d: dict) -> str:
    B, G, CO, PB = d["boundaries"], d["gap"], d["correction"], d["probe"]

    axis_rows = "".join(
        f"<tr><td>{esc(a)}</td><td>{ticks(b)}</td><td>{ticks(c)}</td>"
        f"<td>{'<span class=hot>differs</span>' if s == 'differs' else '<span class=ok>' + esc(s) + '</span>'}</td></tr>"
        for a, b, c, s in d["axes"])

    probe_rows = "".join(
        f"<tr><td>{esc(r['case'])}<div class='dim'>{esc(r['why'])}</div></td>"
        f"<td class='num'>{'HIT' if r['strict'] else '&mdash;'}</td>"
        f"<td class='num'>{'HIT' if r['case_hit'] else '&mdash;'}</td>"
        f"<td class='num'>{'HIT' if r['full_cov'] else '&mdash;'}</td></tr>"
        for r in PB["rows"])

    hash_rows = "".join(f"<tr><td>{ticks(k)}</td><td class='mono'>{esc(v)}</td></tr>"
                        for k, v in d["hashes"].items())

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Metric audit &amp; threshold correction</title><style>{CSS}</style></head><body>
<h1>Metric-definition audit &amp; threshold-provenance correction</h1>
<p class="subtitle">Preflight for EVAL-NATQ2-H-001 &middot; verdict <strong>{esc(d['verdict'])}</strong>
&middot; {d['state']['runs_consumed']} runs consumed &middot; reserve {d['state']['reserve_bytes']} bytes
&middot; head <code>{esc(d['head'])}</code> &middot; {esc(d['generated_utc'])}</p>
<div class="rule"></div>

<div class="callout warn">
<p><strong>The historical 20/40 is not a NATQ-002 baseline and must stop being read as one.</strong>
NATQ-001 <code>strict_recall@10</code> and NATQ-002 <code>case_hit@10</code> are
<strong>{esc(d['verdict'])}</strong>. They differ on two independent axes at once &mdash; one counts a case
only when <em>every</em> gold span is retrieved, the other when <em>any</em> one is; and one additionally
requires the retrieved chunk to carry the same <code>section_path</code> as the gold span, which NATQ-002
gold evidence does not even record. On identical retrieval,
<code>strict_recall@10 &le; case_hit@10</code> always, so 0.50 is a <em>lower bound</em> on what the old
number would have been under the new metric, not an estimate of it. The two are also measured on different
question sets with no shared cases, so no paired reading survives even if the definitions were aligned.</p>
</div>

<div class="grid">
<div class="card"><div class="big">{esc(d['verdict'])}</div><div class="cap">metric equivalence</div></div>
<div class="card"><div class="big">{len(PB['separating'])}/{len(PB['rows'])}</div><div class="cap">synthetic cases that separate them</div></div>
<div class="card"><div class="big">{yn(d['h_vs_bm25_same_definition'])}</div><div class="cap">H and BM25 share a definition</div></div>
<div class="card"><div class="big">{d['state']['frozen_artifacts_unchanged']}/{d['state']['frozen_artifacts_checked']}</div><div class="cap">frozen artifacts unchanged</div></div>
</div>

<h2>1 &mdash; Where the two metrics part company</h2>
<table><thead><tr><th style="width:22%">Axis</th><th style="width:31%">NATQ-001 strict_recall@10</th>
<th style="width:31%">NATQ-002 case_hit@10</th><th>Status</th></tr></thead>
<tbody>{axis_rows}</tbody></table>
<p>Read from the scoring code, not from the metric names. The ALL/ANY split lives in
<code>score_system</code>&rsquo;s <code>fully_recalled = found == len(spans)</code>; the predicate split lives
in <code>dict_overlaps</code>, which tests <code>list(section_path)</code> equality that the NATQ-002 runner
never tests. Sixteen of the forty validation cases carry more than one gold span, so the aggregation choice
is live on 40% of the partition; <code>section_path</code> is missing from 100% of NATQ-002 gold evidence,
so the predicate choice is not a tuning knob but a schema fact.</p>

<h2>2 &mdash; Synthetic demonstration</h2>
<p>Hand-constructed fixtures only. No corpus, no database, no benchmark case, no protected partition.
The point is to show the divergence is a property of the definitions rather than of any dataset.</p>
<table><thead><tr><th style="width:55%">Fixture</th><th class="num">strict@10</th>
<th class="num">case_hit@10</th><th class="num">full_cov@10</th></tr></thead>
<tbody>{probe_rows}</tbody></table>
<p><strong>{esc(', '.join(PB['separating']))}</strong> separate strict from case_hit.
<strong>{esc(', '.join(PB['predicate_only']))}</strong> is the one that matters most: it still disagrees
after the aggregation is matched, which is why <code>case_full_coverage@10</code> is the closest analogue of
the historical metric and still not the same function.</p>

<h2>3 &mdash; SYSTEM-H and the frozen BM25 comparator</h2>
<div class="callout win">
<p><strong>Same definition: {esc(d['h_vs_bm25_same_definition'])}.</strong> The EVAL-NATQ2-H-001
<code>span_hit</code> clause and the frozen BM25 runner implement the same predicate at the same depth with
the same aggregation and the same denominators, over the same 40 validation cases. The comparator&rsquo;s
<code>case_hit@10 = {d['bm25_case_hit_at_10']}</code> is measured on exactly the metric the preregistration
names.</p>
</div>
<p><strong>Residual requirement.</strong> {ticks(d['h_vs_bm25_residual'])}</p>
<p><strong>Recommended control.</strong> {ticks(d['h_vs_bm25_control'])}</p>

<h2>4 &mdash; Threshold provenance: the contradictory row</h2>
<p>Classification <strong>{esc(CO['classification'])}</strong> &middot; affects the protocol:
{yn(CO['affects_protocol'])}.</p>
<table><thead><tr><th style="width:26%">Item</th><th>Value</th></tr></thead><tbody>
<tr><td>As rendered in STATUS-V2-007</td><td><span class="hot">{esc(CO['rendered'])}</span></td></tr>
<tr><td>Underlying field</td><td><code>{esc(CO['field'])}</code> = <code>true</code></td></tr>
<tr><td>Which reads as</td><td>{esc(CO['reads_as'])}</td></tr>
<tr><td>Corrected wording</td><td><span class="ok">{esc(CO['corrected_label'])} &mdash; {esc(CO['corrected_value'])}</span></td></tr>
<tr><td>Boolean flipped on assumption</td><td>{yn(not CO['boolean_flipped'])}</td></tr>
</tbody></table>
<p>{esc(CO['why'])} The stored data was already correct in every artifact that governs the run, so nothing
was amended: the floors remain 0.80 and 0.65 exactly as approved, and every hash is untouched. This is a
label defect in one delivered table, recorded rather than quietly rebuilt.</p>

<h2>5 &mdash; Are the qualification boundaries unambiguous?</h2>
<ul>
<li>At 0.80: {esc(B['at_0_80'])}</li>
<li>At 0.65: {esc(B['at_0_65'])}</li>
<li>Between them: {esc(B['the_interval'])}</li>
<li>{esc(B['reachability'])}</li>
</ul>
<div class="callout warn">
<p><strong>One gap, flagged and not repaired: {esc(G['classification'])}.</strong> {esc(G['text'])}</p>
<p>Worked example &mdash; {esc(G['example'])}</p>
<p>Proposed replacement clause: <em>{esc(G['proposal'])}</em></p>
<p>{esc(G['consequence'])} Applying this would be a protocol change and must be issued as a replacement
preregistration with its own hash, on an explicit coordinator ruling. It has not been applied here.</p>
</div>

<h2>6 &mdash; What this changes about the run</h2>
<ul>{''.join(f'<li>{ticks(f)}</li>' for f in d['findings'])}</ul>

<h2>7 &mdash; New artifacts</h2>
<table><thead><tr><th style="width:38%">File</th><th>SHA256</th></tr></thead><tbody>{hash_rows}</tbody></table>
<p class="foot">Authoritative SYSTEM-H config hash <code>{esc(d['authoritative_h_config_hash'])}</code>, preserved.
No system was run, no run was consumed, no reserve or holdout was opened, and the BM25 comparator was neither
rerun nor tuned. Prior status recorded at head <code>{esc(d['recorded_head_of_prior_status'])}</code>.</p>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/STATUS-V2-008.pdf")
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    ST, G, CO, PB, B = d["state"], d["gap"], d["correction"], d["probe"], d["boundaries"]

    # 1. Every forbidden action must still be false.
    for k, v in d["constraints"].items():
        if v is not False:
            raise SystemExit(f"refusing to build: constraint {k} is not false")
    # 2. Nothing scored, nothing consumed, reserve untouched.
    if ST["runs_consumed"] != 0 or ST["h_natq002_scored"] or ST["supported"] is not None \
            or ST["reserve_bytes"] != 0 or ST["reserve_count"] != 60:
        raise SystemExit("refusing to build: a run, a score, or a reserve access is being reported")
    # 3. Frozen artifacts must all have reproduced.
    if ST["frozen_artifacts_unchanged"] != ST["frozen_artifacts_checked"]:
        raise SystemExit("refusing to build: a frozen artifact changed during the audit")
    # 4. The verdict must be the audited one. A later EQUIVALENT needs its own report.
    if d["verdict"] != "NOT_EQUIVALENT":
        raise SystemExit("refusing to build: this document only renders the NOT_EQUIVALENT verdict")
    # 5. The probe must actually separate the metrics, or the verdict is unsupported.
    if len(PB["separating"]) < 1 or len(PB["predicate_only"]) < 1:
        raise SystemExit("refusing to build: the probe exhibits no separating case")
    # 6. The correction must not be smuggled in as a protocol amendment.
    if CO["affects_protocol"] is not False or CO["classification"] != "PRESENTATION_ONLY":
        raise SystemExit("refusing to build: the correction is not classified presentation-only")
    if CO["boolean_flipped"] is not True:
        raise SystemExit("refusing to build: a boolean was flipped rather than the label corrected")
    # 7. The decision-rule gap must stay a proposal.
    if "NOT APPLIED" not in G["classification"]:
        raise SystemExit("refusing to build: the decision-rule change is not marked unapplied")
    if not B["no_gap_or_overlap_between_the_two_floors"]:
        raise SystemExit("refusing to build: the qualification floors do not partition cleanly")

    doc = build_html(d)
    flat = " ".join(doc.split())
    # 8. The headline finding must be on the page, in both its parts.
    if "is not a NATQ-002 baseline" not in flat:
        raise SystemExit("refusing to build: the page does not say the 20/40 is not a NATQ-002 baseline")
    if "lower bound" not in flat:
        raise SystemExit("refusing to build: the page does not state the direction of the inequality")
    # 9. The unpaired-datasets point must survive, or an aligned metric would look sufficient.
    if "no shared cases" not in flat:
        raise SystemExit("refusing to build: the page does not state the datasets share no cases")

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
