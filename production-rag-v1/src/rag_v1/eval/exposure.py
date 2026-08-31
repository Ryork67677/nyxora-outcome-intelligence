"""Which GOLD cases were already spent on tuning, and must never enter a holdout.

EXP-000 through EXP-014R scored the same 22 development cases nineteen times over. Every
chunker, every fusion weight and every routing decision in this project was chosen while
looking at those results. A GOLD case that asks the same question, or rests on the same
bytes, is not a fresh measurement — it is a memory of one.

The comparison is deliberately blunt and entirely pre-retrieval. It looks at question
text, at evidence identity, at evidence overlap and at claim text. It never looks at
whether a case is easy or hard, because that is exactly the knowledge a split must not
be built from.

Uncertainty resolves toward exposure. A case this module cannot classify is ``UNKNOWN``,
and ``UNKNOWN`` is treated as contaminated for holdout purposes.
"""

from __future__ import annotations

import re

EXPOSED_DIRECT = "EXPOSED_DIRECT"
EXPOSED_EVIDENCE_OVERLAP = "EXPOSED_EVIDENCE_OVERLAP"
EXPOSED_FACT_PARAPHRASE = "EXPOSED_FACT_PARAPHRASE"
EXPOSED_DERIVED = "EXPOSED_DERIVED"
UNEXPOSED = "UNEXPOSED"
UNKNOWN = "UNKNOWN"

#: Any of these bars a case from validation and holdout.
CONTAMINATED = frozenset({EXPOSED_DIRECT, EXPOSED_EVIDENCE_OVERLAP,
                          EXPOSED_FACT_PARAPHRASE, EXPOSED_DERIVED, UNKNOWN})

#: Two questions counted as the same question when their content words agree this far.
#: Chosen to be generous toward exposure rather than precise: a false positive costs one
#: holdout case, a false negative costs the holdout's independence.
PARAPHRASE_JACCARD = 0.70
#: A claim restating a tuned fact, by the same measure.
CLAIM_JACCARD = 0.80

_WORD = re.compile(r"[a-z0-9_.]+")
_STOP = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "does", "do", "did",
    "what", "which", "when", "where", "who", "how", "why", "of", "for", "to", "in",
    "on", "at", "by", "with", "and", "or", "that", "this", "it", "its", "can", "may",
    "must", "should", "will", "if", "from", "as", "into", "per", "you", "your",
})


def tokens(text: str | None) -> set[str]:
    """Content words, lowercased. Identifiers keep their dots and underscores."""
    if not text:
        return set()
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 1}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def normalise_question(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def spans_of(record: dict) -> list[dict]:
    """Evidence anchors in either schema.

    Batches 004 onward carry ``expected_evidence`` as a list; batches 001-003 predate it
    and keep one anchor flat on the record. Reading only the list shape silently skips
    45 of the 150 cases, which in an exposure audit means declaring them clean without
    having looked.
    """
    listed = record.get("expected_evidence") or []
    out = []
    for span in listed:
        if span.get("version_id") and span.get("char_start") is not None:
            out.append({"version_id": span["version_id"],
                        "char_start": span["char_start"],
                        "char_end": span["char_end"],
                        "evidence_text": span.get("evidence_text")})
    if out:
        return out
    if record.get("version_id") and record.get("char_start") is not None:
        return [{"version_id": record["version_id"],
                 "char_start": record["char_start"],
                 "char_end": record["char_end"],
                 "evidence_text": record.get("evidence_text")}]
    return []


def claims_of(record: dict) -> list[str]:
    for key in ("atomic_claims", "proposed_atomic_claims", "expected_claims"):
        value = record.get(key)
        if value:
            return [c for c in value if isinstance(c, str)]
    return []


def overlap(first: dict, second: dict) -> int:
    """Characters shared by two anchors in the same document. 0 if different documents."""
    if first["version_id"] != second["version_id"]:
        return 0
    return max(0, min(first["char_end"], second["char_end"])
               - max(first["char_start"], second["char_start"]))


def classify(case: dict, historical: list[dict]) -> dict:
    """Decide one GOLD case against every historical exposed case.

    Returns the status and the evidence for it: which historical cases matched, on which
    criterion, and with what measurement. A verdict nobody can check is not an audit.
    """
    case_spans = spans_of(case)
    case_question = normalise_question(case.get("question")
                                       or case.get("proposed_question"))
    case_tokens = tokens(case_question)
    case_claims = [tokens(c) for c in claims_of(case)]

    matches: list[dict] = []
    for other in historical:
        other_spans = spans_of(other)
        other_question = normalise_question(other.get("question"))
        # A — identifier equality.
        if case.get("candidate_id") and case.get("candidate_id") == other.get("case_id"):
            matches.append({"case_id": other["case_id"], "criterion": "A_exact_id",
                            "detail": "identical case identifier"})
            continue
        # B — the same question, word for word after normalisation.
        if case_question and case_question == other_question:
            matches.append({"case_id": other["case_id"], "criterion": "B_exact_question",
                            "detail": "normalised question text is identical"})
            continue
        # C and D — evidence identity, then evidence overlap.
        identical = [(s, o) for s in case_spans for o in other_spans
                     if s["version_id"] == o["version_id"]
                     and s["char_start"] == o["char_start"]
                     and s["char_end"] == o["char_end"]]
        if identical:
            span = identical[0][0]
            matches.append({
                "case_id": other["case_id"], "criterion": "C_exact_evidence",
                "detail": (f"same anchor {span['version_id']} "
                           f"{span['char_start']}-{span['char_end']}")})
            continue
        overlapping = [(s, o, overlap(s, o)) for s in case_spans for o in other_spans
                       if overlap(s, o) > 0]
        if overlapping:
            span, other_span, chars = max(overlapping, key=lambda t: t[2])
            matches.append({
                "case_id": other["case_id"], "criterion": "D_evidence_overlap",
                "detail": (f"{chars} characters shared in {span['version_id']} "
                           f"({span['char_start']}-{span['char_end']} vs "
                           f"{other_span['char_start']}-{other_span['char_end']})"),
                "overlap_chars": chars})
            continue
        # E — the same fact stated as a claim, whatever the question asks.
        other_claims = [tokens(c) for c in claims_of(other)]
        best_claim = max((jaccard(a, b) for a in case_claims for b in other_claims),
                         default=0.0)
        if best_claim >= CLAIM_JACCARD:
            matches.append({"case_id": other["case_id"], "criterion": "E_same_claim",
                            "detail": f"claim token overlap {best_claim:.2f}",
                            "similarity": round(best_claim, 3)})
            continue
        # F — a paraphrase of a question the systems were tuned against.
        similarity = jaccard(case_tokens, tokens(other_question))
        if similarity >= PARAPHRASE_JACCARD:
            matches.append({"case_id": other["case_id"], "criterion": "F_paraphrase",
                            "detail": f"question token overlap {similarity:.2f}",
                            "similarity": round(similarity, 3)})
    # G — a composed case is exposed if any of its hops is.
    if len(case_spans) > 1 and matches:
        for match in matches:
            match["composition"] = "multi_span_case; exposure of any hop exposes the case"

    if not case_spans and not case_question:
        return {"status": UNKNOWN, "matches": [],
                "reason": ("neither an anchor nor a question could be read from this "
                           "record, so exposure cannot be ruled out")}
    if not matches:
        if not case_spans:
            return {"status": UNKNOWN, "matches": [],
                    "reason": ("no evidence anchor to compare; question text alone "
                               "cannot rule out evidence-level exposure")}
        return {"status": UNEXPOSED, "matches": [],
                "reason": ("no historical case shares this question, its anchor, an "
                           "overlapping anchor, or its claim")}
    ranked = {"A_exact_id": EXPOSED_DIRECT, "B_exact_question": EXPOSED_DIRECT,
              "C_exact_evidence": EXPOSED_DIRECT,
              "D_evidence_overlap": EXPOSED_EVIDENCE_OVERLAP,
              "E_same_claim": EXPOSED_FACT_PARAPHRASE,
              "F_paraphrase": EXPOSED_FACT_PARAPHRASE}
    order = [EXPOSED_DIRECT, EXPOSED_EVIDENCE_OVERLAP, EXPOSED_FACT_PARAPHRASE,
             EXPOSED_DERIVED]
    statuses = [ranked[m["criterion"]] for m in matches]
    status = min(statuses, key=order.index)
    return {"status": status, "matches": matches,
            "reason": "; ".join(f"{m['case_id']} via {m['criterion']}: {m['detail']}"
                                for m in matches[:4])}


__all__ = [
    "CLAIM_JACCARD", "CONTAMINATED", "EXPOSED_DERIVED", "EXPOSED_DIRECT",
    "EXPOSED_EVIDENCE_OVERLAP", "EXPOSED_FACT_PARAPHRASE", "PARAPHRASE_JACCARD",
    "UNEXPOSED", "UNKNOWN", "claims_of", "classify", "jaccard", "normalise_question",
    "overlap", "spans_of", "tokens",
]
