"""UI de gestão e busca (T18) — FastAPI + frontend estático.

Responsabilidade deste pacote
    ``ManagementUiApi`` / ``DefaultManagementUiApi``: listagem, indexação,
    progresso, cron e buscas exact/semantic — sem CRUD de config/token.

Motivo da separação
    Superfície ENG-001 / BR-017 distinta de MCP (T17) e do domínio de índices.
"""

from github_rag.ui.api import DefaultManagementUiApi, default_web_root
from github_rag.ui.labels import STATE_LABELS, state_label
from github_rag.ui.ports import ManagementUiApi

__all__ = [
    "DefaultManagementUiApi",
    "ManagementUiApi",
    "STATE_LABELS",
    "default_web_root",
    "state_label",
]
