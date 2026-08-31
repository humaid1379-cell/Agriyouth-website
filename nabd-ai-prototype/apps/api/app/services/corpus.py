"""Deterministic frozen-corpus parser.

The corpus is authored as UTF-8 text with explicit ``<<<PAGE n>>>`` markers and ``## ``
section headings. Character offsets are recorded against the normalised file content, so
``normalise(file)[char_start:char_end]`` always reproduces an excerpt exactly.

PyMuPDF is used during seeding only, to render a derived read-only PDF facsimile of each
source and to cross-check the page count. It is never used at request time, and there is
no upload or dynamic ingestion path anywhere in the runtime.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.domain.canonical import normalise_text, text_sha256
from app.domain.injection_patterns import scan_for_instruction_like

PAGE_MARKER = re.compile(r"^<<<PAGE (\d+)>>>$", re.MULTILINE)
HEADING_PREFIX = "## "


@dataclass(frozen=True, slots=True)
class ParsedBlock:
    page_number: int
    section_heading: str
    block_index: int
    char_start: int
    char_end: int
    text: str

    @property
    def text_sha256(self) -> str:
        return text_sha256(self.text)

    @property
    def instruction_like_flags(self) -> tuple[str, ...]:
        return scan_for_instruction_like(self.text)


@dataclass(frozen=True, slots=True)
class ParsedPage:
    page_number: int
    char_start: int
    char_end: int
    section_headings: tuple[str, ...]
    block_count: int

    @property
    def primary_heading(self) -> str:
        return self.section_headings[0] if self.section_headings else ""


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    raw_text: str
    pages: tuple[ParsedPage, ...]
    blocks: tuple[ParsedBlock, ...]

    @property
    def extracted_text(self) -> str:
        return "\n\n".join(block.text for block in self.blocks)

    @property
    def extracted_text_sha256(self) -> str:
        return text_sha256(self.extracted_text)

    def slice(self, char_start: int, char_end: int) -> str:
        return self.raw_text[char_start:char_end]

    def page(self, page_number: int) -> ParsedPage | None:
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None

    def page_text(self, page_number: int) -> str | None:
        page = self.page(page_number)
        if page is None:
            return None
        return self.raw_text[page.char_start : page.char_end]


class CorpusParseError(ValueError):
    """Raised when a source file does not satisfy the frozen corpus format."""


def parse_source_text(raw: str) -> ParsedDocument:
    """Parse authored source text into pages and blocks with exact offsets."""
    text = normalise_text(raw)
    if text != raw:
        raise CorpusParseError(
            "source file is not already NFC-normalised with \\n line endings; "
            "re-author the file so that offsets are reproducible"
        )

    markers = list(PAGE_MARKER.finditer(text))
    if not markers:
        raise CorpusParseError("source file contains no <<<PAGE n>>> marker")
    if markers[0].start() != 0:
        raise CorpusParseError("source file must begin with a <<<PAGE 1>>> marker")

    pages: list[ParsedPage] = []
    blocks: list[ParsedBlock] = []
    block_index = 0

    for position, marker in enumerate(markers):
        page_number = int(marker.group(1))
        if page_number != position + 1:
            raise CorpusParseError(
                f"page markers must be sequential from 1; found {page_number} at position "
                f"{position + 1}"
            )
        body_start = marker.end() + 1
        body_end = markers[position + 1].start() if position + 1 < len(markers) else len(text)

        headings: list[str] = []
        page_block_count = 0
        current_heading = ""
        cursor = body_start

        for chunk in re.split(r"\n{2,}", text[body_start:body_end]):
            chunk_start = text.index(chunk, cursor) if chunk else cursor
            cursor = chunk_start + len(chunk)
            if not chunk.strip():
                continue
            # A heading owns the first line of its chunk; the remainder is body text.
            if chunk.lstrip().startswith(HEADING_PREFIX):
                head_line, separator, remainder = chunk.partition("\n")
                current_heading = head_line.strip()[len(HEADING_PREFIX) :].strip()
                headings.append(current_heading)
                if not separator:
                    continue
                chunk_start += len(head_line) + 1
                chunk = remainder
                if not chunk.strip():
                    continue
            stripped = chunk.strip()
            leading = len(chunk) - len(chunk.lstrip())
            start = chunk_start + leading
            end = start + len(stripped)
            blocks.append(
                ParsedBlock(
                    page_number=page_number,
                    section_heading=current_heading,
                    block_index=block_index,
                    char_start=start,
                    char_end=end,
                    text=text[start:end],
                )
            )
            block_index += 1
            page_block_count += 1

        pages.append(
            ParsedPage(
                page_number=page_number,
                char_start=body_start,
                char_end=body_end,
                section_headings=tuple(headings),
                block_count=page_block_count,
            )
        )

    if not blocks:
        raise CorpusParseError("source file contains no retrievable text block")

    document = ParsedDocument(raw_text=text, pages=tuple(pages), blocks=tuple(blocks))
    for block in document.blocks:
        if document.slice(block.char_start, block.char_end) != block.text:
            raise CorpusParseError(
                f"block {block.block_index} offsets do not reproduce its text exactly"
            )
    return document


def parse_source_file(path: Path) -> ParsedDocument:
    return parse_source_text(path.read_text(encoding="utf-8"))
