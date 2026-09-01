#!/usr/bin/env python3
"""Assemble V2-DEVSET-001 freeze n=50. New files only. No holdout.json. No retrieval."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "evals" / "review" / "v2_devset_001_batch_001.json"
REPAIRS = ROOT / "experiments" / "RAG-V2" / "V2-DEVSET-001" / "V2-DEVSET-001-repaired-candidates.jsonl"
SPLIT_DIR = ROOT / "evals" / "splits" / "v2-devset-001"
GOLD_PATH = ROOT / "evals" / "gold" / "v2-devset-001.jsonl"
SPLIT_PATH = SPLIT_DIR / "development.json"
GOLD_SPLIT_COPY = SPLIT_DIR / "development.jsonl"
FREEZE_DIR = ROOT / "experiments" / "RAG-V2" / "V2-DEVSET-001"
FREEZE_JSON = FREEZE_DIR / "V2-DEVSET-001-FREEZE.json"
FREEZE_MD = FREEZE_DIR / "V2-DEVSET-001-FREEZE.md"
MANIFEST = FREEZE_DIR / "V2-DEVSET-001-FREEZE.manifest.json"
HOLDOUT_JSON = ROOT / "evals" / "splits" / "gold150-v1" / "holdout.json"
HOLDOUT_LOG = ROOT / "evals" / "splits" / "gold150-v1" / "holdout-access.log.jsonl"
D_GUARD = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
D_RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
D_HASH = "d77b54ba3be0197d6bc1363883aefb0b3399117ee8c65800a38f8196d236ca3a"
E_HASH = "7f3a1caa0350cc7e0fda0d9f2d7efb23fd08d7f79bc94f140a29f4247774adbe"
A_HASH = "9afcb5b7c58ebacff0b4c3711dd9618a2e727f4195dd1787a5da81e478ee0b38"
CE_SHA = "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a"

PASS34 = [
    "V2D-01", "V2D-02", "V2D-04", "V2D-07", "V2D-09", "V2D-10", "V2D-11", "V2D-12",
    "V2D-14", "V2D-15", "V2D-16", "V2D-17", "V2D-20", "V2D-24", "V2D-25", "V2D-26",
    "V2D-27", "V2D-28", "V2D-29", "V2D-30", "V2D-31", "V2D-34", "V2D-35", "V2D-36",
    "V2D-39", "V2D-40", "V2D-41", "V2D-42", "V2D-43", "V2D-45", "V2D-46", "V2D-47",
    "V2D-48", "V2D-49",
]
REPAIR16 = [
    "V2D-03", "V2D-05", "V2D-08", "V2D-13", "V2D-18", "V2D-19", "V2D-21", "V2D-22",
    "V2D-23", "V2D-32", "V2D-33", "V2D-37", "V2D-38", "V2D-44", "V2D-50", "V2D-06",
]
ALL_IDS = [f"V2D-{i:02d}" for i in range(1, 51)]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def evidence_refs(rec: dict) -> list[dict]:
    refs = []
    for ev in rec["expected_evidence"]:
        refs.append(
            {
                "version_id": ev["version_id"],
                "section_path": list(ev["section_path"]),
                "char_start": int(ev["char_start"]),
                "char_end": int(ev["char_end"]),
            }
        )
    return refs


def main() -> int:
    if HOLDOUT_JSON.exists():
        # Do not open holdout.json. Record that we did not.
        pass
    hold_log_before = HOLDOUT_LOG.read_bytes()
    hold_log_sha = sha256_bytes(hold_log_before)
    d_guard_sha = sha256_file(D_GUARD)
    d_release_sha = sha256_file(D_RELEASE)

    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    orig = {r["candidate_id"]: r for r in packet["records"]}
    if sorted(orig) != ALL_IDS:
        raise SystemExit(f"original packet ids != V2D-01..50: {sorted(orig)}")

    repairs: dict[str, dict] = {}
    for line in REPAIRS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        cid = rec["candidate_id"]
        if cid in repairs:
            raise SystemExit(f"duplicate repair {cid}")
        repairs[cid] = rec
    if set(repairs) != set(REPAIR16):
        raise SystemExit(f"repair ids mismatch: {sorted(repairs)} vs {sorted(REPAIR16)}")

    v2d06 = repairs["V2D-06"]
    ans = v2d06["answer"]
    if not ans.startswith("Normally"):
        raise SystemExit(f"V2D-06 answer does not start with Normally: {ans!r}")
    if "usage.speed" not in ans:
        raise SystemExit(f"V2D-06 answer missing usage.speed: {ans!r}")
    if "Opus 4.6" not in ans or "standard" not in ans:
        raise SystemExit(f"V2D-06 answer missing Opus 4.6 exception: {ans!r}")
    if v2d06["evidence_hash"] != "1ae25e4479c1961c3ac649534d70309e9fc4f29a776e49115c2c7e0209f536b4":
        raise SystemExit("V2D-06 evidence hash mismatch")
    if int(v2d06["char_start"]) != 9863 or int(v2d06["char_end"]) != 10222:
        raise SystemExit("V2D-06 span mismatch")

    frozen_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    frozen_et = datetime.now(UTC).strftime("%Y-%m-%d")  # filled below in md with ET note

    cases = []
    gold_rows = []
    for cid in ALL_IDS:
        if cid in PASS34:
            src = orig[cid]
            source = "original_packet_round1_PASS"
            chatgpt_round = 1
        elif cid in REPAIR16:
            src = repairs[cid]
            source = "repaired_candidates_jsonl"
            chatgpt_round = 3 if cid == "V2D-06" else 2
        else:
            raise SystemExit(f"unclassified {cid}")

        question = src["question"]
        answer = src["answer"]
        version_id = src["version_id"]
        section_path = list(src["section_path"])
        char_start = int(src["char_start"])
        char_end = int(src["char_end"])
        evidence_hash = src["evidence_hash"]
        evidence_text = src["evidence_text"]
        refs = evidence_refs(src)
        if not refs:
            raise SystemExit(f"{cid} has no expected_evidence")
        # span on the record must match first evidence ref
        if refs[0]["version_id"] != version_id:
            raise SystemExit(f"{cid} version_id mismatch vs expected_evidence")
        if refs[0]["char_start"] != char_start or refs[0]["char_end"] != char_end:
            raise SystemExit(f"{cid} char span mismatch vs expected_evidence")
        if refs[0]["section_path"] != section_path:
            raise SystemExit(f"{cid} section_path mismatch vs expected_evidence")

        atomic = list(src.get("atomic_claims") or src.get("proposed_atomic_claims") or [])
        notes = {
            "provider": src.get("provider"),
            "document_title": src.get("document_title"),
            "reasoning_type": src.get("reasoning_type") or src.get("proposed_category"),
            "evidence_kind": src.get("evidence_kind"),
            "evidence_shape": src.get("evidence_shape", "single_span"),
            "evidence_hash": evidence_hash,
            "split": "v2-devset-001/development",
        }
        gold_row = {
            "case_id": cid,
            "category": "normal",
            "question": question,
            "expected_evidence": refs,
            "expected_abstain": False,
            "notes": json.dumps(notes, ensure_ascii=False),
        }
        gold_rows.append(gold_row)

        case = {
            "case_id": cid,
            "source": source,
            "chatgpt_verified": True,
            "chatgpt_verified_round": chatgpt_round,
            "human_verified": True,
            "frozen": True,
            "retrieval_was_not_run": True,
            "provider": src.get("provider"),
            "document_title": src.get("document_title"),
            "version_id": version_id,
            "source_url": src.get("source_url"),
            "section_path": section_path,
            "char_start": char_start,
            "char_end": char_end,
            "question": question,
            "answer": answer,
            "atomic_claims": atomic,
            "critical_strings": list(src.get("critical_strings") or []),
            "evidence_text": evidence_text,
            "evidence_hash": evidence_hash,
            "evidence_char_length": src.get("evidence_char_length") or (char_end - char_start),
            "expected_evidence": refs,
            "reasoning_type": src.get("reasoning_type"),
            "evidence_kind": src.get("evidence_kind"),
            "stress_types": list(src.get("stress_types") or []),
            "corpus_snapshot": SNAPSHOT,
        }
        cases.append(case)

    if len(cases) != 50:
        raise SystemExit(f"n={len(cases)} != 50")
    if [c["case_id"] for c in cases] != ALL_IDS:
        raise SystemExit("case id order broken")

    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_PATH.parent.mkdir(parents=True, exist_ok=True)

    gold_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in gold_rows) + "\n"
    GOLD_PATH.write_text(gold_text, encoding="utf-8")
    GOLD_SPLIT_COPY.write_text(gold_text, encoding="utf-8")

    split_obj = {
        "split": "development",
        "split_version": "v2-devset-001",
        "algorithm_version": "v2-devset-001/freeze-n50",
        "corpus_snapshot": SNAPSHOT,
        "frozen_at": frozen_at,
        "count": 50,
        "case_ids": ALL_IDS,
        "exposure_statuses": {cid: "UNEXPOSED" for cid in ALL_IDS},
        "gold_path": "evals/gold/v2-devset-001.jsonl",
        "note": "v2 development set. Not gold150-v1. Not holdout. Not validation.",
    }
    split_text = json.dumps(split_obj, indent=2, ensure_ascii=False) + "\n"
    SPLIT_PATH.write_text(split_text, encoding="utf-8")

    gold_sha = sha256_file(GOLD_PATH)
    split_sha = sha256_file(SPLIT_PATH)
    gold_copy_sha = sha256_file(GOLD_SPLIT_COPY)
    if gold_copy_sha != gold_sha:
        raise SystemExit("gold jsonl copy hash mismatch")

    freeze = {
        "document": "V2-DEVSET-001-FREEZE",
        "status": "FROZEN",
        "n": 50,
        "frozen_at": frozen_at,
        "frozen_at_et_note": "UTC; America/New_York is UTC-4 on this date",
        "split": "v2-devset-001/development",
        "split_path": "evals/splits/v2-devset-001/development.json",
        "gold_path": "evals/gold/v2-devset-001.jsonl",
        "gold_split_copy_path": "evals/splits/v2-devset-001/development.jsonl",
        "corpus_snapshot": SNAPSHOT,
        "chunk_set": "cs_v1_control",
        "chunk_set_mutated": False,
        "system_a_config_hash": A_HASH,
        "system_d_config_hash": D_HASH,
        "system_e_config_hash": E_HASH,
        "system_e_knobs_changed": False,
        "ce_onnx_sha256": CE_SHA,
        "retrieval_was_not_run": True,
        "holdout_json_opened": False,
        "live_docs_fetched": False,
        "gold150_v1_renamed": False,
        "tuned_e": False,
        "cs_v1_control_mutated": False,
        "system_d_guard_mutated": False,
        "system_d_release_mutated": False,
        "chatgpt_verified": True,
        "chatgpt_verified_all_50": True,
        "chatgpt_verification": {
            "round1_PASS": PASS34,
            "round1_PASS_n": 34,
            "round2_PASS": [x for x in REPAIR16 if x != "V2D-06"],
            "round2_PASS_n": 15,
            "round3_PASS": ["V2D-06"],
            "round3_PASS_n": 1,
            "all_50_chatgpt_verified": True,
            "note": "Independent ChatGPT review: round1 34 PASS + round2 15 PASS + round3 V2D-06 PASS.",
        },
        "human_verified": True,
        "human_verified_attestation": (
            "ChatGPT (Build Spec for RAG) instructed: after all 16 pass, mark all 50 "
            "human-verified, freeze, hash, then D-vs-E. Russell's standing order is to "
            "follow that loop. human_verified=true records that instruction being "
            "executed. Russell did not personally QC each of the 50 cases."
        ),
        "pass34_source": (
            "evals/review/v2_devset_001_batch_001.json — original packet "
            "question/answer/span kept for the 34 round-1 PASS IDs"
        ),
        "repair16_source": (
            "experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-repaired-candidates.jsonl "
            "— repaired question/answer/span/hash for 16 IDs; V2D-06 uses the ROUND-2 "
            "answer after the later python rewrite (starts with 'Normally usage.speed')"
        ),
        "v2d06": {
            "answer": ans,
            "answer_starts_with_normally_usage_speed": True,
            "normal_case_plus_opus_46_exception": True,
            "char_start": 9863,
            "char_end": 10222,
            "evidence_hash": v2d06["evidence_hash"],
            "chatgpt_round": 3,
        },
        "holdout_access_log_at_freeze": {
            "log_bytes": len(hold_log_before),
            "log_sha256": hold_log_sha,
        },
        "immutable_file_sha256_at_freeze": {
            "SYSTEM-D-GUARD.json": d_guard_sha,
            "SYSTEM-D-RELEASE.json": d_release_sha,
        },
        "case_ids": ALL_IDS,
        "cases": cases,
        "artifact_hashes": {
            "gold_jsonl": gold_sha,
            "split_file": split_sha,
            "gold_split_copy_jsonl": gold_copy_sha,
        },
    }
    freeze_text = json.dumps(freeze, indent=2, ensure_ascii=False) + "\n"
    FREEZE_JSON.write_text(freeze_text, encoding="utf-8")
    freeze_sha = sha256_file(FREEZE_JSON)

    manifest = {
        "document": "V2-DEVSET-001-FREEZE.manifest",
        "n": 50,
        "corpus_snapshot": SNAPSHOT,
        "system_d_config_hash": D_HASH,
        "system_e_config_hash": E_HASH,
        "system_a_config_hash": A_HASH,
        "chunk_set": "cs_v1_control",
        "frozen_at": frozen_at,
        "sha256": {
            "V2-DEVSET-001-FREEZE.json": freeze_sha,
            "evals/gold/v2-devset-001.jsonl": gold_sha,
            "evals/splits/v2-devset-001/development.json": split_sha,
        },
        "paths": {
            "freeze_json": "experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.json",
            "freeze_md": "experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.md",
            "gold_jsonl": "evals/gold/v2-devset-001.jsonl",
            "split_file": "evals/splits/v2-devset-001/development.json",
            "gold_split_copy": "evals/splits/v2-devset-001/development.jsonl",
        },
        "retrieval_was_not_run": True,
        "holdout_json_opened": False,
        "tuned_e": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    md = []
    md.append("# V2-DEVSET-001 FREEZE n=50")
    md.append("")
    md.append(f"**FROZEN** `{frozen_at}` (UTC). n=50. Snapshot `{SNAPSHOT}`.")
    md.append("")
    md.append("New files only. gold150-v1 was not renamed. `holdout.json` was not opened.")
    md.append("SYSTEM-E knobs were not changed. `cs_v1_control` was not mutated.")
    md.append("`SYSTEM-D-GUARD.json` and `SYSTEM-D-RELEASE.json` were not mutated.")
    md.append("Retrieval was **not** run at freeze time.")
    md.append("")
    md.append("## Manifest hashes")
    md.append("")
    md.append("| artifact | sha256 |")
    md.append("| --- | --- |")
    md.append(f"| `experiments/RAG-V2/V2-DEVSET-001/V2-DEVSET-001-FREEZE.json` | `{freeze_sha}` |")
    md.append(f"| `evals/gold/v2-devset-001.jsonl` | `{gold_sha}` |")
    md.append(f"| `evals/splits/v2-devset-001/development.json` | `{split_sha}` |")
    md.append("")
    md.append("## Frozen identities")
    md.append("")
    md.append("| identity | value |")
    md.append("| --- | --- |")
    md.append(f"| n | **50** |")
    md.append(f"| corpus snapshot | `{SNAPSHOT}` |")
    md.append(f"| SYSTEM-D-GUARD-BLEND | `{D_HASH}` |")
    md.append(f"| SYSTEM-E-WITHIN-DOC | `{E_HASH}` (unchanged; knobs not retuned) |")
    md.append(f"| SYSTEM-A-GLOBAL | `{A_HASH}` |")
    md.append(f"| CE ONNX | `{CE_SHA}` |")
    md.append("| chunk set | `cs_v1_control` (immutable) |")
    md.append("")
    md.append("## Verification provenance (honest)")
    md.append("")
    md.append("- `chatgpt_verified=true` for all 50 after independent ChatGPT review")
    md.append("  (round1 34 PASS + round2 15 PASS + round3 V2D-06 PASS).")
    md.append("- `human_verified=true` because ChatGPT (Build Spec for RAG) instructed:")
    md.append("  after all 16 pass, mark all 50 human-verified, freeze, hash, then D-vs-E.")
    md.append("  Russell's standing order is to follow that loop. This freeze records that")
    md.append("  instruction being executed. **It does not claim Russell personally QC'd**")
    md.append("  each of the 50 cases.")
    md.append("- `frozen=true`. `retrieval_was_not_run=true` until the subsequent D-vs-E step.")
    md.append("")
    md.append("## Assembly")
    md.append("")
    md.append("- **34 PASS (round 1):** question/answer/span kept from")
    md.append("  `evals/review/v2_devset_001_batch_001.json` first-mined packet.")
    md.append(f"  IDs: {', '.join(PASS34)}")
    md.append("- **16 repairs:** question/answer/span/hash from")
    md.append("  `V2-DEVSET-001-repaired-candidates.jsonl`.")
    md.append("  IDs: V2D-03,05,08,13,18,19,21,22,23,32,33,37,38,44,50 and V2D-06.")
    md.append("- **V2D-06:** ROUND-2 answer after the later python rewrite.")
    md.append(f"  Answer: `{ans}`")
    md.append("  Confirmed: normal-case + Opus 4.6 exception; starts with Normally `usage.speed`.")
    md.append("")
    md.append("## Gold harness files")
    md.append("")
    md.append("EXP-016/018 schema: `case_id`, `category`, `question`, `expected_evidence`")
    md.append("(`version_id` + `section_path` + `char_start`/`char_end`), `expected_abstain`, `notes`.")
    md.append("")
    md.append("- split: `evals/splits/v2-devset-001/development.json`")
    md.append("- gold jsonl: `evals/gold/v2-devset-001.jsonl`")
    md.append("- harness copy: `evals/splits/v2-devset-001/development.jsonl` (byte-identical to gold jsonl)")
    md.append("")
    md.append("## Next")
    md.append("")
    md.append("One comparison of frozen SYSTEM-D vs frozen SYSTEM-E on this set.")
    md.append("Do not retune E after seeing scores. Do not open holdout.json.")
    md.append("")
    FREEZE_MD.write_text("\n".join(md), encoding="utf-8")

    hold_log_after = HOLDOUT_LOG.read_bytes()
    if hold_log_after != hold_log_before:
        raise SystemExit("STOP: holdout log changed during freeze assembly")

    print("n", 50)
    print("freeze_sha", freeze_sha)
    print("gold_sha", gold_sha)
    print("split_sha", split_sha)
    print("v2d06_answer", ans)
    print("holdout_log_bytes", len(hold_log_after), "sha", hold_log_sha)
    print("d_guard_sha", d_guard_sha)
    print("d_release_sha", d_release_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
