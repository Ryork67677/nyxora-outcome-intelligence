#!/usr/bin/env python3
"""V2-DEVSET-001 plus-4: keep V2D-01..46, mine first 4 unique newcomers, stop.

Does not open holdout.json. Does not run retrieval. Does not fetch live docs.
Does not replace the original 46 records.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import signal
import sys
import time
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rag_v1.db import connect  # noqa: E402
from rag_v1.gold.authoring import build_constraint, build_interaction, build_lifecycle  # noqa: E402
from rag_v1.gold.mining import mine_table_parameters, mine_table_required, mine_table_types  # noqa: E402
from rag_v1.gold.mining_v3 import mine_definition_bullets, mine_prose, mine_row_facts  # noqa: E402
from rag_v1.gold.mining_v5 import mine_constraints, mine_interactions, mine_lifecycle  # noqa: E402
from rag_v1.parsing import _sections_from_markdown  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "export_v2_devset_001", ROOT / "scripts" / "export_v2_devset_001.py")
m = importlib.util.module_from_spec(spec)
sys.modules["export_v2_devset_001"] = m
spec.loader.exec_module(m)

KEEP_PATH = ROOT / "evals/review/v2_devset_001_batch_001.json"
COPY_DIR = ROOT / "experiments/RAG-V2/V2-DEVSET-001"
OUT_DIR = ROOT / "evals/review"
PROGRESS_PATH = COPY_DIR / "mine-progress-plus4.jsonl"
IDENTITY_PATH = COPY_DIR / "v2d-01-46-identity-before-plus4.json"
NEED_NEW = 4
ADVISOR_VID = m.ADVISOR_VID
DOC_TIMEOUT_S = m.DOC_TIMEOUT_S
SNAPSHOT = m.SNAPSHOT
SEED = m.SEED
BATCH = m.BATCH
ID_PREFIX = m.ID_PREFIX
SCHEMA_VERSION = m.SCHEMA_VERSION
E_HASH = m.E_HASH


class EarlyStop(Exception):
    pass


class DocTimeout(Exception):
    pass


def identity_of(rec: dict) -> dict:
    return {
        "candidate_id": rec["candidate_id"],
        "question": rec["question"],
        "proposed_question": rec.get("proposed_question"),
        "version_id": rec["version_id"],
        "char_start": rec["char_start"],
        "char_end": rec["char_end"],
    }


def write_packet(payload: dict, json_path: Path, md_path: Path) -> dict:
    tmp = dict(payload)
    tmp.pop("batch_sha256", None)
    json_path.write_text(json.dumps(tmp, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(json_path.read_bytes()).hexdigest()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    md_path.write_text(m.render_md(payload), encoding="utf-8")
    return payload


def write_slice(full: dict, records: list[dict], label: str, start_id: str,
                end_id: str, generated_at: str, generated_et: str) -> None:
    payload = deepcopy(full)
    payload["records"] = records
    payload["candidates"] = len(records)
    payload["generated_at"] = generated_at
    payload["generated_at_et"] = generated_et
    payload["slice"] = label
    payload["slice_range"] = [start_id, end_id]
    payload.pop("batch_sha256", None)
    payload["by_provider"] = dict(Counter(c["provider"] for c in records))
    payload["by_evidence_kind"] = dict(Counter(c["evidence_kind"] for c in records))
    payload["by_reasoning_type"] = dict(Counter(c.get("reasoning_type") for c in records))
    payload["by_stress_type"] = dict(Counter(
        t for c in records for t in (c.get("stress_types") or [])))
    payload["by_confidence"] = dict(Counter(c.get("generator_confidence") for c in records))
    jp = OUT_DIR / f"v2_devset_001_{label}.json"
    mp = OUT_DIR / f"v2_devset_001_{label}.md"
    jp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    payload["batch_sha256"] = hashlib.sha256(jp.read_bytes()).hexdigest()
    jp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = m.render_md(payload)
    old = f"**{len(records)} candidates ·"
    new = (f"**{len(records)} candidates ({label}: {start_id}–{end_id} of 50) ·")
    if old not in md:
        raise SystemExit(f"md header pattern missing for {label}")
    md = md.replace(old, new, 1)
    mp.write_text(md, encoding="utf-8")
    shutil.copy2(jp, COPY_DIR / jp.name)
    shutil.copy2(mp, COPY_DIR / mp.name)
    print(f"wrote {label} n={len(records)} {start_id}..{end_id} md_bytes={mp.stat().st_size}")


def write_status(payload: dict, json_path: Path, md_path: Path,
                 generated_at: str, generated_et: str, newcomers: list[dict],
                 orig_ident: list[dict], unchanged: bool, recovered_n: int) -> None:
    by_p = payload["by_provider"]
    by_s = payload["by_stress_type"]
    lines = [
        "# V2-DEVSET-001 status",
        "",
        (f"Written {generated_at} ({generated_et}). Construction + review packet only. "
         "**Nothing is gold. Nothing is frozen.**"),
        "",
        "## Outcome",
        "",
        "| | |",
        "| --- | --- |",
        f"| candidates exported | **50** (`V2D-01` … `V2D-50`) |",
        "| status of every record | `candidate_unverified` |",
        "| target | n≈50 (preregistered) |",
        "| owner decision | **Russell asked for 50 after 46**. Final n=**50**. "
        "V2D-01..V2D-46 kept unchanged; V2D-47..V2D-50 appended. |",
        "| split role | v2 **development** candidate set, not holdout, not gold150-v1 validation |",
        "",
        "## Pass history",
        "",
        "| pass | gated unique | notes |",
        "| --- | --- | --- |",
        "| 1 | 15 | per-doc miner limits too tight; GOLD gates + overlap collision; Advisor tool `skipped_timeout` at 45s |",
        "| 2 | 46 | GOLD-ish miner limits restored; collision = exact question or exact `version_id`+char span only; Advisor tool re-included as `advisor_narrow` (tables + short/error only); Russell accepted this packet |",
        "| plus-4 | 50 | Russell asked for 50 after 46. Original 46 unchanged. "
        f"Recovered leftover extras: {recovered_n}. Mined first {NEED_NEW - recovered_n} unique newcomers; early-stop. |",
        "",
        "A later unapproved pass that grew past 46 (to 54) was **reverted**. Those extras were not left in JSON dumps; plus-4 re-mined 4 unique non-colliding records rather than restoring the reverted 8.",
        "",
        "## Provider mix (n=50)",
        "",
        "| provider | n |",
        "| --- | --- |",
        f"| anthropic | {by_p.get('anthropic', 0)} |",
        f"| openai | {by_p.get('openai', 0)} |",
        "",
        "## Stress-type mix (a case may carry several tags)",
        "",
        "| stress type | n |",
        "| --- | --- |",
    ]
    for tag, n in sorted(by_s.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {tag} | {n} |")
    lines += [
        "",
        "## Evidence-kind mix",
        "",
        " · ".join(f"{k} {v}" for k, v in payload["by_evidence_kind"].items()),
        "",
        "## GOLD-001 collision checks (exact only)",
        "",
        "Admitted GOLD-001 loaded from `evals/gold`, `evals/golden`, review batches, and `evals/development/v1.jsonl`, filtered by the 150-ID list. `holdout.json` was not opened.",
        "",
        f"plus-4 dropped: `{dict(payload['collisions_dropped'])}`",
        "",
        "## The four appended candidates",
        "",
        "| id | provider | document | question |",
        "| --- | --- | --- | --- |",
    ]
    for r in newcomers:
        q = (r.get("question") or "").replace("|", "\\|")
        lines.append(f"| {r['candidate_id']} | {r['provider']} | {r['document_title']} | {q} |")
    lines += [
        "",
        f"Original 46 id/question/span unchanged vs pre-plus-4 snapshot: **{unchanged}** "
        f"(`{IDENTITY_PATH.relative_to(ROOT)}`).",
        "",
        "## Attestations",
        "",
        "| | |",
        "| --- | --- |",
        "| `holdout_json_opened` | **false** |",
        "| holdout miss IDs used as authoring templates | **false** |",
        "| `retrieval_was_not_run` | **true** |",
        "| systems executed | none (no SYSTEM-A / D / E) |",
        "| live OpenAI/Anthropic docs fetched | **false** |",
        "| cases declared frozen gold | **false** |",
        "| verdicts imported | **false** |",
        "| gold150-v1 split files renamed/moved | **false** |",
        f"| SYSTEM-E config hash | `{E_HASH}` (unchanged) |",
        f"| corpus snapshot | `{SNAPSHOT}` |",
        "| ChatGPT posting | **not done** |",
        "",
        "gold150-v1 validation remains conceptually **`V1-EXPOSED-REGRESSION-40`**. Files were not renamed or moved.",
        "",
        "## Packet paths",
        "",
        "| | |",
        "| --- | --- |",
        "| preregistration | `experiments/RAG-V2/V2-DEVSET-001-preregistration.md` (+ `.json`) |",
        f"| packet json | `evals/review/v2_devset_001_batch_001.json` |",
        f"| packet md | `evals/review/v2_devset_001_batch_001.md` ({md_path.stat().st_size} bytes) |",
        "| copies | `experiments/RAG-V2/V2-DEVSET-001/v2_devset_001_batch_001.{json,md}` |",
        "| slices | `evals/review/v2_devset_001_slice{1,2,3}_of_3.{json,md}` plus copies |",
        "| this status | `experiments/RAG-V2/V2-DEVSET-001-status.md` |",
        "",
        "## Next step",
        "",
        "**Independent ChatGPT verification**, then Russell human QC, **then** freeze. Do not import verdicts in this construction task. Do not freeze. Do not run SYSTEM-D or SYSTEM-E. Do not start EXP-017. Do not optimize E latency.",
        "",
        "The generator discovered evidence and proposed questions. It does not declare gold.",
        "",
    ]
    path = ROOT / "experiments/RAG-V2/V2-DEVSET-001-status.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", path)


def main() -> int:
    prev = json.loads(KEEP_PATH.read_text())
    kept = deepcopy(prev["records"])
    if len(kept) != 46:
        raise SystemExit(f"expected 46 kept records, got {len(kept)}")
    orig_ident = json.loads(IDENTITY_PATH.read_text())["records"]
    now_ident = [identity_of(r) for r in kept]
    if [(x["candidate_id"], x["question"], x["version_id"], x["char_start"], x["char_end"])
            for x in now_ident] != [
            (x["candidate_id"], x["question"], x["version_id"], x["char_start"], x["char_end"])
            for x in orig_ident]:
        raise SystemExit("kept 46 drifted from identity snapshot before mining")

    gold_ids = m.load_gold001_ids()
    prior_q, prior_spans, prior_texts, prior_seen, ingest_counts = (
        m.load_admitted_material(gold_ids))
    # Collision set also includes the 46.
    for rec in kept:
        qn = m.normalise_question(rec.get("proposed_question") or rec.get("question") or "")
        if qn:
            prior_q.add(qn)
        for span in m.evidence_spans_of(rec):
            prior_spans.add((span["version_id"], span["char_start"], span["char_end"]))
    spans_by_vid = m.index_spans(prior_spans)
    print(f"GOLD-001 ids {len(gold_ids)} questions {len(prior_q)} spans {len(prior_spans)}",
          flush=True)

    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    generated_et = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M ET")

    with connect() as conn, conn.cursor() as cur:
        docs = m.load_docs(cur)
    doc_len = {d["version_id"]: len(d["text"]) for d in docs}

    by_provider: dict[str, list] = defaultdict(list)
    for d in docs:
        by_provider[d["provider"]].append(d)
    ordered_docs: list[dict] = []
    buckets = [by_provider[p] for p in sorted(by_provider)]
    while any(buckets):
        for bucket in buckets:
            if bucket:
                ordered_docs.append(bucket.pop(0))

    def _alarm(signum, frame):
        raise DocTimeout()

    signal.signal(signal.SIGALRM, _alarm)

    dropped = Counter()
    newcomers: list[dict] = []
    raw_mined = 0
    skipped_docs: list[dict] = []
    docs_mined = 0

    def accept(rec: dict | None) -> None:
        nonlocal raw_mined
        if rec is None:
            dropped["unauthorable"] += 1
            return
        raw_mined += 1
        if not m.gates(rec, dropped):
            return
        if m.collides(rec, prior_q, prior_spans, prior_texts, spans_by_vid, dropped):
            return
        m.tag_stress(rec, doc_len.get(rec["version_id"], 0))
        qn = m.normalise_question(rec.get("proposed_question") or rec.get("question") or "")
        if qn:
            prior_q.add(qn)
        for span in m.evidence_spans_of(rec):
            prior_spans.add((span["version_id"], span["char_start"], span["char_end"]))
        newcomers.append(rec)
        if len(newcomers) >= NEED_NEW:
            raise EarlyStop()

    def log_progress(i: int, doc: dict, elapsed: float, status: str) -> None:
        rec = {
            "i": i,
            "n_docs": len(ordered_docs),
            "version_id": doc["version_id"],
            "provider": doc["provider"],
            "title": doc["title"],
            "elapsed_s": round(elapsed, 3),
            "status": status,
            "newcomers": len(newcomers),
            "raw_mined": raw_mined,
            "dropped": sum(dropped.values()),
            "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with PROGRESS_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(
            f"  doc {i}/{len(ordered_docs)} {status} {elapsed:.1f}s "
            f"new {len(newcomers)} provider {doc['provider']}",
            flush=True,
        )

    PROGRESS_PATH.write_text("", encoding="utf-8")
    print(f"mining {len(ordered_docs)} documents; early-stop at {NEED_NEW} newcomers",
          flush=True)

    stopped_early = False
    try:
        for i, doc in enumerate(ordered_docs, start=1):
            t0 = time.monotonic()
            status = "ok"
            signal.alarm(DOC_TIMEOUT_S)
            try:
                doc["sections"] = _sections_from_markdown(doc["text"])

                def timed_out() -> bool:
                    return (time.monotonic() - t0) >= DOC_TIMEOUT_S

                advisor = doc["version_id"] == ADVISOR_VID
                for c in mine_table_parameters(doc, limit=4):
                    accept(m.from_candidate_obj(c))
                if timed_out():
                    raise DocTimeout()
                for c in mine_table_required(doc, limit=3):
                    accept(m.from_candidate_obj(c))
                for c in mine_table_types(doc, limit=3):
                    accept(m.from_candidate_obj(c))
                if timed_out():
                    raise DocTimeout()
                if advisor:
                    for rec in m.mine_short_and_error(doc, limit=8):
                        accept(rec)
                    docs_mined += 1
                    status = "advisor_narrow"
                    continue
                for raw in mine_prose(doc, limit=20):
                    accept(m.from_templated(raw))
                if timed_out():
                    raise DocTimeout()
                for raw in mine_row_facts(doc, limit=10):
                    accept(m.from_templated(raw))
                for raw in mine_definition_bullets(doc, limit=10):
                    accept(m.from_templated(raw))
                if timed_out():
                    raise DocTimeout()
                for fact in mine_interactions(doc, limit=40):
                    built = build_interaction(fact)
                    if built:
                        accept(m.finalise_record(doc, built, fact, "configuration_interaction",
                                                 "high"))
                    else:
                        dropped["interaction_unbuilt"] += 1
                if timed_out():
                    raise DocTimeout()
                for fact in mine_constraints(doc, limit=40):
                    built = build_constraint(fact)
                    if built:
                        accept(m.finalise_record(doc, built, fact, "constraint_statement",
                                                 "high"))
                    else:
                        dropped["constraint_unbuilt"] += 1
                if timed_out():
                    raise DocTimeout()
                for fact in mine_lifecycle(doc, limit=30):
                    built = build_lifecycle(fact)
                    if built:
                        accept(m.finalise_record(doc, built, fact, "lifecycle_statement",
                                                 "medium"))
                    else:
                        dropped["lifecycle_unbuilt"] += 1
                if timed_out():
                    raise DocTimeout()
                for rec in m.mine_long_paragraphs(doc, limit=8):
                    accept(rec)
                if timed_out():
                    raise DocTimeout()
                for rec in m.mine_short_and_error(doc, limit=16):
                    accept(rec)
                docs_mined += 1
            except DocTimeout:
                status = "skipped_timeout"
                dropped["doc_timeout"] += 1
                skipped_docs.append({
                    "version_id": doc["version_id"],
                    "provider": doc["provider"],
                    "title": doc["title"],
                })
            finally:
                signal.alarm(0)
                log_progress(i, doc, time.monotonic() - t0, status)
    except EarlyStop:
        stopped_early = True
        signal.alarm(0)
        print(f"early stop with {len(newcomers)} newcomers after {docs_mined} docs",
              flush=True)

    if len(newcomers) < NEED_NEW:
        raise SystemExit(f"only mined {len(newcomers)} newcomers; need {NEED_NEW}")
    newcomers = newcomers[:NEED_NEW]

    # Renumber only the new four.
    for i, rec in enumerate(newcomers, start=47):
        rec["candidate_id"] = f"V2D-{i:02d}"
        rec["verification_status"] = "candidate_unverified"
        rec["retrieval_was_not_run"] = True
        rec["chatgpt_verified"] = None
        rec["claude_proposed"] = True

    # Original 46 must be bit-identical to the loaded copies.
    records = list(kept) + newcomers
    after_ident = [identity_of(r) for r in records[:46]]
    unchanged = [
        (x["candidate_id"], x["question"], x["version_id"], x["char_start"], x["char_end"])
        for x in after_ident
    ] == [
        (x["candidate_id"], x["question"], x["version_id"], x["char_start"], x["char_end"])
        for x in orig_ident
    ]
    if not unchanged:
        raise SystemExit("original 46 mutated during plus-4")

    payload = {
        "task": "V2-DEVSET-001",
        "batch": BATCH,
        "id_prefix": ID_PREFIX,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "generated_at_et": generated_et,
        "corpus_snapshot": SNAPSHOT,
        "selection_seed": SEED,
        "preregistration": "experiments/RAG-V2/V2-DEVSET-001-preregistration.md",
        "system_e_config_hash": E_HASH,
        "system_e_hash_unchanged": True,
        "candidate_pool_size": 46 + len(newcomers),
        "raw_mined_authored": raw_mined,
        "candidates": len(records),
        "by_provider": dict(Counter(c["provider"] for c in records)),
        "by_evidence_kind": dict(Counter(c["evidence_kind"] for c in records)),
        "by_reasoning_type": dict(Counter(c.get("reasoning_type") for c in records)),
        "by_stress_type": dict(Counter(
            t for c in records for t in (c.get("stress_types") or []))),
        "by_confidence": dict(Counter(c.get("generator_confidence") for c in records)),
        "gold001_ids_excluded": sorted(gold_ids),
        "gold001_id_count": len(gold_ids),
        "gold001_admitted_questions_loaded": len(prior_q),
        "gold001_admitted_spans_loaded": len(prior_spans),
        "gold001_ids_seen_in_sources": sorted(prior_seen),
        "collisions_dropped": dict(dropped),
        "ingest_notes": dict(ingest_counts),
        "docs_attempted": docs_mined + len(skipped_docs),
        "docs_completed": docs_mined,
        "docs_skipped_timeout": skipped_docs,
        "mine_progress": str(PROGRESS_PATH.relative_to(ROOT)),
        "holdout_json_opened": False,
        "holdout_miss_ids_used_as_templates": False,
        "holdout_miss_template_ids_excluded": sorted(m.HOLDOUT_MISS_TEMPLATE_IDS),
        "retrieval_was_not_run": True,
        "systems_executed": [],
        "live_docs_fetched": False,
        "verification_status": "candidate_unverified — nothing in this file is gold",
        "v1_exposed_regression_40_note": (
            "gold150-v1 validation is conceptually V1-EXPOSED-REGRESSION-40; "
            "split files were not renamed or moved."
        ),
        "next_step": "independent ChatGPT verification, then Russell human QC, then freeze",
        "records": records,
        "owner_requested_n": 50,
        "owner_requested_by": "Russell York",
        "prior_owner_accepted_n": 46,
        "plus4_early_stop": stopped_early,
        "plus4_recovered_leftover": 0,
        "original_46_unchanged": True,
    }

    json_path = OUT_DIR / "v2_devset_001_batch_001.json"
    md_path = OUT_DIR / "v2_devset_001_batch_001.md"
    payload = write_packet(payload, json_path, md_path)
    shutil.copy2(json_path, COPY_DIR / json_path.name)
    shutil.copy2(md_path, COPY_DIR / md_path.name)

    write_slice(payload, records[0:18], "slice1_of_3", "V2D-01", "V2D-18",
                generated_at, generated_et)
    write_slice(payload, records[18:36], "slice2_of_3", "V2D-19", "V2D-36",
                generated_at, generated_et)
    write_slice(payload, records[36:50], "slice3_of_3", "V2D-37", "V2D-50",
                generated_at, generated_et)

    write_status(payload, json_path, md_path, generated_at, generated_et,
                 newcomers, orig_ident, unchanged, recovered_n=0)

    print("raw_mined_authored", raw_mined)
    print("newcomers", [r["candidate_id"] for r in newcomers])
    for r in newcomers:
        print("NEW", r["candidate_id"], r["provider"], r["document_title"],
              "|", r["question"])
    print("original_46_unchanged", unchanged)
    print("wrote", json_path, "n", payload["candidates"])
    print("md_bytes", md_path.stat().st_size)
    print("json_bytes", json_path.stat().st_size)
    print("holdout_json_opened", payload["holdout_json_opened"])
    print("retrieval_was_not_run", payload["retrieval_was_not_run"])
    print("live_docs_fetched", payload["live_docs_fetched"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
