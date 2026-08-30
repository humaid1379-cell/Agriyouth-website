"""Deterministic mock adapter (the default model mode).

The mock is not a stub that returns a canned answer. It derives its claims from the
admitted excerpts by selecting, for each excerpt, the sentence with the highest overlap
with the question terms. The claim statement is that exact sentence, so the verifier can
locate it at exact character offsets and the citation-accuracy checks are meaningful
rather than tautological.

It is deterministic: the same corpus, the same question and the same fault profile always
produce byte-identical output, which is what makes replay testing possible.
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.adapters.protocol import ModelAdapterError, ModelFault, RawModelResponse
from app.domain.enums import Materiality, Severity, SupportState
from app.domain.limits import MODEL_OUTPUT_MAX_CHARS
from app.domain.reason_codes import ReasonCode
from app.schemas.evidence import EvidenceExcerpt
from app.schemas.model_io import DraftRequest, VerificationRequest
from app.services.retrieval import question_terms

MOCK_MODEL_REVISION = "deterministic-mock-1.0.0"

#: Claims beyond this index are context rather than answer-bearing.
MATERIAL_CLAIM_COUNT = 2
MAX_CLAIMS = 4
MAX_STATEMENT_CHARS = 500

_SENTENCE_SPLIT = re.compile(r"(?<=[.;])\s+")
_WORD_TOKEN = re.compile(r"[a-z0-9]+")


def _sentences(text: str) -> list[tuple[int, str]]:
    """Split into sentences, returning (offset_within_text, sentence)."""
    spans: list[tuple[int, str]] = []
    cursor = 0
    for piece in _SENTENCE_SPLIT.split(text):
        if not piece:
            continue
        start = text.index(piece, cursor)
        cursor = start + len(piece)
        spans.append((start, piece))
    return spans or [(0, text)]


def _truncate_at_word(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit)
    return text[: cut if cut > 0 else limit]


def _word_set(text: str) -> frozenset[str]:
    return frozenset(_WORD_TOKEN.findall(text.casefold()))


def term_weights(excerpts: tuple[EvidenceExcerpt, ...], terms: tuple[str, ...]) -> dict[str, int]:
    """Integer inverse-document-frequency weights over the admitted excerpts.

    A term that appears in nearly every admitted excerpt ("policy", "request") carries
    little information about which sentence answers the question; a term that appears in
    few of them ("tier", "manager") carries a lot. Weights are integers so that nothing
    downstream introduces a floating-point value, and they depend only on the frozen
    excerpt set, so they are reproducible.
    """
    total = len(excerpts) or 1
    document_words = [_word_set(excerpt.text) for excerpt in excerpts]
    weights: dict[str, int] = {}
    for term in terms:
        frequency = sum(1 for words in document_words if term in words)
        weights[term] = (100 * (total + 1)) // (frequency + 1)
    return weights


def _sentence_score(
    sentence: str,
    terms: tuple[str, ...],
    weights: dict[str, int],
    section_heading: str = "",
) -> int:
    """Weighted distinct-term overlap, plus a bonus when the section heading matches.

    The heading bonus mirrors the retrieval index, which also weights ``section_heading``
    above body text. Without it a definitional "Purpose and Scope" paragraph outscores the
    paragraph that actually answers the question, purely because it restates the subject.
    """
    words = _word_set(sentence)
    body = sum(weights.get(term, 100) for term in terms if term in words)
    heading_words = _word_set(section_heading)
    bonus = sum(weights.get(term, 100) for term in terms if term in heading_words)
    return body + bonus


def best_span(excerpt: EvidenceExcerpt, terms: tuple[str, ...]) -> tuple[int, int, str]:
    """Pick the sentence in ``excerpt`` with the highest question-term overlap.

    Returns offsets relative to the excerpt text, plus the sentence itself. Ties resolve to
    the earliest sentence so the choice is stable.
    """
    weights = term_weights((excerpt,), terms)
    best_score = -1
    best_offset = 0
    best_text = excerpt.text
    for offset, sentence in _sentences(excerpt.text):
        score = _sentence_score(sentence, terms, weights, excerpt.section_heading)
        if score > best_score:
            best_score = score
            best_offset = offset
            best_text = sentence
    trimmed = _truncate_at_word(best_text.strip(), MAX_STATEMENT_CHARS)
    start = best_offset + best_text.index(trimmed) if trimmed in best_text else best_offset
    return start, start + len(trimmed), trimmed


def select_claim_sentences(
    excerpts: tuple[EvidenceExcerpt, ...], terms: tuple[str, ...]
) -> list[tuple[EvidenceExcerpt, str]]:
    """Choose the answer-bearing sentences across all admitted excerpts.

    Ranking sentences globally rather than taking one per excerpt in retrieval order means
    the material claims are the passages that actually answer the question, not whichever
    paragraph happened to rank first. Ordering is fully determined by
    ``(-score, excerpt.rank, offset)``, so the selection is reproducible.
    """
    weights = term_weights(excerpts, terms)
    scored: list[tuple[int, int, int, EvidenceExcerpt, str]] = []
    for excerpt in excerpts:
        for offset, sentence in _sentences(excerpt.text):
            trimmed = _truncate_at_word(sentence.strip(), MAX_STATEMENT_CHARS)
            if len(trimmed) < 40 or trimmed not in excerpt.text:
                continue
            scored.append(
                (
                    -_sentence_score(trimmed, terms, weights, excerpt.section_heading),
                    excerpt.rank,
                    offset,
                    excerpt,
                    trimmed,
                )
            )
    scored.sort(key=lambda row: (row[0], row[1], row[2]))

    chosen: list[tuple[EvidenceExcerpt, str]] = []
    per_excerpt: dict[str, int] = {}
    seen: set[str] = set()
    for _, _, _, excerpt, sentence in scored:
        if len(chosen) >= MAX_CLAIMS:
            break
        if sentence in seen or per_excerpt.get(excerpt.excerpt_id, 0) >= 2:
            continue
        seen.add(sentence)
        per_excerpt[excerpt.excerpt_id] = per_excerpt.get(excerpt.excerpt_id, 0) + 1
        chosen.append((excerpt, sentence))
    return chosen


class DeterministicMockAdapter:
    """In-process adapter. No network, no credentials, no telemetry, no tools."""

    name = "DeterministicMockAdapter"
    supports_tool_calling = False
    supports_fallback = False

    def __init__(self, fault: ModelFault = ModelFault.NONE) -> None:
        self.fault = fault

    # -- draft ------------------------------------------------------------------
    def draft(self, request: DraftRequest) -> RawModelResponse:
        if self.fault is ModelFault.DRAFT_TIMEOUT:
            raise ModelAdapterError(ReasonCode.MODEL_TIMEOUT, detail="mock draft timeout")
        if self.fault is ModelFault.UNAVAILABLE:
            raise ModelAdapterError(ReasonCode.MODEL_UNAVAILABLE, detail="mock endpoint down")
        if self.fault is ModelFault.FALLBACK_ATTEMPT:
            raise ModelAdapterError(
                ReasonCode.MODEL_FALLBACK_ATTEMPTED,
                severity=Severity.S0_CRITICAL,
                detail="a second provider was offered and refused",
            )
        if self.fault is ModelFault.DRAFT_MALFORMED:
            return RawModelResponse(
                '{"claims": [ {"claim_ref": "C01", "statement": ', 4, MOCK_MODEL_REVISION
            )
        if self.fault is ModelFault.DRAFT_REFUSAL:
            return RawModelResponse(
                json.dumps({"refusal": "I cannot assist with this request."}),
                4,
                MOCK_MODEL_REVISION,
            )
        if self.fault is ModelFault.TOOL_REQUEST:
            return RawModelResponse(
                json.dumps(
                    {
                        "tool_call": {"name": "http_post", "url": "https://ops.example/webhook"},
                        "claims": [],
                    }
                ),
                4,
                MOCK_MODEL_REVISION,
            )

        terms = question_terms(request.normalised_question)
        claims: list[dict[str, Any]] = []
        for index, (excerpt, statement) in enumerate(
            select_claim_sentences(request.excerpts, terms)
        ):
            claims.append(
                {
                    "claim_ref": f"C{index + 1:02d}",
                    "statement": statement,
                    "materiality": (
                        Materiality.MATERIAL.value
                        if index < MATERIAL_CLAIM_COUNT
                        else Materiality.NON_MATERIAL.value
                    ),
                    "proposed_evidence_ids": [excerpt.excerpt_id],
                }
            )

        sources = sorted({f"{e.source_id}@{e.source_version}" for e in request.excerpts})
        payload = {
            "claims": claims,
            "assumptions": [
                "Only the admitted synthetic excerpts were used; no outside knowledge was applied."
            ],
            "unresolved_points": [
                "Any matter not stated in the admitted excerpts is outside this draft."
            ],
            "draft_summary": (
                "The admitted excerpts from "
                + ", ".join(sources)
                + " state the classification, evidence and review requirements quoted in the "
                "claims below. Each claim is reproduced verbatim from its cited excerpt so "
                "that it can be verified at exact character offsets."
            ),
        }
        text = json.dumps(payload, ensure_ascii=False)
        if self.fault is ModelFault.OVERSIZED_OUTPUT:
            padding = "x" * (MODEL_OUTPUT_MAX_CHARS + 100 - len(text))
            payload["draft_summary"] = str(payload["draft_summary"]) + padding
            text = json.dumps(payload, ensure_ascii=False)
        return RawModelResponse(text, 5, MOCK_MODEL_REVISION)

    # -- verify -----------------------------------------------------------------
    def verify(self, request: VerificationRequest) -> RawModelResponse:
        if self.fault is ModelFault.VERIFIER_TIMEOUT:
            raise ModelAdapterError(ReasonCode.MODEL_TIMEOUT, detail="mock verifier timeout")
        if self.fault is ModelFault.VERIFIER_MALFORMED:
            return RawModelResponse('{"verified_claims": [', 4, MOCK_MODEL_REVISION)

        by_id = {excerpt.excerpt_id: excerpt for excerpt in request.excerpts}
        verified: list[dict[str, Any]] = []

        for claim in request.draft_claims:
            excerpt_id = claim.proposed_evidence_ids[0]
            excerpt = by_id.get(excerpt_id)

            if self.fault is ModelFault.FABRICATED_CITATION and claim.claim_ref == "C01":
                verified.append(
                    {
                        "claim_ref": claim.claim_ref,
                        "support_state": SupportState.SUPPORTED.value,
                        "evidence_ids": ["EXC-fabricated-000000000000-not-admitted"],
                        "support_spans": [],
                        "conflict_ids": [],
                        "qualification": "",
                        "verification_note": (
                            "Cited an excerpt identifier outside the admitted set."
                        ),
                    }
                )
                continue

            if self.fault is ModelFault.VERIFIER_DISAGREEMENT and claim.claim_ref == "C01":
                verified.append(
                    {
                        "claim_ref": claim.claim_ref,
                        "support_state": SupportState.UNSUPPORTED.value,
                        "evidence_ids": [],
                        "support_spans": [],
                        "conflict_ids": [],
                        "qualification": "",
                        "verification_note": "No admitted excerpt states this claim.",
                    }
                )
                continue

            if self.fault is ModelFault.PARTIAL_SUPPORT and claim.claim_ref == "C01":
                verified.append(
                    {
                        "claim_ref": claim.claim_ref,
                        "support_state": SupportState.PARTIALLY_SUPPORTED.value,
                        "evidence_ids": [excerpt_id] if excerpt else [],
                        "support_spans": [],
                        "conflict_ids": [],
                        "qualification": (
                            "The excerpt supports the requirement but not the stated period."
                        ),
                        "verification_note": "Partial support only.",
                    }
                )
                continue

            if excerpt is None or claim.statement not in excerpt.text:
                verified.append(
                    {
                        "claim_ref": claim.claim_ref,
                        "support_state": SupportState.UNSUPPORTED.value,
                        "evidence_ids": [],
                        "support_spans": [],
                        "conflict_ids": [],
                        "qualification": "",
                        "verification_note": "The claim text was not located in the cited excerpt.",
                    }
                )
                continue

            start = excerpt.text.index(claim.statement)
            verified.append(
                {
                    "claim_ref": claim.claim_ref,
                    "support_state": SupportState.SUPPORTED.value,
                    "evidence_ids": [excerpt_id],
                    "support_spans": [
                        {
                            "excerpt_id": excerpt_id,
                            "quote_start": start,
                            "quote_end": start + len(claim.statement),
                            "quoted_text": claim.statement,
                        }
                    ],
                    "conflict_ids": [],
                    "qualification": "",
                    "verification_note": "Located verbatim in the cited excerpt.",
                }
            )

        payload = {
            "verified_claims": verified,
            "verifier_notes": (
                "Each claim was checked against the admitted excerpts only. Support spans "
                "are exact substrings at the recorded offsets."
            ),
        }
        return RawModelResponse(json.dumps(payload, ensure_ascii=False), 5, MOCK_MODEL_REVISION)
