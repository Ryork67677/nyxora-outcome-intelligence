"""Group cases that would leak the same fact across a split boundary.

A split is only independent if the holdout cannot be answered from something already
seen. Two cases quoting the same sentence, or restating the same claim in different
words, are one measurement wearing two hats — put one in development and the other in
the holdout and the holdout is partly a memory test.

Clustering is deliberately conservative: anything that looks shared is treated as
shared, because a false cluster costs a little balance and a missed one costs the
holdout's meaning. Clusters are built with union-find so that transitive overlap —
A shares with B, B shares with C — keeps all three together.
"""

from __future__ import annotations

from rag_v1.eval.exposure import claims_of, jaccard, normalise_question, overlap, tokens

#: Characters of shared evidence that make two cases one fact. One character is a
#: boundary touch; this is the point where two anchors are quoting the same material.
OVERLAP_CHARS = 40
#: Claim wording that differs but says the same thing.
CLAIM_JACCARD = 0.80
#: Question wording that differs but asks the same thing.
QUESTION_JACCARD = 0.75


class _Union:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left, right):
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[b] = a


def _reason(first: dict, second: dict) -> tuple[str, str] | None:
    """Why these two cases are the same fact, or None if they are not."""
    for a in first["spans"]:
        for b in second["spans"]:
            if (a["version_id"] == b["version_id"]
                    and a["char_start"] == b["char_start"]
                    and a["char_end"] == b["char_end"]):
                return ("same_exact_evidence",
                        (f"identical anchor {a['version_id']} "
                         f"{a['char_start']}-{a['char_end']}"))
    best = max(((overlap(a, b), a, b) for a in first["spans"] for b in second["spans"]),
               key=lambda t: t[0], default=(0, None, None))
    if best[0] >= OVERLAP_CHARS:
        return ("overlapping_evidence",
                f"{best[0]} characters shared in {best[1]['version_id']}")
    for a in first["claim_tokens"]:
        for b in second["claim_tokens"]:
            score = jaccard(a, b)
            if score >= CLAIM_JACCARD:
                return ("same_atomic_claim", f"claim token overlap {score:.2f}")
    score = jaccard(first["question_tokens"], second["question_tokens"])
    if score >= QUESTION_JACCARD:
        return ("question_paraphrase", f"question token overlap {score:.2f}")
    return None


def build(cases: list[dict], spans_of) -> dict:
    """Cluster cases by shared fact. Singletons are clusters of one and are reported."""
    prepared = []
    for case in cases:
        prepared.append({
            "candidate_id": case["candidate_id"],
            "spans": spans_of(case),
            "claim_tokens": [tokens(c) for c in claims_of(case)],
            "question_tokens": tokens(normalise_question(
                case.get("question") or case.get("proposed_question"))),
        })
    union = _Union([p["candidate_id"] for p in prepared])
    links = []
    for index, first in enumerate(prepared):
        for second in prepared[index + 1:]:
            found = _reason(first, second)
            if found:
                union.union(first["candidate_id"], second["candidate_id"])
                links.append({"a": first["candidate_id"], "b": second["candidate_id"],
                              "kind": found[0], "detail": found[1]})
    groups: dict[str, list[str]] = {}
    for item in prepared:
        groups.setdefault(union.find(item["candidate_id"]), []).append(
            item["candidate_id"])
    clusters = []
    for index, (root, members) in enumerate(sorted(groups.items()), start=1):
        member_links = [link for link in links
                        if link["a"] in members and link["b"] in members]
        clusters.append({
            "cluster_id": f"FC-{index:03d}",
            "members": sorted(members),
            "size": len(members),
            "root": root,
            "reasons": member_links,
            "shared_identity": (member_links[0]["kind"] if member_links else "singleton"),
        })
    return {"clusters": clusters, "links": links,
            "thresholds": {"overlap_chars": OVERLAP_CHARS,
                           "claim_jaccard": CLAIM_JACCARD,
                           "question_jaccard": QUESTION_JACCARD},
            "multi_member_clusters": [c for c in clusters if c["size"] > 1]}


__all__ = ["CLAIM_JACCARD", "OVERLAP_CHARS", "QUESTION_JACCARD", "build"]
