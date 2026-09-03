"""Database-level invariants the EXP-006 ablation depends on.

These run against the live corpus when it is present and skip cleanly when it is
not, so the suite still passes on a fresh checkout with no database.
"""

from __future__ import annotations

import pytest

CONTROL = "cs_v1_control"
CONTROL_ENRICHED = "cs_9c954ccda98fd7fad38c509c"
BOUNDED = "cs_2722bf8b72dcf3eb404336d7"
BOUNDED_ENRICHED = "cs_fcaebc23c86104500e483609"

PAIRS = [(CONTROL, CONTROL_ENRICHED), (BOUNDED, BOUNDED_ENRICHED)]


@pytest.fixture(scope="module")
def cursor():
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.db import connect

    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chunk_set")
            if cur.fetchone()[0] == 0:
                pytest.skip("no chunk sets ingested")
            yield cur
    except psycopg.OperationalError:
        pytest.skip("database unavailable")


def _count(cursor, sql, params):
    cursor.execute(sql, params)
    return cursor.fetchone()[0]


@pytest.mark.parametrize(("source", "enriched"), PAIRS)
def test_enriched_set_has_identical_chunk_boundaries(cursor, source, enriched):
    # If a boundary moved, A->B would no longer isolate enrichment.
    if _count(cursor, "SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (enriched,)) == 0:
        pytest.skip(f"{enriched} not built")
    diffs = _count(
        cursor,
        """
        SELECT count(*) FROM chunk a
        JOIN chunk b ON b.chunk_set_id=%s AND b.version_id=a.version_id AND b.ordinal=a.ordinal
        WHERE a.chunk_set_id=%s
          AND (a.char_start, a.char_end, a.section_path, a.chunk_type)
              IS DISTINCT FROM (b.char_start, b.char_end, b.section_path, b.chunk_type)
        """,
        (enriched, source),
    )
    assert diffs == 0


@pytest.mark.parametrize(("source", "enriched"), PAIRS)
def test_enrichment_does_not_touch_the_canonical_body(cursor, source, enriched):
    if _count(cursor, "SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (enriched,)) == 0:
        pytest.skip(f"{enriched} not built")
    diffs = _count(
        cursor,
        """
        SELECT count(*) FROM chunk a
        JOIN chunk b ON b.chunk_set_id=%s AND b.version_id=a.version_id AND b.ordinal=a.ordinal
        WHERE a.chunk_set_id=%s AND a.text IS DISTINCT FROM b.text
        """,
        (enriched, source),
    )
    assert diffs == 0


@pytest.mark.parametrize(("source", "enriched"), PAIRS)
def test_enriched_search_text_starts_with_its_header_then_the_body(cursor, source, enriched):
    if _count(cursor, "SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (enriched,)) == 0:
        pytest.skip(f"{enriched} not built")
    bad = _count(
        cursor,
        """
        SELECT count(*) FROM chunk
        WHERE chunk_set_id=%s
          AND (search_text IS NULL
               OR context_header IS NULL
               OR search_text <> context_header || chr(10) || text)
        """,
        (enriched,),
    )
    assert bad == 0


@pytest.mark.parametrize(("source", "enriched"), PAIRS)
def test_no_duplicate_headers_were_stacked(cursor, source, enriched):
    if _count(cursor, "SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (enriched,)) == 0:
        pytest.skip(f"{enriched} not built")
    # Counting occurrences of "Provider:" anywhere would be wrong: four chunk
    # bodies legitimately discuss a field called "Provider:" in their prose. The
    # real invariant is that no *body* was ever enriched, so re-running enrichment
    # cannot prepend a second header.
    bodies_already_enriched = _count(
        cursor,
        "SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND text LIKE 'Provider:%%'",
        (enriched,),
    )
    assert bodies_already_enriched == 0

    # And search_text carries exactly one header: everything after the first
    # newline must equal the untouched body.
    mismatched = _count(
        cursor,
        """
        SELECT count(*) FROM chunk
        WHERE chunk_set_id=%s
          AND substring(search_text from length(context_header) + 2) <> text
        """,
        (enriched,),
    )
    assert mismatched == 0


def test_unenriched_sets_leave_search_text_null(cursor):
    # NULL means "index chunk.text verbatim", which is what keeps the pre-EXP-006
    # tsvectors byte-identical and EXP-000..EXP-005 reproducible.
    for chunk_set in (CONTROL, BOUNDED):
        non_null = _count(
            cursor,
            "SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND search_text IS NOT NULL",
            (chunk_set,),
        )
        assert non_null == 0, chunk_set


def test_search_vector_indexes_search_text_when_present(cursor):
    if _count(cursor, "SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CONTROL_ENRICHED,)) == 0:
        pytest.skip("enriched set not built")
    # A header-only term must be findable in the enriched set and not in the plain one.
    enriched_hits = _count(
        cursor,
        "SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND search_vector @@ phraseto_tsquery('simple','Provider')",
        (CONTROL_ENRICHED,),
    )
    plain_hits = _count(
        cursor,
        "SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND search_vector @@ phraseto_tsquery('simple','Provider')",
        (CONTROL,),
    )
    assert enriched_hits > plain_hits


def test_lexical_search_still_uses_the_gin_index(cursor):
    # Guards the EXP-005 planner regression: an extra join made Postgres abandon
    # the GIN index and the evaluation went from under a second to over a minute.
    from rag_v1.retrieval import _LEXICAL_SQL, BM25_B, BM25_K1, query_terms

    cursor.execute("SELECT snapshot_id FROM corpus_snapshot WHERE chunk_set_id=%s LIMIT 1", (CONTROL,))
    row = cursor.fetchone()
    if not row:
        pytest.skip("no snapshot for the control chunk set")
    snapshot_id = row[0]

    cursor.execute(
        "EXPLAIN " + _LEXICAL_SQL,
        {
            "terms": query_terms("Which HTTP status code does request_too_large return?"),
            "snapshot_id": snapshot_id,
            "chunk_set_id": CONTROL,
            "k": 10,
            "k1": BM25_K1,
            "b": BM25_B,
            # EXP-012 added an optional document restriction to the scoring select.
            # NULL means "whole snapshot", i.e. exactly the pre-EXP-012 query, and
            # the plan must be unchanged in that case.
            "version_ids": None,
        },
    )
    plan = "\n".join(r[0] for r in cursor.fetchall())
    assert "idx_chunk_search_vector" in plan, plan


def test_lexical_search_keeps_the_gin_index_when_documents_are_restricted(cursor):
    """EXP-012 routes to a document subset; that must not cost the GIN plan.

    This is the FAIL-0001 failure mode: an extra predicate gave the planner another
    way to reach the rows and it abandoned the index, taking the evaluation from
    under a second to over a minute.
    """
    from rag_v1.retrieval import _LEXICAL_SQL, BM25_B, BM25_K1, query_terms

    cursor.execute("SELECT snapshot_id FROM corpus_snapshot WHERE chunk_set_id=%s LIMIT 1", (CONTROL,))
    row = cursor.fetchone()
    if not row:
        pytest.skip("no snapshot for the control chunk set")
    cursor.execute("SELECT DISTINCT version_id FROM chunk WHERE chunk_set_id=%s LIMIT 5", (CONTROL,))
    versions = [r[0] for r in cursor.fetchall()]
    if not versions:
        pytest.skip("no versions")

    cursor.execute(
        "EXPLAIN " + _LEXICAL_SQL,
        {
            "terms": query_terms("Which HTTP status code does request_too_large return?"),
            "snapshot_id": row[0],
            "chunk_set_id": CONTROL,
            "k": 10,
            "k1": BM25_K1,
            "b": BM25_B,
            "version_ids": versions,
        },
    )
    plan = "\n".join(r[0] for r in cursor.fetchall())
    assert "idx_chunk_search_vector" in plan, plan


def test_retrieval_ordering_is_deterministic(cursor):
    # BM25 ties reorder on last-bit float noise unless scores are rounded before
    # sorting; this is the regression test for that fix.
    from rag_v1.retrieval import lexical_search

    cursor.execute("SELECT snapshot_id FROM corpus_snapshot WHERE chunk_set_id=%s LIMIT 1", (CONTROL,))
    row = cursor.fetchone()
    if not row:
        pytest.skip("no snapshot for the control chunk set")
    question = "Which HTTP status code does the Claude API return with the request_too_large error type?"
    first = [h.chunk_id for h in lexical_search(question, row[0], 25)]
    second = [h.chunk_id for h in lexical_search(question, row[0], 25)]
    assert first == second
