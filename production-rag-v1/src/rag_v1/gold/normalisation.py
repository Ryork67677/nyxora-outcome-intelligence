"""Text normalisation for evidence comparison — and only for comparison.

A claim is checked by looking for its literal strings inside the anchored evidence. That
works until the source is Markdown: ``GOLD-B002-02``'s row writes the URL scheme as
``https\\://``, escaping the colon so the renderer does not turn it into a link, while
the natural claim writes ``https://``. Those are the same fact, and failing the check on
a backslash the renderer would drop is a defect in the checker, not in the evidence.

The rule is deliberately narrow: **undo Markdown backslash escapes, and nothing else.**
A backslash followed by one of the ASCII punctuation characters CommonMark permits to be
escaped is replaced by that character. No other character is added, removed or folded —
no case folding, no whitespace collapsing, no quote or dash substitution — because each
of those would let a claim match evidence that does not actually say it.

This never touches stored text. Evidence is stored raw, hashed raw, and displayed raw;
normalisation exists only inside a comparison, so the exact source form survives for
audit and the hash keeps meaning what it meant.
"""

from __future__ import annotations

import re

#: The ASCII punctuation CommonMark allows a backslash to escape. Anything else after a
#: backslash is left alone, because in Markdown it is not an escape either.
ESCAPABLE = r"!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~"
_MARKDOWN_ESCAPE = re.compile(r"\\([" + ESCAPABLE + r"])")


def unescape_markdown(text: str) -> str:
    """Drop Markdown backslash escapes. ``https\\://`` becomes ``https://``."""
    return _MARKDOWN_ESCAPE.sub(r"\1", text)


def normalise_for_comparison(text: str) -> str:
    """The only transformation permitted before comparing a claim to its evidence."""
    return unescape_markdown(text)


def contains_claim_string(evidence: str, claim_string: str) -> bool:
    """Is ``claim_string`` present in ``evidence``, ignoring Markdown escaping?

    Case-insensitive, matching the validator's existing behaviour, and normalising both
    sides so a claim may be written in either form.
    """
    return (normalise_for_comparison(claim_string).lower()
            in normalise_for_comparison(evidence).lower())


__all__ = [
    "ESCAPABLE",
    "contains_claim_string",
    "normalise_for_comparison",
    "unescape_markdown",
]
