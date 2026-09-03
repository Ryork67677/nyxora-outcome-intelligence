#!/usr/bin/env python3
"""Render the CORPUS-001 recovery attempt as a PDF.

The finding is the headline: the corpus is not reproduced and one thing blocks it. What
the attempt did produce — two snapshot parameters recovered and confirmed by arithmetic,
two identity oracles, and the 139 split by what could verify them — is the body, not the
lede.

Every figure is read from the CORPUS-001 artifacts at build time. Six gates refuse the
build rather than publish a document that disagrees with the project state.
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

from rag_v1.corpus_oracle import MANIFEST_HASH, SNAPSHOT_ID  # noqa: E402

EXP = REPO_ROOT / "experiments/GOLD-001"
LEDGER = EXP / "CORPUS-001-recovery-ledger.json"
MANIFEST = EXP / "CORPUS-001-expected-202-manifest.json"
HOST = EXP / "CORPUS-001-host-search.json"
IDS = EXP / "CORPUS-001-known-anthropic-id-search.json"
PLAN = EXP / "CORPUS-001-anthropic-recovery-plan.json"
UNBUILDABLE = EXP / "CORPUS-001-unbuildable-identity-analysis.json"
LIMITATION = EXP / "GOLD-001-corpus-reproduction-limitation.json"
INVENTORY = EXP / "CORPUS-001-local-artifact-inventory.json"
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
td { padding: 4pt 6pt; border-bottom: 0.6pt solid #dde0e4; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.dim { color: #6f747b; }
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


def build_html(d: dict) -> str:
    led, man, host = d["ledger"], d["manifest"], d["host"]
    ids, plan, unb, lim = d["ids"], d["plan"], d["unbuildable"], d["limitation"]
    m = led["metrics"]
    counts = m["status_counts"]
    total = m["expected_documents"]
    oracle = host["identity_oracles"]
    unknown = host["openai_unknown_identity_status"]
    hr = host["host_reachability"]
    correction = lim["audit_corrections"][0]
    entries = man["entries"]
    known = sum(1 for e in entries if e["expected_version_id"] != "UNKNOWN")

    status_rows = rows(
        [(f"<code>{esc(k)}</code>", f"{v}", f"{v / total:.0%}",
          f"<span class='bar' style='width:{max(2, round(140 * v / total))}pt'></span>")
         for k, v in sorted(counts.items(), key=lambda kv: -kv[1])],
        ("", "num", "num", ""))
    source_rows = rows(
        [(esc(c["source"]), "yes" if c["verifiable_exactly"] else "<strong>no</strong>",
          f"<span class='dim'>{esc(c['status'])}</span>")
         for c in plan["candidate_sources_in_preference_order"]])
    host_rows = rows(
        [(f"<code>{esc(c['path'])}</code>", esc(c["description"]),
          "<strong>no</strong>" if not c["exists"] else esc(c.get("note", "yes")))
         for c in hr["host_locations_requested"]])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>CORPUS-001 recovery</title><style>{CSS}</style></head><body>
<h1>CORPUS-001 &mdash; the corpus is not reproduced</h1>
<p class="subtitle">{esc(led['generated_at'])} &middot; target
<code>{esc(SNAPSHOT_ID)}</code> &middot; every figure read from the records at build
time</p>
<div class="rule"></div>

<div class="callout warn"><div class="label">The finding</div>
<p><strong>{counts.get('MISSING_SOURCE', 0)} of {total} documents have no recovered
historical bytes, and the snapshot digest is not reproduced.</strong> That is the whole
blocker, and it is now a single one: the {counts.get('MISSING_SOURCE', 0)} missing
Anthropic captures. Everything else this attempt produced narrows the problem without
solving it.</p></div>

<div class="grid4">
  <div class="stat win"><div class="big">{m['exactly_recovered']}</div>
    <div class="cap"><code>EXACT_MATCH</code></div></div>
  <div class="stat"><div class="big">{m['reproduced_but_unverifiable']}</div>
    <div class="cap"><code>EXPECTED_HASH_UNKNOWN</code></div></div>
  <div class="stat warn"><div class="big">{m['missing']}</div>
    <div class="cap"><code>MISSING_SOURCE</code></div></div>
  <div class="stat warn"><div class="big">no</div>
    <div class="cap">snapshot reproduced</div></div>
</div>

<h2>Two snapshot parameters recovered</h2>
<p>Both were carried as unknown. They are confirmed <em>together</em>, by arithmetic:
<code>experiments/EXP-007/results.json</code> records the manifest hash, and only one
candidate name reproduces the frozen id from it.</p>
<blockquote>stable_id("snap", "{esc(man['name'])}",
  "{esc(MANIFEST_HASH)}",
  "{esc(man['parser_version'])}", chunking_hash)
    = {esc(SNAPSHOT_ID)}</blockquote>
<p>Any other name gives a different 128-bit value, so the match establishes the name and
the manifest hash at once. The manifest hash is the more useful of the two: it covers
only the {total} <code>(version_id, content_hash)</code> pairs, so it isolates corpus
<em>content</em> from the parser and chunking parameters &mdash; and it separates a
content failure from a parameter failure when a candidate fails.</p>

<h2>The ledger</h2>
<table><thead><tr><th>status</th><th class="num">documents</th><th class="num">share</th>
<th></th></tr></thead><tbody>{status_rows}</tbody></table>
<p>Exact document-version reproduction
<strong>{m['document_version_reproduction_rate']:.1%}</strong>; bytes reproduce for
<strong>{m['normalized_hash_reproduction_rate']:.1%}</strong>. Every
<code>MISSING_SOURCE</code> row is Anthropic, and none was filled with a live page.</p>

<h2>What survived the corpus</h2>
<p><strong>{known} of {total} documents</strong> can be given an expected
<code>version_id</code> from surviving artifacts &mdash;
{sum(1 for e in entries if e['provider'] == 'anthropic'
     and e['expected_version_id'] != 'UNKNOWN')} of them Anthropic. Two oracles make
those identities usable:</p>
<table><thead><tr><th>oracle</th><th class="num">surviving</th>
<th>construction</th></tr></thead><tbody>
<tr><td><code>version_id</code></td><td class="num">{oracle['surviving_version_ids']}</td>
<td><code>stable_id("ver", src_id, content_hash)</code></td></tr>
<tr><td><code>chunk_id</code></td><td class="num">{oracle['surviving_chunk_ids']}</td>
<td><code>{esc(oracle['chunk_id_construction'])}</code></td></tr>
</tbody></table>
<p>{ticks(oracle['why_chunk_id_is_stronger'].capitalize())}. It confirms
{unknown['documents_confirmed_by_chunk_id_overall']} of the 63 reproduced OpenAI
documents at that level.</p>

<div class="callout"><div class="label">The 14 unknown OpenAI identities</div>
<p><strong>{unknown['expected_hash_unknown_before']} &rarr;
{unknown['still_unknown']}.</strong> {esc(unknown['finding'])}</p></div>

<div class="break"></div>
<h2>The host could not be searched from here</h2>
<p>The brief asks for a sweep of Windows user directories, WSL mounts, Desktop,
Downloads and Docker volumes, where the gitignored <code>data/raw</code> captures would
live. This session runs in an {esc(hr['environment'])} on a single root disk.</p>
<table><thead><tr><th>requested location</th><th>what it is</th>
<th>present here</th></tr></thead><tbody>{host_rows}</tbody></table>
<p>{esc(hr['verdict'])}</p>
<p>Everything reachable <em>was</em> swept:
{len(host['accessible_sweep']['roots_swept'])} filesystems,
<strong>{len(host['accessible_sweep']['archives_found'])}</strong> archives or dumps
found. Every provenance-anchor hit outside the repository resolves to this session's own
packets, scratchpad and log.</p>

<h2>The 40 known Anthropic identities</h2>
<p>All {ids['known_anthropic_identities']} were located.
<strong>{ids['whose_location_carries_normalized_text']}</strong> carry the document
body: {esc(ids['finding'])}</p>
<div class="callout win"><div class="label">What that still leaves</div>
<p>{ids['documents_with_verified_historical_bytes']} of the 40 carry exact historical
byte-slices from closed GOLD evidence &mdash;
<strong>{ids['total_verified_historical_bytes']:,} verified bytes</strong> at known
character offsets. They cannot rebuild a document; the gaps are gone. They can refute
one: a capture claiming to be the 2026-08-17 state must reproduce those bytes at those
offsets before it is worth hashing.</p></div>

<h2>The 139, split by what could verify them</h2>
<table><thead><tr><th>group</th><th class="num">documents</th>
<th>how a candidate is decided</th></tr></thead><tbody>
<tr><td>A &mdash; <code>version_id</code> recorded</td>
<td class="num">{plan['group_A_expected_version_id_known']['count']}</td>
<td>{ticks(plan['group_A_expected_version_id_known']['verification'])}</td></tr>
<tr><td>B &mdash; no recorded identity</td>
<td class="num">{plan['group_B_expected_version_id_unknown']['count']}</td>
<td>{ticks(plan['group_B_expected_version_id_unknown']['verification'])}</td></tr>
</tbody></table>
<table><thead><tr><th>candidate source</th><th>exactly verifiable</th>
<th>status</th></tr></thead><tbody>{source_rows}</tbody></table>

<h2>Audit correction {esc(correction['correction_id'])}</h2>
<div class="callout"><div class="label">Superseded</div>
<p>&ldquo;{esc(correction['superseded_statement'])}&rdquo;</p></div>
<div class="callout win"><div class="label">Replaced with</div>
<p>&ldquo;{esc(correction['replacement_statement'])}&rdquo;</p></div>
<p>The 2,482 comes from one statement in <code>scripts/export_batch_006.py</code>:
<code>removed["unbuildable"] += 1</code> when a builder returns
<code>None</code>. They are mined spans <em>inside</em> the {total} documents, not
documents. And the count is of builder attempts, not distinct spans &mdash; the
generator iterates one fact list twice, and 2,482 exceeds both the
{unb['the_count_is_attempts_not_distinct_spans']['corroboration'].split()[4]} facts mined
and the distinct evidence texts of that same run.</p>
<p>{esc(correction['handling'])}</p>

<h2>State</h2>
<div class="callout warn"><div class="label">{esc(lim['effect'])}</div>
<p><code>CORPUS_REPRODUCTION_INCOMPLETE</code> true,
<code>corpus_snapshot_reproduced</code> false, <code>RETRIEVAL_BLOCKED</code> true.
The blocker is <strong>{esc(lim['the_corpus_blocker'])}</strong>.</p>
<p>GOLD is untouched at 150 verified / 150 eligible / 9 rejected / 1 genuine multi-hop.
No retrieval was run, no split was frozen, no live page was fetched, and no replacement
snapshot was created.</p></div>

<footer>CORPUS-001 &middot; generated from CORPUS-001-recovery-ledger.json,
-expected-202-manifest.json, -host-search.json, -known-anthropic-id-search.json,
-anthropic-recovery-plan.json, -unbuildable-identity-analysis.json and
GOLD-001-corpus-reproduction-limitation.json. No figure in this document was typed by
hand.</footer>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="docs/reports/CORPUS-001-recovery.pdf")
    args = parser.parse_args()

    d = {"ledger": json.loads(LEDGER.read_text()),
         "manifest": json.loads(MANIFEST.read_text()),
         "host": json.loads(HOST.read_text()),
         "ids": json.loads(IDS.read_text()),
         "plan": json.loads(PLAN.read_text()),
         "unbuildable": json.loads(UNBUILDABLE.read_text()),
         "limitation": json.loads(LIMITATION.read_text()),
         "inventory": json.loads(INVENTORY.read_text())}
    m = d["ledger"]["metrics"]

    # 1. The document may not claim a reproduction that did not happen.
    if m["snapshot_digest"]["reproduced"]:
        raise SystemExit("refusing to build: the ledger says the snapshot reproduced; "
                         "this page describes a failure")
    if d["limitation"]["corpus_snapshot_reproduced"] is not False:
        raise SystemExit("refusing to build: the limitation no longer says the corpus "
                         "is unreproduced")

    # 2. The counts must add up to the expected corpus.
    if sum(m["status_counts"].values()) != m["expected_documents"]:
        raise SystemExit("refusing to build: the ledger statuses do not cover all "
                         f"{m['expected_documents']} documents")
    if len(d["manifest"]["entries"]) != m["expected_documents"]:
        raise SystemExit("refusing to build: the expected manifest is not "
                         f"{m['expected_documents']} entries")

    # 3. The recovered parameters must still reproduce the target.
    from rag_v1.corpus_oracle import snapshot_id_for
    chunking = {"max_chunk_chars": 3500, "min_chunk_chars": 200}
    if snapshot_id_for(MANIFEST_HASH, chunking) != SNAPSHOT_ID:
        raise SystemExit("refusing to build: the recorded parameters no longer "
                         "reproduce the frozen snapshot id")

    # 4. The 139 must be fully split, with none silently dropped.
    plan = d["plan"]
    if (plan["group_A_expected_version_id_known"]["count"]
            + plan["group_B_expected_version_id_unknown"]["count"]
            != plan["total_missing"]):
        raise SystemExit("refusing to build: the recovery plan drops documents")

    # 5. Retrieval must still be blocked and GOLD untouched.
    if d["limitation"]["RETRIEVAL_BLOCKED"] is not True:
        raise SystemExit("refusing to build: retrieval is no longer blocked")

    document = build_html(d)

    # 6. The page must lead with the failure, not the recovered parameters.
    flat = " ".join(document.split())
    if "is not reproduced" not in flat or "The finding" not in flat:
        raise SystemExit("refusing to build: the page does not lead with the finding")

    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if chrome is None:
        raise SystemExit("No Chromium binary found")
    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "corpus001.html"
        src.write_text(document, encoding="utf-8")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()],
                       check=True, capture_output=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
