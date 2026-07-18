"""Helpers — testes T07 catalog sync."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from unittest import mock

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import CatalogEntry, RepoOrigin, RepoState
from github_rag.catalog.repository import CatalogRepository
from github_rag.catalog.sync import CatalogSync
from github_rag.config import AppConfig, ConfigLoader
from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import DiscoveredGitHubRepo
from github_rag.sources.local.discovery import (
    DiscoveredLocalRepo,
    LocalDiscoveryIssue,
    LocalDiscoveryResult,
)

SECRET_TOKEN_VALUE = "bdd-catalog-sync-secret-token-do-not-leak"
TOKEN_ENV_NAME = "GITHUB_TOKEN"


class FakeGitHubDiscovery:
    """Discovery GitHub controlada para testes."""

    def __init__(
        self,
        repos_by_connection: dict[str, Sequence[DiscoveredGitHubRepo]] | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self._repos_by_connection = dict(repos_by_connection or {})
        self._error = error
        self.calls: list[str] = []

    def discover(self, connection_name: str, connection: object) -> tuple[DiscoveredGitHubRepo, ...]:
        self.calls.append(connection_name)
        if self._error is not None:
            raise self._error
        return tuple(self._repos_by_connection.get(connection_name, ()))


class FakeLocalDiscovery:
    """Discovery local controlada para testes."""

    def __init__(self, result: LocalDiscoveryResult | None = None) -> None:
        self._result = result or LocalDiscoveryResult(repos=(), issues=())
        self.calls: int = 0

    def discover(self, config: AppConfig) -> LocalDiscoveryResult:
        self.calls += 1
        return self._result


class RecordingCatalog:
    """Proxy que registra mutações sobre ``InMemoryCatalogRepository``."""

    def __init__(self, inner: InMemoryCatalogRepository | None = None) -> None:
        self._inner = inner or InMemoryCatalogRepository()
        self.upsert_calls = 0
        self.deactivate_calls = 0
        self.forbidden_calls: list[str] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def upsert_repository(self, **kwargs: Any) -> CatalogEntry:
        self.upsert_calls += 1
        return self._inner.upsert_repository(**kwargs)

    def deactivate_repository(self, repository_id: int) -> CatalogEntry:
        self.deactivate_calls += 1
        return self._inner.deactivate_repository(repository_id)

    def mark_queued(self, repository_id: int) -> CatalogEntry:
        self.forbidden_calls.append("mark_queued")
        return self._inner.mark_queued(repository_id)

    def mark_indexing(self, repository_id: int) -> CatalogEntry:
        self.forbidden_calls.append("mark_indexing")
        return self._inner.mark_indexing(repository_id)

    def mark_updated(self, repository_id: int, commit: str) -> CatalogEntry:
        self.forbidden_calls.append("mark_updated")
        return self._inner.mark_updated(repository_id, commit)

    def mark_error(self, repository_id: int, message: str, error_at: Any) -> CatalogEntry:
        self.forbidden_calls.append("mark_error")
        return self._inner.mark_error(repository_id, message, error_at)

    def start_execution(self, repository_id: int, commit_target: str) -> Any:
        self.forbidden_calls.append("start_execution")
        return self._inner.start_execution(repository_id, commit_target)

    def reconcile_repository(self, repository_id: int) -> CatalogEntry:
        self.forbidden_calls.append("reconcile_repository")
        return self._inner.reconcile_repository(repository_id)


def load_app_config(payload: dict[str, Any], *, token_value: str = SECRET_TOKEN_VALUE) -> AppConfig:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with mock.patch.dict("os.environ", {TOKEN_ENV_NAME: token_value}, clear=False):
            return ConfigLoader().load(path)


def github_config(
    *,
    connection_name: str = "github-microservices",
    orgs: list[str] | None = None,
    repos: list[str] | None = None,
) -> AppConfig:
    return load_app_config(
        {
            "connections": {
                connection_name: {
                    "type": "github",
                    "token": {"env": TOKEN_ENV_NAME},
                    "orgs": orgs or ["my-org"],
                    "repos": repos or ["my-org/*"],
                    "revisions": {"branches": ["main"]},
                }
            }
        }
    )


def mixed_config() -> AppConfig:
    return load_app_config(
        {
            "connections": {
                "github-microservices": {
                    "type": "github",
                    "token": {"env": TOKEN_ENV_NAME},
                    "orgs": ["my-org"],
                    "repos": ["my-org/*"],
                    "revisions": {"branches": ["main"]},
                },
                "local-microservices": {
                    "type": "git",
                    "url": "file:///repos/*",
                    "revisions": {"branches": ["main"]},
                },
            }
        }
    )


def empty_config() -> AppConfig:
    return load_app_config({"connections": {}})


def gh_repo(
    full_name: str,
    *,
    connection_name: str = "github-microservices",
    private: bool = False,
) -> DiscoveredGitHubRepo:
    org, name = full_name.split("/", 1)
    return DiscoveredGitHubRepo(
        connection_name=connection_name,
        full_name=full_name,
        org=org,
        name=name,
        private=private,
    )


def local_repo(
    *,
    connection_name: str = "local-microservices",
    local_path: str = "/repos/svc-a",
    repo_identifier: str = "svc-a",
) -> DiscoveredLocalRepo:
    return DiscoveredLocalRepo(
        connection_name=connection_name,
        local_path=local_path,
        repo_identifier=repo_identifier,
        origin=RepoOrigin.LOCAL,
    )


def make_sync(
    *,
    catalog: CatalogRepository | RecordingCatalog | None = None,
    github: FakeGitHubDiscovery | None = None,
    local: FakeLocalDiscovery | None = None,
) -> tuple[CatalogSync, CatalogRepository | RecordingCatalog, FakeGitHubDiscovery, FakeLocalDiscovery]:
    cat = catalog if catalog is not None else InMemoryCatalogRepository()
    gh = github if github is not None else FakeGitHubDiscovery()
    loc = local if local is not None else FakeLocalDiscovery()
    sync = CatalogSync(catalog=cat, github_discovery=gh, local_discovery=loc)  # type: ignore[arg-type]
    return sync, cat, gh, loc


def seed_active(
    catalog: InMemoryCatalogRepository | RecordingCatalog,
    *,
    connection_name: str,
    repo_identifier: str,
    origin: RepoOrigin = RepoOrigin.GITHUB,
    github_org: str | None = "my-org",
    local_path: str | None = None,
    state: RepoState = RepoState.NOT_INDEXED,
    last_processed_commit: str | None = None,
) -> CatalogEntry:
    entry = catalog.upsert_repository(
        connection_name=connection_name,
        origin=origin,
        repo_identifier=repo_identifier,
        github_org=github_org,
        local_path=local_path,
    )
    if state != RepoState.NOT_INDEXED or last_processed_commit is not None:
        # Atalho de teste: mutação direta via API pública quando possível.
        if state == RepoState.QUEUED:
            entry = catalog.mark_queued(entry.id)
        elif state == RepoState.UP_TO_DATE and last_processed_commit:
            entry = catalog.mark_queued(entry.id)
            entry = catalog.mark_indexing(entry.id)
            entry = catalog.mark_updated(entry.id, last_processed_commit)
        elif state == RepoState.ERROR:
            entry = catalog.mark_queued(entry.id)
            entry = catalog.mark_indexing(entry.id)
            from datetime import datetime, timezone

            entry = catalog.mark_error(
                entry.id, "seed", datetime.now(timezone.utc)
            )
        elif state == RepoState.INDEXING:
            entry = catalog.mark_queued(entry.id)
            entry = catalog.mark_indexing(entry.id)
    return catalog.get_repository(entry.id)


def github_discovery_error() -> GitHubDiscoveryError:
    return GitHubDiscoveryError(
        f"acesso negado ao listar org (HTTP 401); token={SECRET_TOKEN_VALUE}"
    )
