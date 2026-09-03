"""One shape for a generator defect, whichever batch recorded it.

Batches 004 and 005 wrote a defect as ``defect`` / ``seen_in`` / ``detail``. Batch 006
also records the fix it proposes and the batch that fix is preregistered for, because
that is what the next preregistration has to be written from. Three separate renderers
crashed on the newer shape, each in the same way, which is the argument for reading it
in one place instead of six.

Nothing is invented here: a field the record does not carry comes back ``None``, and a
renderer decides what to do about that.
"""

from __future__ import annotations

#: Old key → new key, for every field whose name changed between batches.
ALIASES = {
    "name": "defect",
    "from_case": "seen_in",
    "description": "detail",
}


def normalise(entry: dict) -> dict:
    """Read a defect record written in any batch's shape."""
    out = {
        "id": entry.get("id"),
        "defect": entry.get("defect") or entry.get("name") or entry.get("summary"),
        "seen_in": entry.get("seen_in") or entry.get("from_case"),
        "detail": entry.get("detail") or entry.get("description"),
        "proposed_fix": entry.get("proposed_fix") or entry.get("check"),
        "preregistered_for": entry.get("preregistered_for"),
    }
    return out


def normalise_all(entries: list[dict] | None) -> list[dict]:
    return [normalise(entry) for entry in (entries or [])]


def line(entry: dict) -> str:
    """One Markdown bullet for a defect, in whichever shape it was written."""
    defect = normalise(entry)
    label = f"{defect['id']}. " if defect["id"] else ""
    where = f" (seen in {defect['seen_in']})" if defect["seen_in"] else ""
    text = f"- **{label}{defect['defect']}**{where}. {defect['detail'] or ''}".rstrip()
    if defect["proposed_fix"]:
        target = (f", preregistered for {defect['preregistered_for']}"
                  if defect["preregistered_for"] else "")
        text += f"\n  - *Proposed fix{target}:* {defect['proposed_fix']}"
    return text


__all__ = ["ALIASES", "line", "normalise", "normalise_all"]
