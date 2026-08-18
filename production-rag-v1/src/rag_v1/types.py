from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ChunkType = Literal["prose", "code", "table", "table_row"]
Category = Literal["exact_lookup", "version_conflict", "multi_hop", "ambiguous", "missing_info", "normal"]


class ParsedSection(BaseModel):
    path: list[str]
    char_start: int
    char_end: int


class ParsedDocument(BaseModel):
    normalized_text: str
    sections: list[ParsedSection]
    parser_name: str
    parser_version: str


class ChunkRecord(BaseModel):
    chunk_id: str
    version_id: str
    ordinal: int
    section_path: list[str]
    chunk_type: ChunkType
    char_start: int
    char_end: int
    text: str
    content_hash: str
    metadata: dict = Field(default_factory=dict)
    # Set only where a chunker needs the indexed/embedded representation to differ
    # from the canonical body (EXP-010 carryover at forced splits). Left None by
    # every earlier chunker, so their stored rows are unchanged.
    context_header: str | None = None
    search_text: str | None = None


class SearchHit(BaseModel):
    chunk_id: str
    version_id: str
    section_path: list[str]
    char_start: int
    char_end: int
    text: str
    score: float
    rank: int
    retriever: str
    metadata: dict = Field(default_factory=dict)


class EvidenceRef(BaseModel):
    version_id: str
    section_path: list[str]
    char_start: int
    char_end: int

    @model_validator(mode="after")
    def valid_span(self):
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self


class ExpectedClaim(BaseModel):
    text: str
    match_type: Literal["contains", "exact", "regex", "human"] = "human"
    alternatives: list[str] = Field(default_factory=list)
    critical: bool = True


class EvalCase(BaseModel):
    case_id: str
    category: Category
    question: str
    expected_claims: list[ExpectedClaim] = Field(default_factory=list)
    expected_evidence: list[EvidenceRef] = Field(default_factory=list)
    expected_abstain: bool = False
    notes: str | None = None


class RetrievalCaseResult(BaseModel):
    case_id: str
    category: Category
    k: int
    expected_evidence_count: int
    evidence_found_count: int
    recall: float
    found: list[EvidenceRef] = Field(default_factory=list)
    missed: list[EvidenceRef] = Field(default_factory=list)
    hits: list[SearchHit] = Field(default_factory=list)
