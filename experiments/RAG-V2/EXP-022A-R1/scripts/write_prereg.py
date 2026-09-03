#!/usr/bin/env python3
"""Write EXP-022A-R1 preregistration BEFORE any CE logits are generated."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/rag-v1/repo/production-rag-v1")
OUT = ROOT / "experiments/RAG-V2/EXP-022A-R1"


def main() -> int:
    now = datetime.now(UTC).replace(microsecond=0)
    now_et = now.astimezone(ZoneInfo("America/New_York"))
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_et = now_et.strftime("%Y-%m-%dT%H:%M:%S%z")
    ts_et = ts_et[:-2] + ":" + ts_et[-2:]

    obj = {
        "experiment_id": "EXP-022A-R1",
        "title": "CONTROLLED CE REPLAY + SYSTEM-J RECOGNIZABILITY",
        "status": "AUTHORIZED_SINGLE_DEVELOPMENT_REPLAY",
        "phase": "preregistration_before_any_raw_CE_logits_are_generated",
        "chatgpt_authorization": "EXP-022A-R1 AUTHORIZED after EXP-022A STOPPED_MISSING_STORED_H_CE_LOGITS",
        "protocol_copy": "/workspace/NATQ-001-post/EXP-022A-R1-ASSIGNMENT.md",
        "chatgpt_source": "/workspace/chatgpt-after-exp-022a.txt",
        "preregistered_at_utc": ts,
        "preregistered_at_et": ts_et,
        "scored_before_prereg_hash": False,
        "tuned_after_seeing_scores": False,
        "n_evals": 1,
        "second_run_forbidden": True,
        "retune_forbidden": True,
        "holdout_run_forbidden": True,
        "release_freeze_forbidden": True,
        "development_replay": True,
        "not_independent_validation": True,
        "not_EVAL_NATQ_VAL_002": True,
        "not_a_second_validation_claim": True,
        "not_a_release_evaluation": True,
        "not_a_holdout_evaluation": True,
        "original_EXP-022A": {
            "status": "CLOSED",
            "closed_as": "STOPPED_MISSING_STORED_H_CE_LOGITS",
            "scored": False,
            "EXP-022A_CE_RECOGNIZABILITY_SUPPORTED": "unevaluated",
            "do_not_modify_or_rewrite_EXP-022A": True,
            "produced_no_CE_scoring": True,
            "produced_no_mechanism_result": True,
        },
        "do_not_modify_SYSTEM_H": True,
        "do_not_modify_SYSTEM_I": True,
        "do_not_modify_SYSTEM_J": True,
        "do_not_modify_SYSTEM_K": True,
        "do_not_overwrite_SYSTEM_G": True,
        "do_not_overwrite_SYSTEM_E": True,
        "do_not_test_SYSTEM_K": True,
        "do_not_rerun_SYSTEM_A": True,
        "do_not_rerun_BM25": True,
        "do_not_rerun_dense": True,
        "do_not_rerun_E_L10_discovery": True,
        "do_not_rerun_projection": True,
        "do_not_rerun_parent_discovery": True,
        "do_not_use_0_7_0_3_blend": True,
        "do_not_use_retrieval_norm": True,
        "do_not_use_a_norm": True,
        "do_not_use_BM25_or_projection_in_ranking": True,
        "do_not_use_MMR": True,
        "do_not_use_section_or_diversity_bonuses": True,
        "do_not_build_coverage_aware_selector": True,
        "do_not_change_W_L_P": True,
        "do_not_change_CE": True,
        "do_not_open_holdout_json": True,
        "do_not_modify_historical_EVAL_NATQ_VAL_001_artifacts": True,
        "do_not_fabricate_historical_logits": True,
        "natq_validation_status": "DEVELOPMENT / MODEL-SELECTION DATA; not independent validation",
        "environment_drift_note": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical PostgreSQL 16.13 / pgvector 0.6.0. CE replay uses stored membership so should not depend on pgvector; still record drift.",
        "hypothesis": {
            "statement": (
                "A single frozen-CE pass over the exact stored SYSTEM-J candidate memberships "
                "(which include every SYSTEM-H candidate) lets us rank ARM H (H subset) vs ARM J "
                "(full J) CE-only. If J's extra evidence is recognizable, J CE-only strict Recall@10 "
                "improves over H by >=2 cases and span Recall@10 by >=2 spans with at most one strict regression."
            ),
            "question": "Are the additional candidates recovered by SYSTEM-J recognizable as relevant by the frozen cross-encoder when both arms are ranked CE-only from one shared CE pass?",
            "this_is_a_reranker_recognizability_diagnostic": True,
            "this_is_a_development_replay": True,
            "this_is_not_independent_validation": True,
            "this_is_not_a_release_architecture": True,
            "one_CE_call_per_query_on_exact_J_IDS_stored_order": True,
            "do_not_score_H_and_extras_as_two_separate_CE_passes": True,
            "no_new_retrieval_prior": True,
            "no_coverage_aware_selection": True,
            "no_SYSTEM_K": True,
            "no_blend": True,
            "no_BM25_in_ranking": True,
            "no_projection_in_ranking": True,
            "no_a_norm": True,
            "no_retrieval_norm": True,
            "no_named_case_handling": True,
            "no_second_variant": True,
        },
        "candidate_membership": {
            "source": "experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl",
            "H_IDS": "stored system_h_union_ids",
            "J_IDS": "stored system_j_union_ids",
            "require_H_subset_J_every_query": True,
            "exact_H_pairs": 4753,
            "exact_J_pairs": 7485,
            "exact_J_only_pairs": 2732,
            "do_not_rerun_retrieval": True,
            "STOP_if_counts_mismatch": True,
        },
        "arms": {
            "ranking_key": [
                "raw frozen CE logit DESC",
                "canonical chunk_id ASC",
            ],
            "ARM_H": {
                "name": "SYSTEM-H candidate pool ranked CE-only",
                "pool": "exact stored system_h_union_ids from EXP-021A-pools.jsonl",
                "logits": "raw CE logits from THIS replay's single J-pool CE pass, restricted to H_IDS",
                "n_H_candidates_expected": 4753,
            },
            "ARM_J": {
                "name": "SYSTEM-J candidate pool ranked CE-only",
                "pool": "exact stored system_j_union_ids from EXP-021A-pools.jsonl",
                "logits": "raw CE logits from THIS replay's single J-pool CE pass",
                "n_J_candidates_expected": 7485,
            },
            "one_CE_call_per_query": "score exact J_IDS texts in stored order once; do not score H and extras as two separate CE passes (that would change length-bucket batches)",
        },
        "frozen_identities": {
            "SYSTEM-H-V2-DEV-CANDIDATE": {
                "config_hash": "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a",
                "file_sha256": "7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475",
                "path": "experiments/RAG-V2/SYSTEM-H-V2-DEV-CANDIDATE/SYSTEM-H-V2-DEV-CANDIDATE.json",
            },
            "SYSTEM-J-LOCAL-W20-UNION": {
                "config_hash": "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787",
                "file_sha256": "70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd",
                "path": "experiments/RAG-V2/SYSTEM-J-LOCAL-W20-UNION/SYSTEM-J-LOCAL-W20-UNION.json",
            },
            "SYSTEM-K-W20-SECTION-COMPRESS": {
                "config_hash": "eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8",
                "file_sha256": "20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e",
                "path": "experiments/RAG-V2/SYSTEM-K-W20-SECTION-COMPRESS/SYSTEM-K-W20-SECTION-COMPRESS.json",
                "not_tested": True,
            },
        },
        "cross_encoder": {
            "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
            "revision": "233902d25c440f23af6f7d6e94d2946bac0bee0a",
            "artifact_sha256": "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a",
            "constructor": "CrossEncoderReranker(pad='batch', bucket_by_length=True)",
            "fast": False,
            "threads": 4,
            "pad": "batch",
            "bucket_by_length": True,
            "batch_size": 16,
            "max_length": 512,
            "truncation": "longest_first",
            "padding": "PERF-003 D1 dynamic padding",
            "score_pairs_returns_raw_logits_and_unpermutes_buckets": True,
        },
        "observability": {
            "persist_every_raw_CE_logit": True,
            "jsonl": "logs/EXP-022A-R1-raw-ce-logits.jsonl",
            "append_safe": True,
            "row_minimum": [
                "case_id",
                "chunk_id",
                "candidate_arm (H if in H_IDS else J_ONLY)",
                "raw_ce_logit (float)",
                "raw_ce_logit_hex (IEEE float.hex() or struct.pack big-endian double hex)",
                "input_hash (sha256 of deterministic payload: case_id, chunk_id, query, text)",
                "ce_artifact_sha",
                "tokenizer_identity (path or tokenizer.json sha)",
                "max_length=512",
                "query association (case_id + query sha256, not holdout questions)",
            ],
            "persistence_gate_before_aggregate_metrics": {
                "exactly_7485_unique_case_id_chunk_id_J_pairs": True,
                "exactly_4753_H_member_pairs": True,
                "exactly_2732_J_only_pairs": True,
                "zero_missing_logits": True,
                "zero_duplicate_disagreements": True,
                "every_H_candidate_has_one_logit": True,
                "every_J_candidate_has_one_logit": True,
                "hash_completed_jsonl": True,
                "if_fails": "STOP WITHOUT COMPUTING MECHANISM METRICS; write STOP report",
            },
        },
        "dataset": {
            "name": "NATQ-001",
            "split": "validation",
            "role": "DEVELOPMENT / MODEL-SELECTION DATA",
            "not_independent_validation": True,
            "n": 40,
            "path": "evals/splits/natq-001/validation.jsonl",
            "validation_sha256": "a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6",
            "holdout_sha256_recorded_file_not_opened": "6a7cf781c7538106605e8c85607405cd3dee2db37fdbb556aaadc913b3141dd3",
            "holdout_lock_sha256": "03e0d5749e61e73e6b9582109a74a4a9672610b7bf794daf25f46999e5ad40b2",
            "snapshot": "snap_689e336380a054d8039dc35b2c09cd0a",
            "chunk_set": "cs_v1_control",
            "load_only_validation_jsonl": True,
            "do_not_open_natq_holdout_json": True,
            "do_not_open_v1_holdout_json": True,
            "stored_H_J_pools": "experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl",
        },
        "PRIMARY": {
            "metric": "strict_full_case_Recall@10",
            "definition": "A case succeeds iff ALL gold evidence spans have at least one covering canonical chunk in the CE-only top-10 (same overlap rule as EXP-017 span_in_hits / EVAL-NATQ-VAL-001). Ranking is raw frozen CE logit DESC, then canonical chunk_id ASC. No BM25, projection, a_norm, retrieval_norm, or 0.7/0.3 blend.",
            "comparison": "H CE-only vs J CE-only",
            "report": "numerator/40",
        },
        "SECONDARY": [
            {"metric": "evidence_span_Recall@10", "report": "numerator/53"},
            {
                "metric": "MRR",
                "definition": "summarise definition: mean 1/rank over all gold spans, 0 if rank missing",
            },
            {
                "metric": "document_Recall@10",
                "definition": "cases with all gold version_ids in CE-only top-10; also mean document recall",
            },
            {
                "metric": "multi_span_strict_Recall@10",
                "definition": "same 12-case def as EXP-021A: n_gold_spans>1 or tag multi_span",
            },
            {"metric": "multi_span_span_Recall@10"},
            {"metric": "OpenAI_strict_and_span"},
            {"metric": "Anthropic_strict_and_span"},
        ],
        "PAIRED": {
            "per_case": [
                "H CE-only strict PASS/FAIL",
                "J CE-only strict PASS/FAIL",
            ],
            "aggregate": [
                "J rescues over H",
                "J regressions vs H",
                "both pass",
                "both fail",
            ],
            "mcnemar_exact_p": "diagnostic; n01=J success H fail, n10=J fail H success; no significance claim required",
        },
        "MECHANISM_GATE": {
            "label": "EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED",
            "do_not_change_after_seeing_results": True,
            "preserve_original_unobserved_EXP-022A_gate": True,
            "this_is_a_mechanism_gate_not_a_release_gate": True,
            "EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED_iff_ALL": [
                "J CE-only strict R@10 improves over H CE-only by >= 2 cases",
                "J CE-only span R@10 improves over H CE-only by >= 2 spans",
                "J strict regressions vs H <= 1",
                "no integrity/provenance failure",
            ],
        },
        "diagnostics_after_aggregates": {
            "four_SYSTEM_J_recovered_spans": [
                {"case_id": "NATQ-C-004", "span_index": 0},
                {"case_id": "NATQ-C-005", "span_index": 1},
                {"case_id": "NATQ-C-044", "span_index": 0},
                {"case_id": "NATQ-C-044", "span_index": 1},
            ],
            "report_per_span": [
                "raw CE logit",
                "J CE-only rank",
                "enters top10 yes/no",
                "n higher-ranked same version_id",
                "n higher-ranked same section_path",
            ],
            "diagnostic_only": True,
            "no_named_case_handling": True,
            "multi_span_per_case": [
                "required span count",
                "n in J pool",
                "n in J CE-only top10",
                "CE-only ranks of every in-pool gold span",
                "unique version_ids in top10",
                "unique section_paths in top10",
                "redundancy count (top10 minus unique version; top10 minus unique section)",
            ],
        },
        "latency": {
            "report": [
                "total CE wall time",
                "mean/median per-query CE time",
                "H-pair count",
                "J-only pair count",
                "full J-pair count",
            ],
            "no_cross_host_architecture_claim": True,
        },
        "harness_fix_non_scoring_follow_up": {
            "defect": "EVAL-NATQ-VAL-001 did not persist full-pool raw CE logits",
            "requirement": (
                "Future development/validation reranker executions must persist: "
                "candidate membership, raw reranker logits, query/candidate association, "
                "model fingerprint, input/config fingerprint"
            ),
            "do_not_modify_historical_EVAL_NATQ_VAL_001": True,
            "do_not_fabricate_historical_logits": True,
            "non_scoring": True,
        },
        "holdout_protection": {
            "natq_holdout_access_log_before": {
                "path": "evals/splits/natq-001/holdout-access.log.jsonl",
                "bytes": 0,
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            "natq_holdout_access_log_after_must_equal_before": True,
            "v1_holdout_access_log": {
                "path": "evals/splits/gold150-v1/holdout-access.log.jsonl",
                "bytes": 235,
                "sha256": "45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3",
            },
            "do_not_open_natq_holdout_json": True,
            "do_not_open_v1_holdout_json": True,
        },
        "STOP": {
            "after": "EXP-022A-R1 controlled CE replay and REPORT",
            "do_not_build_coverage_aware_selector": True,
            "do_not_test_SYSTEM_K": True,
            "do_not_modify_W_L_P": True,
            "do_not_change_CE": True,
            "do_not_run_holdout": True,
            "return_to_coordinator_ChatGPT": True,
        },
    }

    import json

    pre_json = OUT / "EXP-022A-R1-preregistration.json"
    pre_md = OUT / "EXP-022A-R1-preregistration.md"
    pre_sha_path = OUT / "EXP-022A-R1-preregistration.json.sha256"
    pre_json.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sha = hashlib.sha256(pre_json.read_bytes()).hexdigest()
    pre_sha_path.write_text(sha + "\n", encoding="utf-8")

    md = f"""# EXP-022A-R1 — CONTROLLED CE REPLAY + SYSTEM-J RECOGNIZABILITY

**PREREGISTRATION. HASHED BEFORE ANY RAW CE LOGITS ARE GENERATED.**

Written {ts} UTC ({ts_et} ET). ChatGPT-authorized EXP-022A-R1 after EXP-022A STOPPED_MISSING_STORED_H_CE_LOGITS. Assignment: `/workspace/NATQ-001-post/EXP-022A-R1-ASSIGNMENT.md`. ChatGPT source: `/workspace/chatgpt-after-exp-022a.txt`.

Machine-readable twin: `experiments/RAG-V2/EXP-022A-R1/EXP-022A-R1-preregistration.json` sha256 `{sha}`.

NATQ-001 validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**. This is a **development replay / diagnostic**, not independent validation, not EVAL-NATQ-VAL-002, not a second validation claim, not a release evaluation, not a holdout evaluation. Locked holdout n=60 remains unseen. Do not open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json`.

Original EXP-022A is **CLOSED** as `STOPPED_MISSING_STORED_H_CE_LOGITS`. It produced no CE scoring and no mechanism result. `EXP-022A_CE_RECOGNIZABILITY_SUPPORTED` remains **unevaluated**. Do **not** modify or rewrite EXP-022A.

One controlled CE replay. Score frozen CE once over exact stored SYSTEM-J candidate memberships (which include H). Persist every raw CE logit. Then CE-only rank ARM H (H subset) vs ARM J (full J). Ranking: raw CE logit DESC, canonical chunk_id ASC.

---

## Frozen identities (not modified)

| | |
| --- | --- |
| SYSTEM-H-V2-DEV-CANDIDATE config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| SYSTEM-J-LOCAL-W20-UNION config_hash | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| SYSTEM-J file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |
| SYSTEM-K-W20-SECTION-COMPRESS config_hash (not tested) | `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` |
| SYSTEM-K file SHA256 | `20d967e2f56fed88f617d1c18474abc86b9f984f32a30cc195f42d6fef03ad7e` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| chunk set | `cs_v1_control` |
| validation.jsonl | sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` n=40 |
| stored pools | `experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl` |
| frozen CE ONNX sha | `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a` |
| frozen CE revision | `233902d25c440f23af6f7d6e94d2946bac0bee0a` |

Exact stored membership counts (STOP if mismatch): H pairs **4753**, J pairs **7485**, J-only **2732**. H_IDS ⊆ J_IDS every query.

Closed ceilings (not modified): SYSTEM-H 34/40 cases, 46/53 spans, mean pool 118.83; SYSTEM-J 37/40, 50/53, 187.12; SYSTEM-K 35/40, 48/53, 146.78 (K not tested). EXP-021A_SUPPORTED=true. EXP-021B_SUPPORTED=false. EXP-022A closed unscored.

## Question

Are the additional candidates recovered by SYSTEM-J recognizable as relevant by the frozen cross-encoder when both arms are ranked CE-only from **one shared CE pass** over exact stored J memberships?

This is a **reranker recognizability diagnostic / development replay**, not a release architecture.

## Ranking (both arms)

raw frozen CE logit DESC, then deterministic canonical chunk_id ASC.

Do **not** combine CE with BM25, projection scores, a_norm, retrieval_norm, MMR, section/diversity bonuses, or the SYSTEM-H 0.7/0.3 blend.

## ONE CE call per query

For each of 40 queries, ONE CE call on the exact J_IDS texts (stored order), batch_size=16, D1 bucketing (`CrossEncoderReranker(pad='batch', bucket_by_length=True)`, fast=False, threads=4, max_length=512, longest_first). Do **not** score H and extras as two separate CE passes (that would change length-bucket batches). Persist every pair immediately to `logs/EXP-022A-R1-raw-ce-logits.jsonl`.

## Persistence gate (before aggregate metrics)

Verify exactly 7485 unique (case_id, chunk_id) J pairs, 4753 H-member, 2732 J-only, zero missing, zero duplicate disagreements, every H and every J candidate has one logit. Hash the completed jsonl. If this gate fails: **STOP WITHOUT computing mechanism metrics**.

## PRIMARY

strict full-case Recall@10: H CE-only vs J CE-only. Report numerator/40.

## SECONDARY

evidence-span Recall@10 numerator/53; MRR (summarise definition: mean 1/rank over all gold spans, 0 if rank missing); document Recall@10; multi-span strict Recall@10 and multi-span span Recall@10 (same 12-case definition as EXP-021A: n_gold_spans>1 or tag multi_span); OpenAI/Anthropic strict and span.

## PAIRED

J rescues over H, J regressions vs H, both pass, both fail. McNemar exact p diagnostic (n01=J success H fail, n10=J fail H success). No significance claim required.

## GATE (do not change after seeing results)

`EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED` iff ALL:

1. J CE-only strict R@10 improves over H CE-only by >= 2 cases
2. J CE-only span R@10 improves over H CE-only by >= 2 spans
3. J strict regressions vs H <= 1
4. no integrity/provenance failure

Preserve the original unobserved EXP-022A gate. Mechanism gate, not release gate.

## Diagnostics (after aggregates only)

Four SYSTEM-J recovered spans: NATQ-C-004 s0, NATQ-C-005 s1, NATQ-C-044 s0, NATQ-C-044 s1. For each: raw CE logit, J CE-only rank, whether top10, n higher-ranked same version_id, n higher-ranked same section_path. Diagnostic only. No named-case rules.

Multi-span: required span count; n in J pool; n in J CE-only top10; CE-only ranks of every in-pool gold span; unique version_ids / section_paths in top10; redundancy count (top10 minus unique version; top10 minus unique section).

## Latency

total CE wall time; mean/median per-query CE time; H-pair count; J-only pair count; full J-pair count. No cross-host architecture claim.

## Harness fix (NON-SCORING follow-up)

EVAL-NATQ-VAL-001 did not persist full-pool raw CE logits. Future development/validation reranker runs must persist candidate membership, raw logits, query/candidate association, model fingerprint, and input/config fingerprint. Do not modify historical EVAL-NATQ-VAL-001 artifacts. Do not fabricate historical logits.

## Environment

Record current environment. Known drift remains: PostgreSQL 16.15 / pgvector 0.8.6 vs historical PostgreSQL 16.13 / pgvector 0.6.0. CE replay uses stored membership so should not depend on pgvector; still record drift.

## Holdout

Before and after: NATQ access log 0 bytes sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. V1 log 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Neither holdout.json may be opened.

## STOP

Return to coordinator ChatGPT. Do not build a coverage-aware selector. Do not test SYSTEM-K. Do not modify W/L/P. Do not change CE. Do not open holdout.
"""
    pre_md.write_text(md, encoding="utf-8")
    print("prereg json sha256", sha)
    print("wrote", pre_json)
    print("wrote", pre_md)
    print("wrote", pre_sha_path)
    got = pre_sha_path.read_text(encoding="utf-8").strip()
    assert got == sha
    print("prereg sha file ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
