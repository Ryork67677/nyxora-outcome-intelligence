#!/usr/bin/env python3
"""Prove the EVAL-NATQ2-H-002 decision rule is exhaustive and mutually exclusive.

The repair adds one FAIL clause: a significant regression now fails instead of falling
through to INCONCLUSIVE. Adding a clause to a three-way rule is exactly the kind of edit
that quietly creates an overlap, so the rule is enumerated over its full state space
rather than argued about. Synthetic values only; no run, no data.

State space: whether the preregistered 95% bootstrap interval includes zero, the sign of
the mean delta, and where case_hit@10 sits relative to the two floors. Every reachable
combination is classified and checked.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "EVAL-NATQ2-H-002-BOUNDARY-CHECK.json"
PASS_FLOOR, FAIL_FLOOR = 0.80, 0.65


def is_pass(ci_includes_zero: bool, delta: float, case_hit: float) -> bool:
    """PASS — unchanged from EVAL-NATQ2-H-001."""
    return (not ci_includes_zero) and delta > 0 and case_hit >= PASS_FLOOR


def is_fail(ci_includes_zero: bool, delta: float, case_hit: float) -> bool:
    """FAIL — the replacement clause approved by the coordinator.

    Third disjunct is new: an interval excluding zero with a negative mean delta is a
    decisive regression and must not be reported as INCONCLUSIVE.
    """
    return (ci_includes_zero
            or ((not ci_includes_zero) and delta < 0)
            or case_hit < FAIL_FLOOR)


def classify(ci_includes_zero: bool, delta: float, case_hit: float) -> str:
    p, f = is_pass(ci_includes_zero, delta, case_hit), is_fail(ci_includes_zero, delta, case_hit)
    if p and f:
        return "OVERLAP"
    if p:
        return "PASS"
    if f:
        return "FAIL"
    return "INCONCLUSIVE"


# case_hit@10 moves in steps of 1/40 on this partition, so the two floors are exactly
# attainable. The probes sit on and either side of both floors.
CASE_HIT_PROBES = [
    ("0.625 = 25/40, just below the FAIL floor", 0.625),
    ("0.650 = 26/40, exactly the FAIL floor", 0.650),
    ("0.675 = 27/40, inside the inconclusive band", 0.675),
    ("0.775 = 31/40, just below the PASS floor", 0.775),
    ("0.800 = 32/40, exactly the PASS floor", 0.800),
    ("0.825 = 33/40, above the PASS floor", 0.825),
]
DELTA_PROBES = [
    ("positive", 0.06),
    ("zero", 0.0),
    ("negative", -0.06),
]


def main() -> int:
    rows = []
    for ci_label, ci in (("includes zero", True), ("excludes zero", False)):
        for d_label, d in DELTA_PROBES:
            # An interval excluding zero cannot straddle a zero mean in any real
            # bootstrap, but the combination is enumerated rather than assumed away.
            for c_label, c in CASE_HIT_PROBES:
                rows.append({
                    "ci": ci_label, "delta_sign": d_label, "delta": d,
                    "case_hit_at_10": c, "case_hit_note": c_label,
                    "verdict": classify(ci, d, c),
                })

    overlaps = [r for r in rows if r["verdict"] == "OVERLAP"]
    unclassified = [r for r in rows if r["verdict"] not in {"PASS", "FAIL", "INCONCLUSIVE"}]
    inconclusive = [r for r in rows if r["verdict"] == "INCONCLUSIVE"]

    # The regression the repair targets: significant, negative, case_hit above the floor.
    regression = [r for r in rows
                  if r["ci"] == "excludes zero" and r["delta"] < 0
                  and r["case_hit_at_10"] >= FAIL_FLOOR]
    regression_all_fail = all(r["verdict"] == "FAIL" for r in regression)

    # Under the OLD rule those same states were INCONCLUSIVE. Show the repair bites.
    def old_fail(ci, d, c):
        return ci or c < FAIL_FLOOR

    def old_classify(ci, d, c):
        p = is_pass(ci, d, c)
        return "PASS" if p else ("FAIL" if old_fail(ci, d, c) else "INCONCLUSIVE")

    changed = [{"ci": r["ci"], "delta": r["delta"], "case_hit_at_10": r["case_hit_at_10"],
                "old": old_classify(r["ci"] == "includes zero", r["delta"], r["case_hit_at_10"]),
                "new": r["verdict"]}
               for r in rows
               if old_classify(r["ci"] == "includes zero", r["delta"], r["case_hit_at_10"])
               != r["verdict"]]

    # Residual: the only states still INCONCLUSIVE, described so nothing hides in "otherwise".
    residual = sorted({(r["ci"], r["delta_sign"],
                        "case_hit >= 0.80" if r["case_hit_at_10"] >= PASS_FLOOR
                        else ("0.65 <= case_hit < 0.80" if r["case_hit_at_10"] >= FAIL_FLOOR
                              else "case_hit < 0.65"))
                       for r in inconclusive})

    payload = {
        "record_id": "EVAL-NATQ2-H-002-BOUNDARY-CHECK",
        "purpose": "Exhaustiveness and mutual-exclusivity proof for the replacement decision rule.",
        "uses_real_data": False, "uses_database": False, "systems_run": 0,
        "floors": {"PASS": PASS_FLOOR, "FAIL": FAIL_FLOOR},
        "states_enumerated": len(rows),
        "mutually_exclusive": not overlaps,
        "overlap_states": overlaps,
        "exhaustive": not unclassified,
        "unclassified_states": unclassified,
        "regression_states_checked": len(regression),
        "every_significant_regression_now_fails": regression_all_fail,
        "states_whose_verdict_the_repair_changes": changed,
        "residual_inconclusive_states": [
            {"ci": a, "delta_sign": b, "case_hit_band": c} for a, b, c in residual],
        "residual_note": (
            "Two families remain INCONCLUSIVE by design: a significant improvement whose "
            "case_hit@10 lands in the 0.65-0.80 band, which is the band's whole purpose; and "
            "the degenerate combination of an interval excluding zero with a mean delta of "
            "exactly zero, which a percentile bootstrap cannot produce because the interval "
            "brackets the resampled mean. The latter is enumerated for completeness, not "
            "because it is reachable."),
        "boundary_semantics": {
            "PASS at exactly 0.80": classify(False, 0.06, 0.800),
            "just below at 0.775": classify(False, 0.06, 0.775),
            "FAIL at exactly 0.65": classify(False, 0.06, 0.650),
            "just below at 0.625": classify(False, 0.06, 0.625),
            "significant regression at 0.70": classify(False, -0.06, 0.700),
            "non-significant at 0.90": classify(True, 0.06, 0.900),
        },
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")

    print(f"states enumerated              {len(rows)}")
    print(f"mutually exclusive             {not overlaps}")
    print(f"exhaustive                     {not unclassified}")
    print(f"significant regressions FAIL   {regression_all_fail} ({len(regression)} states)")
    print(f"verdicts changed by the repair {len(changed)}")
    for k, v in payload["boundary_semantics"].items():
        print(f"  {k:<34} {v}")
    ok = (not overlaps) and (not unclassified) and regression_all_fail
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
