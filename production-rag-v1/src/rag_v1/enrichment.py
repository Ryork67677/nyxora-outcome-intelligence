"""Structural contextual enrichment of chunk search text (EXP-006).

What this is
------------
A chunk is indexed with a small header naming where it came from:

    Provider: anthropic
    Document: Message Batches
    Section: Batches > Create a Message Batch > Body Parameters
    <canonical chunk body>

Rules this deliberately follows:

* **Source-grounded only.** Provider, document title and section path all come
  from rows already in the database. Nothing is summarised, inferred or generated,
  so the header cannot invent content that is not in the corpus.
* **The canonical body is never touched.** The header lives in ``search_text``;
  ``chunk.text`` stays exactly what the source said, because that is what a
  citation quotes back to a user. Synthesised metadata must never become apparent
  source content.
* **Idempotent.** Enriching an already-enriched text returns it unchanged, so a
  repeated ingest cannot stack duplicate headers.
* **Deterministic.** Same inputs, same bytes. Field selection is hashed into the
  chunk set's identity so two enrichment variants can never be conflated.

Whether any of this actually helps retrieval is the question EXP-006 measures; it
is not assumed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rag_v1.ids import config_hash

HEADER_SENTINEL = "Provider:"
FIELD_ORDER = ("provider", "document", "section")


@dataclass(frozen=True)
class EnrichmentConfig:
    """Which source-native fields go into the header."""

    name: str = "structural_v1"
    fields: tuple[str, ...] = FIELD_ORDER
    separator: str = " > "

    @property
    def config_hash(self) -> str:
        return config_hash({"name": self.name, "fields": list(self.fields), "separator": self.separator})

    def as_dict(self) -> dict:
        return {"name": self.name, "fields": list(self.fields), "separator": self.separator}


#: The configuration used by EXP-006 B and D.
STRUCTURAL_V1 = EnrichmentConfig()

#: Exploratory field ablations (EXP-006 section 20). Selected on the development
#: set and labelled as such wherever they are reported.
VARIANTS: dict[str, EnrichmentConfig] = {
    "E1_section_only": EnrichmentConfig(name="E1_section_only", fields=("section",)),
    "E2_document_section": EnrichmentConfig(name="E2_document_section", fields=("document", "section")),
    "E3_provider_document_section": STRUCTURAL_V1,
}


def build_context_header(
    provider: str,
    document_title: str,
    section_path: list[str],
    config: EnrichmentConfig = STRUCTURAL_V1,
) -> str:
    """Render the structural header for one chunk.

    A field is omitted entirely when the source does not supply it, rather than
    emitted empty — an empty label would add a term with no information.
    """
    lines: list[str] = []
    for field_name in config.fields:
        if field_name == "provider" and provider:
            lines.append(f"Provider: {provider}")
        elif field_name == "document" and document_title:
            lines.append(f"Document: {document_title}")
        elif field_name == "section" and section_path:
            lines.append(f"Section: {config.separator.join(section_path)}")
    return "\n".join(lines)


def is_enriched(text: str) -> bool:
    return text.startswith(HEADER_SENTINEL) or text.lstrip().startswith(HEADER_SENTINEL)


def enrich(text: str, header: str) -> str:
    """Prepend the header to the searchable text, once.

    Returns ``text`` unchanged when there is no header, and refuses to stack a
    second header on already-enriched text.
    """
    if not header:
        return text
    if is_enriched(text):
        return text
    return f"{header}\n{text}"


@dataclass
class EnrichmentStats:
    """Counts used by the report to describe what enrichment actually added."""

    chunks: int = 0
    headers_built: int = 0
    header_chars: int = 0
    distinct_headers: set[str] = field(default_factory=set)

    def observe(self, header: str) -> None:
        self.chunks += 1
        if header:
            self.headers_built += 1
            self.header_chars += len(header)
            self.distinct_headers.add(header)

    def as_dict(self) -> dict:
        return {
            "chunks": self.chunks,
            "headers_built": self.headers_built,
            "mean_header_chars": round(self.header_chars / self.headers_built, 1)
            if self.headers_built
            else 0,
            "distinct_headers": len(self.distinct_headers),
        }
