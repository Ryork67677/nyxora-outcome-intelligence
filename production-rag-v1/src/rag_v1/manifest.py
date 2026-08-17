from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SourceEntry(BaseModel):
    provider: str
    title: str
    canonical_url: str
    local_path: Path
    authority_class: str = "official_docs"
    authority_rank: int = 100
    captured_at: str | None = None
    metadata: dict = Field(default_factory=dict)


class Manifest(BaseModel):
    sources: list[SourceEntry]


def load_manifest(path: Path) -> Manifest:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest = Manifest.model_validate(data)
    base = path.parent
    for item in manifest.sources:
        if not item.local_path.is_absolute():
            item.local_path = (base / item.local_path).resolve()
    return manifest
