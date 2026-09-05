#!/usr/bin/env python3
"""Build SYSTEM-H-RUNTIME-MANIFEST.json — the runtime identity gate.

Every score-determining component is hashed or fingerprinted and compared against the
recovered authoritative records. If ANY component is unresolved or mismatched the
manifest is not written and the process exits non-zero, so a failed gate cannot be
mistaken for a passed one.

Read-only with respect to the database: it verifies, it does not build.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJ = Path("/home/user/nyxora-outcome-intelligence/production-rag-v1")
WT = Path("/tmp/claude-0/-home-user-nyxora-outcome-intelligence/"
          "a8bea47d-4ca9-5639-86a8-168ef0a4dcb2/scratchpad/natq")
REF = "origin/grok/v2-natq-20260903"
sys.path.insert(0, str(PROJ / "src"))

# Authoritative values, every one read from a recovered artifact rather than typed from chat.
H_CONFIG_HASH = "7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a"
G_CONFIG_HASH = "563a7b790564fa1efb96257e988c4b1ccfab45146825d2a366b2fee0ca5d5790"
G_CE_D1_HASH = "6d108568f3131bad87d8617f5c2fb88ea14428e397d59ff54ff8e11cc4647b7d"
G_CE_D1_SHA = "cf0c985c5f7738e7fc5422039fd6940621d8dcd8f91de41abe3784ac53a6a7ec"
CE_SHA = "5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a"
CE_REV = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
PROJ_CFG_HASH = "7fd5034c9510a1e08ec76bd22b020703c586dd12e7c02659397df05c5c365a8e"
PROJ_SET_ID = "ps_v2_ovl_win448_s224"
PROJ_COUNT = 18057
PROJ_FINGERPRINT = "bd95feaeacf98559"
BUNDLE_SHA = "913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3"
SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
CHUNK_SET = "cs_v1_control"
CE_DIR = WT / "experiments/EXP-015/models/cross-encoder-ms-marco-MiniLM-L6-v2" / CE_REV


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def blob_sha(path: str) -> str:
    out = subprocess.run(["git", "cat-file", "blob", f"{REF}:{path}"],
                         capture_output=True, cwd=PROJ.parent)
    return hashlib.sha256(out.stdout).hexdigest() if out.returncode == 0 else ""


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def gate(name: str, ok: bool, detail: str = "") -> bool:
        checks.append((name, bool(ok), detail))
        return bool(ok)

    # --- code, from the recovered worktree ---
    code = {}
    for label, rel in [
        ("runner", "experiments/RAG-V2/EVAL-NATQ-VAL-001/scripts/run_eval_natq_val_001.py"),
        ("exp019a_prior", "experiments/EXP-019A/scripts/run_exp019a.py"),
        ("projection_builder", "experiments/EXP-017/scripts/build_projections.py"),
        ("projection_retrieval", "experiments/EXP-017/scripts/projection_retrieval.py"),
        ("system_e_candidate_gen", "experiments/EXP-018/scripts/system_e.py"),
        ("local_bm25_w20", "experiments/EXP-018B/scripts/local_bm25_batched.py"),
        ("cross_encoder", "experiments/EXP-015/scripts/cross_encoder.py"),
        ("perf003_d1_path", "experiments/PERF-003/scripts/v2_system_g_ce.py"),
        ("rag_v1_systems", "src/rag_v1/systems.py"),
        ("rag_v1_retrieval", "src/rag_v1/retrieval.py"),
        ("rag_v1_ids", "src/rag_v1/ids.py"),
        ("rag_v1_embedders_transformer", "src/rag_v1/embedders_transformer.py"),
    ]:
        f = WT / rel
        local = sha(f) if f.exists() else ""
        ref = blob_sha(rel)
        code[label] = {"path": rel, "sha256": local, "git_blob_sha256": ref,
                       "worktree_matches_ref": bool(local) and local == ref}
        gate(f"code {label} present and matches {REF}", code[label]["worktree_matches_ref"])

    # --- recovered configuration artifacts ---
    cfgs = {}
    for label, rel in [
        ("system_h_upstream", "experiments/RAG-V2/SYSTEM-H-V2-DEV-CANDIDATE/SYSTEM-H-V2-DEV-CANDIDATE.json"),
        ("system_g_projection_prior", "experiments/EXP-019A/SYSTEM-G-PROJECTION-PRIOR.json"),
        ("exp019a_preregistration", "experiments/EXP-019A/EXP-019A-preregistration.json"),
        ("exp019a_results", "experiments/EXP-019A/EXP-019A-results.json"),
        ("system_g_ce_d1", "experiments/PERF-003/SYSTEM-G-CE-D1.json"),
        ("perf003_preregistration", "experiments/PERF-003/PERF-003-preregistration.json"),
        ("exp017_projection_build", "experiments/EXP-017/EXP-017-projection-build.json"),
    ]:
        cfgs[label] = {"path": rel, "sha256": blob_sha(rel)}
        gate(f"config {label} recovered", bool(cfgs[label]["sha256"]))

    gate("SYSTEM-G-CE-D1.json matches recorded file sha", cfgs["system_g_ce_d1"]["sha256"] == G_CE_D1_SHA,
         cfgs["system_g_ce_d1"]["sha256"])

    hcfg = json.loads(subprocess.run(
        ["git", "cat-file", "blob", f"{REF}:experiments/RAG-V2/SYSTEM-H-V2-DEV-CANDIDATE/"
         "SYSTEM-H-V2-DEV-CANDIDATE.json"], capture_output=True, cwd=PROJ.parent).stdout)
    gate("upstream SYSTEM-H record carries the authoritative config hash",
         H_CONFIG_HASH in json.dumps(hcfg))
    gate("upstream SYSTEM-H parent SYSTEM-G config hash matches",
         hcfg.get("parent_SYSTEM_G_config_hash") == G_CONFIG_HASH)
    gate("upstream SYSTEM-H parent CE-D1 config hash matches",
         hcfg.get("parent_SYSTEM_G_CE_D1_config_hash") == G_CE_D1_HASH)
    gate("runner pins the authoritative SYSTEM-H config hash",
         H_CONFIG_HASH in (WT / code["runner"]["path"]).read_text())

    # --- cross-encoder artifact ---
    ce_model = CE_DIR / "onnx/model.onnx"
    ce_ok = ce_model.exists() and sha(ce_model) == CE_SHA
    gate("CE artifact present and SHA256 matches the frozen value", ce_ok,
         sha(ce_model) if ce_model.exists() else "absent")
    ce_files = {p.name: sha(p) for p in sorted(CE_DIR.rglob("*")) if p.is_file()}
    gate("CE tokenizer present", "tokenizer.json" in ce_files)

    # --- embedding bundle ---
    bundle = PROJ / "data/cache/models/exp009/onnx.tar.gz"
    gate("MiniLM bundle SHA256 matches the value pinned in the recovered encoder",
         bundle.exists() and sha(bundle) == BUNDLE_SHA)

    # --- materialized projection identity ---
    from rag_v1.db import connect
    with connect() as c, c.cursor() as cur:
        cur.execute("SELECT config_hash FROM search_projection_set WHERE projection_set_id=%s", (PROJ_SET_ID,))
        row = cur.fetchone()
        set_hash = row[0] if row else ""
        cur.execute("SELECT count(*) FROM search_projection WHERE projection_set_id=%s", (PROJ_SET_ID,))
        n_proj = cur.fetchone()[0]
        cur.execute("""SELECT count(*), min(pe.model_fingerprint), max(pe.model_fingerprint)
                       FROM search_projection_embedding pe
                       JOIN search_projection sp ON sp.projection_id = pe.projection_id
                       WHERE sp.projection_set_id=%s""", (PROJ_SET_ID,))
        n_emb, fp_min, fp_max = cur.fetchone()
        cur.execute("SELECT count(*) FROM corpus_snapshot_version WHERE snapshot_id=%s", (SNAPSHOT,))
        n_docs = cur.fetchone()[0]
        cur.execute("""SELECT count(*) FROM chunk c JOIN corpus_snapshot_version sv
                       ON sv.version_id=c.version_id WHERE sv.snapshot_id=%s AND c.chunk_set_id=%s""",
                    (SNAPSHOT, CHUNK_SET))
        n_chunks = cur.fetchone()[0]

    gate("projection set config hash matches the recovered build record", set_hash == PROJ_CFG_HASH, set_hash)
    gate(f"projection count is exactly {PROJ_COUNT}", n_proj == PROJ_COUNT, str(n_proj))
    gate(f"projection embeddings complete ({PROJ_COUNT})", n_emb == PROJ_COUNT, str(n_emb))
    gate(f"projection fingerprint is exactly {PROJ_FINGERPRINT}",
         fp_min == fp_max == PROJ_FINGERPRINT, f"{fp_min}..{fp_max}")
    gate("corpus snapshot intact (202 documents)", n_docs == 202, str(n_docs))
    gate("cs_v1_control intact (14209 chunks)", n_chunks == 14209, str(n_chunks))

    passed = all(ok for _, ok, _ in checks)
    print("RUNTIME IDENTITY GATE")
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    print(f"\n{sum(1 for _, ok, _ in checks if ok)}/{len(checks)} passed")

    if not passed:
        print("\nSTOP: a score-determining component is unresolved. Manifest NOT written.")
        return 1

    manifest = {
        "record_id": "SYSTEM-H-RUNTIME-MANIFEST", "recorded_utc": "2026-09-04",
        "purpose": "Runtime identity gate for a future SYSTEM-H NATQ-002 validation run.",
        "all_score_determining_components_verified": True,
        "authoritative_system_h_config_hash": H_CONFIG_HASH,
        "recovered_from_ref": REF,
        "code": code, "configs": cfgs,
        "cross_encoder": {"name": "cross-encoder/ms-marco-MiniLM-L6-v2", "revision": CE_REV,
                          "model_onnx_sha256": sha(ce_model), "matches_frozen_value": True,
                          "artifact_files": ce_files},
        "embedding_model": {"model_id": "emb_e7d4183fd6eb878ae2fdf080efb6861e",
                            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                            "fingerprint": PROJ_FINGERPRINT, "bundle_sha256": sha(bundle),
                            "bundle_matches_pinned_value": True},
        "projection": {"projection_set_id": PROJ_SET_ID, "config_hash": set_hash,
                       "projection_count": n_proj, "embedding_count": n_emb,
                       "fingerprint": fp_min, "origin": "deterministic rematerialization",
                       "original_rows_recovered": False,
                       "identity_exact": True,
                       "note": ("Original rows were not found in any database, backup or cache. Rebuilt with "
                                "the recovered EXP-017 builder and the recovered src tree against the same "
                                "frozen corpus and the same hash-verified MiniLM bundle. Config hash, count "
                                "and fingerprint all match the recovered build record exactly.")},
        "corpus": {"snapshot_id": SNAPSHOT, "documents": n_docs,
                   "chunk_set_id": CHUNK_SET, "chunks": n_chunks},
        "gate_results": [{"check": n, "pass": ok} for n, ok, _ in checks],
    }
    out = PROJ / "experiments/SYSTEM-H/SYSTEM-H-RUNTIME-MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"\nwrote {out.name}  sha256 {sha(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
