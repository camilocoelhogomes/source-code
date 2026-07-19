"""Timeouts e retries canônicos do e2e (T21 / design §3.7).

Responsabilidade deste módulo
    Defaults de espera/retry compartilhados por launcher e Robot resources.

Motivo da separação
    Timeouts testáveis sem Podman; fonte única de verdade.
"""

from __future__ import annotations

COMPOSE_UP_HEALTHY_TIMEOUT_SECONDS: float = 600.0
INDEXING_TIMEOUT_SECONDS: float = 900.0
INDEXING_POLL_INTERVAL_SECONDS: float = 5.0
SEARCH_TIMEOUT_SECONDS: float = 60.0
SEARCH_HTTP_429_MAX_RETRIES: int = 3
GITHUB_RATE_LIMIT_MAX_RETRIES: int = 3
GITHUB_RATE_LIMIT_WAIT_MIN_SECONDS: float = 30.0
GITHUB_RATE_LIMIT_WAIT_MAX_SECONDS: float = 60.0
