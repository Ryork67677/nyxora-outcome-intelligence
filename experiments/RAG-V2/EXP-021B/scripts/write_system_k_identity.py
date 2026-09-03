#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/rag-v1/repo/production-rag-v1")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from rag_v1.ids import config_hash  # noqa: E402

J_PATH = ROOT / "experiments/RAG-V2/SYSTEM-J-LOCAL-W20-UNION/SYSTEM-J-LOCAL-W20-UNION.json"
K_DIR = ROOT / "experiments/RAG-V2/SYSTEM-K-W20-SECTION-COMPRESS"


def main() -> int:
    j = json.loads(J_PATH.read_text(encoding="utf-8"))
    assert j["config_hash"] == "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787"

    now = datetime.now(UTC)
    now_et = now.astimezone(ZoneInfo("America/New_York"))
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    generated_at_et = now_et.strftime("%Y-%m-%dT%H:%M:%S") + now_et.strftime("%z")
    generated_at_et = generated_at_et[:-2] + ":" + generated_at_et[-2:]

    cfg = deepcopy(j["config"])
    cfg["name"] = "SYSTEM-K-W20-SECTION-COMPRESS"
    cfg["parent_system_j"] = "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787"
    cfg["one_change_from_J"] = (
        "two-pass section-stratified compression of SYSTEM-J W20-only extras (J minus H) onto frozen SYSTEM-H: "
        "EXTRA_BUDGET=30; group extras by (version_id, section_path); within-group order local BM25 raw score DESC, "
        "local BM25 rank ASC, canonical chunk_id ASC; Pass 1 take the best from every group ranked globally by "
        "local BM25 raw score DESC, parent rank ASC, local BM25 rank ASC, version_id ASC, section_path ASC "
        "(canonical JSON string), canonical chunk_id ASC until budget exhausted; Pass 2 take the second-best from "
        "each group with the same global keys until EXTRA_BUDGET=30; never take a third from a section; never drop "
        "any SYSTEM-H candidate; preserve H order then selected extras in selection order; no learned weights, no MMR, "
        "no tuning. Does not increase W/L/P. Does not include EXP-020A parent-balanced projection. No CE, no blend, "
        "no coverage selector, no final top10."
    )
    cfg["extra_budget"] = 30
    cfg["compression"] = (
        "section-stratified two-pass on J-H extras; max 2 per (version_id, section_path); max 30 extras/query"
    )
    cfg["local_w20_union"] = True
    cfg["candidate_generation_only"] = True
    cfg["exp021b_runs_ce"] = False
    cfg["exp021b_runs_final_ranking"] = False
    cfg["exp021b_prereg"] = "experiments/RAG-V2/EXP-021B/EXP-021B-preregistration.md"

    k_hash = config_hash(cfg)
    print("SYSTEM-K config_hash", k_hash)

    parents = deepcopy(j["parents"])
    parents["SYSTEM-J-LOCAL-W20-UNION"] = "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787"

    ce = deepcopy(j["cross_encoder"])
    ce["note"] = "Frozen SYSTEM-H CE identity retained; EXP-021B does not run CE."

    obj = {
        "name": "SYSTEM-K-W20-SECTION-COMPRESS",
        "status": "DEVELOPMENT",
        "DEVELOPMENT_ARCHITECTURE_FROZEN": False,
        "RELEASE_FROZEN": False,
        "VALIDATION_RUN": False,
        "NEW_HOLDOUT_RUN": False,
        "independently_validated": False,
        "does_not_overwrite_SYSTEM_H": True,
        "does_not_overwrite_SYSTEM_I": True,
        "does_not_overwrite_SYSTEM_J": True,
        "does_not_overwrite_SYSTEM_G": True,
        "does_not_overwrite_SYSTEM_G_CE_D1": True,
        "does_not_overwrite_SYSTEM_E": True,
        "NOT_a_release_freeze": True,
        "kind": "development_candidate_generation_identity",
        "generated_at": generated_at,
        "generated_at_et": generated_at_et,
        "parent_SYSTEM_H_config_hash": "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a",
        "parent_SYSTEM_H_file_sha256": "7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475",
        "parent_SYSTEM_J_config_hash": "b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787",
        "parent_SYSTEM_J_file_sha256": "70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd",
        "does_not_overwrite_SYSTEM_I_config_hash": "9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6",
        "candidate_generation_only": True,
        "exp021b_runs_ce": False,
        "exp021b_runs_final_ranking": False,
        "config": cfg,
        "config_hash": k_hash,
        "parents": parents,
        "snapshot": j["snapshot"],
        "chunk_set": j["chunk_set"],
        "projection_set_id": j["projection_set_id"],
        "projection_config_hash": j["projection_config_hash"],
        "encoder": j["encoder"],
        "cross_encoder": ce,
        "parent_n": 10,
        "W": 20,
        "L": 10,
        "P": 20,
        "extra_budget": 30,
        "note": (
            "NEW identity. Frozen SYSTEM-H candidate pool PLUS a deterministic two-pass "
            "section-stratified compressed subset of SYSTEM-J W20-only extras (EXTRA_BUDGET=30). "
            "Does not overwrite SYSTEM-H/I/J/G/E. Candidate-generation / compression only. Not a release freeze. "
            "NATQ-001 validation n=40 is DEVELOPMENT / MODEL-SELECTION DATA. Holdout unopened. "
            "Does not include EXP-020A parent-balanced projection."
        ),
    }

    k_json = K_DIR / "SYSTEM-K-W20-SECTION-COMPRESS.json"
    k_json.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    file_sha = hashlib.sha256(k_json.read_bytes()).hexdigest()
    print("SYSTEM-K file sha256", file_sha)
    print("generated_at", generated_at)
    print("generated_at_et", generated_at_et)

    obj2 = json.loads(k_json.read_text(encoding="utf-8"))
    assert config_hash(obj2["config"]) == k_hash
    assert obj2["config_hash"] == k_hash

    md = f"""# SYSTEM-K-W20-SECTION-COMPRESS

NEW development identity. Frozen SYSTEM-H candidate pool PLUS a deterministic two-pass section-stratified compressed subset of SYSTEM-J W20-only extras (`EXTRA_BUDGET=30`). Written {generated_at} UTC ({generated_at_et} ET). Does **not** overwrite SYSTEM-H / SYSTEM-I / SYSTEM-J / SYSTEM-G / SYSTEM-E. Candidate-generation / compression only. EXP-021B does not run CE or final ranking.

| | |
| --- | --- |
| name | `SYSTEM-K-W20-SECTION-COMPRESS` |
| **config_hash** | `{k_hash}` |
| file SHA256 | `{file_sha}` |
| parent SYSTEM-H config_hash | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| parent SYSTEM-H file SHA256 | `7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475` |
| parent SYSTEM-J config_hash | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| parent SYSTEM-J file SHA256 | `70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd` |
| does not overwrite SYSTEM-I config_hash | `9103a51eaaebcbc581df452279ea06c880abb7524053606428dfd77649d4b3d6` |
| status | DEVELOPMENT |
| DEVELOPMENT_ARCHITECTURE_FROZEN | false |
| RELEASE_FROZEN | false |
| extra_budget | 30 |
| holdout | UNTOUCHED |

`config_hash` is `rag_v1.ids.config_hash` over the `config` object only.

## One change from SYSTEM-J

Keep every frozen SYSTEM-H candidate (never removed; preserve H order). Compress SYSTEM-J's W20-only extras (`J minus H`, processed in stored `added_w20` order) with a two-pass section-stratified algorithm:

- `EXTRA_BUDGET = 30` extras/query maximum.
- Group extras by `(version_id, section_path)` from `cs_v1_control`. Canonical section key is `json.dumps(section_path, ensure_ascii=True, separators=(',', ':'))`.
- Within each group order by local BM25 raw score DESC, local BM25 rank ASC, canonical `chunk_id` ASC.
- Pass 1 (section coverage): take the best candidate from every group; rank those representatives globally by local BM25 raw score DESC, parent rank ASC, local BM25 rank ASC, `version_id` ASC, section_path ASC (canonical JSON string), canonical `chunk_id` ASC; add until budget exhausted.
- Pass 2 (limited same-section depth): if budget remains, take the second-best from each group with the same global keys; add until 30; never take a third from a section.

Therefore: max two W20-only additions per `(version_id, section_path)` AND max 30 total W20-only additions/query. No learned weights. No MMR lambda. No tuning.

SYSTEM-K pool = H (all) then selected extras in selection order (Pass 1 then Pass 2). Dedup by `chunk_id`. Exact SYSTEM-H superset on every query.

Does **not** include EXP-020A parent-balanced projection top-1. Does not increase W/L/P. Does not re-run SYSTEM-A or projection for the K pool itself. Local BM25 W=20 recompute is score-association + identity check of stored `w20_by_parent` only.

## Frozen knobs unchanged

L=10, P=20, W=20, PARENT_N=10, SYSTEM-A, E-L10, projection set `ps_v2_ovl_win448_s224`, MiniLM, CE identity (unused in EXP-021B), blend 0.7/0.3 (unused in EXP-021B). Inherited SYSTEM-J `local_w20_union = true`.

## Do-nots

Do not overwrite SYSTEM-H, SYSTEM-I, SYSTEM-J, SYSTEM-G, SYSTEM-E, `cs_v1_control`, `ps_v2_ovl_win448_s224`. Do not open holdout. Do not run CE/final ranking in EXP-021B. Do not increase W/L/P. Do not change EXTRA_BUDGET after seeing results. Do not freeze as a release.
"""
    k_md = K_DIR / "SYSTEM-K-W20-SECTION-COMPRESS.md"
    k_md.write_text(md, encoding="utf-8")
    print("wrote", k_json)
    print("wrote", k_md)

    h = hashlib.sha256
    assert (
        h((ROOT / "experiments/RAG-V2/SYSTEM-H-V2-DEV-CANDIDATE/SYSTEM-H-V2-DEV-CANDIDATE.json").read_bytes()).hexdigest()
        == "7cd3a5f3d5fcf9c66561c9e9cbfbc213f49e6efa0fdf0005869b085c3eafe475"
    )
    assert (
        h((ROOT / "experiments/RAG-V2/SYSTEM-I-PARENT-BALANCED-CANDIDATES/SYSTEM-I-PARENT-BALANCED-CANDIDATES.json").read_bytes()).hexdigest()
        == "63a78f1d88876c3f55033dc13ce3e6bad1fe768ce5252d315f31652769a9fd19"
    )
    assert (
        h((ROOT / "experiments/RAG-V2/SYSTEM-J-LOCAL-W20-UNION/SYSTEM-J-LOCAL-W20-UNION.json").read_bytes()).hexdigest()
        == "70acac77f33dbe1f7fc0f2e9b81f8a995c7fd0e9f47bab662f03f12cdecc0fdd"
    )
    print("H/I/J unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
