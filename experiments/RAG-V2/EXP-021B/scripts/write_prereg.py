#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/rag-v1/repo/production-rag-v1")
OUT = ROOT / "experiments/RAG-V2/EXP-021B"
K_JSON = ROOT / "experiments/RAG-V2/SYSTEM-K-W20-SECTION-COMPRESS/SYSTEM-K-W20-SECTION-COMPRESS.json"


def main() -> int:
    k = json.loads(K_JSON.read_text(encoding="utf-8"))
    k_hash = k["config_hash"]
    k_sha = hashlib.sha256(K_JSON.read_bytes()).hexdigest()
    assert k_hash == "eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8"

    now = datetime.now(UTC)
    now_et = now.astimezone(ZoneInfo("America/New_York"))
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_et = now_et.strftime("%Y-%m-%dT%H:%M:%S") + now_et.strftime("%z")
    ts_et = ts_et[:-2] + ":" + ts_et[-2:]

    obj = {
        "experiment_id": "EXP-021B",
        "title": "SECTION-STRATIFIED LOCAL-W20 COMPRESSION",
        "status": "AUTHORIZED_SINGLE_DEVELOPMENT_RUN",
        "phase": "preregistration_before_examining_SYSTEM_K_aggregate_candidate_metrics",
        "chatgpt_authorization": "EXP-021B AUTHORIZED after EXP-021A_SUPPORTED=true",
        "protocol_copy": "/workspace/NATQ-001-post/EXP-021B-ASSIGNMENT.md",
        "chatgpt_source": "/workspace/chatgpt-after-exp-021a.txt",
        "preregistered_at_utc": ts,
        "preregistered_at_et": ts_et,
        "scored_before_prereg_hash": False,
        "tuned_after_seeing_scores": False,
        "n_evals": 1,
        "second_run_forbidden": True,
        "retune_forbidden": True,
        "holdout_run_forbidden": True,
        "release_freeze_forbidden": True,
        "do_not_modify_SYSTEM_H": True,
        "do_not_modify_SYSTEM_I": True,
        "do_not_modify_SYSTEM_J": True,
        "do_not_overwrite_SYSTEM_G": True,
        "do_not_overwrite_SYSTEM_E": True,
        "do_not_run_CE": True,
        "do_not_run_final_ranking": True,
        "do_not_run_blend": True,
        "do_not_run_coverage_selector": True,
        "do_not_run_MMR": True,
        "do_not_run_answer_generation": True,
        "do_not_include_EXP020A_parent_balanced_projection": True,
        "do_not_increase_W": True,
        "do_not_increase_L": True,
        "do_not_increase_P": True,
        "do_not_change_EXTRA_BUDGET_after_seeing_results": True,
        "do_not_try_another_budget": True,
        "EXTRA_BUDGET": 30,
        "natq_validation_status": "DEVELOPMENT / MODEL-SELECTION DATA; not independent validation",
        "environment_drift_note": "PostgreSQL 16.15 / pgvector 0.8.6 vs historical PostgreSQL 16.13 / pgvector 0.6.0. Do not silently treat environments as identical.",
        "hypothesis": {
            "statement": (
                "Section-aware two-pass compression of SYSTEM-J W20-only extras (EXTRA_BUDGET=30, "
                "max two extras per (version_id, section_path), never drop SYSTEM-H) preserves most of "
                "SYSTEM-J's candidate-recall gain while returning the candidate pool close to SYSTEM-H scale "
                "on NATQ-001 validation n=40 (development / model-selection data)."
            ),
            "one_mechanism_only": True,
            "no_ce_change": True,
            "no_blend_change": True,
            "no_L_P_W_parent_count_change": True,
            "no_coverage_selector": True,
            "no_mmr": True,
            "no_learned_weights": True,
            "no_named_case_handling": True,
            "no_parent_balanced_projection": True,
            "no_second_variant": True,
            "no_second_budget": True,
            "use_stored_EXP021A_H_J_ids": True,
            "bm25_recompute_is_score_association_and_identity_check_only": True,
        },
        "system": {
            "name": "SYSTEM-K-W20-SECTION-COMPRESS",
            "config_hash": k_hash,
            "path": "experiments/RAG-V2/SYSTEM-K-W20-SECTION-COMPRESS/SYSTEM-K-W20-SECTION-COMPRESS.json",
            "file_sha256": k_sha,
            "parent_SYSTEM_H_config_hash": "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a",
            "parent_SYSTEM_H_file_sha256": "7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475",
            "parent_SYSTEM_J_config_hash": "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787",
            "parent_SYSTEM_J_file_sha256": "70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd",
            "does_not_overwrite_SYSTEM_I_config_hash": "9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6",
            "pipeline": {
                "frozen_SYSTEM_H": "exact stored system_h_union_ids from EXP-021A-pools.jsonl; never removed; preserve H order",
                "source_extras": "exact stored system_j_union_ids minus H; process extras in stored added_w20 order (must equal J-H)",
                "score_association": (
                    "recompute local_bm25_per_parent_batched(query, parents, W=20) with exact E-L10 semantics used in EXP-021A "
                    "ONLY to attach scores/ranks to already-known W20 ids. VERIFY [h.chunk_id for h in hits] EXACTLY equals "
                    "stored w20_by_parent[vid] for every parent. If mismatch, STOP. Identity check of existing W20, not a new model."
                ),
                "first_parent_association": (
                    "If a chunk appears in multiple parent W20 lists, associate the extra with the FIRST parent in SYSTEM-H "
                    "parent order that listed it (same first-seen as EXP-021A added_w20). Group version_id is that parent. "
                    "Confirm chunk.version_id == that parent (STOP if not)."
                ),
                "grouping": "Group EXTRAS by (version_id, section_path). Canonical section key: json.dumps(section_path if already list else list(section_path), ensure_ascii=True, separators=(',', ':'))",
                "within_group_order": [
                    "local BM25 raw score DESC",
                    "local BM25 rank ASC",
                    "canonical chunk_id ASC",
                ],
                "pass_1_section_coverage": (
                    "Take the best candidate from every group. Rank those group representatives globally by "
                    "(1) local BM25 raw score DESC (2) parent rank ASC (3) local BM25 rank ASC (4) version_id ASC "
                    "(5) section_path ASC using the canonical JSON string (6) canonical chunk_id ASC. "
                    "Add until EXTRA_BUDGET=30 exhausted or none remain."
                ),
                "pass_2_limited_same_section_depth": (
                    "If budget remains: take the second-best candidate, if any, from each group. Order with the EXACT "
                    "same global deterministic keys as Pass 1. Add until EXTRA_BUDGET=30 reached. Do NOT take a third "
                    "candidate from a section."
                ),
                "pool": "SYSTEM-K = H (all, never removed, preserve H order) then selected extras in selection order (Pass 1 then Pass 2). Dedup by chunk_id. Assert set(H)subseteq set(K). Assert len(selected extras)<=30. Assert no third from same group.",
                "unchanged_global_lanes": "Do not re-run SYSTEM-A or projection for the K pool itself. Use stored H/J ids. BM25 recompute is score-association + identity check only. EXP-020A parent-balanced projection top-1 is NOT included. W=20 L=10 P=20 PARENT_N=10 unchanged.",
            },
        },
        "algorithm": {
            "EXTRA_BUDGET": 30,
            "compression": "section-stratified two-pass on J-H extras; max 2 per (version_id, section_path); max 30 extras/query",
            "never_drop_H": True,
            "max_per_group": 2,
            "no_learned_weights": True,
            "no_mmr_lambda": True,
            "no_tuning": True,
            "budget_selected_from_engineering_pool_size_target_NOT_from_gold_case_identities": True,
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
            "load_only_validation_jsonl": True,
            "do_not_open_natq_holdout_json": True,
            "do_not_open_v1_holdout_json": True,
            "do_not_open_evals_splits_natq-001_holdout.json": True,
            "do_not_open_evals_splits_gold150-v1_holdout.json": True,
            "stored_pools": "experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl",
        },
        "baseline_SYSTEM_H": {
            "candidate_full_case_Recall_at_pool": "34/40",
            "candidate_span_micro": "46/53",
            "mean_pool": 118.83,
            "SYSTEM_H_config_hash": "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a",
        },
        "baseline_SYSTEM_J": {
            "candidate_full_case_Recall_at_pool": "37/40",
            "candidate_span_micro": "50/53",
            "multi_span_all_gold_in_pool": "10/12",
            "mean_pool": 187.12,
            "mean_additions": 68.3,
            "candidate_generation_latency_ms_mean": 1301.0,
            "SYSTEM_J_config_hash": "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787",
            "EXP-021A_SUPPORTED": True,
        },
        "PRIMARY": {
            "metric": "candidate_full_case_Recall@pool",
            "definition": "A case succeeds iff EVERY gold evidence span overlaps at least one canonical chunk in the SYSTEM-K candidate union (same overlap rule as EXP-017 span_in_hits / EXP-021A). No top-10 ranking.",
            "baseline_H": "34/40",
            "baseline_J": "37/40",
            "report": "numerator/40",
        },
        "SECONDARY": [
            {"metric": "candidate_span_Recall@pool", "baseline_H": "46/53", "baseline_J": "50/53"},
            {
                "metric": "multi_span_all_gold_in_pool",
                "definition": "same 12-case definition as EXP-021A: n_gold_spans>1 or tag multi_span",
            },
            {"metric": "OpenAI_and_Anthropic_candidate_recall_case_and_span"},
            {"metric": "mean_median_p95_pool_size"},
            {"metric": "mean_median_additions_K_extras_selected"},
            {
                "metric": "compression_ratio_vs_SYSTEM_J",
                "definition": "mean_K / mean_J and 1 - that",
            },
            {
                "metric": "candidate_generation_latency",
                "definition": (
                    "compression selection mean/median ms (the new work); inherited SYSTEM-J candidate-gen mean 1301.0 ms "
                    "from EXP-021A (W20 already computed); SYSTEM-K candidate-gen = J cg + compression "
                    "(do not pretend A/projection were re-run); separately report W20 score-association recompute mean ms; "
                    "estimated CE pairs = sum(pool_size); CE was NOT run"
                ),
            },
            {"metric": "exact_SYSTEM_H_superset_check"},
        ],
        "MECHANISM_GATE": {
            "label": "EXP-021B_SUPPORTED",
            "do_not_change_after_seeing_results": True,
            "do_not_lower_gate": True,
            "do_not_change_EXTRA_BUDGET_after_seeing_results": True,
            "EXP-021B_SUPPORTED_iff_ALL": [
                "candidate full-case Recall@pool >= 36/40",
                "candidate span Recall@pool >= 49/53",
                "mean candidate pool <= 150",
                "SYSTEM-K contains every SYSTEM-H candidate on every query",
                "no benchmark-integrity or provenance failure",
            ],
            "interpretation": {
                "36_40": "preserves the original qualification threshold",
                "49_53": "retains at least three of SYSTEM-J's four-span improvement over SYSTEM-H",
                "mean_pool_le_150": "requires material compression versus SYSTEM-J",
            },
            "this_is_not_independent_validation": True,
            "this_is_not_a_claim_of_statistical_significance": True,
        },
        "diagnostics_after_aggregates": {
            "four_SYSTEM_J_recovered_spans": [
                {"case_id": "NATQ-C-004", "span_index": 0},
                {"case_id": "NATQ-C-005", "span_index": 1},
                {"case_id": "NATQ-C-044", "span_index": 0},
                {"case_id": "NATQ-C-044", "span_index": 1},
            ],
            "report_per_span": [
                "retained by SYSTEM-K yes/no",
                "group section_path",
                "local BM25 rank",
                "compression pass selected in (1/2/none)",
                "compressed candidate position",
            ],
            "diagnostic_only": True,
            "no_named_case_handling": True,
            "also_report_all_newly_lost_or_newly_retained_gold_spans_vs_SYSTEM_J": True,
            "do_not_increase_W_or_chase": ["NATQ-C-014 s1", "NATQ-C-179 s0", "NATQ-C-026 s1"],
        },
        "anti_overfit": {
            "do_not_increase_W": True,
            "do_not_increase_L_P": True,
            "do_not_alter_parent_count": True,
            "do_not_alter_BM25_weights": True,
            "do_not_alter_CE": True,
            "do_not_add_adjacency_expansion": True,
            "do_not_add_named_case_rules": True,
            "do_not_add_coverage_aware_selector": True,
            "do_not_add_query_rewriting": True,
            "do_not_create_a_second_variant": True,
            "do_not_try_another_budget": True,
            "do_not_include_EXP020A_parent_balanced_projection": True,
            "one_mechanism_one_variant_one_run": True,
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
            "after": "EXP-021B candidate-generation / compression run and REPORT",
            "do_not_run_final_ranking": True,
            "do_not_run_CE": True,
            "do_not_try_another_budget": True,
            "do_not_alter_the_30_candidate_budget_after_results": True,
            "return_to_coordinator_ChatGPT": True,
        },
    }

    pre_json = OUT / "EXP-021B-preregistration.json"
    pre_md = OUT / "EXP-021B-preregistration.md"
    pre_sha_path = OUT / "EXP-021B-preregistration.json.sha256"
    pre_json.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sha = hashlib.sha256(pre_json.read_bytes()).hexdigest()
    pre_sha_path.write_text(sha + "\n", encoding="utf-8")
    print("prereg json sha256", sha)

    md = f"""# EXP-021B — SECTION-STRATIFIED LOCAL-W20 COMPRESSION

**PREREGISTRATION. HASHED BEFORE COMPUTING ANY SYSTEM-K AGGREGATE CANDIDATE METRICS.**

Written {ts} UTC ({ts_et} ET). ChatGPT-authorized EXP-021B after EXP-021A_SUPPORTED=true. Assignment: `/workspace/NATQ-001-post/EXP-021B-ASSIGNMENT.md`.

Machine-readable twin: `experiments/RAG-V2/EXP-021B/EXP-021B-preregistration.json` sha256 `{sha}`.

NATQ-001 validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**. This is not independent validation. Locked holdout n=60 remains unseen. Do not open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json`.

One mechanism. One variant. One run. Candidate-generation / compression only. No CE. No final ranking. No blend. No coverage selector. No MMR. No answer generation. Do not overwrite SYSTEM-H / SYSTEM-I / SYSTEM-J / G / E. Do not increase W/L/P. Do not include EXP-020A parent-balanced projection. Do not change EXTRA_BUDGET after seeing results. Do not try another budget.

---

## Frozen parents (not modified)

| | |
| --- | --- |
| SYSTEM-H-V2-DEV-CANDIDATE config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| SYSTEM-J-LOCAL-W20-UNION config_hash | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| SYSTEM-J file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |
| SYSTEM-I-PARENT-BALANCED-CANDIDATES config_hash (not modified) | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| projection | `ps_v2_ovl_win448_s224` n=18057 |
| validation.jsonl | sha256 `a240958eb6b77b293bd70f717ee60476d2d09b510458057fd927d67359331ad6` n=40 |
| stored pools | `experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl` |

## New identity

| | |
| --- | --- |
| name | `SYSTEM-K-W20-SECTION-COMPRESS` |
| config_hash | `{k_hash}` |
| identity file SHA256 | `{k_sha}` |
| EXTRA_BUDGET | 30 |

## Mechanism (preregistered)

For each of 40 validation cases from stored EXP-021A-pools.jsonl:

- H = exact stored `system_h_union_ids` (list, preserve order)
- J = exact stored `system_j_union_ids`
- EXTRAS = J minus H as sets; process extras in stored `added_w20` order as the J-H list (must equal J-H)
- Parents = stored parents list; parent_rank is 1-based index in that list

Attach to every EXTRA (do not run a NEW retrieval model; do not increase W): parent `version_id`, parent rank used by SYSTEM-H, `section_path` from control chunks (`cs_v1_control`), parent-local BM25 raw score, parent-local BM25 rank, canonical `chunk_id`.

Score/rank association: recompute `local_bm25_per_parent_batched(query, parents, W=20)` with exact E-L10 semantics used in EXP-021A, ONLY to attach scores to already-known W20 ids. VERIFY that for every parent, `[h.chunk_id for h in hits]` EXACTLY equals stored `w20_by_parent[vid]`. If any mismatch, STOP. This is identity check of existing W20, not a new model.

If a chunk appears in multiple parent W20 lists, associate the extra with the FIRST parent in SYSTEM-H parent order that listed it (same first-seen as EXP-021A `added_w20`). Group `version_id` is that parent. Confirm `chunk.version_id == that parent` (STOP if not).

GROUP EXTRAS by `(version_id, section_path)`. Canonical section key: `json.dumps(section_path if already list else list(section_path), ensure_ascii=True, separators=(',', ':'))`.

Within each group order by: (1) local BM25 raw score DESC (2) local BM25 rank ASC (3) canonical chunk_id ASC.

**PASS 1 — SECTION COVERAGE:** Take the best candidate from every group. Rank those group representatives globally by: (1) local BM25 raw score DESC (2) parent rank ASC (3) local BM25 rank ASC (4) version_id ASC (5) section_path ASC (canonical JSON string) (6) canonical chunk_id ASC. Add until EXTRA_BUDGET=30 exhausted or none remain.

**PASS 2 — LIMITED SAME-SECTION DEPTH:** If budget remains, take the second-best candidate, if any, from each group. Order with the EXACT same global deterministic keys as Pass 1. Add until EXTRA_BUDGET=30 reached. Do NOT take a third candidate from a section.

Therefore: max two W20-only additions per `(version_id, section_path)` AND max 30 total W20-only additions/query. No learned weights. No MMR lambda. No tuning.

SYSTEM-K pool = H (all, never removed, preserve H order) then selected extras in selection order (Pass 1 then Pass 2). Dedup by chunk_id. Assert set(H) ⊆ set(K) for every query. Assert len(selected extras) ≤ 30. Assert no third from same group.

Do NOT re-run SYSTEM-A or projection for the K pool itself. Use stored H/J ids. BM25 recompute is score-association + identity check only.

## PRIMARY

candidate full-case Recall@pool. Baseline SYSTEM-H **34/40**. Baseline SYSTEM-J **37/40**.

## SECONDARY

- candidate span Recall@pool, H **46/53**, J **50/53**
- multi-span all-gold-in-pool (same 12-case definition as EXP-021A: n_gold_spans>1 or tag multi_span)
- OpenAI and Anthropic candidate recall (case and span)
- mean / median / p95 pool size
- mean / median additions (K extras selected)
- compression ratio vs SYSTEM-J (mean_K / mean_J and 1 - that)
- candidate-generation latency (compression selection; inherited J cg 1301.0 ms; K = J cg + compression; W20 score-association recompute separately; estimated CE pairs = sum(pool_size); CE was NOT run)
- exact SYSTEM-H superset check

## Gate (do not change after seeing results)

`EXP-021B_SUPPORTED` iff ALL:

1. candidate full-case Recall@pool >= 36/40
2. candidate span Recall@pool >= 49/53
3. mean candidate pool <= 150
4. SYSTEM-K contains every SYSTEM-H candidate on every query
5. no benchmark-integrity or provenance failure

Do NOT change these thresholds after seeing results. Do NOT change EXTRA_BUDGET after seeing results. Do NOT try another budget.

## Diagnostics (after aggregates only)

Four SYSTEM-J recovered spans: NATQ-C-004 s0, NATQ-C-005 s1, NATQ-C-044 s0, NATQ-C-044 s1.

For each: retained by SYSTEM-K yes/no; group section_path; local BM25 rank; compression pass selected in (1/2/none); compressed candidate position.

Diagnostic only. No named-case rule. Also report all newly lost or newly retained gold spans across all 40 vs SYSTEM-J (K vs J membership). Do NOT increase W or chase NATQ-C-014 s1, NATQ-C-179 s0, NATQ-C-026 s1.

## Environment

Record environment again. Known current drift: PostgreSQL 16.15 / pgvector 0.8.6 versus historical PostgreSQL 16.13 / pgvector 0.6.0. The reconstructed candidate baseline has remained exact so far, but preserve this as an explicit reproducibility note. Do not silently treat environments as identical.

## Holdout

Before and after: NATQ access log 0 bytes sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. V1 log 235 bytes sha `45b83a77f6f332174d641956f076dd0c0cae44fe48f4f2892ac7030a4c0143b3`. Neither holdout.json may be opened.

## STOP

Do not run CE. Do not run final ranking. Do not try another budget. Do not alter the 30-candidate budget after results. Return to coordinator ChatGPT.
"""
    pre_md.write_text(md, encoding="utf-8")
    print("wrote", pre_json)
    print("wrote", pre_md)
    print("wrote", pre_sha_path)
    # confirm sha file matches
    got = pre_sha_path.read_text(encoding="utf-8").strip()
    assert got == sha
    print("prereg sha file ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
