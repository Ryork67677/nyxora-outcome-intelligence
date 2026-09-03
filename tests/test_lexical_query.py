from rag_v1.retrieval import query_terms


def test_identifier_survives_as_one_term():
    # The whole point of the 'simple' config is that identifiers are not mangled.
    terms = query_terms("Which HTTP code does request_too_large return?")
    assert "request_too_large" in terms
    assert "request" not in terms


def test_dotted_and_hyphenated_identifiers_are_kept_whole():
    terms = query_terms("Does anthropic-beta accept gpt-5.6-luna?")
    assert "anthropic-beta" in terms
    assert "gpt-5.6-luna" in terms


def test_terms_are_deduplicated_in_first_occurrence_order():
    assert query_terms("token limit token budget") == ["token", "limit", "budget"]


def test_single_characters_are_dropped():
    # A single character carries no retrieval signal and matches most of the corpus.
    assert query_terms("a b max_turns") == ["max_turns"]


def test_empty_query_yields_no_terms():
    # lexical_search relies on this to avoid issuing an unbounded scan.
    assert query_terms("?? -- !") == []
