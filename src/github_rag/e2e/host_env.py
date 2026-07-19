"""Env do app no host apontando para infra exposta pelo compose dev/e2e."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

_DEFAULT_HOST = "127.0.0.1"


def default_zoekt_index_dir(repo_root: Path, *, e2e: bool = False) -> Path:
    """Diretório host compartilhado com o serviço zoekt (bind mount)."""
    name = "e2e-zoekt-index" if e2e else "dev-zoekt-index"
    return (repo_root / ".data" / name).resolve()


def build_host_delivery_env(
    *,
    repo_root: Path,
    config_path: Path,
    repos_dir: Path,
    zoekt_index_dir: Path,
    zoekt_index_bin: str | None = None,
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Monta env para ``python -m github_rag.delivery`` no host.

    Responsabilidade
        URLs localhost alinhadas às portas publicadas em docker-compose.dev.yml.

    Motivo da separação
        Launcher e2e não duplica strings de wiring; testável sem Podman.
    """
    zoekt_index_dir.mkdir(parents=True, exist_ok=True)
    merged: dict[str, str] = dict(os.environ)
    host = merged.get("GITHUB_RAG_DEV_HOST", _DEFAULT_HOST).strip() or _DEFAULT_HOST
    merged.update(
        {
            "GITHUB_RAG_APP_ROOT": str(repo_root.resolve()),
            "CONFIG_PATH": str(config_path.resolve()),
            "DATABASE_URL": (
                f"postgresql+psycopg://github_rag:github_rag@{host}:5432/github_rag"
            ),
            "ZOEKT_URL": f"http://{host}:6070",
            "ZOEKT_INDEX_DIR": str(zoekt_index_dir.resolve()),
            "QDRANT_URL": f"http://{host}:6333",
            "OPENAI_BASE_URL": f"http://{host}:11434/v1",
            "OPENAI_API_KEY": merged.get("OPENAI_API_KEY", "local"),
            "SLM_MODEL": merged.get("SLM_MODEL", "qwen2.5-coder:3b"),
            "EMBEDDING_MODEL": merged.get("EMBEDDING_MODEL", "nomic-embed-text"),
            "EMBEDDING_DIMENSIONS": merged.get("EMBEDDING_DIMENSIONS", "768"),
            "UI_HOST": host,
            "UI_PORT": merged.get("UI_PORT", "8080"),
            "MCP_PORT": merged.get("MCP_PORT", "8001"),
            "MCP_TRANSPORT": merged.get("MCP_TRANSPORT", "sse"),
            "MCP_HOST": host,
            "INDEX_WORKERS": merged.get("INDEX_WORKERS", "2"),
            "QUERY_WORKERS": merged.get("QUERY_WORKERS", "4"),
            "INDEX_CRON": merged.get("INDEX_CRON", "0 2 * * *"),
        }
    )
    # file:// repos montados via fixture path no host (local-e2e-fixture)
    merged.setdefault("HOST_REPOS", str(repos_dir.resolve()))
    if zoekt_index_bin:
        merged["ZOEKT_INDEX_BIN"] = str(zoekt_index_bin)
    if extra:
        merged.update({k: str(v) for k, v in extra.items()})
    return merged
