# NABD AI Decision Review - API image.
#
# Runs as a non-root user, mounts the synthetic corpus read-only, and needs no outbound
# network access in the default MODEL_MODE=mock configuration.

FROM python:3.12.8-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv/api

# Build dependencies are installed, used, then removed so the runtime image carries no
# compiler toolchain.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/app ./app

RUN pip install --no-cache-dir . \
    && apt-get purge -y --auto-remove build-essential

COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
COPY scripts /srv/scripts
COPY contracts /srv/contracts

RUN groupadd --system --gid 10001 nabd \
    && useradd --system --uid 10001 --gid nabd --home /srv --shell /usr/sbin/nologin nabd \
    && mkdir -p /srv/artifacts \
    && chown -R nabd:nabd /srv

USER nabd

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
