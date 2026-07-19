"""Serialização MCP ↔ DTOs T16/catálogo (T17).

Responsabilidade deste módulo
    Mapear ``include_*`` → ``DetailFields``, projetar evidências JSON e omitir
    nulls (BDD-012 / D-T17-005/007/008/010).

Motivo da separação
    Isola a política de envelope da borda MCP da orquestração das tools e do
    domínio ``QueryService`` (I-T17-005).
"""

from __future__ import annotations

import base64
from typing import Any

from github_rag.catalog.models import CatalogEntry
from github_rag.query.types import DetailFields, FileContent, QueryHit, TreeListing


def details_from_includes(
    *,
    include_repository: bool = False,
    include_path: bool = False,
    include_commit: bool = False,
    include_snippet: bool = False,
) -> DetailFields:
    """Args MCP ``include_*`` → ``DetailFields`` T16.

    Responsabilidade
        Traduzir intenção do agente na política BDD-012 / REQ-030.

    Motivo da separação
        Handlers não montam ``DetailFields`` ad hoc; um único mapeamento
        (I-T17-005).
    """
    return DetailFields(
        repository=include_repository,
        path=include_path,
        commit=include_commit,
        snippet=include_snippet,
    )


def omit_nulls(data: dict[str, Any]) -> dict[str, Any]:
    """Remove chaves cujo valor é ``None``.

    Responsabilidade
        Garantir omissão BDD-012 na borda JSON (não emitir ``null``).

    Motivo da separação
        Política de envelope isolada da lógica de tool.
    """
    out: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            out[key] = omit_nulls(value)
        elif isinstance(value, list):
            out[key] = [
                omit_nulls(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            out[key] = value
    return out


def repo_entry_to_dict(entry: CatalogEntry) -> dict[str, Any]:
    """``CatalogEntry`` → RepoEvidence MCP (I-T17-008).

    Responsabilidade
        Projetar catálogo ativo com estados REQ-020 e commits; sem
        ``local_path``/token.

    Motivo da separação
        ``list_repos`` não vaza montagens/segredos (BR-008 / MCP-10).
    """
    return {
        "repo_key": entry.repo_identifier,
        "repository_id": entry.id,
        "origin": entry.origin.value,
        "connection_name": entry.connection_name,
        "state": entry.state.value,
        "last_processed_commit": entry.last_processed_commit,
        "current_main_commit": entry.current_main_commit,
    }


def hit_to_dict(hit: QueryHit) -> dict[str, Any]:
    """``QueryHit`` → HitEvidence JSON (I-T17-005/010).

    Responsabilidade
        Envelope de hit: ``kind``/``score``/``line_number`` + quatro opcionais
        se não-None; nunca metadados de chunk/SLM.

    Motivo da separação
        Não vazar DTOs T10/T13; alinha omissão BDD-012 (MCP-02/03/09).
    """
    return omit_nulls(
        {
            "kind": hit.kind,
            "score": hit.score,
            "line_number": hit.line_number,
            "repository": hit.repository,
            "path": hit.path,
            "commit": hit.commit,
            "snippet": hit.snippet,
        }
    )


def file_to_dict(content: FileContent) -> dict[str, Any]:
    """``FileContent`` → FileEvidence (I-T17-007).

    Responsabilidade
        UTF-8 texto ou ``content_base64``; metadados opcionais omitidos se None.

    Motivo da separação
        Encoding fica na superfície MCP; T16 devolve ``bytes`` (MCP-11).
    """
    payload: dict[str, Any] = {
        "repository": content.repository,
        "path": content.path,
        "commit": content.commit,
    }
    try:
        text = content.content.decode("utf-8")
    except UnicodeDecodeError:
        payload["content_base64"] = base64.b64encode(content.content).decode("ascii")
        payload["content_encoding"] = "base64"
    else:
        payload["content"] = text
        payload["content_encoding"] = "utf-8"
    return omit_nulls(payload)


def tree_to_dict(tree: TreeListing) -> dict[str, Any]:
    """``TreeListing`` → JSON de ``list_tree``.

    Responsabilidade
        ``paths`` + ``repository``/``commit`` opcionais omitidos se None.

    Motivo da separação
        Mesmo envelope omit-null das demais tools.
    """
    return omit_nulls(
        {
            "paths": list(tree.paths),
            "repository": tree.repository,
            "commit": tree.commit,
        }
    )
