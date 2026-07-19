"""Resolução de escopo de repositório e commit para QueryService (T16).

Responsabilidade deste módulo
    Localizar CatalogEntry por id/repo_key e resolver commit de browse.

Motivo da separação
    Isola regras I-T16-005/012 da orquestração de busca/browse.
"""

from __future__ import annotations

from github_rag.catalog.errors import RepositoryNotFoundError
from github_rag.catalog.models import CatalogEntry
from github_rag.catalog.repository import CatalogRepository
from github_rag.query.errors import (
    QueryCommitUnavailableError,
    QueryRepositoryNotFoundError,
    QueryValidationError,
)


def resolve_catalog_entry(
    catalog: CatalogRepository,
    *,
    repo_key: str | None,
    repository_id: int | None,
    require_scope: bool,
) -> CatalogEntry | None:
    """Resolve entrada ativa do catálogo.

    Returns
        ``None`` quando escopo multi-repo é permitido e nenhum id/key foi dado.
    """
    if repo_key is None and repository_id is None:
        if require_scope:
            raise QueryValidationError(
                "browse exige repo_key ou repository_id"
            )
        return None

    entry_by_id: CatalogEntry | None = None
    if repository_id is not None:
        try:
            entry_by_id = catalog.get_repository(repository_id)
        except RepositoryNotFoundError as exc:
            raise QueryRepositoryNotFoundError(
                f"repositório inexistente: id={repository_id}"
            ) from exc
        if not entry_by_id.active:
            raise QueryRepositoryNotFoundError(
                f"repositório inativo: id={repository_id}"
            )

    entry_by_key: CatalogEntry | None = None
    if repo_key is not None:
        for entry in catalog.list_active_catalog():
            if entry.repo_identifier == repo_key:
                entry_by_key = entry
                break
        if entry_by_key is None:
            raise QueryRepositoryNotFoundError(
                f"repositório inexistente ou inativo: key={repo_key}"
            )

    if entry_by_id is not None and entry_by_key is not None:
        if entry_by_id.id != entry_by_key.id:
            raise QueryValidationError(
                "repo_key e repository_id referem repositórios distintos"
            )
        return entry_by_id

    return entry_by_id if entry_by_id is not None else entry_by_key


def resolve_browse_commit(
    entry: CatalogEntry,
    *,
    commit_sha: str | None,
) -> str:
    """Resolve SHA de browse: explícito ou last_processed_commit."""
    if commit_sha is not None and commit_sha.strip() != "":
        return commit_sha
    if entry.last_processed_commit is None:
        raise QueryCommitUnavailableError(
            "commit indisponível: sem commit_sha e sem last_processed_commit"
        )
    return entry.last_processed_commit
