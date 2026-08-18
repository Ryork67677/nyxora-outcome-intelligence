"""EXP-006 enrichment tests.

The A→B and C→D comparisons are only an ablation of enrichment if the enriched
chunk sets differ from their sources in exactly one respect: the indexed text. If
enrichment ever mutates the canonical body, changes a boundary, or stacks a second
header on re-ingest, the comparison silently stops meaning what the report says.
"""

from __future__ import annotations

import pytest

from rag_v1.enrichment import (
    STRUCTURAL_V1,
    VARIANTS,
    EnrichmentConfig,
    build_context_header,
    enrich,
    is_enriched,
)

BODY = "There is a limit of 100,000 messages in a single request."
SECTION = ["Batches", "Create a Message Batch", "Body Parameters"]


def header() -> str:
    return build_context_header("anthropic", "Message Batches", SECTION)


def test_canonical_body_is_never_mutated():
    # The header goes into search_text only; chunk.text is what a citation quotes.
    enriched = enrich(BODY, header())
    assert enriched.endswith(BODY)
    assert BODY in enriched
    # The body itself is untouched, character for character.
    assert enriched[len(header()) + 1:] == BODY


def test_enrichment_is_idempotent():
    # A repeated ingest must not stack a second header.
    once = enrich(BODY, header())
    twice = enrich(once, header())
    assert once == twice
    assert once.count("Provider:") == 1


def test_enrichment_is_deterministic():
    assert enrich(BODY, header()) == enrich(BODY, header())
    assert build_context_header("anthropic", "T", SECTION) == build_context_header("anthropic", "T", SECTION)


def test_header_is_source_grounded():
    # Every line must be traceable to a field the caller supplied. Nothing is
    # summarised, inferred or invented.
    text = header()
    assert "anthropic" in text
    assert "Message Batches" in text
    for part in SECTION:
        assert part in text
    for line in text.splitlines():
        assert line.split(":", 1)[0] in {"Provider", "Document", "Section"}


def test_missing_fields_are_omitted_not_emitted_empty():
    # An empty label would add a term carrying no information.
    text = build_context_header("", "", SECTION)
    assert "Provider:" not in text
    assert "Document:" not in text
    assert text.startswith("Section:")


def test_empty_header_leaves_text_untouched():
    assert enrich(BODY, "") == BODY


def test_is_enriched_detects_header():
    assert not is_enriched(BODY)
    assert is_enriched(enrich(BODY, header()))


def test_variants_have_distinct_identities():
    hashes = {name: cfg.config_hash for name, cfg in VARIANTS.items()}
    assert len(set(hashes.values())) == len(hashes), hashes


def test_variant_field_subsets_produce_shorter_headers():
    section_only = build_context_header("anthropic", "Message Batches", SECTION, VARIANTS["E1_section_only"])
    full = build_context_header("anthropic", "Message Batches", SECTION, STRUCTURAL_V1)
    assert len(section_only) < len(full)
    assert "Provider:" not in section_only
    assert "Document:" not in section_only


@pytest.mark.parametrize("fields", [("section",), ("document", "section"), ("provider", "document", "section")])
def test_field_order_is_stable_regardless_of_config_order(fields):
    cfg = EnrichmentConfig(name="t", fields=fields)
    text = build_context_header("anthropic", "Doc", SECTION, cfg)
    labels = [line.split(":", 1)[0] for line in text.splitlines()]
    assert labels == sorted(labels, key=lambda label: ["Provider", "Document", "Section"].index(label))
