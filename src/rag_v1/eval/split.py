"""Assign the 150 approved cases to development, validation and holdout.

The order of priorities is fixed and is not negotiable by later stages: contamination
first, then fact-cluster integrity, then the rare-case policy, then sizes, then balance.
A balance objective may never move a contaminated case out of development, and may never
split a cluster.

Everything here runs on pre-retrieval metadata only. Nothing in this module can see
whether a case is easy or hard, and that is the point — a split chosen with performance
knowledge is not a measurement instrument.
"""

from __future__ import annotations

import random
from collections import Counter

DEVELOPMENT = "development"
VALIDATION = "validation"
HOLDOUT = "holdout"
SPLITS = (DEVELOPMENT, VALIDATION, HOLDOUT)

#: Recorded in the manifest and required to reproduce an assignment.
SEED = 689336380
ALGORITHM_VERSION = "eval-split-001/v1"

#: Strata balanced across validation and holdout, in the order the brief gives them.
STRATA = ("provider", "reasoning_stratum", "evidence_shape", "group")


def stratum_of(case: dict) -> dict:
    """The pre-retrieval facts a split may be balanced on.

    ``reasoning_stratum`` buckets the legacy records that predate the field rather than
    inventing a label for them: the record keeps ``reasoning_type = null`` and the
    bucket exists only inside this computation.
    """
    reasoning = case.get("reasoning_type")
    return {
        "provider": case.get("provider") or "unknown",
        "reasoning_stratum": reasoning or "unlabeled_legacy",
        "evidence_shape": case.get("evidence_shape") or "single_span",
        "group": case["group"],
    }


def assign(cases: list[dict], clusters: list[dict], contaminated: set[str],
           forced_holdout: set[str], targets: dict[str, int],
           seed: int = SEED) -> dict:
    """Place every cluster in exactly one split, honouring the priority order."""
    by_id = {c["candidate_id"]: c for c in cases}
    interventions: list[dict] = []

    units = []
    for cluster in clusters:
        members = cluster["members"]
        unit = {
            "cluster_id": cluster["cluster_id"],
            "members": members,
            "size": len(members),
            "contaminated": bool(set(members) & contaminated),
            "forced_holdout": bool(set(members) & forced_holdout),
            "strata": [stratum_of(by_id[m]) for m in members],
        }
        # A cluster with an exposed member is exposed entirely: the clean members quote
        # the same fact, so promoting them would leak it.
        if unit["contaminated"] and unit["forced_holdout"]:
            interventions.append({
                "cluster_id": cluster["cluster_id"],
                "issue": "cluster is both contaminated and holds a rare-category case",
                "resolution": "contamination wins; the cluster goes to development",
                "members": members})
            unit["forced_holdout"] = False
        units.append(unit)

    assigned: dict[str, str] = {}
    counts = Counter()

    def place(unit: dict, split: str) -> None:
        for member in unit["members"]:
            assigned[member] = split
        counts[split] += unit["size"]
        unit["assigned"] = split

    # 1. Contamination. Every exposed or unknown case, and anything clustered with one.
    for unit in units:
        if unit["contaminated"]:
            place(unit, DEVELOPMENT)

    # 2. Rare-category policy, for clean cases only.
    for unit in units:
        if "assigned" not in unit and unit["forced_holdout"]:
            place(unit, HOLDOUT)

    # 3. Everything else, balanced. Deterministic: a fixed seed, and a stable sort.
    remaining = [u for u in units if "assigned" not in u]
    rng = random.Random(seed)
    rng.shuffle(remaining)
    remaining.sort(key=lambda u: (-u["size"], u["cluster_id"]))

    overall = Counter()
    for case in cases:
        for key, value in stratum_of(case).items():
            overall[(key, value)] += 1
    total = len(cases)
    observed: dict[str, Counter] = {s: Counter() for s in SPLITS}
    for member, split in assigned.items():
        for key, value in stratum_of(by_id[member]).items():
            observed[split][(key, value)] += 1

    def cost(unit: dict, split: str) -> float:
        """How far this placement pushes the split from its proportional share."""
        room = targets[split] - counts[split]
        if room < unit["size"]:
            return float("inf")
        share = targets[split] / total if total else 0
        penalty = 0.0
        for stratum in unit["strata"]:
            for key, value in stratum.items():
                want = overall[(key, value)] * share
                have = observed[split][(key, value)]
                penalty += max(0.0, have + 1 - want)
        # Prefer the split furthest from full, so sizes converge together.
        return penalty - (room / max(targets[split], 1))

    for unit in remaining:
        options = sorted(SPLITS, key=lambda s: (cost(unit, s), s))
        best = options[0]
        if cost(unit, best) == float("inf"):
            best = max(SPLITS, key=lambda s: targets[s] - counts[s])
            interventions.append({
                "cluster_id": unit["cluster_id"], "size": unit["size"],
                "issue": "no split had room for this cluster within its target",
                "resolution": f"placed in {best}, the split with the most room",
                "members": unit["members"]})
        place(unit, best)
        for stratum in unit["strata"]:
            for key, value in stratum.items():
                observed[best][(key, value)] += 1

    return {"assignment": assigned, "counts": dict(counts), "units": units,
            "interventions": interventions, "seed": seed,
            "algorithm_version": ALGORITHM_VERSION, "targets": targets}


__all__ = ["ALGORITHM_VERSION", "DEVELOPMENT", "HOLDOUT", "SEED", "SPLITS",
           "STRATA", "VALIDATION", "assign", "stratum_of"]
