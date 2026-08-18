"""EXP-010 tests: the B->D comparison is only an isolation of encoder alignment
if the chunk set really is aligned and nothing else moved.

Each test pins one invariant the conclusion depends on.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CONTROL_SET = "cs_v1_control"
ALIGNED_SET = "cs_v4_encoder_aligned"
CONTROL_SNAP = "snap_689e336380a054d8039dc35b2c09cd0a"
ALIGNED_SNAP = "snap_1ad94e790cec69f85f58fb0b916a4b6b"
TRANSFORMER_MODEL = "emb_e7d4183fd6eb878ae2fdf080efb6861e"
MODEL_FINGERPRINT = "bd95feaeacf98559"
WINDOW = 512
GATES = Path("experiments/EXP-010/ingestion-gates.json")
RESULTS = Path("experiments/EXP-010/results.json")


@pytest.fixture(scope="module")
def cursor():
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.db import connect

    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (ALIGNED_SET,))
            if cur.fetchone()[0] == 0:
                pytest.skip("encoder-aligned chunk set not built")
            yield cur
    except psycopg.OperationalError:
        pytest.skip("database unavailable")


@pytest.fixture(scope="module")
def tokenizer():
    pytest.importorskip("tokenizers")
    from rag_v1.chunkers.encoder_aligned import encoder_tokenizer

    return encoder_tokenizer()


@pytest.fixture(scope="module")
def gates():
    if not GATES.exists():
        pytest.skip("ingestion gates not run")
    return json.loads(GATES.read_text())


# -- 1. tokenizer-based size enforcement -----------------------------------------

def test_chunk_limits_are_measured_in_encoder_tokens_not_characters():
    """The budget must come from the model and its tokenizer, not from a guess."""
    pytest.importorskip("tokenizers")
    from rag_v1.chunkers.encoder_aligned import encoder_budget

    budget = encoder_budget()
    assert budget["max_position_embeddings"] == WINDOW
    # Measured empirically ([CLS] ... [SEP]), never assumed.
    assert budget["special_token_overhead_measured"] == 2
    assert budget["usable_payload_tokens"] == WINDOW - 2
    assert budget["target_payload_tokens"] < budget["usable_payload_tokens"]
    assert budget["hard_payload_tokens"] < budget["usable_payload_tokens"]


def test_every_aligned_chunk_is_within_the_hard_payload_cap(cursor, tokenizer):
    from rag_v1.chunkers.encoder_aligned import HARD_PAYLOAD_TOKENS

    cursor.execute(
        "SELECT chunk_id, coalesce(search_text, text) FROM chunk WHERE chunk_set_id=%s",
        (ALIGNED_SET,),
    )
    rows = cursor.fetchall()
    # The cap is on the *payload*, so special tokens must be excluded from the
    # measurement. encode_batch adds them by default, and comparing that against a
    # payload cap reports a violation that does not exist.
    encodings = tokenizer.encode_batch([r[1] for r in rows], add_special_tokens=False)
    over = [(rows[i][0], len(e.ids)) for i, e in enumerate(encodings)
            if len(e.ids) > HARD_PAYLOAD_TOKENS]
    assert not over, f"{len(over)} chunks exceed the hard payload cap, e.g. {over[:3]}"


# -- 2. zero truncation through the real encoding path ---------------------------

def test_no_aligned_chunk_truncates_in_the_actual_encoder(cursor):
    """Measured through the encoder's own tokenizer, not from stored metadata."""
    pytest.importorskip("onnxruntime")
    from rag_v1.embedders_transformer import TransformerEncoder

    encoder = TransformerEncoder(max_seq=WINDOW).load()
    cursor.execute(
        "SELECT coalesce(search_text, text) FROM chunk WHERE chunk_set_id=%s", (ALIGNED_SET,)
    )
    texts = [r[0] for r in cursor.fetchall()]
    encodings = encoder._tokenizer.encode_batch(texts)
    # With fixed-width padding a full attention mask means the sequence filled the
    # window, which is exactly the truncation condition.
    filled = sum(1 for e in encodings if sum(e.attention_mask) >= WINDOW)
    assert filled == 0, f"{filled} chunks fill or exceed the {WINDOW}-token window"


def test_control_set_still_truncates_which_is_why_the_experiment_exists(gates):
    """Guards against the gate silently passing because it measures nothing."""
    control = gates["distribution"]["control"]
    aligned = gates["distribution"]["encoder_aligned"]
    assert control["chunks_over_512"] > 0
    assert aligned["chunks_over_512"] == 0
    assert aligned["corpus_token_coverage"] == 1.0
    assert control["corpus_token_coverage"] < 1.0


# -- 3/4. determinism -------------------------------------------------------------

def test_chunk_boundaries_and_ids_are_deterministic():
    """Re-chunking one document must reproduce identical spans, ids and hashes."""
    pytest.importorskip("tokenizers")
    psycopg = pytest.importorskip("psycopg")
    from rag_v1.chunkers.encoder_aligned import chunk
    from rag_v1.db import connect
    from rag_v1.parsing import _sections_from_markdown
    from rag_v1.types import ParsedDocument

    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT v.version_id, v.normalized_text, v.parser_name, v.parser_version
                   FROM document_version v
                   JOIN corpus_snapshot_version sv ON sv.version_id=v.version_id
                   WHERE sv.snapshot_id=%s ORDER BY v.version_id LIMIT 1""",
                (CONTROL_SNAP,),
            )
            row = cur.fetchone()
    except psycopg.OperationalError:
        pytest.skip("database unavailable")
    if not row:
        pytest.skip("no versions")

    version_id, text, parser_name, parser_version = row
    doc = ParsedDocument(normalized_text=text, sections=_sections_from_markdown(text),
                         parser_name=parser_name, parser_version=parser_version)
    first = chunk(doc, version_id)
    second = chunk(doc, version_id)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert [(c.char_start, c.char_end) for c in first] == [(c.char_start, c.char_end) for c in second]
    assert [c.content_hash for c in first] == [c.content_hash for c in second]


# -- 5. evidence preservation -----------------------------------------------------

def test_all_expected_evidence_spans_survive_in_both_chunk_sets(gates):
    for name in ("control", "encoder_aligned"):
        gate = gates["evidence_gate"][name]
        assert gate["spans_total"] == 22
        assert gate["spans_mapped"] == 22, f"{name} lost evidence spans: {gate['missing']}"
        assert gate["passed"]


def test_evidence_is_anchored_on_source_spans_not_chunk_ids(gates):
    for span in gates["evidence_gate"]["encoder_aligned"]["spans"]:
        assert "section_path" in span and "span" in span
        assert isinstance(span["span"], list) and len(span["span"]) == 2


# -- 6. lineage -------------------------------------------------------------------

def test_section_lineage_and_version_survive_splitting(cursor):
    cursor.execute(
        """
        SELECT count(*) FROM chunk
        WHERE chunk_set_id=%s AND (section_path IS NULL OR version_id IS NULL
              OR char_end <= char_start)
        """,
        (ALIGNED_SET,),
    )
    assert cursor.fetchone()[0] == 0

    # Every split piece names the control chunk it came from.
    cursor.execute(
        """
        SELECT count(*) FROM chunk
        WHERE chunk_set_id=%s AND metadata->>'encoder_aligned_split' = 'true'
          AND metadata->>'control_chunk_id' IS NULL
        """,
        (ALIGNED_SET,),
    )
    assert cursor.fetchone()[0] == 0


def test_split_pieces_stay_inside_their_parent_control_chunk(cursor):
    """A piece may never claim source text its parent did not contain."""
    cursor.execute(
        """
        SELECT count(*)
        FROM chunk a
        JOIN chunk p ON p.chunk_id = a.metadata->>'control_chunk_id'
                    AND p.chunk_set_id = %s
        WHERE a.chunk_set_id = %s
          AND (a.char_start < p.char_start OR a.char_end > p.char_end
               OR a.version_id <> p.version_id)
        """,
        (CONTROL_SET, ALIGNED_SET),
    )
    assert cursor.fetchone()[0] == 0


# -- 7/8. table and code integrity ------------------------------------------------

def test_table_row_groups_carry_a_header_and_stay_within_budget(cursor, tokenizer):
    cursor.execute(
        """
        SELECT chunk_id, context_header, coalesce(search_text, text)
        FROM chunk
        WHERE chunk_set_id=%s AND metadata->>'table_header_carried' = 'true'
        """,
        (ALIGNED_SET,),
    )
    rows = cursor.fetchall()
    if not rows:
        pytest.skip("no carried table headers in this build")
    for chunk_id, header, encoded in rows:
        assert header, f"{chunk_id} claims a carried header but stores none"
        assert encoded.startswith(header), f"{chunk_id} header is not the prefix of its search text"
    lengths = [len(e.ids) for e in tokenizer.encode_batch([r[2] for r in rows])]
    assert max(lengths) <= WINDOW


def test_carried_headers_are_compact_enough_to_leave_room_for_content(cursor, tokenizer):
    """A header that dwarfs its rows is a defect, not context."""
    from rag_v1.chunkers.encoder_aligned import MAX_CARRYOVER_TOKENS

    cursor.execute(
        "SELECT context_header FROM chunk WHERE chunk_set_id=%s AND context_header IS NOT NULL",
        (ALIGNED_SET,),
    )
    headers = [r[0] for r in cursor.fetchall()]
    if not headers:
        pytest.skip("no carryover in this build")
    lengths = [len(e.ids) for e in tokenizer.encode_batch(headers, add_special_tokens=False)]
    assert max(lengths) <= MAX_CARRYOVER_TOKENS


def test_code_pieces_are_split_on_line_boundaries(cursor):
    """Code is cut between lines, never through one."""
    cursor.execute(
        """
        SELECT c.text, v.normalized_text, c.char_start, c.char_end
        FROM chunk c JOIN document_version v ON v.version_id=c.version_id
        WHERE c.chunk_set_id=%s AND c.metadata->>'block_kind'='code'
          AND c.metadata->>'encoder_aligned_split'='true'
          AND c.metadata->>'part_index' IS NOT NULL
        LIMIT 200
        """,
        (ALIGNED_SET,),
    )
    rows = cursor.fetchall()
    if not rows:
        pytest.skip("no split code blocks")
    for _text, full, start, end in rows:
        before = full[start - 1:start]
        after = full[end:end + 1]
        assert before in ("", "\n", " ", "\t") or start == 0
        assert after in ("", "\n", " ", "\t") or end == len(full)


# -- 9. cross-representation fusion ----------------------------------------------

def test_region_fusion_does_not_double_reward_one_evidence_region():
    from rag_v1.retrieval import rrf_fuse_regions
    from rag_v1.types import SearchHit

    def hit(cid, start, end, rank, retriever):
        return SearchHit(chunk_id=cid, version_id="v1", section_path=["S"], char_start=start,
                         char_end=end, text="t", score=1.0, rank=rank, retriever=retriever)

    # One passage cut two ways: three overlapping dense pieces vs one lexical chunk.
    dense = [hit("a1", 0, 100, 1, "dense"), hit("a2", 90, 200, 2, "dense"),
             hit("a3", 190, 300, 3, "dense")]
    lexical = [hit("c1", 0, 300, 1, "lexical")]
    fused = rrf_fuse_regions([lexical, dense], rrf_k=60, top_k=10)

    assert len(fused) == 1, "one source region must collapse to one fused result"
    contributions = fused[0].metadata["rrf_contributions"]
    assert set(contributions) == {"lexical", "dense"}
    # The dense retriever contributes once, at its best rank — not three times.
    assert contributions["dense"] == pytest.approx(1.0 / 61)
    assert fused[0].metadata["merged_members"] == 4


def test_region_fusion_keeps_distinct_regions_apart():
    from rag_v1.retrieval import rrf_fuse_regions
    from rag_v1.types import SearchHit

    def hit(cid, version, section, start, end, rank, retriever):
        return SearchHit(chunk_id=cid, version_id=version, section_path=section,
                         char_start=start, char_end=end, text="t", score=1.0, rank=rank,
                         retriever=retriever)

    hits = [
        hit("a", "v1", ["S"], 0, 50, 1, "dense"),
        hit("b", "v1", ["S"], 100, 150, 2, "dense"),   # same section, no overlap
        hit("c", "v1", ["T"], 0, 50, 3, "dense"),      # different section
        hit("d", "v2", ["S"], 0, 50, 4, "dense"),      # different version
    ]
    fused = rrf_fuse_regions([hits], rrf_k=60, top_k=10)
    assert len(fused) == 4


def test_region_fusion_reduces_to_plain_rrf_within_one_chunk_set():
    """Same-set lists must fuse identically, or cell C stops being a reproduction."""
    from rag_v1.retrieval import rrf_fuse, rrf_fuse_regions
    from rag_v1.types import SearchHit

    def hit(cid, start, rank, retriever):
        return SearchHit(chunk_id=cid, version_id="v1", section_path=["S"], char_start=start,
                         char_end=start + 50, text="t", score=1.0, rank=rank, retriever=retriever)

    # Non-overlapping chunks, as a real chunk set produces.
    lexical = [hit("c1", 0, 1, "lexical"), hit("c2", 100, 2, "lexical")]
    dense = [hit("c2", 100, 1, "dense"), hit("c1", 0, 2, "dense")]
    plain = rrf_fuse([lexical, dense], rrf_k=60, top_k=10)
    regions = rrf_fuse_regions([lexical, dense], rrf_k=60, top_k=10)
    assert [h.chunk_id for h in plain] == [h.chunk_id for h in regions]
    assert [round(h.score, 12) for h in plain] == [round(h.score, 12) for h in regions]


# -- 10. canonical text ------------------------------------------------------------

def test_canonical_chunk_text_is_the_untouched_source_span(cursor):
    """chunk.text must equal the source slice; carryover lives only in search_text."""
    cursor.execute(
        """
        SELECT c.chunk_id, c.text, substring(v.normalized_text from c.char_start+1
               for c.char_end-c.char_start)
        FROM chunk c JOIN document_version v ON v.version_id=c.version_id
        WHERE c.chunk_set_id=%s
        LIMIT 3000
        """,
        (ALIGNED_SET,),
    )
    for chunk_id, text, source in cursor.fetchall():
        assert text == source, f"{chunk_id} mutated its canonical source text"


def test_control_chunk_set_was_not_modified(cursor):
    """EXP-010 must leave every earlier chunk set byte-identical."""
    cursor.execute("SELECT count(*) FROM chunk WHERE chunk_set_id=%s", (CONTROL_SET,))
    assert cursor.fetchone()[0] == 14209
    cursor.execute(
        "SELECT count(*) FROM chunk WHERE chunk_set_id=%s AND search_text IS NOT NULL",
        (CONTROL_SET,),
    )
    assert cursor.fetchone()[0] == 0, "control chunks gained a search_text representation"


# -- 11/12. encoder identity and cache isolation ----------------------------------

def test_encoder_fingerprint_is_unchanged_from_exp009():
    pytest.importorskip("onnxruntime")
    from rag_v1.embedders_transformer import MODEL_CARD, TransformerEncoder

    encoder = TransformerEncoder(max_seq=WINDOW)
    assert encoder.model_version == MODEL_FINGERPRINT
    assert MODEL_CARD["model_identifier"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert MODEL_CARD["dimension"] == 384
    assert MODEL_CARD["query_prefix"] is None and MODEL_CARD["document_prefix"] is None


def test_embedding_cache_is_isolated_by_chunk_set_not_conflated(cursor):
    """Both chunk sets share one encoder; vectors must stay separated by chunk set."""
    cursor.execute(
        """
        SELECT c.chunk_set_id, count(*)
        FROM chunk_embedding ce JOIN chunk c ON c.chunk_id=ce.chunk_id
        WHERE ce.model_id=%s GROUP BY 1
        """,
        (TRANSFORMER_MODEL,),
    )
    counts = dict(cursor.fetchall())
    assert counts.get(CONTROL_SET) == 14209
    assert counts.get(ALIGNED_SET, 0) > 0
    # A chunk is embedded under exactly one row per model.
    cursor.execute(
        """
        SELECT count(*) FROM (
          SELECT chunk_id FROM chunk_embedding WHERE model_id=%s
          GROUP BY chunk_id HAVING count(*) > 1
        ) dup
        """,
        (TRANSFORMER_MODEL,),
    )
    assert cursor.fetchone()[0] == 0


def test_stored_vectors_carry_the_expected_model_fingerprint(cursor):
    cursor.execute(
        "SELECT DISTINCT model_fingerprint FROM chunk_embedding WHERE model_id=%s",
        (TRANSFORMER_MODEL,),
    )
    prints = {r[0] for r in cursor.fetchall()}
    assert prints == {MODEL_FINGERPRINT}, f"unexpected fingerprints: {prints}"


# -- 13. query leakage -------------------------------------------------------------

def test_the_chunker_never_sees_the_evaluation_questions():
    """Chunk boundaries must not depend on the golden set in any way."""
    from rag_v1.chunkers import encoder_aligned

    source = Path(encoder_aligned.__file__).read_text()
    for banned in ("golden", "evals/", "load_cases", "expected_evidence", "case_id"):
        assert banned not in source, f"chunker references the evaluation set via {banned!r}"


def test_chunker_config_contains_no_corpus_or_query_fitted_value():
    from rag_v1.chunkers.encoder_aligned import SPEC

    # Every limit must be traceable to the encoder, not to this corpus or these
    # questions.
    assert SPEC.config["limits_measured_in"].startswith("encoder WordPiece tokens")
    assert SPEC.config["encoder_window_tokens"] == WINDOW
    assert SPEC.config["special_token_overhead"] == 2


# -- 14. baseline reproduction -----------------------------------------------------

def test_reproduction_gates_pass():
    if not RESULTS.exists():
        pytest.skip("EXP-010 results not built")
    gates = json.loads(RESULTS.read_text())["reproduction_gate"]
    failed = {k: v["checks"] for k, v in gates.items() if not v["reproduced"]}
    assert not failed, f"reproduction gates failed: {failed}"


def test_frozen_baseline_numbers_are_unchanged():
    if not RESULTS.exists():
        pytest.skip("EXP-010 results not built")
    cfg = json.loads(RESULTS.read_text())["configurations"]["A_bm25_control"]
    assert cfg["macro_span_recall"] == 0.475
    assert cfg["cases_fully_recalled"] == 9
    assert cfg["spans_found_at_10"] == 10


def test_retrieval_config_declares_no_forbidden_component():
    if not RESULTS.exists():
        pytest.skip("EXP-010 results not built")
    payload = json.loads(RESULTS.read_text())
    cfg = payload["retrieval_config"]
    assert cfg["reranker"] is None
    assert cfg["query_rewriting"] is False and cfg["query_expansion"] is False
    assert cfg["stemming"] is False and cfg["enrichment"] is None
    assert cfg["ann_index"] is False
    assert payload["candidate_pool"] == 50 and payload["rrf_k"] == 60 and payload["top_k"] == 10
    assert payload["encoder_window"] == WINDOW
