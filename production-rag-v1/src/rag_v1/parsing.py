from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup

from rag_v1.types import ParsedDocument, ParsedSection

PARSER_VERSION = "v1.0"


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def _sections_from_markdown(text: str) -> list[ParsedSection]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [ParsedSection(path=["Document"], char_start=0, char_end=len(text))]

    sections: list[ParsedSection] = []
    heading_stack: list[tuple[int, str]] = []
    for idx, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        heading_stack = [(l, t) for l, t in heading_stack if l < level]
        heading_stack.append((level, title))
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections.append(
            ParsedSection(path=[t for _, t in heading_stack], char_start=start, char_end=end)
        )

    if matches[0].start() > 0:
        sections.insert(0, ParsedSection(path=["Preamble"], char_start=0, char_end=matches[0].start()))
    return sections


def parse_markdown(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8")
    return ParsedDocument(
        normalized_text=text,
        sections=_sections_from_markdown(text),
        parser_name="markdown",
        parser_version=PARSER_VERSION,
    )


def parse_text(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8")
    return ParsedDocument(
        normalized_text=text,
        sections=[ParsedSection(path=["Document"], char_start=0, char_end=len(text))],
        parser_name="text",
        parser_version=PARSER_VERSION,
    )


def parse_html(path: Path) -> ParsedDocument:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("main") or soup.find("article") or soup.body or soup

    lines: list[str] = []
    for node in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "table"], recursive=True):
        if node.name and node.name.startswith("h"):
            level = int(node.name[1])
            lines.append(f"{'#' * level} {node.get_text(' ', strip=True)}")
        elif node.name == "pre":
            code = node.get_text("\n", strip=False)
            lines.extend(["```", code.rstrip(), "```"])
        elif node.name == "table":
            for tr in node.find_all("tr"):
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if cells:
                    lines.append(" | ".join(cells))
        else:
            txt = node.get_text(" ", strip=True)
            if txt:
                lines.append(txt)

    text = "\n\n".join(lines).strip() + "\n"
    return ParsedDocument(
        normalized_text=text,
        sections=_sections_from_markdown(text),
        parser_name="html-to-markdown",
        parser_version=PARSER_VERSION,
    )


def parse_file(path: Path) -> ParsedDocument:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return parse_markdown(path)
    if suffix in {".html", ".htm"}:
        return parse_html(path)
    if suffix == ".txt":
        return parse_text(path)
    raise ValueError(f"Unsupported file type: {path}")
