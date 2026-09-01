"""PERF-001 was a read-only audit. These tests assert it stayed read-only.

The value of a performance audit that runs alongside a live experiment is
entirely in what it did *not* do. An audit that quietly reran a system, or
edited the thing it was measuring, would have contaminated EXP-018B and would
be worth less than no audit at all. So the constraints are asserted, not
claimed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "experiments" / "PERF-001"
MEASUREMENTS = json.loads((AUDIT / "PERF-001-measurements.json").read_text())


def test_audit_artifacts_exist():
    for name in ("PERF-001-report.md", "PERF-001-measurements.json",
                 "PERF-001-proposed.patch", "PERF-001-report.pdf"):
        assert (AUDIT / name).is_file(), name


def test_no_patch_was_applied():
    assert MEASUREMENTS["patch_applied"] is False
    # The proposed change is documentation. If it had been applied, the batched
    # entry point would exist in the module it targets.
    retrieval = (ROOT / "src" / "rag_v1" / "retrieval.py").read_text()
    assert "local_lexical_search_batch" not in retrieval
    assert "_LOCAL_BATCH_SQL" not in retrieval


def test_scoring_semantics_are_untouched():
    """The three constants and the tie-break that define a BM25 score."""
    retrieval = (ROOT / "src" / "rag_v1" / "retrieval.py").read_text()
    assert "BM25_K1 = 1.2" in retrieval
    assert "BM25_B = 0.75" in retrieval
    assert "ORDER BY round(scored.score::numeric, 9) DESC, scored.chunk_id" in retrieval


def test_term_statistics_are_still_full_corpus():
    """The invariant every proposed optimization has to preserve.

    The corpus and weighted CTEs must not be restricted to routed documents:
    the version_ids filter belongs to the scoring select alone.
    """
    retrieval = (ROOT / "src" / "rag_v1" / "retrieval.py").read_text()
    sql = retrieval.split("_LEXICAL_SQL = ")[1].split('"""')[1]
    before_scoring = sql.split("SELECT * FROM (")[0]
    assert "version_ids" not in before_scoring
    assert sql.count("version_ids") >= 1


def test_every_declared_constraint_is_negative():
    for name, value in MEASUREMENTS["constraints_observed"].items():
        assert value is False, f"{name} should be False"


def test_no_experiment_was_started_or_touched():
    experiments = {p.name for p in (ROOT / "experiments").iterdir() if p.is_dir()}
    for forbidden in ("EXP-017", "EXP-018", "EXP-018B", "EXP-019"):
        assert forbidden not in experiments


def _audit_text(path: Path) -> str:
    """Every audit artifact as text, including the rendered PDF.

    The PDF is the deliverable people actually circulate, so scanning only the
    Markdown would check the wrong document.
    """
    if path.suffix != ".pdf":
        return path.read_text()
    from pypdf import PdfReader

    return "\n".join(page.extract_text() for page in PdfReader(path).pages)


def test_no_case_identifier_leaked_into_the_audit():
    """The audit is about code, not about cases, so it should name almost none.

    Note this deliberately does NOT open the frozen holdout to compare against:
    reading it to prove you did not read it is self-defeating. Scanning for the
    identifier *shape* is sufficient and costs no holdout access.
    """
    blob = "\n".join(_audit_text(p) for p in sorted(AUDIT.iterdir()))
    found = set(re.findall(r"\b(?:GOLD-B\d{3}-\d{2}|HA-\d{2}|V2D-\d+)\b", blob))
    # The four EXP-018 pool rescues are disclosed in the handoff as diagnostic
    # only, and are cited here to name what a bad optimization would break.
    assert found <= {"V2D-11", "V2D-33", "V2D-34", "V2D-43"}, sorted(found)


def test_holdout_access_log_was_not_written_by_this_audit():
    from rag_v1.eval.splits import ACCESS_LOG

    log = Path(ACCESS_LOG)
    assert not log.exists() or "PERF-001" not in log.read_text()


def test_ce_question_is_reported_unanswerable_rather_than_estimated():
    """EXP-015 found no cross-encoder here, so question 6 has no answer.

    Reporting it as blocked is the finding. A plausible number would be worse
    than none, because it would be acted on.
    """
    assert MEASUREMENTS["repository_state"]["cross_encoder_implementation_present"] is False
    ids = [u["question"] for u in MEASUREMENTS["unanswerable_here"]]
    assert any(q.startswith("6 -") for q in ids)


def test_avg_len_equivalence_claim_is_recorded_as_bitwise():
    proof = MEASUREMENTS["avg_len_equivalence_proof"]
    assert proof["float8send_bitwise_identical"] is True
    # The stored quantities must be the exact integers, not the float.
    assert isinstance(proof["n"], int) and isinstance(proof["sum_length"], int)
    assert proof["avg_direct_float8"] == proof["avg_from_exact_sum_float8"]
