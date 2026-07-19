"""Serialização CatalogEntry/execuções → JSON da UI (T18).

Responsabilidade deste módulo
    Projetar read-models do catálogo para dicts JSON estáveis da Management UI.

Motivo da separação
    Rotas FastAPI não conhecem detalhes de ``FileProgress``/labels.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from github_rag.catalog.models import (
    CatalogEntry,
    FileProgress,
    IndexingExecution,
    Progress,
)
from github_rag.sources.local.discovery import LocalDiscoveryIssue
from github_rag.ui.labels import state_label


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _progress_view(progress: Progress | None) -> dict[str, Any] | None:
    if progress is None:
        return None
    return {
        "percent": progress.percent,
        "files_processed": progress.files_processed,
        "files_total": progress.files_total,
        "current_stage": progress.current_stage,
    }


def repo_to_view(entry: CatalogEntry) -> dict[str, Any]:
    """CatalogEntry → RepoView JSON.

    Responsabilidade: listagem (origem, estado, progresso agregado).
    Motivo da separação: listagem ≠ detalhe com files[].
    """
    return {
        "id": entry.id,
        "connection_name": entry.connection_name,
        "origin": entry.origin.value,
        "repo_identifier": entry.repo_identifier,
        "state": entry.state.value,
        "state_label": state_label(entry.state),
        "progress": _progress_view(entry.progress),
    }


def file_progress_to_view(fp: FileProgress) -> dict[str, Any]:
    """FileProgress → flags booleanas por etapa (REQ-022).

    Responsabilidade: expor passagem Zoekt/Tree-sitter/metadados.
    Motivo da separação: timestamps internos ≠ flags de UI.
    """
    return {
        "path": fp.file_path,
        "zoekt": fp.zoekt_at is not None,
        "tree_sitter": fp.tree_sitter_at is not None,
        "metadata_persisted": fp.metadata_persisted_at is not None,
    }


def repo_to_detail(
    entry: CatalogEntry, files: Sequence[FileProgress]
) -> dict[str, Any]:
    """CatalogEntry + files → RepoDetailView.

    Responsabilidade: detalhe com progresso por arquivo.
    Motivo da separação: BDD-007 exige flags por path.
    """
    view = repo_to_view(entry)
    view["current_execution_id"] = entry.current_execution_id
    view["files"] = [file_progress_to_view(f) for f in files]
    return view


def execution_to_view(execution: IndexingExecution) -> dict[str, Any]:
    """IndexingExecution → ExecutionView (REQ-023).

    Responsabilidade: histórico com mensagem/horário de erro.
    Motivo da separação: auditoria distinta do estado corrente.
    """
    return {
        "id": execution.id,
        "status": execution.status.value,
        "started_at": execution.started_at.isoformat(),
        "finished_at": _iso(execution.finished_at),
        "error_message": execution.error_message,
        "error_at": _iso(execution.error_at),
        "commit_target": execution.commit_target,
    }


def issue_to_view(issue: LocalDiscoveryIssue) -> dict[str, str]:
    """LocalDiscoveryIssue → JSON UI (BDD-018 / T25).

    Responsabilidade: projetar connection_name/path/message sem extras.
    Motivo da separação: serialize ≠ store ≠ discovery.
    """
    return {
        "connection_name": issue.connection_name,
        "path": issue.path,
        "message": issue.message,
    }
