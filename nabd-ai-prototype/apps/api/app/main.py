"""FastAPI application.

Security posture of the HTTP layer:

* one error envelope, never leaking secrets, prompts, credentials, hidden settings or
  unauthorized case content;
* a strict Content-Security-Policy and the usual hardening headers;
* a request size and correlation-id middleware;
* a startup self-check that fails fast if the rule catalog, corpus manifest or prohibited
  inventory is not in the expected state.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import routes_admin, routes_cases, routes_review, routes_session
from app.config import get_settings
from app.domain.enums import ModelMode
from app.domain.errors import ControlError
from app.domain.reason_codes import ReasonCode, message_for
from app.domain.versions import ENVIRONMENT_ID, PRODUCT_NAME
from app.rules import assert_catalog_loaded
from app.schemas.api import HealthResponse

LOGGER = logging.getLogger("nabd")

MAX_REQUEST_BYTES = 64 * 1024

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
    "Cache-Control": "no-store",
    # The API serves JSON only. Nothing may be loaded, framed or connected to from it.
    "Content-Security-Policy": (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    ),
}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    assert_catalog_loaded()

    from app.services.fixtures import load_corpus_fixtures, primary_authorization

    corpus = load_corpus_fixtures()
    authorization = primary_authorization()
    if authorization.source_manifest_sha256 != corpus.manifest_sha256:
        raise RuntimeError(
            "the authorization fixture does not admit the current corpus manifest hash"
        )
    LOGGER.info(
        "started environment=%s model_mode=%s corpus=%s",
        settings.environment_id,
        settings.model_mode.value,
        corpus.manifest_sha256[:16],
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=f"{PRODUCT_NAME} API",
        version="0.1.0",
        summary=(
            "Isolated synthetic prototype. Decision-support only: it does not approve, "
            "execute, transmit or activate any institutional action."
        ),
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    @app.middleware("http")
    async def request_guard(
        request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        request.state.correlation_id = uuid.uuid4().hex
        declared = request.headers.get("content-length")
        if declared and int(declared) > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": ReasonCode.REQUEST_LIMIT_EXCEEDED.value,
                        "message": message_for(ReasonCode.REQUEST_LIMIT_EXCEEDED),
                        "case_id": None,
                        "state": None,
                        "correlation_id": request.state.correlation_id,
                        "safe_to_display": True,
                    }
                },
            )
        started = time.monotonic()
        response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        response.headers["X-Correlation-Id"] = request.state.correlation_id
        LOGGER.info(
            "%s %s -> %s in %dms",
            request.method,
            request.url.path,
            response.status_code,
            int((time.monotonic() - started) * 1000),
        )
        return response

    @app.exception_handler(ControlError)
    async def control_error_handler(request: Request, exc: ControlError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(status_code=exc.http_status, content=exc.envelope(correlation_id))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Validation detail is deliberately dropped: it can echo submitted content back.
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        error = ControlError(ReasonCode.REQUEST_CONTRACT_INVALID)
        return JSONResponse(status_code=422, content=error.envelope(correlation_id))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        code = ReasonCode.NOT_FOUND if exc.status_code == 404 else ReasonCode.ACCESS_DENIED
        error = ControlError(code)
        return JSONResponse(status_code=exc.status_code, content=error.envelope(correlation_id))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        # Fail closed and disclose nothing about the internal failure.
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        LOGGER.exception("unhandled error correlation_id=%s", correlation_id)
        error = ControlError(ReasonCode.INTERNAL_CONTROL_FAILURE)
        return JSONResponse(status_code=500, content=error.envelope(correlation_id))

    app.include_router(routes_session.router)
    app.include_router(routes_cases.router)
    app.include_router(routes_review.router)
    app.include_router(routes_admin.router)

    @app.get("/health/live", response_model=HealthResponse, tags=["health"])
    def health_live() -> HealthResponse:
        return HealthResponse(status="live", environment_id=ENVIRONMENT_ID)

    @app.get("/health/ready", response_model=HealthResponse, tags=["health"])
    def health_ready() -> HealthResponse:
        checks: dict[str, str] = {}
        try:
            from sqlalchemy import text

            from app.repositories.database import get_engine

            with get_engine().connect() as connection:
                connection.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:  # noqa: BLE001 - readiness must not leak the underlying error
            checks["database"] = "unavailable"

        try:
            from app.services.fixtures import load_corpus_fixtures

            load_corpus_fixtures()
            checks["corpus_manifest"] = "ok"
        except Exception:  # noqa: BLE001
            checks["corpus_manifest"] = "unavailable"

        try:
            assert_catalog_loaded()
            checks["rule_catalog"] = "ok"
        except Exception:  # noqa: BLE001
            checks["rule_catalog"] = "unavailable"

        checks["model_mode"] = get_settings().model_mode.value
        ready = all(
            value == "ok"
            for key, value in checks.items()
            if key in {"database", "corpus_manifest", "rule_catalog"}
        )
        return HealthResponse(
            status="ready" if ready else "not_ready",
            environment_id=ENVIRONMENT_ID,
            checks=checks,
        )

    return app


app = create_app()


def default_model_mode() -> ModelMode:
    return get_settings().model_mode
