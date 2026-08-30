"""The ``nabd-canonical-json-v1`` serialization profile and packet sealing helpers.

Profile rules:

* UTF-8 JSON with sorted object keys and compact separators.
* ISO-8601 UTC timestamps rendered with a trailing ``Z`` and millisecond precision.
* Line endings normalised to ``\\n``.
* Unicode normalised to NFC.
* No floating-point values anywhere in the preimage; risk and score fields are integers
  or enumerated strings so that serialization can never drift between platforms.

The resulting SHA-256 is a tamper-evidence reference. It is not proof of truth, immutable
storage, authorization or authorship.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Final
from uuid import UUID

from app.domain.versions import CANONICAL_JSON_PROFILE

PROFILE_ID: Final[str] = CANONICAL_JSON_PROFILE
HASH_ALGORITHM: Final[str] = "SHA-256"
VERIFIER_METHOD: Final[str] = "recompute-canonical-json-sha256"

#: Field omitted from the packet hash preimage (it holds the hash itself).
PACKET_HASH_OMITTED_PATH: Final[tuple[str, str]] = ("integrity", "packet_sha256")


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented under the canonical profile."""


def normalise_text(value: str) -> str:
    """Apply NFC normalisation and normalise line endings to ``\\n``."""
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def format_timestamp(value: datetime) -> str:
    """Render a timezone-aware datetime as ISO-8601 UTC with millisecond precision."""
    if value.tzinfo is None:
        raise CanonicalizationError("naive datetime is not canonicalizable")
    as_utc = value.astimezone(UTC)
    return as_utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{as_utc.microsecond // 1000:03d}Z"


def utc_now() -> datetime:
    """Millisecond-truncated UTC now, so stored and canonical values always agree."""
    now = datetime.now(UTC)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


def to_canonical_value(value: Any) -> Any:
    """Recursively convert a Python value into canonical-profile primitives."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, Enum):
        return to_canonical_value(value.value)
    if isinstance(value, str):
        return normalise_text(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise CanonicalizationError(
            "floating-point values are prohibited in the canonical profile"
        )
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        raise CanonicalizationError("non-integral Decimal is prohibited in the canonical profile")
    if isinstance(value, datetime):
        return format_timestamp(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        raise CanonicalizationError("raw bytes are prohibited in the canonical profile")
    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("object keys must be strings")
            converted[normalise_text(key)] = to_canonical_value(item)
        return converted
    if isinstance(value, Sequence):
        return [to_canonical_value(item) for item in value]
    raise CanonicalizationError(f"unsupported type in canonical preimage: {type(value)!r}")


def canonical_dumps(payload: Mapping[str, Any]) -> str:
    """Serialize a mapping using the ``nabd-canonical-json-v1`` profile."""
    return json.dumps(
        to_canonical_value(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return canonical_dumps(payload).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical serialization of ``payload``."""
    return sha256_hex(canonical_bytes(payload))


def packet_preimage(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return the packet mapping with only ``integrity.packet_sha256`` removed."""
    section, field = PACKET_HASH_OMITTED_PATH
    preimage = {key: value for key, value in packet.items()}
    integrity = preimage.get(section)
    if isinstance(integrity, Mapping):
        preimage[section] = {k: v for k, v in integrity.items() if k != field}
    return preimage


def compute_packet_hash(packet: Mapping[str, Any]) -> str:
    """Compute the packet seal over everything except ``integrity.packet_sha256``."""
    return canonical_sha256(packet_preimage(packet))


def verify_packet_hash(packet: Mapping[str, Any]) -> bool:
    integrity = packet.get("integrity")
    if not isinstance(integrity, Mapping):
        return False
    recorded = integrity.get("packet_sha256")
    return isinstance(recorded, str) and recorded == compute_packet_hash(packet)


def text_sha256(text: str) -> str:
    """SHA-256 over NFC-normalised, ``\\n``-normalised UTF-8 text."""
    return sha256_hex(normalise_text(text).encode("utf-8"))


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:  # noqa: PTH123 - stdlib open is intentional here
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
