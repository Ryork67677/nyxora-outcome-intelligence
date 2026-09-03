"""Frozen EXP-016 exact-identifier matcher.

Defined in EXP-016-preregistration.md before any EXP-016 scores.
Do not retune after seeing scores.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag_v1.query_views import _TOKEN_RE, identifiers as qv_identifiers  # noqa: E402

_QUOTED_RE = re.compile(r"`([^`]+)`|\"([^\"]+)\"|'([^']+)'")
_CAMEL_RE = re.compile(r"^(?:[A-Z][a-z]+(?:[A-Z][a-zA-Z0-9]*)+|[a-z]+(?:[A-Z][a-zA-Z0-9]+)+)$")
_SNAKE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+$")
_DOTTED_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z0-9_.]+$")
_SCREAMING_RE = re.compile(r"^[A-Z0-9_]{3,}$")
_VERSION_RE = re.compile(r"^v?\d+(?:\.\d+)*[A-Za-z0-9._-]*$", re.IGNORECASE)
_HYPHEN_CODE_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+$")
_STRIP = "`.,:;?!()[]{}"


def _is_identifier_token(tok: str) -> bool:
    if not tok or not any(c.isalnum() for c in tok):
        return False
    if _CAMEL_RE.match(tok):
        return True
    if _SNAKE_RE.match(tok):
        return True
    if _DOTTED_RE.match(tok):
        return True
    if _SCREAMING_RE.match(tok):
        return True
    if any(c.isdigit() for c in tok) and _VERSION_RE.match(tok):
        return True
    if len(tok) >= 5 and _HYPHEN_CODE_RE.match(tok):
        return True
    return False


def extract_identifiers(text: str) -> set[str]:
    """Frozen identifier-token set for a query or passage."""
    out: set[str] = set()
    if not text:
        return out
    for match in _QUOTED_RE.finditer(text):
        inner = next(g for g in match.groups() if g is not None).strip()
        if inner and any(c.isalnum() for c in inner):
            out.add(inner)
            for part in _TOKEN_RE.findall(inner):
                stripped = part.strip(_STRIP)
                if _is_identifier_token(stripped):
                    out.add(stripped)
    out |= qv_identifiers(text)
    for token in _TOKEN_RE.findall(text):
        stripped = token.strip("`").strip(".,:;?!()[]{}")
        if _is_identifier_token(stripped):
            out.add(stripped)
    return out


def has_exact_identifier_overlap(query: str, candidate_text: str) -> bool:
    return bool(extract_identifiers(query) & extract_identifiers(candidate_text))


def overlapping_identifiers(query: str, candidate_text: str) -> list[str]:
    return sorted(extract_identifiers(query) & extract_identifiers(candidate_text))
