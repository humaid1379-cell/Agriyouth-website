"""Frozen component version identifiers.

These are control-plane constants. The authorization fixture lists the exact set it
permits; a mismatch is a mandatory stop, never a warning.
"""

from __future__ import annotations

from typing import Final

ENVIRONMENT_ID: Final[str] = "ISOLATED_PROTOTYPE_V1"
BUSINESS_SCOPE_ID: Final[str] = "BUSINESS_UNIT_V1"
DATA_BOUNDARY_ID: Final[str] = "SYNTHETIC_ONLY"
PRODUCT_NAME: Final[str] = "NABD AI Decision Review"
BRAND_STATEMENT_EN: Final[str] = "Governed intelligence. Human authority."
BRAND_STATEMENT_AR: Final[str] = "ذكاء محكوم. سلطة بشرية."

WORKFLOW_VERSION: Final[str] = "workflow-v1.0.0"
SCHEMA_VERSION: Final[str] = "nabd-schema-v1"
CANONICAL_JSON_PROFILE: Final[str] = "nabd-canonical-json-v1"
RULE_CATALOG_VERSION: Final[str] = "rule-catalog-v1.0.0"
CORPUS_VERSION: Final[str] = "synthetic_policy_collection_v1"
RETRIEVAL_VERSION: Final[str] = "retrieval-lexical-v1.0.0"
PROMPT_DRAFT_VERSION: Final[str] = "prompt-draft-v1.0.0"
PROMPT_VERIFY_VERSION: Final[str] = "prompt-verify-v1.0.0"
PACKET_SCHEMA_VERSION: Final[str] = "decision-readiness-packet-v1"
AUDIT_CHAIN_VERSION: Final[str] = "audit-chain-sha256-v1"
TEVV_PLAN_VERSION: Final[str] = "tevv-plan-v1.0.0"
USE_CASE_CONTRACT_ID: Final[str] = "UC-POLICY-SOP-EVIDENCE-V1"
AUTHORIZATION_FIXTURE_ID: Final[str] = "SYNTHETIC_DEMO_AUTHORIZATION"

#: Exact component-version fingerprint surfaced by the admin configuration endpoint and
#: embedded in every packet's version lineage.
COMPONENT_VERSIONS: Final[dict[str, str]] = {
    "workflow": WORKFLOW_VERSION,
    "schema": SCHEMA_VERSION,
    "canonical_json_profile": CANONICAL_JSON_PROFILE,
    "rule_catalog": RULE_CATALOG_VERSION,
    "corpus": CORPUS_VERSION,
    "retrieval": RETRIEVAL_VERSION,
    "prompt_draft": PROMPT_DRAFT_VERSION,
    "prompt_verify": PROMPT_VERIFY_VERSION,
    "packet_schema": PACKET_SCHEMA_VERSION,
    "audit_chain": AUDIT_CHAIN_VERSION,
    "use_case_contract": USE_CASE_CONTRACT_ID,
}
