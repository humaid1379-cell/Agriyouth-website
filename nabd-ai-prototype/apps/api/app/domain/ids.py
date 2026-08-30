"""Sortable identifier generation.

Case identity uses a UUIDv7-shaped value: a 48-bit big-endian Unix millisecond timestamp
followed by random bits, with the version and variant nibbles set. Python 3.12 has no
``uuid.uuid7``, so it is constructed here rather than pulled from a dependency.
"""

from __future__ import annotations

import secrets
import time
from uuid import UUID

_PREFIXES = {
    "case": "CASE",
    "excerpt": "EXC",
    "claim": "CLM",
    "packet": "PKT",
    "disposition": "DSP",
    "event": "EVT",
    "rule_result": "RUL",
    "uncertainty": "UNC",
    "model_run": "MRN",
    "session": "SES",
    "stop": "STP",
    "tevv_run": "TVR",
    "defect": "DEF",
    "evidence_record": "EVR",
    "status_record": "STR",
    "kill_switch": "KSW",
    "assertion": "AST",
}


def uuid7() -> UUID:
    """Generate a time-ordered UUID (version 7 layout)."""
    unix_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    raw = bytearray(unix_ms.to_bytes(6, "big") + secrets.token_bytes(10))
    raw[6] = (raw[6] & 0x0F) | 0x70
    raw[8] = (raw[8] & 0x3F) | 0x80
    return UUID(bytes=bytes(raw))


def new_case_id() -> str:
    return f"{_PREFIXES['case']}-{uuid7()}"


def new_id(kind: str) -> str:
    """Generate a prefixed sortable identifier for a governed record kind."""
    if kind not in _PREFIXES:
        raise KeyError(f"unknown identifier kind: {kind}")
    return f"{_PREFIXES[kind]}-{uuid7()}"


def derived_id(kind: str, case_id: str, suffix: str) -> str:
    """Deterministic identifier derived from a case and a stable suffix.

    Used where replay must reproduce the same identifier, for example claim and excerpt
    identifiers inside a single case.
    """
    if kind not in _PREFIXES:
        raise KeyError(f"unknown identifier kind: {kind}")
    short = case_id.rsplit("-", 1)[-1][:12]
    return f"{_PREFIXES[kind]}-{short}-{suffix}"
