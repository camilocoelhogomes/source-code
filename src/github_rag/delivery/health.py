"""Readiness HTTP de entrega (T19).

Responsabilidade deste módulo
    Payload e registro de ``GET /healthz`` sem dados de domínio/segredos.

Motivo da separação
    Probe de compose isolado das rotas ``/api`` da T18 (I-T19-007).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypedDict


class HealthzBody(TypedDict):
    status: str
    ui: str
    mcp: str


def healthz_payload(*, ui_ready: bool, mcp_ready: bool) -> HealthzBody:
    """Monta o JSON de ``GET /healthz``.

    Responsabilidade
        Expor readiness mínimo UI+MCP sem catálogo/código/token.

    Motivo da separação
        Contrato de observabilidade (compose healthcheck) isolado do domain
        e das rotas ``/api`` da T18 (I-T19-007).
    """
    if ui_ready and mcp_ready:
        return {"status": "ok", "ui": "ready", "mcp": "ready"}
    return {
        "status": "starting",
        "ui": "ready" if ui_ready else "not_ready",
        "mcp": "ready" if mcp_ready else "not_ready",
    }


def register_health_routes(app: Any, *, get_state: Callable[[], Any]) -> None:
    """Registra ``GET /healthz`` no FastAPI da UI.

    Responsabilidade
        Responder 200 só quando UI e MCP estiverem ready pós-boot; payload
        via ``healthz_payload``.

    Motivo da separação
        Composition root adiciona probe de entrega sem alterar contratos T18
        de gestão/busca.
    """
    from fastapi.responses import JSONResponse

    @app.get("/healthz")
    def healthz() -> Any:
        state = get_state()
        if isinstance(state, Mapping):
            ui_ready = bool(state.get("ui_ready"))
            mcp_ready = bool(state.get("mcp_ready"))
        else:
            ui_ready = bool(getattr(state, "ui_ready", False))
            mcp_ready = bool(getattr(state, "mcp_ready", False))
        body = healthz_payload(ui_ready=ui_ready, mcp_ready=mcp_ready)
        if body["status"] == "ok":
            return body
        return JSONResponse(status_code=503, content=body)
