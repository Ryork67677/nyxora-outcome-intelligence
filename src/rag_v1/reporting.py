from __future__ import annotations

import json
from pathlib import Path


def paired_compare(old_path: Path, new_path: Path, threshold: float = 1.0) -> dict:
    old = json.loads(old_path.read_text(encoding="utf-8"))
    new = json.loads(new_path.read_text(encoding="utf-8"))
    old_cases = {c["case_id"]: c for c in old["cases"]}
    new_cases = {c["case_id"]: c for c in new["cases"]}
    shared = sorted(set(old_cases) & set(new_cases))

    rescued = []
    regressed = []
    unchanged_good = []
    unchanged_bad = []
    for cid in shared:
        a = old_cases[cid]["recall"] >= threshold
        b = new_cases[cid]["recall"] >= threshold
        if not a and b:
            rescued.append(cid)
        elif a and not b:
            regressed.append(cid)
        elif a and b:
            unchanged_good.append(cid)
        else:
            unchanged_bad.append(cid)
    return {
        "shared_cases": len(shared),
        "rescued": rescued,
        "regressed": regressed,
        "unchanged_good": unchanged_good,
        "unchanged_bad": unchanged_bad,
        "net_rescued": len(rescued) - len(regressed),
    }
