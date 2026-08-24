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


#: Markdown link plumbing, in the three shapes CommonMark allows a link to be written.
#: The label is kept and everything else goes: a question is read by a person, and
#: ``[`ComputerTool`][agents.tool.ComputerTool]`` names a class while looking like a
#: syntax error. Order matters — inline first, then full reference, then collapsed and
#: shortcut, so a longer form is never half-consumed by a shorter pattern.
_INLINE_LINK = re.compile(r"\[(?P<label>[^\]]*)\]\((?:[^()]*|\([^()]*\))*\)")
_REFERENCE_LINK = re.compile(r"\[(?P<label>[^\]]*)\]\[(?P<ref>[^\]]*)\]")
_IMAGE_PREFIX = re.compile(r"!(?=\[)")
#: A link whose label is a code span, written across the label and the reference. The
#: backticks are the project's own convention for an identifier and are kept; only the
#: reference is plumbing.
_LINK_LIKE = re.compile(r"\]\s*[\[(]")


def strip_markdown_links(text: str) -> str:
    """Reduce every Markdown link in ``text`` to its visible label.

    ``[label](url)``, ``[label][ref]`` and ``[label][]`` all become ``label``; an image
    ``![alt](src)`` becomes ``alt``. A code-span label keeps its backticks, because in
    this project backticks mark an identifier and are not link syntax.

    This is for authoring a question or an answer. It must never be applied to stored
    evidence: evidence is anchored by offset and hashed as written, and rewriting it
    would break both.
    """
    out = _IMAGE_PREFIX.sub("", text)
    for _ in range(4):  # nested labels resolve from the inside out; four is generous
        replaced = _INLINE_LINK.sub(lambda m: m.group("label"), out)
        replaced = _REFERENCE_LINK.sub(lambda m: m.group("label"), replaced)
        if replaced == out:
            break
        out = replaced
    return out


def has_markdown_link(text: str) -> bool:
    """Would ``strip_markdown_links`` change this text? Cheap enough to assert with."""
    return bool(_LINK_LIKE.search(text)) and strip_markdown_links(text) != text


__all__ = [
    "ESCAPABLE",
    "contains_claim_string",
    "has_markdown_link",
    "normalise_for_comparison",
    "strip_markdown_links",
    "unescape_markdown",
]
