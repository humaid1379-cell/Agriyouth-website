"""The prohibited-connection inventory (Section 15.1).

This module is the machine-readable source of truth behind ``SECURITY_BOUNDARIES.md``, the
admin configuration endpoint and the automated prohibited-path tests. Adding a package,
route or environment variable that matches any entry here fails the test suite.
"""

from __future__ import annotations

from typing import Final, NamedTuple


class ProhibitedIntegration(NamedTuple):
    integration_id: str
    category: str
    enforcement: str
    forbidden_modules: tuple[str, ...]
    forbidden_env_vars: tuple[str, ...]
    forbidden_route_fragments: tuple[str, ...]


PROHIBITED_INTEGRATIONS: Final[tuple[ProhibitedIntegration, ...]] = (
    ProhibitedIntegration(
        "PROHIB-01",
        "Email, SMS, chat or notification service",
        "No SDK or dependency, no route, denial test",
        ("smtplib", "email.message", "twilio", "sendgrid", "slack_sdk", "aiosmtplib", "mailgun"),
        ("SMTP_HOST", "SMTP_URL", "SENDGRID_API_KEY", "TWILIO_AUTH_TOKEN", "SLACK_WEBHOOK_URL"),
        ("/send", "/notify", "/email", "/sms", "/message"),
    ),
    ProhibitedIntegration(
        "PROHIB-02",
        "Webhook or generic HTTP action tool",
        "No outbound action client, allowlist test",
        ("requests", "aiohttp", "httpx_action", "webhooks"),
        ("WEBHOOK_URL", "CALLBACK_URL", "ACTION_ENDPOINT", "OUTBOUND_HTTP_ALLOWLIST"),
        ("/webhook", "/callback", "/action", "/dispatch", "/trigger"),
    ),
    ProhibitedIntegration(
        "PROHIB-03",
        "Public web search, browser or scraper",
        "No dependency or route",
        ("selenium", "playwright.sync_api", "bs4", "scrapy", "googlesearch", "serpapi"),
        ("SEARCH_API_KEY", "BROWSER_ENDPOINT", "SERP_API_KEY"),
        ("/search/web", "/browse", "/fetch-url", "/scrape"),
    ),
    ProhibitedIntegration(
        "PROHIB-04",
        "Payment, procurement or transaction service",
        "No dependency, route or schema field",
        ("stripe", "braintree", "paypalrestsdk", "square"),
        ("STRIPE_API_KEY", "PAYMENT_ENDPOINT", "MERCHANT_ID"),
        ("/pay", "/payment", "/charge", "/invoice", "/purchase", "/transaction"),
    ),
    ProhibitedIntegration(
        "PROHIB-05",
        "Operational database write",
        "Separate demo database only; no external DSN configuration",
        (),
        ("OPERATIONAL_DATABASE_URL", "PROD_DATABASE_URL", "WAREHOUSE_DSN", "EXTERNAL_DSN"),
        ("/write-back", "/sync", "/upsert-operational"),
    ),
    ProhibitedIntegration(
        "PROHIB-06",
        "Repository mutation or dynamic source ingestion",
        "No upload endpoint; source directory is read-only at runtime",
        ("git", "pygit2", "dulwich"),
        ("SOURCE_UPLOAD_DIR", "INGEST_ENDPOINT", "REPO_WRITE_TOKEN"),
        ("/upload", "/ingest", "/import", "/sources/create", "/documents/add"),
    ),
    ProhibitedIntegration(
        "PROHIB-07",
        "OAuth or real identity-provider integration",
        "Synthetic server sessions only",
        ("authlib", "msal", "python_jose", "oauthlib", "requests_oauthlib"),
        ("OAUTH_CLIENT_SECRET", "OIDC_ISSUER", "AZURE_TENANT_ID", "IDP_METADATA_URL"),
        ("/oauth", "/oidc", "/saml", "/sso"),
    ),
    ProhibitedIntegration(
        "PROHIB-08",
        "External telemetry or crash reporting",
        "Disabled; local structured logs only",
        ("sentry_sdk", "datadog", "ddtrace", "newrelic", "opentelemetry.exporter.otlp"),
        ("SENTRY_DSN", "DATADOG_API_KEY", "OTEL_EXPORTER_OTLP_ENDPOINT", "NEW_RELIC_LICENSE_KEY"),
        ("/telemetry", "/crash-report"),
    ),
    ProhibitedIntegration(
        "PROHIB-09",
        "Model tool or function calling",
        "Explicitly disabled; the output schema rejects tool requests",
        (),
        ("MODEL_TOOLS_ENABLED", "ENABLE_FUNCTION_CALLING"),
        ("/tools", "/functions"),
    ),
    ProhibitedIntegration(
        "PROHIB-10",
        "Provider or model fallback",
        "The adapter rejects any configuration mismatch",
        (),
        ("FALLBACK_MODEL", "FALLBACK_ENDPOINT", "SECONDARY_PROVIDER", "MODEL_ROUTER_URL"),
        ("/models/select", "/provider/switch"),
    ),
)

#: Every module name that must not be importable from the runtime image.
FORBIDDEN_MODULES: Final[frozenset[str]] = frozenset(
    module for entry in PROHIBITED_INTEGRATIONS for module in entry.forbidden_modules
)

#: Every environment variable name that must not be present or consumed.
FORBIDDEN_ENV_VARS: Final[frozenset[str]] = frozenset(
    name for entry in PROHIBITED_INTEGRATIONS for name in entry.forbidden_env_vars
)

#: Every route fragment that must not appear in the mounted API surface.
FORBIDDEN_ROUTE_FRAGMENTS: Final[frozenset[str]] = frozenset(
    fragment for entry in PROHIBITED_INTEGRATIONS for fragment in entry.forbidden_route_fragments
)


def inventory_payload() -> list[dict[str, str]]:
    return [
        {
            "integration_id": entry.integration_id,
            "category": entry.category,
            "enforcement": entry.enforcement,
            "status": "ABSENT_BY_DESIGN",
        }
        for entry in PROHIBITED_INTEGRATIONS
    ]
