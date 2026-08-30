"""Deterministic read-only retrieval.

Eligibility, business scope, lifecycle, access and manifest filters are applied **before**
ranking and return. Ranking is PostgreSQL ``ts_rank_cd`` over a generated ``tsvector``,
descending, with ``excerpt_id`` ascending as the tie break, so the same corpus and the same
question always produce the same ordered excerpts.

On SQLite (isolated unit tests only) the same filter set runs against a portable lexical
scorer that reproduces the ordering contract without the PostgreSQL index.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import Select, func, literal_column, select
from sqlalchemy.orm import Session

from app.domain.canonical import utc_now
from app.domain.enums import DataClassification, TrustLabel
from app.domain.ids import derived_id
from app.domain.limits import (
    EXCERPT_MAX_CHARS,
    EXCERPTS_USED_MAX,
    RETRIEVAL_CANDIDATE_MAX,
    TOTAL_EVIDENCE_CONTEXT_MAX_CHARS,
)
from app.repositories.tables import SourceBlockRow, SourceVersionRow
from app.schemas.evidence import EvidenceExcerpt
from app.services.fixtures import SourceManifestItem

RETRIEVAL_SERVICE_ID = "service:controlled-retrieval"

_WORD = re.compile(r"[A-Za-z0-9]+")

#: Deliberately small stop list. Retrieval must stay explainable, not clever.
_STOPWORDS = frozenset(
    """a an the and or of to in for on at by is are was were be been being do does did
    what which who whom whose when where how why must shall should may can could would
    it its this that these those with within from into about as if then than there here
    i me my we our you your they them their he she his her""".split()
)


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    excerpts: tuple[EvidenceExcerpt, ...]
    candidate_count: int
    total_context_chars: int
    truncated_by_excerpt_limit: bool
    truncated_by_context_limit: bool


def question_terms(question: str) -> tuple[str, ...]:
    """Deterministic term extraction: lowercase word tokens minus a small stop list."""
    tokens = [token.casefold() for token in _WORD.findall(question)]
    return tuple(dict.fromkeys(token for token in tokens if token not in _STOPWORDS and len(token) > 2))


def _eligible_keys(eligible: tuple[SourceManifestItem, ...]) -> list[str]:
    return sorted(item.source_key for item in eligible)


def _postgres_query(terms: tuple[str, ...], keys: list[str]) -> Select[tuple[SourceBlockRow, float]]:
    # Terms are OR-combined: a policy question rarely has one passage containing every
    # word, and AND semantics would silently retrieve nothing. Terms come from a
    # ``[A-Za-z0-9]+`` tokeniser and are passed as a bound parameter, so the query text
    # cannot carry operators from user input.
    tsquery = func.to_tsquery("english", " | ".join(terms))
    # ``search_vector`` is the stored generated column created by migration 0003. It is
    # PostgreSQL-only, so it is referenced literally rather than mapped onto the ORM class
    # that SQLite unit tests also use.
    rank = func.ts_rank_cd(literal_column("source_blocks.search_vector"), tsquery)
    return (
        select(SourceBlockRow, rank.label("rank_score"))
        .join(SourceVersionRow, SourceVersionRow.source_version_key == SourceBlockRow.source_version_key)
        .where(SourceBlockRow.source_version_key.in_(keys))
        .where(SourceVersionRow.lifecycle == "ACTIVE")
        .where(rank > 0)
        .order_by(rank.desc(), SourceBlockRow.source_block_id.asc())
        .limit(RETRIEVAL_CANDIDATE_MAX)
    )


def _portable_score(text: str, heading: str, terms: tuple[str, ...]) -> int:
    """Integer lexical score. Integers keep the canonical profile floating-point free."""
    body = text.casefold()
    head = heading.casefold()
    score = 0
    for term in terms:
        occurrences = body.count(term)
        if occurrences:
            score += 10 * min(occurrences, 5)
        if term in head:
            score += 15
    return score


def retrieve(
    session: Session,
    *,
    case_id: str,
    question: str,
    eligible: tuple[SourceManifestItem, ...],
) -> RetrievalResult:
    """Return admitted excerpts under the frozen retrieval contract."""
    terms = question_terms(question)
    keys = _eligible_keys(eligible)
    if not terms or not keys:
        return RetrievalResult((), 0, 0, False, False)

    scored: list[tuple[SourceBlockRow, int]] = []
    dialect = session.get_bind().dialect.name

    if dialect == "postgresql":
        rows = session.execute(_postgres_query(terms, keys)).all()
        # ts_rank_cd returns a float; scale to an integer so nothing downstream carries a
        # floating-point value into the canonical packet preimage.
        scored = [(row[0], int(round(float(row[1]) * 1_000_000))) for row in rows]
    else:
        candidates = session.execute(
            select(SourceBlockRow)
            .join(
                SourceVersionRow,
                SourceVersionRow.source_version_key == SourceBlockRow.source_version_key,
            )
            .where(SourceBlockRow.source_version_key.in_(keys))
            .where(SourceVersionRow.lifecycle == "ACTIVE")
            .order_by(SourceBlockRow.source_block_id.asc())
        ).scalars()
        for block in candidates:
            score = _portable_score(block.text, block.section_heading, terms)
            if score > 0:
                scored.append((block, score))
        scored.sort(key=lambda pair: (-pair[1], pair[0].source_block_id))
        scored = scored[:RETRIEVAL_CANDIDATE_MAX]

    candidate_count = len(scored)
    by_key = {item.source_key: item for item in eligible}

    excerpts: list[EvidenceExcerpt] = []
    total_chars = 0
    truncated_by_excerpt_limit = False
    truncated_by_context_limit = False
    retrieved_at = utc_now()

    for rank, (block, score) in enumerate(scored):
        if len(excerpts) >= EXCERPTS_USED_MAX:
            truncated_by_excerpt_limit = True
            break
        text = block.text[:EXCERPT_MAX_CHARS]
        if total_chars + len(text) > TOTAL_EVIDENCE_CONTEXT_MAX_CHARS:
            truncated_by_context_limit = True
            break
        item = by_key.get(block.source_version_key)
        if item is None:  # pragma: no cover - defensive; the filter above guarantees this
            continue
        excerpt_id = derived_id("excerpt", case_id, f"{block.source_version_key}-{block.block_index}")
        excerpts.append(
            EvidenceExcerpt(
                produced_by=RETRIEVAL_SERVICE_ID,
                created_at=retrieved_at,
                excerpt_id=excerpt_id,
                case_id=case_id,
                source_id=item.source_id,
                source_version=item.source_version,
                page_number=block.page_number,
                section_heading=block.section_heading,
                block_index=block.block_index,
                char_start=block.char_start,
                char_end=block.char_start + len(text),
                text=text,
                text_sha256=block.text_sha256,
                source_sha256=item.source_sha256,
                rank=rank,
                retrieval_score=score,
                trust_label=TrustLabel.UNTRUSTED_CONTENT,
                data_classification=DataClassification.SYNTHETIC_UNTRUSTED_CONTENT,
                instruction_like_flags=tuple(block.instruction_like_flags or ()),
            )
        )
        total_chars += len(text)

    # Deterministic final ordering: rank ascending, then excerpt_id ascending.
    excerpts.sort(key=lambda excerpt: (excerpt.rank, excerpt.excerpt_id))
    return RetrievalResult(
        excerpts=tuple(excerpts),
        candidate_count=candidate_count,
        total_context_chars=total_chars,
        truncated_by_excerpt_limit=truncated_by_excerpt_limit,
        truncated_by_context_limit=truncated_by_context_limit,
    )
