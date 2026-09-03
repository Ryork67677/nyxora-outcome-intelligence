"""EXP-011 tests: query-side transforms are only interpretable if they are
deterministic, lossless where it matters, and blind to the evaluation set.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_v1.query_views import (
    QUERY_TRANSFORM_VERSION,
    build_views,
    decompose_query,
    identifiers,
    numbers,
    raw_view,
    structured_query,
    technical_normalized_query,
)

RESULTS = Path("experiments/EXP-011/results.json")
TRANSFORMER_MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
MODEL_FINGERPRINT = "bd95feaeacf98559"
CONTROL_SET = "cs_v1_control"

# Held-out strings written for these tests. None is a golden question.
PROBES = [
    "How do I set max_tokens when calling client.messages.create?",
    "What is the default top_p value for the Responses API?",
    "Why does the server return HTTP 429 after 4000 requests per minute?",
    "Could you please explain what tool_choice does in version 2024-06-01?",
    "list the batch limits",
    "max_output_tokens",
]


# -- 1. determinism ----------------------------------------------------------

@pytest.mark.parametrize("query", PROBES)
def test_normalization_is_deterministic(query):
    assert technical_normalized_query(query).text == technical_normalized_query(query).text


@pytest.mark.parametrize("query", PROBES)
def test_decomposition_is_deterministic(query):
    assert decompose_query(query) == decompose_query(query)
    assert structured_query(query).text == structured_query(query).text


def test_transforms_are_pure_functions_of_the_query_string():
    """No hidden state may make the same query transform differently over time."""
    first = [v.text for v in build_views(PROBES[0])]
    for _ in range(5):
        build_views(PROBES[2])  # unrelated work in between
    assert [v.text for v in build_views(PROBES[0])] == first


# -- 2/3. preservation guarantees --------------------------------------------

@pytest.mark.parametrize("query", PROBES)
def test_identifiers_survive_every_view(query):
    expected = identifiers(query)
    for view in build_views(query):
        assert expected <= identifiers(view.text), (
            f"{view.name} dropped identifiers: {expected - identifiers(view.text)}"
        )


@pytest.mark.parametrize(
    "identifier",
    ["max_tokens", "max_output_tokens", "top_p", "tool_choice", "client.messages.create"],
)
def test_named_identifiers_are_never_corrupted(identifier):
    query = f"What is the default for {identifier} in the API?"
    for view in build_views(query):
        assert identifier in view.text, f"{view.name} corrupted {identifier}"


@pytest.mark.parametrize("query", PROBES)
def test_numbers_and_versions_survive_every_view(query):
    expected = numbers(query)
    for view in build_views(query):
        assert expected <= numbers(view.text), (
            f"{view.name} dropped numbers: {expected - numbers(view.text)}"
        )


def test_http_status_codes_survive():
    for view in build_views("What does HTTP 429 mean?"):
        assert "429" in view.text


def test_provider_names_are_preserved_but_never_invented():
    with_provider = build_views("What is the Anthropic Messages API rate limit?")
    for view in with_provider:
        assert "Anthropic" in view.text

    # A query naming no provider must not acquire one.
    without = build_views("What is the rate limit?")
    for view in without:
        for provider in ("Anthropic", "OpenAI", "Claude"):
            assert provider not in view.text, f"{view.name} invented a provider name"


# -- 4. the original query is always retained --------------------------------

def test_raw_view_is_byte_identical_to_the_user_query():
    for query in PROBES:
        assert raw_view(query).text == query


def test_multi_view_configurations_always_include_the_raw_query():
    for views in (("raw",), ("raw", "normalized"), ("raw", "normalized", "structured")):
        built = build_views(PROBES[0], views)
        assert built[0].name == "raw"
        assert built[0].text == PROBES[0]


def test_a_transform_never_returns_an_empty_query():
    for query in ["how do I do it?", "what is that", "the", "?"]:
        for view in build_views(query):
            assert view.text.strip(), f"{view.name} emptied {query!r}"


# -- 5. leakage controls -----------------------------------------------------

def _code_only(path: str) -> str:
    """Source with comments and docstrings removed.

    The prose in this module *describes* the leakage rules, so it necessarily
    contains words like "golden". Checking raw text would flag the documentation
    that explains the guarantee. Only executable code is inspected.
    """
    import io
    import tokenize

    out = []
    with open(path, "rb") as handle:
        tokens = list(tokenize.tokenize(io.BytesIO(handle.read()).readline))
    prev_type = tokenize.INDENT
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and prev_type in (
            tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.NL, tokenize.ENCODING
        ):
            continue  # docstring
        out.append(tok.string)
        if tok.type not in (tokenize.NL, tokenize.NEWLINE):
            prev_type = tok.type
    return " ".join(out)


def test_transform_module_has_no_reference_to_the_evaluation_set():
    code = _code_only("src/rag_v1/query_views.py")
    for banned in ("golden", "evals", "load_cases", "expected_evidence", "case_id",
                   "EvidenceRef", "section_path", "version_id", "chunk_id"):
        assert banned not in code, f"query transform code references {banned!r}"


def test_transform_module_hardcodes_no_golden_question_or_evidence():
    """The strongest available check: no golden text may appear in the module."""
    from rag_v1.evals.io import load_cases

    golden = Path("evals/golden/v1.jsonl")
    if not golden.exists():
        pytest.skip("golden set unavailable")
    source = Path("src/rag_v1/query_views.py").read_text().lower()
    for case in load_cases(golden):
        question = case.question.lower().strip("?. ")
        assert question not in source, f"{case.case_id} question is hardcoded"
        for ref in case.expected_evidence:
            # Only distinctive strings can constitute leakage. A single ordinary
            # noun such as "Configuration" appearing in a section path is a word of
            # English, not evidence, and flagging it would make this test noise.
            full_path = " ".join(ref.section_path).lower()
            assert full_path not in source, f"{case.case_id} section path leaked"
            for part in ref.section_path:
                if len(part.split()) > 1:
                    assert part.lower() not in source, f"{case.case_id} section path leaked"


def test_transforms_import_nothing_from_the_eval_package():
    import rag_v1.query_views as mod

    source = Path(mod.__file__).read_text()
    imported = [ln.strip() for ln in source.splitlines()
                if ln.startswith(("import ", "from ")) and "__future__" not in ln]
    # Only the standard library, and only what is needed to parse a string. Any
    # project import would be a route for corpus or evaluation knowledge to enter.
    assert imported == ["import re", "from dataclasses import dataclass, field"], (
        f"unexpected imports in query transforms: {imported}"
    )
    assert "rag_v1" not in " ".join(imported)


# -- 6. decomposition behaviour ----------------------------------------------

def test_decomposition_extracts_only_terms_present_in_the_question():
    query = "What is the maximum batch size for the Responses API?"
    parts = decompose_query(query)
    lowered = query.lower()
    for entity in parts["entities"]:
        for word in entity.split():
            assert word.lower() in lowered
    for op in parts["operations"]:
        assert op in lowered
    # asked_property may come from a phrase alias, which is recorded as added.
    view = structured_query(query)
    for added in view.added_terms:
        assert added["rule"].startswith(("decompose_query", "PHRASE_ALIASES"))


def test_structured_view_records_its_fields_for_inspection():
    view = structured_query("How many requests can a batch create at most?")
    assert set(view.fields) == {"entities", "operations", "asked_property",
                                "identifiers", "numbers"}


# -- 7. query embedding cache ------------------------------------------------

def test_query_embedding_cache_is_keyed_on_text_and_fingerprint():
    from rag_v1.query_cache import CachedQueryEmbedder

    class Counting:
        model_version = "fp1"

        def __init__(self):
            self.calls = 0

        def embed(self, texts):
            self.calls += 1
            return [[float(len(t))] for t in texts]

    inner = Counting()
    cache = CachedQueryEmbedder(inner, fingerprint="fp1")
    assert cache.embed(["alpha"]) == [[5.0]]
    assert cache.embed(["alpha"]) == [[5.0]]
    assert inner.calls == 1, "identical query was re-encoded"
    assert cache.hits == 1 and cache.misses == 1

    # A different fingerprint must not read the first model's vectors.
    other = CachedQueryEmbedder(Counting(), fingerprint="fp2")
    assert other.key("alpha") != cache.key("alpha")


def test_query_cache_does_not_touch_document_embeddings():
    source = Path("src/rag_v1/query_cache.py").read_text()
    for banned in ("chunk_embedding", "INSERT", "UPDATE", "DELETE"):
        assert banned not in source, f"query cache references {banned!r}"


# -- 8. document side is frozen ----------------------------------------------

@pytest.fixture(scope="module")
def cursor():
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.db import connect

    try:
        with connect() as conn, conn.cursor() as cur:
            yield cur
    except psycopg.OperationalError:
        pytest.skip("database unavailable")


def test_document_embeddings_are_unchanged_from_exp009(cursor):
    cursor.execute(
        """
        SELECT count(*) FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id
        WHERE ce.model_id=%s AND c.chunk_set_id=%s
        """,
        (TRANSFORMER_MODEL, CONTROL_SET),
    )
    assert cursor.fetchone()[0] == 14209
    cursor.execute(
        "SELECT DISTINCT model_fingerprint FROM chunk_embedding WHERE model_id=%s",
        (TRANSFORMER_MODEL,),
    )
    assert {r[0] for r in cursor.fetchall()} == {MODEL_FINGERPRINT}


def test_control_chunks_are_unchanged(cursor):
    cursor.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CONTROL_SET,))
    assert cursor.fetchone()[0] == 14209


# -- 9/10/11. labelled fusion ------------------------------------------------

def _hit(chunk_id, rank, retriever="lexical", start=0):
    from rag_v1.types import SearchHit

    return SearchHit(chunk_id=chunk_id, version_id="v1", section_path=["S"], char_start=start,
                     char_end=start + 10, text="t", score=1.0, rank=rank, retriever=retriever)


def test_labelled_fusion_is_deterministic():
    from rag_v1.retrieval import rrf_fuse_labelled

    lists = [("bm25(raw)", [_hit("a", 1), _hit("b", 2)]),
             ("transformer(raw)", [_hit("b", 1), _hit("c", 2)])]
    first = rrf_fuse_labelled(lists, rrf_k=60, top_k=10)
    second = rrf_fuse_labelled(lists, rrf_k=60, top_k=10)
    assert [(h.chunk_id, h.rank, round(h.score, 12)) for h in first] == \
           [(h.chunk_id, h.rank, round(h.score, 12)) for h in second]


def test_two_views_are_not_collapsed_by_sharing_a_retriever_name():
    """The defect plain RRF has: both BM25 lists carry retriever='lexical'."""
    from rag_v1.retrieval import rrf_fuse_labelled

    lists = [("bm25(raw)", [_hit("a", 1)]), ("bm25(normalized)", [_hit("a", 1)])]
    fused = rrf_fuse_labelled(lists, rrf_k=60, top_k=10)
    assert fused[0].metadata["source_count"] == 2
    assert set(fused[0].metadata["rrf_contributions"]) == {"bm25(raw)", "bm25(normalized)"}


def test_one_list_cannot_reward_the_same_chunk_twice():
    from rag_v1.retrieval import rrf_fuse_labelled

    duplicated = [("bm25(raw)", [_hit("a", 1), _hit("a", 5)])]
    fused = rrf_fuse_labelled(duplicated, rrf_k=60, top_k=10)
    assert len(fused) == 1
    # Scored at its best rank only.
    assert fused[0].score == pytest.approx(1.0 / 61)


def test_fusion_records_contribution_provenance():
    from rag_v1.retrieval import rrf_fuse_labelled

    lists = [("bm25(raw)", [_hit("a", 3)]), ("transformer(structured)", [_hit("a", 7)])]
    fused = rrf_fuse_labelled(lists, rrf_k=60, top_k=10)
    meta = fused[0].metadata
    assert meta["source_ranks"] == {"bm25(raw)": 3, "transformer(structured)": 7}
    assert meta["contributing_sources"] == ["bm25(raw)", "transformer(structured)"]
    assert meta["rrf_contributions"]["bm25(raw)"] == pytest.approx(1 / 63)


def test_identical_view_text_is_deduplicated_before_retrieval():
    """A view that collapses to the raw text must not be fused twice."""
    # A query with no filler and no aliasable phrase normalizes to itself.
    query = "max_output_tokens"
    views = build_views(query, ("raw", "normalized"))
    assert views[0].text == views[1].text
    by_text: dict[str, list[str]] = {}
    for view in views:
        by_text.setdefault(view.text, []).append(view.name)
    assert len(by_text) == 1, "duplicate view texts must collapse to one retrieval"


# -- 12. reproduction --------------------------------------------------------

def test_exp011a_reproduces_the_frozen_hybrid():
    if not RESULTS.exists():
        pytest.skip("EXP-011 results not built")
    payload = json.loads(RESULTS.read_text())
    gate = payload["reproduction_gate"]["A_raw_query_control"]
    assert gate["reproduced"], gate["checks"]
    cfg = payload["configurations"]["A_raw_query_control"]
    assert cfg["macro_span_recall"] == 0.775
    assert cfg["cases_fully_recalled"] == 15
    assert cfg["spans_found_at_10"] == 17


def test_results_declare_a_frozen_document_side():
    if not RESULTS.exists():
        pytest.skip("EXP-011 results not built")
    payload = json.loads(RESULTS.read_text())
    assert payload["chunk_set"] == CONTROL_SET
    assert payload["transformer_fingerprint"] == MODEL_FINGERPRINT
    assert payload["query_transform_version"] == QUERY_TRANSFORM_VERSION
    cfg = payload["retrieval_config"]
    assert cfg["reranker"] is None
    assert cfg["llm_query_rewriting"] is False
    assert cfg["metadata_filtering"] is False
    assert cfg["ann_index"] is False
    assert payload["candidate_pool"] == 50 and payload["rrf_k"] == 60 and payload["top_k"] == 10


def test_no_configuration_exceeds_the_three_view_budget():
    if not RESULTS.exists():
        pytest.skip("EXP-011 results not built")
    payload = json.loads(RESULTS.read_text())
    for key, cfg in payload["configurations"].items():
        assert len(cfg["query_views"]) <= 3, f"{key} uses more than three query views"
