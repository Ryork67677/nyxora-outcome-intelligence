#!/usr/bin/env python3
"""EXP-019B: one preregistered CE-necessity ablation (G vs G-NO-CE).

PREREG MUST ALREADY BE HASHED. Does not compute no-CE ranks until the
frozen prereg sha matches. One no-CE variant. Does not re-minmax the
combined retrieval_norm list. Does not overwrite SYSTEM-F. Does not
open gold150-v1 holdout.json. Does not load validation. Does not run
PERF-003. Does not rerun CE.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "EXP-018" / "scripts"))

from rag_v1.evals.io import load_cases  # noqa: E402
from rag_v1.ids import config_hash  # noqa: E402

from system_e import (  # noqa: E402
    BLEND_A,
    BLEND_CE,
    HOLD_LOCK_SHA,
    HOLD_LOG_SHA_AT_PREREG,
    MINMAX_DEGENERATE,
    TOP_K,
    embedding_status,
    holdout_log_state,
)

OUT_DIR = ROOT / "experiments" / "EXP-019B"
GOLD_JSONL = ROOT / "evals" / "gold" / "v2-devset-001.jsonl"
SPLIT_PATH = ROOT / "evals" / "splits" / "v2-devset-001" / "development.json"
D_FREEZE = ROOT / "experiments" / "EXP-016" / "SYSTEM-D-GUARD.json"
D_RELEASE = ROOT / "experiments" / "EVAL-HOLDOUT-001" / "SYSTEM-D-RELEASE.json"
E_FILE = ROOT / "experiments" / "EXP-018" / "SYSTEM-E-WITHIN-DOC.json"
E_L10_FILE = ROOT / "experiments" / "EXP-018B" / "SYSTEM-E-L10-WITHIN-DOC.json"
F_FILE = ROOT / "experiments" / "EXP-017" / "SYSTEM-F-PROJECTION.json"
G_FILE = ROOT / "experiments" / "EXP-019A" / "SYSTEM-G-PROJECTION-PRIOR.json"
EXP017_RESULTS = ROOT / "experiments" / "EXP-017" / "EXP-017-results.json"
EXP019A_RESULTS = ROOT / "experiments" / "EXP-019A" / "EXP-019A-results.json"
RECOVERED = ROOT / "experiments" / "EXP-019A" / "EXP-019A-recovered-union.jsonl"
PREREG_JSON = OUT_DIR / "EXP-019B-preregistration.json"
PREREG_MD = OUT_DIR / "EXP-019B-preregistration.md"

PREREG_JSON_SHA = "eb542d641b60ba907cca321ca6943682257f7088da2028816d04144365dd2c74"
G_CONFIG_HASH = "563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790"
G_FILE_SHA = "7f4ff6db09f32e55cac820cbc00d87ce2ae91886d444c3bad20ac3e04c7f0f61"
F_CONFIG_HASH = "83ba5f2e834ecdffbfe4fb554cf84860ad35cf7010e9764e5cdea9e38598f678"
F_FILE_SHA = "e68d8c7a5782420bfd63cc57882ce96eacd5d919ac6197d271b9e11e399c3ff5"
EXP019A_PREREG_SHA = "f14001eff07b63c7916d7e27567d15ccd1e53b52918ae66f0d24ca37abb54cf3"
EXP017_PREREG_SHA = "053a6bf14df088ca9e2283bc3e8dfb0769848a48c54c51a77fbe045795a80cc6"
GOLD_SHA = "cb687f3cc88b38d4beed7ad4bc829296a30518aaaf45cce0677ec568b1bf77e5"
SPLIT_SHA = "6b0c49c9040c215fde6134697c35a1f28458ba7d72ef012c0840feb7f9c3eb17"
FREEZE_SHA = "97ea6befbb4fd845f53da2aef20ba84cedaaf69c0f09e3ad90833b813fee2ad9"
E_FILE_SHA = "e228616beee1bcb13855c2eadee9fc20ec1fae3e54c77b28587114568c64d087"
D_GUARD_SHA = "e9267f5581404e9885598979204c08762cd33f362703e526b20f4d3430c35a82"
D_RELEASE_SHA = "1f097b4b8dd353ecb4812228477338c05769faaede37d52ec6a07f27de729e40"
E_L10_HASH = "bae1c05b5c47c179dc5cd7972a14bd23d102a4d513b674667eb469e17cd85e89"
E_L10_FILE_SHA = "efbd3bc1cc73d3c342a607ef75135515d13680b31fd6058e8f1c13e80d13ed89"
BOOT_SEED = 20260901
BOOT_N = 10000
BASELINE_STRICT = 41
BASELINE_CAND = 46
BASELINE_N = 50



def minmax_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [MINMAX_DEGENERATE] * len(values)
    scale = hi - lo
    return [(v - lo) / scale for v in values]


def apply_blend_exp019a(x_rows: list[dict]) -> list[dict]:
    """Keep E-L10 a_norm and EXP-017 ce_norm exactly. Projection-only a_norm = minmax(proj RRF)."""
    e_rows = [r for r in x_rows if r.get("in_e_l10")]
    extras = [r for r in x_rows if not r.get("in_e_l10")]
    proj_scores = [float(r["projection_fused"]) for r in extras]
    proj_norms = minmax_norm(proj_scores)
    out: list[dict] = []
    for r in e_rows:
        item = dict(r)
        item["a_norm_exp017"] = float(item["a_norm"])
        item["retrieval_norm"] = float(item["a_norm"])
        item["ce_norm_exp017"] = float(item["ce_norm"])
        item["blend_score_exp017"] = float(item["blend_score"])
        item["blend_score"] = BLEND_CE * float(item["ce_norm"]) + BLEND_A * float(item["retrieval_norm"])
        out.append(item)
    for r, pn in zip(extras, proj_norms, strict=True):
        item = dict(r)
        item["a_norm_exp017"] = float(item.get("a_norm", 0.0))
        item["a_norm"] = float(pn)
        item["retrieval_norm"] = float(pn)
        item["ce_norm_exp017"] = float(item["ce_norm"])
        item["blend_score_exp017"] = float(item["blend_score"])
        item["blend_score"] = BLEND_CE * float(item["ce_norm"]) + BLEND_A * float(item["retrieval_norm"])
        out.append(item)
    out.sort(key=lambda r: (-r["blend_score"], r["a_rank"], r["chunk_id"]))
    for i, row in enumerate(out, start=1):
        row["blend_rank"] = i
        row["exp019a_rank"] = i
    return out


def dict_overlaps(row: dict, ref) -> bool:
    return (
        row["version_id"] == ref.version_id
        and list(row["section_path"]) == list(ref.section_path)
        and row["char_start"] < ref.char_end
        and row["char_end"] > ref.char_start
    )


def span_in_hits(hits, ref) -> bool:
    for h in hits:
        if isinstance(h, dict):
            if dict_overlaps(h, ref):
                return True
    return False


def first_span_rank(rows: list[dict], ref, rank_key: str):
    ranks = [r[rank_key] for r in rows if dict_overlaps(r, ref) and r.get(rank_key) is not None]
    return min(ranks) if ranks else None


def score_system(case, rows: list[dict], rank_key: str, pool, gold_cover: dict) -> dict:
    spans = []
    gold_docs = {ref.version_id for ref in case.expected_evidence}
    top_docs = {r["version_id"] for r in rows if r[rank_key] <= TOP_K}
    for i, ref in enumerate(case.expected_evidence):
        in_pool = span_in_hits(pool, ref)
        rank = first_span_rank(rows, ref, rank_key)
        spans.append(
            {
                "span_index": i,
                "covering_chunk_ids": gold_cover[case.case_id][i],
                "in_pool": in_pool,
                "rank": rank,
                "within_10": rank is not None and rank <= TOP_K,
                "doc_in_top_10": ref.version_id in top_docs,
                "pool_rank": None,
            }
        )
    found = sum(1 for s in spans if s["within_10"])
    return {
        "case_id": case.case_id,
        "spans": spans,
        "recall": found / len(spans) if spans else 1.0,
        "fully_recalled": bool(spans) and found == len(spans),
        "doc_recall": (len(gold_docs & top_docs) / len(gold_docs)) if gold_docs else 1.0,
        "gold_docs_in_top_10": sorted(gold_docs & top_docs),
        "gold_docs": sorted(gold_docs),
        "cand_ev_span_flags": [s["in_pool"] for s in spans],
    }


def summarise(per_case: dict, system: str, config_hash_value: str) -> dict:
    all_spans = [s for c in per_case.values() for s in c["spans"]]
    recalls = [c["recall"] for c in per_case.values()]
    return {
        "system": system,
        "config_hash": config_hash_value,
        "macro_span_recall": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
        "cases_fully_recalled": sum(1 for c in per_case.values() if c["fully_recalled"]),
        "cases_total": len(per_case),
        "strict_recall_at_10": (
            f"{sum(1 for c in per_case.values() if c['fully_recalled'])}/{len(per_case)}"
        ),
        "spans_found_at_10": sum(1 for s in all_spans if s["within_10"]),
        "spans_total": len(all_spans),
        "document_recall": round(
            sum(c["doc_recall"] for c in per_case.values()) / len(per_case), 4
        )
        if per_case
        else 0.0,
        "mrr": round(
            sum((1 / s["rank"] for s in all_spans if s["rank"]), 0.0) / len(all_spans), 4
        )
        if all_spans
        else 0.0,
    }


def metrics_from_cases(cases_map, name, cfg_hash, cand_flags, pool_sizes, latency_mean, extra=None):
    s = summarise(cases_map, name, cfg_hash)
    n_spans = len(cand_flags)
    out = {
        "source": name,
        "config_hash": cfg_hash,
        **{k: s[k] for k in s if k not in ("system", "config_hash")},
        "candidate_evidence_recall": round((sum(cand_flags) / n_spans) if n_spans else 1.0, 4),
        "candidate_evidence_spans": f"{sum(cand_flags)}/{n_spans}",
        "candidate_evidence_n": sum(cand_flags),
        "candidate_evidence_d": n_spans,
        "pool_size_mean": round(statistics.mean(pool_sizes), 2) if pool_sizes else 0.0,
        "pool_size_max": max(pool_sizes) if pool_sizes else 0,
        "latency_ms_mean": latency_mean,
    }
    if extra:
        out.update(extra)
    return out


def paired(control_full: dict, variant_full: dict) -> dict:
    rescues = [cid for cid, ok in variant_full.items() if ok and not control_full[cid]]
    regressions = [cid for cid, ok in variant_full.items() if control_full[cid] and not ok]
    return {
        "rescues": rescues,
        "regressions": regressions,
        "net": len(rescues) - len(regressions),
        "both_correct": [cid for cid, ok in variant_full.items() if ok and control_full[cid]],
        "neither": [cid for cid, ok in variant_full.items() if (not ok) and (not control_full[cid])],
    }


def env_fingerprint(emb: dict) -> dict:
    import platform
    deps = {}
    for name in ("numpy", "onnxruntime", "pgvector", "psycopg", "pydantic", "tokenizers"):
        try:
            mod = __import__(name)
            deps[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            deps[name] = None
    return {
        "host": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "executable": sys.executable,
        },
        "postgres_version": emb.get("postgres_version"),
        "pgvector_extversion": emb.get("pgvector_extversion"),
        "known_drift": emb.get("known_drift"),
        "dependencies": deps,
        "corpus_snapshot": "snap_689e336380a054d8039dc35b2c09cd0a",
        "chunk_set": "cs_v1_control",
        "transformer_model": "emb_e7d4183fd6eb878ae2fdf080efb6861e",
        "transformer_fingerprint": "bd95feaeacf98559",
    }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(xs: list[float], ndigits: int = 1) -> float:
    return round(statistics.mean(xs), ndigits) if xs else 0.0


def apply_no_ce(g_rows: list[dict]) -> list[dict]:
    """Rank by G's stored retrieval_norm DESC, then existing a_rank, chunk_id.

    Does NOT re-minmax the combined list. Does not invent a new tie-break.
    Projection-only a_rank is 10**9, so E-L10 wins exact retrieval_norm ties.
    """
    out = [dict(r) for r in g_rows]
    out.sort(key=lambda r: (-float(r["retrieval_norm"]), int(r["a_rank"]), r["chunk_id"]))
    for i, row in enumerate(out, start=1):
        row["noce_rank"] = i
        row["blend_rank"] = i
    return out


def mcnemar_exact(n01: int, n10: int) -> dict:
    """Two-sided exact McNemar on discordants (binomial n01 | n01+n10, p=0.5)."""
    n = n01 + n10
    if n == 0:
        return {"n01": n01, "n10": n10, "n_discordant": 0, "p_exact": 1.0, "method": "exact_binomial_no_discordants"}
    # two-sided: 2 * cdf of the smaller count, capped at 1
    k = min(n01, n10)
    tail = 0.0
    # P(X <= k) where X ~ Bin(n, 0.5)
    # use log-space comb via math.comb
    denom = 2**n
    for i in range(0, k + 1):
        tail += math.comb(n, i)
    p = min(1.0, 2.0 * tail / denom)
    return {
        "n01": n01,
        "n10": n10,
        "n_discordant": n,
        "p_exact": p,
        "method": "two_sided_exact_binomial_p05",
        "note": "n01=G success & NO-CE fail (CE-only); n10=G fail & NO-CE success (NO-CE-only)",
    }


def classify_descriptive(
    g_n: int,
    noce_n: int,
    n01: int,
    n10: int,
    p_exact: float,
    mean_delta: float,
    ci_lo: float,
    ci_hi: float,
) -> dict:
    """Descriptive label only. Not a promotion/deletion gate."""
    net = g_n - noce_n
    ci_excludes_zero = (ci_hi < 0) or (ci_lo > 0)
    reasons = [
        f"paired strict R@10 G={g_n}/50 vs G-NO-CE={noce_n}/50 (net {net:+d} toward G)",
        f"discordants n01(CE-only)={n01} n10(NO-CE-only)={n10} McNemar exact p={p_exact:.6g}",
        f"bootstrap mean delta (G-NOCE)={mean_delta:.4f} 95% CI [{ci_lo:.4f}, {ci_hi:.4f}]",
        "n=50 already used for architecture research; ablation not promotion",
        "0-1 case differences are not a CE-delete or CE-promote decision",
    ]
    if noce_n > g_n and ci_hi < 0:
        label = "NO-CE outperforms"
    elif abs(net) <= 1:
        # ChatGPT: 0-1 case difference → CE value questionable, not a release claim
        if ci_excludes_zero:
            label = "CE contribution appears marginal"
        else:
            label = "CE contribution appears marginal"
        reasons.append("effect size is 0-1 cases on n=50; CI/uncertainty recorded as diagnostic")
    elif net >= 2 and ci_lo > 0:
        label = "CE materially contributes"
    else:
        label = "inconclusive on n=50"
    return {
        "label": label,
        "descriptive_only": True,
        "not_a_promotion_gate": True,
        "do_not_promote_or_delete_CE_from_this_result_alone": True,
        "net_strict_G_minus_NOCE": net,
        "ci_excludes_zero": ci_excludes_zero,
        "reasons": reasons,
    }


def main() -> int:
    started = time.time()
    results_path = OUT_DIR / "EXP-019B-results.json"
    report_path = OUT_DIR / "EXP-019B-report.md"
    if results_path.exists():
        raise SystemExit("STOP: EXP-019B results already exist; refusing to overwrite")
    if not PREREG_JSON.exists() or not PREREG_MD.exists():
        raise SystemExit("STOP: preregistration missing; do not score no-CE ranks")
    got_pre = _sha(PREREG_JSON)
    if got_pre != PREREG_JSON_SHA:
        raise SystemExit(f"STOP: prereg json sha {got_pre} != frozen {PREREG_JSON_SHA}")
    pre_obj = json.loads(PREREG_JSON.read_text())
    if pre_obj["statistics"]["bootstrap"]["seed"] != BOOT_SEED:
        raise SystemExit("STOP: bootstrap seed missing/changed in hashed prereg")
    if pre_obj["no_ce_ranks_computed_before_prereg_hash"] is not False:
        raise SystemExit("STOP: prereg claims no-CE ranks were computed before hash")

    hold_before = holdout_log_state()
    if hold_before["log_bytes"] != 235 or hold_before["log_sha256"] != HOLD_LOG_SHA_AT_PREREG:
        raise SystemExit(f"STOP: holdout log drifted before run: {hold_before}")
    if hold_before["lock_sha256"] != HOLD_LOCK_SHA:
        raise SystemExit(f"STOP: holdout lock sha drifted: {hold_before}")

    if _sha(GOLD_JSONL) != GOLD_SHA or _sha(SPLIT_PATH) != SPLIT_SHA:
        raise SystemExit("STOP: gold/split hash mismatch")
    freeze_path = ROOT / "experiments" / "RAG-V2" / "V2-DEVSET-001" / "V2-DEVSET-001-FREEZE.json"
    if _sha(freeze_path) != FREEZE_SHA:
        raise SystemExit("STOP: V2-DEVSET-001 freeze hash mismatch")
    if _sha(D_FREEZE) != D_GUARD_SHA or _sha(D_RELEASE) != D_RELEASE_SHA:
        raise SystemExit("STOP: D freeze file bytes changed")
    if _sha(E_FILE) != E_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-E-WITHIN-DOC.json file SHA256 changed")
    if _sha(E_L10_FILE) != E_L10_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-E-L10 file SHA256 mismatch")
    if json.loads(E_L10_FILE.read_text())["config_hash"] != E_L10_HASH:
        raise SystemExit("STOP: SYSTEM-E-L10 config_hash mismatch")
    if _sha(F_FILE) != F_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-F file SHA256 changed (must not overwrite F)")
    f_obj = json.loads(F_FILE.read_text())
    if f_obj["config_hash"] != F_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-F config_hash mismatch")
    g_obj = json.loads(G_FILE.read_text())
    if g_obj["config_hash"] != G_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-G config_hash mismatch")
    if _sha(G_FILE) != G_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-G file SHA256 mismatch")
    hashed_g = config_hash(g_obj["config"])
    if hashed_g != G_CONFIG_HASH:
        raise SystemExit("STOP: SYSTEM-G config rehash drifted")

    exp017 = json.loads(EXP017_RESULTS.read_text())
    exp019a = json.loads(EXP019A_RESULTS.read_text())
    if exp019a.get("preregistration_json_sha256") != EXP019A_PREREG_SHA:
        raise SystemExit("STOP: EXP-019A results prereg sha mismatch")
    if exp017.get("preregistration_json_sha256") != EXP017_PREREG_SHA:
        raise SystemExit("STOP: EXP-017 results prereg sha mismatch")

    stored_019a = {rec["case_id"]: rec for rec in exp019a["per_case"]}
    stored_017 = {rec["case_id"]: rec for rec in exp017["per_case"]}

    recovered = []
    with RECOVERED.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                recovered.append(json.loads(line))
    if len(recovered) != 50:
        raise SystemExit(f"STOP: recovered union has {len(recovered)} cases, expected 50")
    rec_by_id = {r["case_id"]: r for r in recovered}

    cases = [c for c in load_cases(GOLD_JSONL) if c.expected_evidence]
    if len(cases) != 50:
        raise SystemExit(f"expected 50 v2-devset-001 cases, got {len(cases)}")
    split_ids = json.loads(SPLIT_PATH.read_text())["case_ids"]
    got_ids = [c.case_id for c in cases]
    if got_ids != split_ids or split_ids != [f"V2D-{i:02d}" for i in range(1, 51)]:
        raise SystemExit("STOP: split ids mismatch")

    gold_cover: dict[str, list[list[str]]] = {}
    for case in cases:
        gold_cover[case.case_id] = [list(s["covering_chunk_ids"]) for s in stored_019a[case.case_id]["spans"]]

    identity_mismatches = []
    g_cases = {}
    noce_cases = {}
    g_full = {}
    noce_full = {}
    stored_g_full = {}
    cand_g = []
    cand_noce = []
    pool_sizes = []
    per_case = []
    rank_movements = []
    rank1 = []
    lat_with_ce = []
    lat_no_ce = []
    recon_ms = []
    n_combined_reminmax = 0  # must stay 0

    print("reconstructing G retrieval_norm from recovered union (no CE)...", flush=True)

    for case in cases:
        dump = rec_by_id[case.case_id]
        st_a = stored_019a[case.case_id]
        st_17 = stored_017[case.case_id]
        members = dump["members"]

        mm = {
            "case_id": case.case_id,
            "C_P_set_match": set(dump["C_P"]) == set(st_a["C_P"]),
            "C_P_list_match": dump["C_P"] == st_a["C_P"],
            "e_pool_size_match": dump["e_pool_size"] == st_a["e_pool_size"],
            "x_pool_size_match": dump["x_pool_size"] == st_a["x_pool_size"] == st_a["y_pool_size"] == len(members),
            "recovered_identity_ok": bool(dump.get("identity", {}).get("identity_ok", False)),
        }
        t0 = time.perf_counter()
        g_rows = apply_blend_exp019a(members)
        noce_rows = apply_no_ce(g_rows)
        recon_ms.append((time.perf_counter() - t0) * 1000.0)

        # Identity: reconstructed G gold ranks == EXP-019A stored ranks
        g_by_id = {r["chunk_id"]: r for r in g_rows}
        gold_rank_ok = True
        retrieval_ok = True
        for i, s in enumerate(st_a["spans"]):
            cover = s["covering_chunk_ids"]
            g_ranks = [g_by_id[c]["exp019a_rank"] for c in cover if c in g_by_id]
            recon_g_rank = min(g_ranks) if g_ranks else None
            if recon_g_rank != s["exp019a_rank"]:
                gold_rank_ok = False
            gold_cid = s.get("gold_chunk_id")
            if gold_cid and gold_cid in g_by_id:
                rn = g_by_id[gold_cid].get("retrieval_norm")
                stored_rn = s.get("retrieval_norm")
                if stored_rn is not None and rn is not None and abs(float(rn) - float(stored_rn)) > 1e-12:
                    retrieval_ok = False
        mm["gold_g_rank_ok"] = gold_rank_ok
        mm["retrieval_norm_matches_019A_gold"] = retrieval_ok
        mm["identity_ok"] = (
            mm["C_P_set_match"]
            and mm["C_P_list_match"]
            and mm["e_pool_size_match"]
            and mm["x_pool_size_match"]
            and mm["recovered_identity_ok"]
            and gold_rank_ok
            and retrieval_ok
        )
        if not mm["identity_ok"]:
            identity_mismatches.append(mm)

        g_scored = score_system(case, g_rows, "exp019a_rank", g_rows, gold_cover)
        noce_scored = score_system(case, noce_rows, "noce_rank", noce_rows, gold_cover)

        g_cases[case.case_id] = g_scored
        noce_cases[case.case_id] = noce_scored
        g_full[case.case_id] = g_scored["fully_recalled"]
        noce_full[case.case_id] = noce_scored["fully_recalled"]
        stored_g_full[case.case_id] = bool(st_a["exp019a_full"])
        cand_g.extend(g_scored["cand_ev_span_flags"])
        cand_noce.extend(noce_scored["cand_ev_span_flags"])
        pool_sizes.append(len(g_rows))

        lat = st_17["latency_ms"]
        lat_with_ce.append(float(lat["total"]))
        lat_no_ce.append(float(lat["system_a_retrieval"]) + float(lat["local_bm25"]) + float(lat["projection_lane"]))

        destructions = []
        span_rows = []
        noce_by_id = {r["chunk_id"]: r for r in noce_rows}
        for i, ref in enumerate(case.expected_evidence):
            st = st_a["spans"][i]
            s = {
                "span_index": i,
                "covering_chunk_ids": gold_cover[case.case_id][i],
                "g_rank": st["exp019a_rank"],
                "recon_g_rank": g_scored["spans"][i]["rank"],
                "noce_rank": noce_scored["spans"][i]["rank"],
                "in_g_pool": st["in_019a_pool"],
                "in_noce_pool": noce_scored["spans"][i]["in_pool"],
                "g_in_top_10": st["exp019a_in_top_10"],
                "noce_in_top_10": noce_scored["spans"][i]["within_10"],
                "entered_via_projection": st.get("entered_via_projection"),
                "in_e_l10": st.get("in_e_l10"),
            }
            if s["g_rank"] is not None and s["noce_rank"] is not None:
                s["rank_delta_noce_minus_g"] = int(s["noce_rank"]) - int(s["g_rank"])  # positive = worse under NO-CE
                s["rank_delta_g_minus_noce"] = int(s["g_rank"]) - int(s["noce_rank"])  # positive = G better (lower rank)
            else:
                s["rank_delta_noce_minus_g"] = None
                s["rank_delta_g_minus_noce"] = None
            gold_cids = gold_cover[case.case_id][i]
            gold_member = None
            for cid in gold_cids:
                if cid in noce_by_id:
                    gold_member = noce_by_id[cid]
                    break
            if gold_member is not None:
                s["gold_chunk_id"] = gold_member["chunk_id"]
                s["a_rank"] = gold_member.get("a_rank")
                s["retrieval_norm"] = gold_member.get("retrieval_norm")
                s["ce_norm"] = gold_member.get("ce_norm")
                s["blend_score_g"] = gold_member.get("blend_score")
                s["projection_fused"] = gold_member.get("projection_fused")
            span_rows.append(s)
            rank_movements.append({"case_id": case.case_id, **s})
            if st["exp019a_rank"] == 1 and not noce_scored["spans"][i]["within_10"]:
                destructions.append(s)
                rank1.append({"case_id": case.case_id, **s})

        per_case.append(
            {
                "case_id": case.case_id,
                "g_full": g_full[case.case_id],
                "stored_g_full": stored_g_full[case.case_id],
                "noce_full": noce_full[case.case_id],
                "e_pool_size": dump["e_pool_size"],
                "pool_size": len(g_rows),
                "n_projection_additions": len(dump["C_P"]),
                "identity_ok": mm["identity_ok"],
                "spans": span_rows,
                "rank1_destruction_vs_G": destructions,
                "latency_ms_with_ce_stored_exp017": lat["total"],
                "latency_ms_ce_skipped_retrieval_only": lat_no_ce[-1],
                "latency_ms_exp017_stages": {
                    "system_a_retrieval": lat["system_a_retrieval"],
                    "local_bm25": lat["local_bm25"],
                    "projection_lane": lat["projection_lane"],
                    "cross_encoder": lat["cross_encoder"],
                    "total": lat["total"],
                },
            }
        )

    n_id_fail = len(identity_mismatches)
    if n_id_fail:
        payload = {
            "experiment_id": "EXP-019B",
            "scored": False,
            "stop_reason": "implementation drift: reconstructed G / pool identity != EXP-019A",
            "n_mismatches": n_id_fail,
            "mismatches": identity_mismatches,
            "preregistration_json_sha256": PREREG_JSON_SHA,
            "SYSTEM-G-PROJECTION-PRIOR_config_hash": G_CONFIG_HASH,
            "holdout_json_opened": False,
            "validation_loaded": False,
        }
        results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        report_path.write_text(
            "# EXP-019B\n\nSTOP: pool/G identity drifted vs EXP-019A. No-CE ranks not accepted.\n",
            encoding="utf-8",
        )
        print("STOP identity drift", n_id_fail, flush=True)
        return 2

    cand_n = sum(cand_noce)
    cand_d = len(cand_noce)
    cand_g_n = sum(cand_g)
    if cand_n != BASELINE_CAND or cand_g_n != BASELINE_CAND or cand_d != BASELINE_N:
        payload = {
            "experiment_id": "EXP-019B",
            "scored": False,
            "stop_reason": "implementation drift: candidate Recall@100 != 46/50",
            "cand_noce": f"{cand_n}/{cand_d}",
            "cand_g": f"{cand_g_n}/{cand_d}",
            "preregistration_json_sha256": PREREG_JSON_SHA,
            "holdout_json_opened": False,
        }
        results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        report_path.write_text(
            f"# EXP-019B\n\nSTOP: cand R@100 drifted G={cand_g_n}/{cand_d} NO-CE={cand_n}/{cand_d}.\n",
            encoding="utf-8",
        )
        print("STOP cand drift", cand_n, cand_g_n, flush=True)
        return 2

    # G strict must rematerialize to 41/50
    g_strict_n = sum(1 for v in g_full.values() if v)
    stored_g_strict_n = sum(1 for v in stored_g_full.values() if v)
    if g_strict_n != BASELINE_STRICT or stored_g_strict_n != BASELINE_STRICT:
        raise SystemExit(f"STOP: reconstructed G strict {g_strict_n} stored {stored_g_strict_n} != 41")
    if any(g_full[cid] != stored_g_full[cid] for cid in g_full):
        raise SystemExit("STOP: reconstructed G per-case strict flags != EXP-019A")

    noce_strict_n = sum(1 for v in noce_full.values() if v)
    pair_g_to_noce = paired(g_full, noce_full)  # rescues = NO-CE success & G fail
    pair_noce_to_g = paired(noce_full, g_full)  # rescues = G success & NO-CE fail = CE-only
    ce_only = pair_noce_to_g["rescues"]  # G better
    noce_only = pair_g_to_noce["rescues"]  # NO-CE better
    n01 = len(ce_only)
    n10 = len(noce_only)
    mc = mcnemar_exact(n01, n10)

    # Bootstrap seed was in hashed prereg BEFORE this computation.
    g_arr = np.array([1 if g_full[c.case_id] else 0 for c in cases], dtype=np.int8)
    n_arr = np.array([1 if noce_full[c.case_id] else 0 for c in cases], dtype=np.int8)
    rng = np.random.Generator(np.random.PCG64(BOOT_SEED))
    deltas = np.empty(BOOT_N, dtype=np.float64)
    idx_all = np.arange(BASELINE_N)
    for i in range(BOOT_N):
        idx = rng.choice(idx_all, size=BASELINE_N, replace=True)
        deltas[i] = (g_arr[idx] - n_arr[idx]).mean()
    boot_mean = float(deltas.mean())
    ci_lo = float(np.percentile(deltas, 2.5))
    ci_hi = float(np.percentile(deltas, 97.5))

    m_g = metrics_from_cases(
        g_cases,
        "SYSTEM-G-PROJECTION-PRIOR (CE blend)",
        G_CONFIG_HASH,
        cand_g,
        pool_sizes,
        _mean(lat_with_ce),
    )
    m_noce = metrics_from_cases(
        noce_cases,
        "G-NO-CE (retrieval_norm DESC, inherited two-population minmax)",
        None,
        cand_noce,
        pool_sizes,
        _mean(lat_no_ce),
    )

    clf = classify_descriptive(g_strict_n, noce_strict_n, n01, n10, mc["p_exact"], boot_mean, ci_lo, ci_hi)

    improved = [m for m in rank_movements if m["rank_delta_g_minus_noce"] is not None and m["rank_delta_g_minus_noce"] > 0]
    worsened = [m for m in rank_movements if m["rank_delta_g_minus_noce"] is not None and m["rank_delta_g_minus_noce"] < 0]
    unchanged = [m for m in rank_movements if m["rank_delta_g_minus_noce"] == 0]
    still_none = [m for m in rank_movements if m["rank_delta_g_minus_noce"] is None]

    hold_after = holdout_log_state()
    if hold_after != hold_before:
        raise SystemExit(f"STOP: holdout log changed {hold_before} -> {hold_after}")
    if _sha(F_FILE) != F_FILE_SHA:
        raise SystemExit("STOP: SYSTEM-F mutated during run")
    if _sha(D_FREEZE) != D_GUARD_SHA or _sha(D_RELEASE) != D_RELEASE_SHA:
        raise SystemExit("STOP: D freeze files mutated")
    if _sha(E_FILE) != E_FILE_SHA or _sha(E_L10_FILE) != E_L10_FILE_SHA:
        raise SystemExit("STOP: E / E-L10 mutated")

    emb = embedding_status()
    payload = {
        "experiment_id": "EXP-019B",
        "scored": True,
        "ablation_not_promotion": True,
        "split": "v2-devset-001/development",
        "n": 50,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_et": datetime.now(UTC).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "preregistration_json_sha256": PREREG_JSON_SHA,
        "SYSTEM-G-PROJECTION-PRIOR_config_hash": G_CONFIG_HASH,
        "SYSTEM-G-PROJECTION-PRIOR_file_sha256": G_FILE_SHA,
        "SYSTEM-F-PROJECTION_config_hash": F_CONFIG_HASH,
        "SYSTEM-F-PROJECTION_file_sha256": F_FILE_SHA,
        "one_change": "ablation: remove CE; rank identical G pool by G retrieval_norm DESC then existing a_rank/chunk_id tie-break; do not re-minmax combined list",
        "n_no_ce_variants": 1,
        "tuned_after_seeing_scores": False,
        "n_evals": 1,
        "second_variant": False,
        "validation_loaded": False,
        "holdout_loaded": False,
        "holdout_json_opened": False,
        "RELEASE": "NOT_FROZEN",
        "ce_rerun": False,
        "combined_list_reminmaxed": False,
        "n_combined_reminmax": n_combined_reminmax,
        "pool_identity_equivalent": True,
        "hash_check": {
            "prereg_json_sha256": got_pre,
            "prereg_json_sha256_ok": True,
            "SYSTEM-G-PROJECTION-PRIOR_config_hash": G_CONFIG_HASH,
            "SYSTEM-G-PROJECTION-PRIOR_config_hash_ok": True,
            "SYSTEM-F-PROJECTION_config_hash": F_CONFIG_HASH,
            "SYSTEM-F-PROJECTION_file_sha256_ok": True,
            "holdout_access_log": hold_before,
            "holdout_log_ok": True,
            "bootstrap_seed_in_prereg": BOOT_SEED,
        },
        "holdout_access_log_before": hold_before,
        "holdout_access_log_after": hold_after,
        "holdout_log_unchanged": True,
        "embedding": emb,
        "environment": env_fingerprint(emb),
        "PRIMARY_DIAGNOSTIC": {
            "paired_strict_recall_at_10": {
                "SYSTEM_G": f"{g_strict_n}/50",
                "G_NO_CE": f"{noce_strict_n}/50",
                "delta_G_minus_NOCE_cases": g_strict_n - noce_strict_n,
            },
            "candidate_gold_span_recall_at_100": "46/50",
            "candidate_membership_identical": True,
        },
        "SYSTEM_G_metrics": m_g,
        "G_NO_CE_metrics": m_noce,
        "SECONDARY": {
            "strict_recall_at_10_G": f"{g_strict_n}/50",
            "strict_recall_at_10_NOCE": f"{noce_strict_n}/50",
            "candidate_gold_span_recall_at_100": "46/50",
            "span_recall_at_10_G": m_g["macro_span_recall"],
            "span_recall_at_10_NOCE": m_noce["macro_span_recall"],
            "mrr_G": m_g["mrr"],
            "mrr_NOCE": m_noce["mrr"],
            "document_recall_G": m_g["document_recall"],
            "document_recall_NOCE": m_noce["document_recall"],
            "CE_only_rescues": ce_only,
            "NOCE_only_rescues": noce_only,
            "regressions_G_to_NOCE": pair_g_to_noce["regressions"],
            "regressions_NOCE_to_G": pair_noce_to_g["regressions"],
            "rank1_destructions_vs_G": rank1,
            "rank1_destruction_count": len(rank1),
            "rank_movements": rank_movements,
            "rank_movements_summary": {
                "n_G_better_rank": len(improved),
                "n_NOCE_better_rank": len(worsened),
                "n_unchanged": len(unchanged),
                "n_still_absent": len(still_none),
                "mean_rank_delta_G_minus_NOCE": (
                    round(
                        statistics.mean(
                            [m["rank_delta_g_minus_noce"] for m in rank_movements if m["rank_delta_g_minus_noce"] is not None]
                        ),
                        2,
                    )
                    if any(m["rank_delta_g_minus_noce"] is not None for m in rank_movements)
                    else None
                ),
            },
            "mean_final_candidate_pool": round(statistics.mean(pool_sizes), 2),
            "latency_with_CE_ms_mean": _mean(lat_with_ce),
            "latency_CE_skipped_retrieval_only_ms_mean": _mean(lat_no_ce),
            "latency_note": "CE skipped = A + local BM25 + projection from stored EXP-017 per-query stage times; not 0.2ms blend",
            "recon_sort_ms_mean": _mean(recon_ms, 4),
        },
        "statistics": {
            "mcnemar_exact": mc,
            "bootstrap": {
                "seed": BOOT_SEED,
                "n_resamples": BOOT_N,
                "rng": "numpy.random.Generator(numpy.random.PCG64(20260901))",
                "delta_definition": "mean(G_strict - NOCE_strict); positive means CE helps",
                "mean_delta": round(boot_mean, 6),
                "ci95_percentile": [round(ci_lo, 6), round(ci_hi, 6)],
                "observed_delta": (g_strict_n - noce_strict_n) / BASELINE_N,
            },
            "significance_is_diagnostic_not_a_gate": True,
            "seed_was_in_hashed_prereg_before_no_ce_ranks": True,
        },
        "classification": clf,
        "grok_methodology_check": pre_obj["grok_methodology_check"],
        "tie_break": {
            "order": ["retrieval_norm DESC", "a_rank ASC", "chunk_id ASC"],
            "projection_only_a_rank": 10**9,
            "E_L10_wins_exact_retrieval_norm_ties": True,
        },
        "two_population_minmax": {
            "E_L10_retrieval_norm_minmaxed_on": "E-L10 pool",
            "projection_only_retrieval_norm_minmaxed_on": "P extras",
            "combined_list_reminmaxed": False,
            "inherited_from_G": True,
        },
        "freeze_files_untouched": {
            "SYSTEM-F-PROJECTION.json_sha256": _sha(F_FILE),
            "SYSTEM-D-GUARD.json_sha256": _sha(D_FREEZE),
            "SYSTEM-D-RELEASE.json_sha256": _sha(D_RELEASE),
            "SYSTEM-E-WITHIN-DOC.json_sha256": _sha(E_FILE),
            "SYSTEM-E-L10-WITHIN-DOC.json_sha256": _sha(E_L10_FILE),
            "SYSTEM-G-PROJECTION-PRIOR.json_sha256": _sha(G_FILE),
        },
        "per_case": per_case,
        "runtime_seconds": round(time.time() - started, 1),
    }
    results_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    # report
    lines = [
        "# EXP-019B — cross-encoder necessity ablation (G vs G-NO-CE)",
        "",
        f"Timestamp: {payload['timestamp']} UTC. Dataset: V2-DEVSET-001 n=50 only. "
        f"Prereg json sha256 `{PREREG_JSON_SHA}` (hashed **before** no-CE ranks; seed **{BOOT_SEED}**). "
        f"SYSTEM-G-PROJECTION-PRIOR config_hash `{G_CONFIG_HASH}`. "
        f"SYSTEM-F-PROJECTION untouched config_hash `{F_CONFIG_HASH}` file sha `{F_FILE_SHA}`. "
        f"One ablation. Not retuned. No second no-CE variant. **Ablation, not promotion.**",
        "",
        "gold150-v1 holdout.json not opened. Validation not loaded. "
        "SYSTEM-F / SYSTEM-D / SYSTEM-E-WITHIN-DOC.json / SYSTEM-E-L10-WITHIN-DOC.json / cs_v1_control / "
        "`ps_v2_ovl_win448_s224` not modified. Candidate generation / projections / E-L10 / CE model / weights unchanged. "
        "CE not rerun. Combined retrieval_norm list **not** re-minmaxed. No PERF-003. RELEASE=NOT_FROZEN.",
        "",
        f"Holdout access log: {hold_before['log_bytes']} bytes sha `{hold_before['log_sha256']}` unchanged={hold_after == hold_before}.",
        "",
        "## Grok methodology review (recorded; ranking unchanged)",
        "",
        "1. **G-NO-CE is a valid ablation of SYSTEM-G** (remove CE, keep G's `retrieval_norm` exactly). "
        "It is **not** a valid CE-vs-retrieval-only *system* comparison: the retrieval channel is G's "
        "two-population minmax mix, not a freshly designed retrieval-only ranker.",
        "2. **Hidden two-population minmax:** E-L10 `retrieval_norm` was minmaxed on the E-L10 pool; "
        "projection-only `retrieval_norm` was minmaxed on the P extras. Those two scales are mixed on "
        "one list because G already did that. This run does **not** re-minmax the combined list.",
        "3. **Tie-break:** after `retrieval_norm` DESC, existing EXP-017/019A order: `a_rank` then `chunk_id`. "
        "Projection-only `a_rank=10**9` (1e9), so **E-L10 wins exact `retrieval_norm` ties.** Not a new tie-break.",
        "4. **No gold-label leakage** into no-CE ranks. Candidate membership is the EXP-017/019A projection-RRF "
        "union, not CE. Same n=50 already used for architecture research: ablation not promotion, as ChatGPT said.",
        "5. **No second no-CE variant.** Classification is descriptive. Significance is diagnostic, not a gate.",
        "",
        "## Method",
        "",
        "Prefer stored `experiments/EXP-019A/EXP-019A-recovered-union.jsonl` + `EXP-019A-results.json`. "
        "Reconstruct G via frozen EXP-019A `apply_blend_exp019a` (E-L10 keep `a_norm`; projection-only "
        "`minmax(projection-RRF)` over P extras). Verify gold ranks and `retrieval_norm` against EXP-019A. "
        "Then rank the **same** rows by `retrieval_norm DESC`, `a_rank ASC`, `chunk_id ASC`. "
        "No new RRF/blend/normalization. CE skipped latency = stored EXP-017 A + local BM25 + projection "
        "(not the 0.2 ms blend).",
        "",
        f"Pool identity-equivalent = **True**. cand R@100 stayed **46/50**. Reconstructed G strict R@10 = **41/50**.",
        "",
        "## PRIMARY DIAGNOSTIC",
        "",
        f"paired strict R@10: **SYSTEM-G {g_strict_n}/50** vs **G-NO-CE {noce_strict_n}/50** "
        f"(delta G−NO-CE = {g_strict_n - noce_strict_n:+d} cases).",
        "",
        "## SECONDARY",
        "",
        f"- cand R@100: 46/50 both (identity-equivalent True)",
        f"- span R@10: G {m_g['macro_span_recall']} / NO-CE {m_noce['macro_span_recall']}",
        f"- MRR: G {m_g['mrr']} / NO-CE {m_noce['mrr']}",
        f"- document recall: G {m_g['document_recall']} / NO-CE {m_noce['document_recall']}",
        f"- CE-only rescues (G yes, NO-CE no): {ce_only or '—'}",
        f"- NO-CE-only rescues (NO-CE yes, G no): {noce_only or '—'}",
        f"- rank-1 destructions vs G: {len(rank1)}",
        f"- rank movements (gold spans; positive delta = G better / lower rank number): "
        f"G-better {len(improved)}, NO-CE-better {len(worsened)}, unchanged {len(unchanged)}, still absent {len(still_none)}; "
        f"mean rank delta G−NO-CE {payload['SECONDARY']['rank_movements_summary']['mean_rank_delta_G_minus_NOCE']}",
        f"- latency with CE (EXP-017 stored total): mean {payload['SECONDARY']['latency_with_CE_ms_mean']} ms",
        f"- latency CE skipped (A + local BM25 + projection only): mean {payload['SECONDARY']['latency_CE_skipped_retrieval_only_ms_mean']} ms",
        f"- mean pool: {payload['SECONDARY']['mean_final_candidate_pool']}",
        "",
        "## Statistics (diagnostic, not a gate)",
        "",
        f"- Exact McNemar on strict discordants: n01 (CE-only) = {n01}, n10 (NO-CE-only) = {n10}, "
        f"p_exact = {mc['p_exact']:.6g}",
        f"- Paired bootstrap of strict R@10 delta (G − NO-CE), seed **{BOOT_SEED}**, {BOOT_N} resamples: "
        f"mean {boot_mean:.6f}, 95% percentile CI [{ci_lo:.6f}, {ci_hi:.6f}]",
        f"- Observed delta: {(g_strict_n - noce_strict_n) / BASELINE_N:.4f} ({g_strict_n - noce_strict_n:+d}/50)",
        "",
        "## Classification (descriptive only)",
        "",
        f"**{clf['label']}**",
        "",
        "Not a promotion gate. Do not promote or delete CE from this result alone. "
        "Support:",
        *[f"- {r}" for r in clf["reasons"]],
        "",
        "## Standing",
        "",
        "No validation. No holdout. No PERF-003. No second no-CE variant. No retune. "
        "SYSTEM-F identity not edited. SYSTEM-G is DEVELOPMENT / NOT_FROZEN. No release freeze. "
        "A final architecture decision must eventually be confirmed using fresh questions.",
        "",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        "done",
        "G", f"{g_strict_n}/50",
        "NOCE", f"{noce_strict_n}/50",
        "cand", "46/50",
        "mcnemar", mc["p_exact"],
        "boot", boot_mean, ci_lo, ci_hi,
        "class", clf["label"],
        "lat_ce", payload["SECONDARY"]["latency_with_CE_ms_mean"],
        "lat_noce", payload["SECONDARY"]["latency_CE_skipped_retrieval_only_ms_mean"],
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
