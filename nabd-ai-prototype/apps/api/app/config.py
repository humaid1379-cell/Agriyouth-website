"""Runtime settings.

Only non-secret, environment-shaped values live here. Authorization fixtures, the use-case
contract, rules, the source manifest and model pinning are build-controlled repository data
files, not settings, so that no deployment can widen them.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.domain.enums import ModelMode

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_DIR = REPO_ROOT / "data" / "synthetic_policy_collection_v1"
DEFAULT_ARTIFACTS_DIR = REPO_ROOT / "artifacts"
DEFAULT_CONTRACTS_DIR = REPO_ROOT / "contracts" / "jsonschema"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=None,
        extra="ignore",
        frozen=True,
        protected_namespaces=(),
    )

    environment_id: Literal["ISOLATED_PROTOTYPE_V1"] = "ISOLATED_PROTOTYPE_V1"
    app_env: Literal["local", "test", "demo"] = Field(default="local", alias="APP_ENV")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )

    database_url: str = Field(
        default="postgresql+psycopg://nabd_app:nabd_app_demo@localhost:5432/nabd_prototype",
        alias="DATABASE_URL",
    )

    demo_session_secret: str = Field(
        default="synthetic-demo-session-key", alias="DEMO_SESSION_SECRET"
    )
    demo_session_ttl_seconds: int = Field(
        default=3600, ge=60, le=28800, alias="DEMO_SESSION_TTL_SECONDS"
    )

    model_mode: ModelMode = Field(default=ModelMode.MOCK, alias="MODEL_MODE")
    live_model_endpoint: str | None = Field(default=None, alias="LIVE_MODEL_ENDPOINT")
    live_model_name: str | None = Field(default=None, alias="LIVE_MODEL_NAME")
    live_model_api_key: str | None = Field(default=None, alias="LIVE_MODEL_API_KEY")
    live_model_config_id: str | None = Field(default=None, alias="LIVE_MODEL_CONFIG_ID")

    enable_vector_retrieval: bool = Field(default=False, alias="ENABLE_VECTOR_RETRIEVAL")

    corpus_dir: Path = Field(default=DEFAULT_CORPUS_DIR, alias="CORPUS_DIR")
    artifacts_dir: Path = Field(default=DEFAULT_ARTIFACTS_DIR, alias="ARTIFACTS_DIR")
    contracts_dir: Path = Field(default=DEFAULT_CONTRACTS_DIR, alias="CONTRACTS_DIR")

    cors_allow_origins: str = Field(default="http://localhost:5173", alias="CORS_ALLOW_ORIGINS")

    @field_validator("enable_vector_retrieval")
    @classmethod
    def _vector_stays_disabled(cls, value: bool) -> bool:
        # Kept behind the flag and off by default; it can never bypass lexical source
        # filters or become required for a passing TEVV run.
        return value

    @model_validator(mode="after")
    def _live_mode_requires_full_pinning(self) -> Settings:
        if self.model_mode is ModelMode.LIVE:
            missing = [
                name
                for name, value in (
                    ("LIVE_MODEL_ENDPOINT", self.live_model_endpoint),
                    ("LIVE_MODEL_NAME", self.live_model_name),
                    ("LIVE_MODEL_CONFIG_ID", self.live_model_config_id),
                )
                if not value
            ]
            if missing:
                raise ValueError(
                    "MODEL_MODE=live requires explicit pinning: " + ", ".join(sorted(missing))
                )
            endpoint = self.live_model_endpoint or ""
            if not endpoint.startswith("https://"):
                raise ValueError("LIVE_MODEL_ENDPOINT must be a single https:// endpoint")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def redacted(self) -> dict[str, object]:
        """Non-secret view for the admin configuration endpoint."""
        return {
            "environment_id": self.environment_id,
            "app_env": self.app_env,
            "model_mode": self.model_mode.value,
            "live_model_configured": bool(self.live_model_endpoint and self.live_model_name),
            "live_model_config_id": self.live_model_config_id,
            "enable_vector_retrieval": self.enable_vector_retrieval,
            "database_engine": "postgresql" if not self.is_sqlite else "sqlite",
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Used by tests that manipulate environment variables."""
    get_settings.cache_clear()


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
