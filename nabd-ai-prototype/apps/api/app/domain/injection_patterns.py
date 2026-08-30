"""Deterministic instruction-like content detector fixture.

This is defence in depth, not a source-authority decision-maker. A match raises a
quarantine condition and a security event; it never decides on its own that a source is
trustworthy, and no third LLM detector is introduced in V1.
"""

from __future__ import annotations

import re
from typing import Final, NamedTuple


class InjectionPattern(NamedTuple):
    pattern_id: str
    description: str
    regex: re.Pattern[str]


def _p(pattern_id: str, description: str, expression: str) -> InjectionPattern:
    return InjectionPattern(pattern_id, description, re.compile(expression, re.IGNORECASE))


INJECTION_PATTERN_SET_VERSION: Final[str] = "injection-patterns-v1.0.0"

INJECTION_PATTERNS: Final[tuple[InjectionPattern, ...]] = (
    _p("INJ-001", "Instruction override phrasing", r"\bignore (all|any|the)? ?(previous|prior|above|preceding) (instructions?|constraints?|rules?|policy)\b"),
    _p("INJ-002", "Role reassignment of the assistant", r"\byou are (now|hereby) (an?|the) [a-z ]{0,24}(agent|approver|administrator|authority)\b"),
    _p("INJ-003", "System or developer role marker in content", r"^\s*(system|developer|assistant)\s*(instruction)?\s*:", ),
    _p("INJ-004", "Directive to disregard governing controls", r"\bdisregard (the|all|any) [a-z ]{0,32}(requirements?|clause|rules?|controls?|policy)\b"),
    _p("INJ-005", "Instruction to override deterministic rules", r"\boverride (the )?(deterministic )?(rules?|controls?|governance|validation)\b"),
    _p("INJ-006", "Claim of granted authority inside content", r"\b(has |have )?granted you (full |complete )?(authority|permission|access)\b"),
    _p("INJ-007", "Instruction to emit an approval outcome", r"\b(mark|set|output|return) (every|all|the|this)? ?[a-z ]{0,24}(as )?(approved|approval)\b"),
    _p("INJ-008", "Instruction to set a route or state", r"\bset the (route|state|status) to\b"),
    _p("INJ-009", "Outbound connector or action instruction", r"\b(call|invoke|trigger|post to) (the )?[a-z ]{0,16}(webhook|endpoint|api|connector)\b"),
    _p("INJ-010", "Messaging or notification instruction", r"\bsend (a |the )?(confirmation )?(email|sms|message|notification)\b"),
    _p("INJ-011", "Instruction to skip human review", r"\b(skip|bypass|without) (the )?(human )?(review|reviewer|approval) requirement\b"),
    _p("INJ-012", "Instruction to suppress citations", r"\b(do not|don't|never) cite (sources?|evidence)\b"),
    _p("INJ-013", "Self-declared highest authority", r"\b(treat|consider) this (note|document|text) as the (highest|final) authority\b"),
    _p("INJ-014", "Embedded tool or function call syntax", r"\b(tool_call|function_call|<\|im_start\|>|```tool)\b"),
    _p("INJ-015", "Embedded URL in policy body", r"https?://"),
)


def scan_for_instruction_like(text: str) -> tuple[str, ...]:
    """Return the sorted pattern IDs that match ``text``. Deterministic and side-effect free."""
    matched = {
        pattern.pattern_id
        for pattern in INJECTION_PATTERNS
        if pattern.regex.search(text) is not None
    }
    return tuple(sorted(matched))


def pattern_descriptions() -> dict[str, str]:
    return {pattern.pattern_id: pattern.description for pattern in INJECTION_PATTERNS}
