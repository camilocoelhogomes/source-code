"""Entry alternativo MCP stdio (Cursor via ``docker compose run -i``).

Responsabilidade
    Subir wiring mínimo e chamar ``McpEvidenceServer.run(transport=\"stdio\")``.

Motivo da separação
    Compose default usa SSE/HTTP + healthcheck (I-T19-015); stdio é caminho
    operacional distinto sem alterar tools T17 (D-T19-007). Não faz bind UI.
"""

from __future__ import annotations

import logging
import os
import sys

from github_rag.concurrency import create_query_limiter
from github_rag.config import ConfigLoader
from github_rag.config.secrets import EnvironSecretResolver
from github_rag.delivery.wiring import wire_catalog, wire_query_service
from github_rag.mcp import DefaultMcpEvidenceServer
from github_rag.settings import load_settings

_LOG = logging.getLogger(__name__)


def main() -> None:
    """Boot mínimo para superfície MCP em transport stdio (sem UI)."""
    environ = os.environ
    try:
        settings = load_settings(environ)
        loader = ConfigLoader(
            secret_resolver=EnvironSecretResolver(environ)
        )
        loader.load(settings.config_path)
        catalog = wire_catalog(environ)
        query = wire_query_service(
            environ, catalog=catalog, settings=settings
        )
        server = DefaultMcpEvidenceServer(
            catalog=catalog,
            query=query,
            query_limiter=create_query_limiter(settings),
        )
        server.run(transport="stdio")
    except SystemExit:
        raise
    except BaseException as exc:
        _LOG.error(
            "delivery_mcp_stdio_failed error_type=%s", type(exc).__name__
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
    sys.exit(0)
