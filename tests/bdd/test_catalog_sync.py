"""
BDD executável — T07-catalog-sync.

Valida BDD-001, BDD-016, BDD-021, BDD-023 e política de ausência
conforme design/interfaces 0.1.0.

Execução:
    python -m pytest tests/bdd/test_catalog_sync.py -q
"""

from __future__ import annotations

import unittest

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin, RepoState
from github_rag.catalog.sync import CatalogSync, CatalogSyncError
from github_rag.sources.local.discovery import LocalDiscoveryIssue, LocalDiscoveryResult
from tests.unit.catalog.sync_helpers import (
    SECRET_TOKEN_VALUE,
    FakeGitHubDiscovery,
    FakeLocalDiscovery,
    RecordingCatalog,
    empty_config,
    gh_repo,
    github_config,
    github_discovery_error,
    local_repo,
    make_sync,
    mixed_config,
    seed_active,
)


class TestCS01GitHubCatalog(unittest.TestCase):
    """CS-01 / BDD-001 — origem github + conexão no catálogo."""

    def test_github_origin_and_connection(self) -> None:
        github = FakeGitHubDiscovery(
            {
                "github-microservices": [
                    gh_repo("my-org/microservice-auth"),
                    gh_repo("my-org/user-api"),
                ]
            }
        )
        sync, _, _, _ = make_sync(github=github)
        result = sync.sync(github_config())
        names = {e.repo_identifier for e in result.active}
        self.assertEqual(names, {"my-org/microservice-auth", "my-org/user-api"})
        for entry in result.active:
            self.assertEqual(entry.origin, RepoOrigin.GITHUB)
            self.assertEqual(entry.connection_name, "github-microservices")
            self.assertEqual(entry.github_org, "my-org")


class TestCS02LocalCatalog(unittest.TestCase):
    """CS-02 / BDD-016 — origem local + conexão/path."""

    def test_local_origin_and_path(self) -> None:
        local = FakeLocalDiscovery(
            LocalDiscoveryResult(repos=(local_repo(),), issues=())
        )
        sync, _, _, _ = make_sync(local=local)
        result = sync.sync(mixed_config())
        entry = next(e for e in result.active if e.origin == RepoOrigin.LOCAL)
        self.assertEqual(entry.connection_name, "local-microservices")
        self.assertEqual(entry.local_path, "/repos/svc-a")
        self.assertEqual(entry.repo_identifier, "svc-a")


class TestCS03MixedConfig(unittest.TestCase):
    """CS-03 / BDD-021 — conexão e origem identificadas."""

    def test_mixed_identified_by_connection_and_origin(self) -> None:
        github = FakeGitHubDiscovery(
            {"github-microservices": [gh_repo("my-org/svc")]}
        )
        local = FakeLocalDiscovery(
            LocalDiscoveryResult(repos=(local_repo(),), issues=())
        )
        sync, _, _, _ = make_sync(github=github, local=local)
        result = sync.sync(mixed_config())
        self.assertEqual(len(result.active), 2)
        origins = {e.origin for e in result.active}
        self.assertEqual(origins, {RepoOrigin.GITHUB, RepoOrigin.LOCAL})


class TestCS04NoCrud(unittest.TestCase):
    """CS-04 / BDD-023 — sem CRUD de definições."""

    def test_public_surface_is_sync_only(self) -> None:
        public = {n for n in dir(CatalogSync) if not n.startswith("_")}
        self.assertIn("sync", public)
        for name in (
            "create_connection",
            "delete_connection",
            "update_repo_definition",
        ):
            self.assertNotIn(name, public)


class TestCS05DeactivateAbsent(unittest.TestCase):
    """CS-05 — ausente sai do catálogo ativo; estado REQ-020."""

    def test_absent_not_listable_state_preserved(self) -> None:
        catalog = InMemoryCatalogRepository()
        old = seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/old-service",
            state=RepoState.UP_TO_DATE,
            last_processed_commit="deadbeef",
        )
        github = FakeGitHubDiscovery(
            {"github-microservices": [gh_repo("my-org/kept")]}
        )
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        result = sync.sync(github_config())
        self.assertNotIn(
            "my-org/old-service", {e.repo_identifier for e in result.active}
        )
        gone = catalog.get_repository(old.id)
        self.assertFalse(gone.active)
        self.assertEqual(gone.state, RepoState.UP_TO_DATE)


class TestCS06PreserveCommits(unittest.TestCase):
    """CS-06 — upsert não reprocessa commits."""

    def test_preserves_commit(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/svc",
            state=RepoState.UP_TO_DATE,
            last_processed_commit="abc",
        )
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/svc")]})
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        entry = sync.sync(github_config()).active[0]
        self.assertEqual(entry.last_processed_commit, "abc")
        self.assertEqual(entry.state, RepoState.UP_TO_DATE)


class TestCS07Reactivate(unittest.TestCase):
    """CS-07 — reativação preserva estado."""

    def test_reactivate(self) -> None:
        catalog = InMemoryCatalogRepository()
        entry = seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/svc",
            state=RepoState.ERROR,
        )
        catalog.deactivate_repository(entry.id)
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/svc")]})
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        active = sync.sync(github_config()).active[0]
        self.assertTrue(active.active)
        self.assertEqual(active.state, RepoState.ERROR)


class TestCS08AbortNoMutation(unittest.TestCase):
    """CS-08 / S-01 — falha GitHub sem upsert/deactivate."""

    def test_abort_before_mutation(self) -> None:
        inner = InMemoryCatalogRepository()
        seed_active(
            inner,
            connection_name="github-microservices",
            repo_identifier="my-org/existing",
        )
        catalog = RecordingCatalog(inner)
        catalog.upsert_calls = 0
        catalog.deactivate_calls = 0
        github = FakeGitHubDiscovery(error=github_discovery_error())
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        with self.assertRaises(CatalogSyncError) as ctx:
            sync.sync(github_config())
        self.assertEqual(catalog.upsert_calls, 0)
        self.assertEqual(catalog.deactivate_calls, 0)
        self.assertNotIn(SECRET_TOKEN_VALUE, str(ctx.exception))
        self.assertEqual(len(inner.list_active_catalog()), 1)


class TestCS09LocalIssues(unittest.TestCase):
    """CS-09 — issues locais não abortam."""

    def test_issues_in_result(self) -> None:
        issue = LocalDiscoveryIssue("local-microservices", "/x", "erro")
        local = FakeLocalDiscovery(
            LocalDiscoveryResult(repos=(local_repo(),), issues=(issue,))
        )
        sync, _, _, _ = make_sync(local=local)
        result = sync.sync(mixed_config())
        self.assertEqual(result.local_issues, (issue,))
        self.assertTrue(any(e.origin == RepoOrigin.LOCAL for e in result.active))


class TestCS10NoIndexing(unittest.TestCase):
    """CS-10 — sync não indexa."""

    def test_no_indexing_side_effects(self) -> None:
        catalog = RecordingCatalog()
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/svc")]})
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        result = sync.sync(github_config())
        self.assertEqual(catalog.forbidden_calls, [])
        self.assertEqual(result.active[0].state, RepoState.NOT_INDEXED)


class TestCS11EmptyConfig(unittest.TestCase):
    """CS-11 — config vazia desativa todos."""

    def test_empty_deactivates(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/svc",
        )
        sync, _, _, _ = make_sync(catalog=catalog)
        result = sync.sync(empty_config())
        self.assertEqual(result.active, ())
        self.assertTrue(result.deactivated)


class TestCS12Req020Only(unittest.TestCase):
    """CS-12 — somente estados REQ-020."""

    def test_closed_enum(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/old",
            state=RepoState.INDEXING,
        )
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/new")]})
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        result = sync.sync(github_config())
        allowed = {s.value for s in RepoState}
        for entry in (*result.active, *result.deactivated):
            self.assertIn(entry.state.value, allowed)


if __name__ == "__main__":
    unittest.main()
