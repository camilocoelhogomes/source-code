# github-rag delivery image — primary platform: linux/amd64 (ENG-006)
# Build: docker build --platform linux/amd64 -t github-rag:local .
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="github-rag" \
      org.opencontainers.image.description="GitHub ETL / MCP / RAG delivery image" \
      org.opencontainers.image.platform="linux/amd64"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install runtime package + dependencies from pyproject.toml (no [dev] extras).
# ENG-009: never use a host virtualenv inside the image.
COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
COPY web ./web

RUN pip install --upgrade pip \
    && pip install .

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080 8001

CMD python -m github_rag.delivery
