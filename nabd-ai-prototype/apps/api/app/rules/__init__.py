"""Deterministic rule engine.

Importing this package registers the frozen rule catalog. Nothing may import
``app.rules.framework`` alone and evaluate rules: an empty registry would make every state
pass with zero controls evaluated, which is exactly the silent failure the engine exists to
prevent. :func:`app.rules.assert_catalog_loaded` is the guard for that.
"""

from __future__ import annotations

from app.rules import catalog as catalog  # noqa: F401  (import registers the rule catalog)
from app.rules.framework import (
    REGISTRY,
    RuleContext,
    RuleOutcomeSpec,
    evaluate_state,
    first_mandatory_stop,
)

#: Every rule id the frozen catalog must contain.
EXPECTED_RULE_IDS: frozenset[str] = frozenset(
    {
        "AUTH-001",
        "ID-001",
        "REQ-001",
        "SCOPE-001",
        "SRC-001",
        "ISO-001",
        "EVD-001",
        "CLM-001",
        "LIM-001",
        "FSM-001",
        "PKT-001",
        "AUD-001",
        "SOD-001",
        "PATH-001",
        "KILL-001",
    }
)


class RuleCatalogError(RuntimeError):
    """The registered catalog does not match the frozen expectation."""


def assert_catalog_loaded() -> None:
    registered = set(REGISTRY.ids())
    if registered != EXPECTED_RULE_IDS:
        missing = sorted(EXPECTED_RULE_IDS - registered)
        unexpected = sorted(registered - EXPECTED_RULE_IDS)
        raise RuleCatalogError(
            f"rule catalog mismatch (missing={missing}, unexpected={unexpected})"
        )


__all__ = [
    "EXPECTED_RULE_IDS",
    "REGISTRY",
    "RuleCatalogError",
    "RuleContext",
    "RuleOutcomeSpec",
    "assert_catalog_loaded",
    "catalog",
    "evaluate_state",
    "first_mandatory_stop",
]
