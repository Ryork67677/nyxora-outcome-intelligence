"""EVAL-SPLIT-001: the split is contamination-aware, deterministic, and locked.

The holdout's only value is that nothing was tuned on it. These tests exist to make that
claim falsifiable: they re-derive the exposure audit, re-check every leakage rule against
the frozen files, and fail if the holdout could be reached by an ordinary script.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from rag_v1.eval.exposure import CONTAMINATED, UNEXPOSED, classify, spans_of
from rag_v1.eval.split import SEED, assign
from rag_v1.eval.splits import (
    FrozenHoldoutError,
    all_evaluable_case_ids,
    is_frozen,
    load,
)

OUT = Path("experiments/EVAL-SPLIT-001")
SPLIT_DIR = Path("evals/splits/gold150-v1")
REPORT = OUT / "EVAL-SPLIT-001-report.json"
LEDGER = OUT / "EVAL-SPLIT-001-exposure-ledger.json"
CLUSTERS = OUT / "EVAL-SPLIT-001-fact-clusters.json"
MANIFEST = OUT / "EVAL-SPLIT-001-manifest.json"
SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
GOLD_SOURCES = {
    "001": "evals/gold/batch_001_v2/overlay.json",
    "002": "evals/review/gold_review_batch_002.json",
    "003": "evals/review/gold_review_batch_003.json",
    "004": "evals/review/gold_review_batch_004_final.json",
    "005": "evals/review/gold_review_batch_005_final.json",
    "006": "evals/review/gold_review_batch_006_final.json",
    "HA": "evals/review/gold_review_HA01_HA60_final.json",
}


def read(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"{path} has not been generated")
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def report() -> dict:
    return read(REPORT)


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    out = []
    for group, rel in GOLD_SOURCES.items():
        payload = json.loads(Path(rel).read_text())
        for record in (payload.get("records") or payload.get("case_records") or []):
            if (record.get("verification_status") == "human_verified"
                    or record.get("human_verified")):
                out.append({"group": group, **record})
    return sorted(out, key=lambda c: c["candidate_id"])


# --------------------------------------------------------------- coverage and identity


def test_every_approved_case_is_assigned_exactly_once(report, cases):
    assignment = report["assignment"]
    assert len(cases) == 150
    assert len(assignment) == 150
    assert sorted(assignment) == sorted(c["candidate_id"] for c in cases)
    members = [c for split in ("development", "validation", "holdout")
               for c in json.loads((SPLIT_DIR / f"{split}.json").read_text())["case_ids"]]
    assert len(members) == 150
    assert len(set(members)) == 150, "a case appears in more than one split"


def test_no_rejected_case_entered_any_split(report):
    """Only human_verified records may be split; the 9 rejections stay out."""
    assigned = set(report["assignment"])
    rejected = set()
    for rel in GOLD_SOURCES.values():
        payload = json.loads(Path(rel).read_text())
        for record in (payload.get("records") or payload.get("case_records") or []):
            if record.get("verification_status") == "human_rejected":
                rejected.add(record["candidate_id"])
    assert rejected, "no rejected cases found — the fixture is wrong"
    assert not (assigned & rejected), sorted(assigned & rejected)


def test_the_split_counts_are_what_the_manifest_claims(report):
    manifest = read(MANIFEST)
    for split, expected in report["counts"].items():
        stored = json.loads((SPLIT_DIR / f"{split}.json").read_text())
        assert stored["count"] == expected == len(stored["case_ids"])
        assert manifest["counts"][split] == expected


# ------------------------------------------------------------------- contamination


def test_no_exposed_case_is_in_validation(report):
    ledger = {r["candidate_id"]: r["exposure_status"] for r in read(LEDGER)["ledger"]}
    for case_id in json.loads((SPLIT_DIR / "validation.json").read_text())["case_ids"]:
        assert ledger[case_id] == UNEXPOSED, f"{case_id} is {ledger[case_id]}"


def test_no_exposed_case_is_in_holdout(report):
    ledger = {r["candidate_id"]: r["exposure_status"] for r in read(LEDGER)["ledger"]}
    for case_id in json.loads((SPLIT_DIR / "holdout.json").read_text())["case_ids"]:
        assert ledger[case_id] == UNEXPOSED, f"{case_id} is {ledger[case_id]}"


def test_unknown_can_never_enter_the_holdout(report):
    """UNKNOWN is contaminated by policy, not by evidence. The rule must hold anyway."""
    assert "UNKNOWN" in CONTAMINATED
    ledger = {r["candidate_id"]: r["exposure_status"] for r in read(LEDGER)["ledger"]}
    holdout = json.loads((SPLIT_DIR / "holdout.json").read_text())["case_ids"]
    validation = json.loads((SPLIT_DIR / "validation.json").read_text())["case_ids"]
    assert not [c for c in holdout + validation if ledger[c] == "UNKNOWN"]


def test_every_contaminated_case_is_in_development(report):
    ledger = read(LEDGER)["ledger"]
    contaminated = {r["candidate_id"] for r in ledger
                    if r["exposure_status"] in CONTAMINATED}
    development = set(json.loads(
        (SPLIT_DIR / "development.json").read_text())["case_ids"])
    assert contaminated <= development, sorted(contaminated - development)


def test_the_exposure_audit_reproduces_from_the_records(cases):
    """Re-derive the ledger rather than trusting the stored one."""
    historical = [json.loads(line) for line
                  in Path("evals/development/v1.jsonl").read_text().splitlines()
                  if line.strip()]
    assert len(historical) == 22
    recomputed = {c["candidate_id"]: classify(c, historical)["status"] for c in cases}
    stored = {r["candidate_id"]: r["exposure_status"] for r in read(LEDGER)["ledger"]}
    assert recomputed == stored


def test_the_historical_exposure_set_is_the_one_the_experiments_used(report):
    historical = report["historical_exposure"]
    assert historical["cases"] == 22
    assert historical["scored"] == 20
    assert historical["abstain_controls"] == 2


# ----------------------------------------------------------------- fact-cluster leakage


def test_no_fact_cluster_straddles_a_split(report):
    assignment = report["assignment"]
    for cluster in read(CLUSTERS)["clusters"]:
        splits = {assignment[m] for m in cluster["members"]}
        assert len(splits) == 1, (
            f"{cluster['cluster_id']} spans {sorted(splits)}: {cluster['members']}")


def test_a_duplicate_fact_cannot_leak_from_development_to_holdout(report):
    """The concrete failure: the same fact scored twice, once tuned and once 'fresh'."""
    assignment = report["assignment"]
    development = {c for c, s in assignment.items() if s == "development"}
    holdout = {c for c, s in assignment.items() if s == "holdout"}
    for cluster in read(CLUSTERS)["clusters"]:
        members = set(cluster["members"])
        assert not (members & development and members & holdout), cluster["cluster_id"]


def test_cases_sharing_an_exact_anchor_are_in_one_split(report, cases):
    """Checked from the records, independently of the stored clusters."""
    assignment = report["assignment"]
    by_anchor: dict[tuple, set[str]] = {}
    for case in cases:
        for span in spans_of(case):
            key = (span["version_id"], span["char_start"], span["char_end"])
            by_anchor.setdefault(key, set()).add(case["candidate_id"])
    for members in by_anchor.values():
        if len(members) < 2:
            continue
        splits = {assignment[m] for m in members}
        assert len(splits) == 1, f"anchor spans {sorted(splits)}: {sorted(members)}"


# ------------------------------------------------------------------------ determinism


def test_the_same_seed_reproduces_the_same_assignment(report, cases):
    from rag_v1.eval import clusters as fact_clusters

    ledger = {r["candidate_id"]: r["exposure_status"] for r in read(LEDGER)["ledger"]}
    contaminated = {c for c, s in ledger.items() if s in CONTAMINATED}
    built = fact_clusters.build(cases, spans_of)
    forced = {c["candidate_id"] for c in cases
              if c.get("reasoning_type") in ("genuine_multi_hop",
                                             "ambiguity_disambiguation")
              and c["candidate_id"] not in contaminated}
    first = assign(cases, built["clusters"], contaminated, forced,
                   report["targets"], seed=SEED)
    second = assign(cases, built["clusters"], contaminated, forced,
                    report["targets"], seed=SEED)
    assert first["assignment"] == second["assignment"]
    assert first["assignment"] == report["assignment"]


def test_a_different_seed_would_produce_a_different_assignment(report, cases):
    """Confirms the seed is actually load-bearing, so recording it is meaningful."""
    from rag_v1.eval import clusters as fact_clusters

    ledger = {r["candidate_id"]: r["exposure_status"] for r in read(LEDGER)["ledger"]}
    contaminated = {c for c, s in ledger.items() if s in CONTAMINATED}
    built = fact_clusters.build(cases, spans_of)
    other = assign(cases, built["clusters"], contaminated, set(), report["targets"],
                   seed=SEED + 1)
    assert other["assignment"] != report["assignment"]


def test_the_split_artifact_hashes_are_stable(report):
    manifest = read(MANIFEST)
    for split, expected in manifest["split_artifact_sha256"].items():
        text = (SPLIT_DIR / f"{split}.json").read_text()
        assert hashlib.sha256(text.encode()).hexdigest() == expected, split


# ----------------------------------------------------------------------- rare cases


def test_the_rare_sentinels_are_placed_by_policy(report):
    rare = report["rare_categories"]
    assert rare["genuine_multi_hop"]["count"] == 1
    for info in rare.values():
        for case_id in info["case_ids"]:
            placement = report["assignment"][case_id]
            if case_id in info["exposed"]:
                assert placement == "development", (
                    f"{case_id} is exposed and must stay in development")
            else:
                assert placement == "holdout", (
                    f"unexposed sentinel {case_id} should be in the holdout")


# ------------------------------------------------------------------ anchors and corpus


def test_all_evidence_anchors_still_validate(cases):
    """The split must not have disturbed the evidence CORPUS-002 verified."""
    corpus = Path("experiments/CORPUS-002/CORPUS-002-gold-anchor-verification.json")
    if not corpus.exists():
        pytest.skip("CORPUS-002 anchor verification is absent")
    summary = json.loads(corpus.read_text())["summary"]
    assert summary["spans_total"] == summary["spans_verified"] == 174
    assert summary["failures"] == []


def test_the_corpus_snapshot_is_unchanged(report):
    assert report["corpus_snapshot"] == SNAPSHOT
    for split in ("development", "validation", "holdout"):
        stored = json.loads((SPLIT_DIR / f"{split}.json").read_text())
        assert stored["corpus_snapshot"] == SNAPSHOT


def test_no_gold_record_was_modified():
    changed = subprocess.run(
        ["git", "status", "--porcelain", "evals/gold/", "evals/review/",
         "experiments/GOLD-001/"],
        capture_output=True, text=True, check=True).stdout.strip()
    assert changed == "", f"GOLD material has uncommitted edits:\n{changed}"


# -------------------------------------------------------------------- holdout guard


def test_the_holdout_is_frozen():
    assert is_frozen() is True
    lock = json.loads((SPLIT_DIR / "holdout.lock.json").read_text())
    assert lock["holdout_frozen"] is True
    assert "challenge-candidate queue" in lock["rule"]
    assert "erratum" in lock["erratum_policy"]


def test_loading_the_holdout_without_the_flag_raises():
    with pytest.raises(FrozenHoldoutError):
        load("holdout")


def test_the_holdout_loads_only_with_an_explicit_flag():
    payload = load("holdout", allow_frozen_holdout=True, reason="test")
    assert payload["count"] == 90


def test_ordinary_helpers_never_enumerate_the_holdout():
    """The accident this guard exists for: a helper that returns 'all the cases'."""
    evaluable = all_evaluable_case_ids()
    holdout = set(json.loads((SPLIT_DIR / "holdout.json").read_text())["case_ids"])
    assert len(evaluable) == 60
    assert not (set(evaluable) & holdout)


def test_development_and_validation_load_freely():
    assert load("development")["count"] == 20
    assert load("validation")["count"] == 40


# ---------------------------------------------------------------------- no retrieval


def test_no_retrieval_was_run_for_this_split(report):
    assert any("No retrieval was run" in item for item in report["not_done"])
    status = json.loads(
        Path("experiments/GOLD-001/GOLD-001-eligibility-status.json").read_text())
    assert status["retrieval_was_not_run"] is True
    assert status["systems_executed"] == []


def test_the_split_carries_no_performance_signal(report):
    """Nothing that could only be known by running a system may appear in the split."""
    text = json.dumps(report)
    for leak in ("bm25_score", "dense_score", "rrf_score", "retrieval_rank",
                 "recall_at", "mrr", "ndcg", "answer_correct"):
        assert leak not in text, f"{leak} appears in the split artifacts"


def test_the_generation_policy_requires_stateless_calls(report):
    policy = report["generation_policy"]["required_runtime_rule"]
    assert "stateless" in policy
    assert "authoring" in policy


def test_all_gates_passed(report):
    assert all(report["gates"].values()), report["gates"]
    assert report["succeeded"] is True
    assert report["holdout_frozen"] is True
