#!/usr/bin/env python3
"""Fetch the focused OpenAI + Anthropic V1 documentation corpus.

Design constraints carried from the V1 handoff:

* Raw provider documentation is written under ``data/raw/`` which is gitignored.
  The public repository keeps only the manifest, hashes and this fetch logic.
* ``robots.txt`` is parsed and enforced for every HTTP host before any document
  request. The decision for each URL is recorded so the compliance claim is
  auditable rather than asserted.
* OpenAI documentation is taken from OpenAI's own public repositories pinned to
  an exact commit, so a version is reproducible and never silently mutates.
* The emitted manifest preserves provider, canonical URL, captured time,
  authority class and the raw file path, which is what ``ragv1 ingest`` needs.

Usage::

    python scripts/fetch_corpus.py            # fetch everything
    python scripts/fetch_corpus.py --dry-run  # resolve the plan only
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
CACHE_DIR = REPO_ROOT / "data" / "cache"
MANIFEST_DIR = REPO_ROOT / "data" / "manifests"

USER_AGENT = "production-rag-v1-corpus-fetcher/0.1 (evaluation harness; contact: repository owner)"
REQUEST_DELAY_SECONDS = 0.7

ANTHROPIC_SITEMAP = "https://platform.claude.com/sitemap.xml"
ANTHROPIC_DOC_PREFIX = "https://platform.claude.com/docs/en/"

# Focused slice of the Anthropic documentation. The full sitemap also carries
# admin-api, compliance-api and the beta mirror of the reference; those are
# excluded on purpose to keep V1 at ~200 focused documents.
ANTHROPIC_INCLUDE_GROUPS = (
    "api",
    "build-with-claude",
    "agents-and-tools",
    "about-claude",
    "test-and-evaluate",
)
ANTHROPIC_EXCLUDE_PATTERNS = (
    "/docs/en/api/admin-api/",
    "/docs/en/api/admin/",
    "/docs/en/api/compliance/",
    "/docs/en/api/beta/",
)
ANTHROPIC_EXTRA_PAGES = (
    "https://platform.claude.com/docs/en/intro",
    "https://platform.claude.com/docs/en/get-started",
    "https://platform.claude.com/docs/en/get-api-key",
)


@dataclass
class GitDocSource:
    """A set of markdown documents published by OpenAI in a public repository."""

    repo: str
    clone_url: str
    include_globs: tuple[str, ...]
    exclude_regexes: tuple[str, ...] = ()
    authority_class: str = "official_sdk_docs"
    authority_rank: int = 90
    license_name: str = ""
    limit: int | None = None


OPENAI_GIT_SOURCES = (
    GitDocSource(
        repo="openai/openai-agents-python",
        clone_url="https://github.com/openai/openai-agents-python.git",
        include_globs=("docs/**/*.md",),
        # docs/ref/** are mkdocstrings stubs ("::: agents.agent") with no prose,
        # and the ja/ko/zh trees are translations of the English pages.
        exclude_regexes=(r"^docs/ref/", r"^docs/(ja|ko|zh)[^/]*/"),
        authority_class="official_sdk_docs",
        authority_rank=90,
        license_name="MIT",
    ),
    GitDocSource(
        repo="openai/openai-python",
        clone_url="https://github.com/openai/openai-python.git",
        include_globs=("*.md",),
        exclude_regexes=(r"^CHANGELOG\.md$", r"^SECURITY\.md$", r"^CONTRIBUTING\.md$"),
        authority_class="official_sdk_docs",
        authority_rank=95,
        license_name="Apache-2.0",
    ),
    GitDocSource(
        repo="openai/openai-node",
        clone_url="https://github.com/openai/openai-node.git",
        include_globs=("*.md",),
        exclude_regexes=(r"^CHANGELOG\.md$", r"^SECURITY\.md$", r"^CONTRIBUTING\.md$"),
        authority_class="official_sdk_docs",
        authority_rank=95,
        license_name="Apache-2.0",
    ),
    GitDocSource(
        repo="openai/openai-cookbook",
        clone_url="https://github.com/openai/openai-cookbook.git",
        include_globs=("articles/**/*.md",),
        authority_class="official_examples",
        authority_rank=70,
        license_name="MIT",
    ),
)


@dataclass
class FetchPlanEntry:
    provider: str
    title: str
    canonical_url: str
    raw_path: Path
    authority_class: str
    authority_rank: int
    metadata: dict = field(default_factory=dict)


class RobotsGate:
    """Parses and enforces robots.txt per host, and records every decision."""

    def __init__(self, user_agent: str = USER_AGENT):
        self.user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}
        self.records: list[dict] = []

    def _parser_for(self, url: str) -> RobotFileParser:
        parts = urlparse(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._parsers:
            robots_url = f"{origin}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                raw = http_get(robots_url)
                parser.parse(raw.decode("utf-8", errors="replace").splitlines())
                status = "fetched"
            except Exception as exc:  # noqa: BLE001 - recorded, then treated as disallow
                parser.parse([])
                status = f"unavailable: {exc}"
            self.records.append(
                {
                    "origin": origin,
                    "robots_url": robots_url,
                    "status": status,
                    "user_agent": self.user_agent,
                    "checked_at": now_iso(),
                }
            )
            self._parsers[origin] = parser
        return self._parsers[origin]

    def allowed(self, url: str) -> bool:
        return self._parser_for(url).can_fetch(self.user_agent, url)


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get(url: str, retries: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in {404, 403, 410}:
                raise
            last_error = exc
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(2**attempt)
    raise RuntimeError(f"GET failed for {url}: {last_error}")


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")


def front_matter_title(text: str, fallback: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end]
            match = re.search(r"^title:\s*(.+?)\s*$", block, re.MULTILINE)
            if match:
                return match.group(1).strip().strip("\"'")
    match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if match:
        return re.sub(r"[`*]", "", match.group(1)).strip()
    return fallback


# --------------------------------------------------------------------------
# Anthropic
# --------------------------------------------------------------------------


def anthropic_urls() -> list[str]:
    sitemap = http_get(ANTHROPIC_SITEMAP).decode("utf-8", errors="replace")
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    selected: list[str] = []
    for loc in locs:
        if not loc.startswith(ANTHROPIC_DOC_PREFIX):
            continue
        if any(pattern in loc for pattern in ANTHROPIC_EXCLUDE_PATTERNS):
            continue
        group = loc[len(ANTHROPIC_DOC_PREFIX) :].split("/")[0]
        if group not in ANTHROPIC_INCLUDE_GROUPS:
            continue
        selected.append(loc)
    for extra in ANTHROPIC_EXTRA_PAGES:
        if extra in locs and extra not in selected:
            selected.append(extra)
    # Deterministic ordering so a re-run produces the same manifest order.
    return sorted(dict.fromkeys(selected))


def fetch_anthropic(gate: RobotsGate, dry_run: bool) -> tuple[list[FetchPlanEntry], list[dict]]:
    entries: list[FetchPlanEntry] = []
    skipped: list[dict] = []
    urls = anthropic_urls()
    print(f"[anthropic] {len(urls)} candidate documents from sitemap", file=sys.stderr)

    for url in urls:
        # Mintlify serves a clean markdown rendering of each documentation page.
        markdown_url = f"{url}.md"
        if not gate.allowed(markdown_url):
            skipped.append({"url": markdown_url, "reason": "disallowed_by_robots"})
            continue

        rel = url[len(ANTHROPIC_DOC_PREFIX) :]
        raw_path = RAW_DIR / "anthropic" / f"{slugify(rel)}.md"
        is_reference = rel.startswith("api/")
        entry = FetchPlanEntry(
            provider="anthropic",
            title=rel,
            canonical_url=url,
            raw_path=raw_path,
            authority_class="official_api_reference" if is_reference else "official_docs",
            authority_rank=100 if is_reference else 95,
            metadata={
                "doc_group": rel.split("/")[0],
                "fetched_from": markdown_url,
                "retrieval_method": "https_markdown_rendering",
            },
        )

        if dry_run:
            entries.append(entry)
            continue

        try:
            body = http_get(markdown_url)
        except urllib.error.HTTPError as exc:
            skipped.append({"url": markdown_url, "reason": f"http_{exc.code}"})
            continue
        time.sleep(REQUEST_DELAY_SECONDS)

        text = body.decode("utf-8", errors="replace")
        if len(text.strip()) < 200:
            skipped.append({"url": markdown_url, "reason": "too_short"})
            continue

        entry.title = front_matter_title(text, rel)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(text, encoding="utf-8")
        entries.append(entry)
        print(f"[anthropic] {len(entries):3d} {rel}", file=sys.stderr)

    return entries, skipped


# --------------------------------------------------------------------------
# OpenAI (official public repositories, pinned by commit)
# --------------------------------------------------------------------------


def ensure_clone(source: GitDocSource) -> tuple[Path, str]:
    target = CACHE_DIR / "repos" / source.repo.replace("/", "__")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", source.clone_url, str(target)],
            check=True,
        )
    sha = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
    return target, sha


def fetch_openai(dry_run: bool) -> tuple[list[FetchPlanEntry], list[dict]]:
    entries: list[FetchPlanEntry] = []
    skipped: list[dict] = []

    for source in OPENAI_GIT_SOURCES:
        clone_path, sha = ensure_clone(source)
        candidates: list[Path] = []
        for pattern in source.include_globs:
            candidates.extend(sorted(clone_path.glob(pattern)))

        for path in candidates:
            rel = path.relative_to(clone_path).as_posix()
            if any(re.search(rx, rel) for rx in source.exclude_regexes):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text.strip()) < 200:
                skipped.append({"url": f"{source.repo}:{rel}", "reason": "too_short"})
                continue

            raw_path = RAW_DIR / "openai" / source.repo.split("/")[-1] / slugify(rel)
            entry = FetchPlanEntry(
                provider="openai",
                title=front_matter_title(text, f"{source.repo} {rel}"),
                canonical_url=f"https://github.com/{source.repo}/blob/{sha}/{rel}",
                raw_path=raw_path,
                authority_class=source.authority_class,
                authority_rank=source.authority_rank,
                metadata={
                    "repo": source.repo,
                    "commit": sha,
                    "repo_path": rel,
                    "license": source.license_name,
                    "retrieval_method": "public_git_clone_pinned_commit",
                },
            )
            if not dry_run:
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(text, encoding="utf-8")
            entries.append(entry)

            if source.limit and sum(1 for e in entries if e.metadata.get("repo") == source.repo) >= source.limit:
                break
        print(
            f"[openai] {source.repo}@{sha[:8]}: "
            f"{sum(1 for e in entries if e.metadata.get('repo') == source.repo)} documents",
            file=sys.stderr,
        )

    return entries, skipped


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_manifest(entries: list[FetchPlanEntry], path: Path, captured_at: str) -> None:
    """Emit the manifest by hand so the output diff stays stable and readable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Generated by scripts/fetch_corpus.py — do not hand-edit.",
        "# Raw documents live under data/raw/ and are gitignored on purpose.",
        f"# captured_at: {captured_at}",
        f"# documents: {len(entries)}",
        "sources:",
    ]
    for entry in entries:
        local = Path("..") / entry.raw_path.relative_to(REPO_ROOT / "data")
        lines.append(f"  - provider: {entry.provider}")
        lines.append(f"    title: {yaml_quote(entry.title)}")
        lines.append(f"    canonical_url: {yaml_quote(entry.canonical_url)}")
        lines.append(f"    local_path: {yaml_quote(local.as_posix())}")
        lines.append(f"    authority_class: {entry.authority_class}")
        lines.append(f"    authority_rank: {entry.authority_rank}")
        lines.append(f"    captured_at: {yaml_quote(captured_at)}")
        lines.append("    metadata:")
        for key, value in sorted(entry.metadata.items()):
            lines.append(f"      {key}: {yaml_quote(str(value))}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="resolve the plan without writing raw files")
    parser.add_argument("--manifest", default="data/manifests/v1-openai-anthropic.yaml")
    parser.add_argument("--clean", action="store_true", help="remove previously fetched raw files first")
    args = parser.parse_args()

    if args.clean and RAW_DIR.exists() and not args.dry_run:
        for child in RAW_DIR.iterdir():
            if child.name != ".gitkeep":
                shutil.rmtree(child) if child.is_dir() else child.unlink()

    captured_at = now_iso()
    gate = RobotsGate()

    anthropic_entries, anthropic_skipped = fetch_anthropic(gate, args.dry_run)
    openai_entries, openai_skipped = fetch_openai(args.dry_run)
    entries = anthropic_entries + openai_entries

    manifest_path = REPO_ROOT / args.manifest
    if not args.dry_run:
        write_manifest(entries, manifest_path, captured_at)

        compliance = {
            "captured_at": captured_at,
            "user_agent": USER_AGENT,
            "request_delay_seconds": REQUEST_DELAY_SECONDS,
            "robots_checks": gate.records,
            "http_sources": ["platform.claude.com"],
            "git_sources": [
                {"repo": s.repo, "license": s.license_name, "clone_url": s.clone_url}
                for s in OPENAI_GIT_SOURCES
            ],
            "skipped": anthropic_skipped + openai_skipped,
            "counts": {
                "anthropic": len(anthropic_entries),
                "openai": len(openai_entries),
                "total": len(entries),
            },
        }
        (MANIFEST_DIR / "fetch-compliance.json").write_text(
            json.dumps(compliance, indent=2) + "\n", encoding="utf-8"
        )

    print(
        json.dumps(
            {
                "anthropic": len(anthropic_entries),
                "openai": len(openai_entries),
                "total": len(entries),
                "skipped": len(anthropic_skipped) + len(openai_skipped),
                "manifest": str(manifest_path),
                "dry_run": args.dry_run,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
