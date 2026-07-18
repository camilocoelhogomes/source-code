"""Testes unitários — T07 CatalogSync (extremos e corners)."""

from __future__ import annotations

import unittest

from github_rag.app.bootstrap import run_catalog_sync
from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin, RepoState
from github_rag.catalog.sync import CatalogSync, CatalogSyncError
from github_rag.sources.github.errors import GitHubDiscoveryError
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


class TestUT01SyncGitHub(unittest.TestCase):
    def test_github_repos_in_active_catalog(self) -> None:
        github = FakeGitHubDiscovery(
            {
                "github-microservices": [
                    gh_repo("my-org/microservice-auth", private=True),
                    gh_repo("my-org/user-api"),
                ]
            }
        )
        sync, catalog, _, _ = make_sync(github=github)
        result = sync.sync(github_config())
        ids = {e.repo_identifier for e in result.active}
        self.assertEqual(ids, {"my-org/microservice-auth", "my-org/user-api"})
        for entry in result.active:
            self.assertEqual(entry.origin, RepoOrigin.GITHUB)
            self.assertEqual(entry.connection_name, "github-microservices")
            self.assertEqual(entry.github_org, "my-org")
            self.assertEqual(entry.state, RepoState.NOT_INDEXED)


class TestUT02SyncLocal(unittest.TestCase):
    def test_local_repo_in_active_catalog(self) -> None:
        local = FakeLocalDiscovery(
            LocalDiscoveryResult(repos=(local_repo(),), issues=())
        )
        sync, _, _, _ = make_sync(
            github=FakeGitHubDiscovery(),
            local=local,
        )
        config = mixed_config()
        # só conexão git: usar config mista mas github vazio
        result = sync.sync(config)
        active_local = [e for e in result.active if e.origin == RepoOrigin.LOCAL]
        self.assertEqual(len(active_local), 1)
        entry = active_local[0]
        self.assertEqual(entry.connection_name, "local-microservices")
        self.assertEqual(entry.local_path, "/repos/svc-a")
        self.assertEqual(entry.repo_identifier, "svc-a")


class TestUT03MixedOrigins(unittest.TestCase):
    def test_mixed_origins_and_connections(self) -> None:
        github = FakeGitHubDiscovery(
            {"github-microservices": [gh_repo("my-org/svc")]}
        )
        local = FakeLocalDiscovery(
            LocalDiscoveryResult(repos=(local_repo(),), issues=())
        )
        sync, _, _, _ = make_sync(github=github, local=local)
        result = sync.sync(mixed_config())
        by_origin = {e.origin: e for e in result.active}
        self.assertEqual(set(by_origin), {RepoOrigin.GITHUB, RepoOrigin.LOCAL})
        self.assertEqual(by_origin[RepoOrigin.GITHUB].connection_name, "github-microservices")
        self.assertEqual(by_origin[RepoOrigin.LOCAL].connection_name, "local-microservices")


class TestUT04DeactivateAbsent(unittest.TestCase):
    def test_absent_repo_soft_deleted_state_preserved(self) -> None:
        catalog = InMemoryCatalogRepository()
        old = seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/old-service",
            state=RepoState.UP_TO_DATE,
            last_processed_commit="abc123",
        )
        github = FakeGitHubDiscovery(
            {"github-microservices": [gh_repo("my-org/new-service")]}
        )
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        result = sync.sync(github_config())
        active_ids = {e.repo_identifier for e in result.active}
        self.assertNotIn("my-org/old-service", active_ids)
        self.assertIn("my-org/new-service", active_ids)
        deactivated = catalog.get_repository(old.id)
        self.assertFalse(deactivated.active)
        self.assertEqual(deactivated.state, RepoState.UP_TO_DATE)
        self.assertEqual(deactivated.last_processed_commit, "abc123")
        self.assertNotEqual(deactivated.state.value, "indisponivel")


class TestUT05PreserveStateAndCommit(unittest.TestCase):
    def test_upsert_preserves_state_and_commit(self) -> None:
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
        result = sync.sync(github_config())
        entry = next(e for e in result.active if e.repo_identifier == "my-org/svc")
        self.assertEqual(entry.state, RepoState.UP_TO_DATE)
        self.assertEqual(entry.last_processed_commit, "abc")


class TestUT06ReactivateSoftDeleted(unittest.TestCase):
    def test_reactivate_preserves_error_state(self) -> None:
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
        result = sync.sync(github_config())
        active = next(e for e in result.active if e.repo_identifier == "my-org/svc")
        self.assertTrue(active.active)
        self.assertEqual(active.state, RepoState.ERROR)


class TestUT07AbortGitHubNoMutation(unittest.TestCase):
    def test_github_error_aborts_before_any_mutation(self) -> None:
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
        local = FakeLocalDiscovery(
            LocalDiscoveryResult(repos=(local_repo(),), issues=())
        )
        sync, _, _, loc = make_sync(catalog=catalog, github=github, local=local)
        with self.assertRaises(CatalogSyncError) as ctx:
            sync.sync(mixed_config())
        self.assertEqual(catalog.upsert_calls, 0)
        self.assertEqual(catalog.deactivate_calls, 0)
        self.assertEqual(loc.calls, 0)
        self.assertEqual(len(inner.list_active_catalog()), 1)
        self.assertIsInstance(ctx.exception.__cause__, GitHubDiscoveryError)


class TestUT08LocalIssuesNonFatal(unittest.TestCase):
    def test_local_issues_do_not_abort(self) -> None:
        issue = LocalDiscoveryIssue(
            connection_name="local-microservices",
            path="/repos/missing",
            message="volume inacessível",
        )
        local = FakeLocalDiscovery(
            LocalDiscoveryResult(repos=(local_repo(),), issues=(issue,))
        )
        sync, _, _, _ = make_sync(
            github=FakeGitHubDiscovery({"github-microservices": []}),
            local=local,
        )
        result = sync.sync(mixed_config())
        self.assertEqual(len(result.local_issues), 1)
        self.assertEqual(result.local_issues[0].path, "/repos/missing")
        self.assertTrue(any(e.repo_identifier == "svc-a" for e in result.active))


class TestUT09DoesNotIndex(unittest.TestCase):
    def test_sync_does_not_call_indexing_apis(self) -> None:
        catalog = RecordingCatalog()
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/svc")]})
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        result = sync.sync(github_config())
        self.assertEqual(catalog.forbidden_calls, [])
        self.assertEqual(result.active[0].state, RepoState.NOT_INDEXED)


class TestUT10EmptyConfigDeactivatesAll(unittest.TestCase):
    def test_empty_config_deactivates_all(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/svc",
        )
        sync, _, _, _ = make_sync(catalog=catalog)
        result = sync.sync(empty_config())
        self.assertEqual(result.active, ())
        self.assertEqual(len(result.deactivated), 1)


class TestUT11OnlyReq020States(unittest.TestCase):
    def test_only_allowed_states(self) -> None:
        allowed = {s.value for s in RepoState}
        catalog = InMemoryCatalogRepository()
        old = seed_active(
            catalog,
            connection_name="github-microservices",
            repo_identifier="my-org/old",
            state=RepoState.INDEXING,
        )
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/new")]})
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        result = sync.sync(github_config())
        for entry in (*result.active, *result.deactivated):
            self.assertIn(entry.state.value, allowed)
            self.assertNotIn(entry.state.value, {"indisponivel", "desatualizado", "unavailable"})
        deactivated = catalog.get_repository(old.id)
        self.assertFalse(deactivated.active)
        self.assertEqual(deactivated.state, RepoState.INDEXING)


class TestUT12Idempotent(unittest.TestCase):
    def test_second_sync_stable(self) -> None:
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/svc")]})
        sync, catalog, _, _ = make_sync(github=github)
        config = github_config()
        first = sync.sync(config)
        second = sync.sync(config)
        self.assertEqual(
            {e.repo_identifier for e in first.active},
            {e.repo_identifier for e in second.active},
        )
        e1 = catalog.list_active_catalog()[0]
        e2 = second.active[0]
        self.assertEqual(e1.state, e2.state)
        self.assertEqual(e1.repo_identifier, e2.repo_identifier)


class TestUT13TokenNotInError(unittest.TestCase):
    def test_catalog_sync_error_hides_token(self) -> None:
        github = FakeGitHubDiscovery(error=github_discovery_error())
        sync, _, _, _ = make_sync(github=github)
        with self.assertRaises(CatalogSyncError) as ctx:
            sync.sync(github_config())
        self.assertNotIn(SECRET_TOKEN_VALUE, str(ctx.exception))
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(ctx.exception))


class TestUT14BootstrapHelper(unittest.TestCase):
    def test_run_catalog_sync_delegates(self) -> None:
        catalog = RecordingCatalog()
        github = FakeGitHubDiscovery({"github-microservices": [gh_repo("my-org/svc")]})
        sync, _, _, _ = make_sync(catalog=catalog, github=github)
        result = run_catalog_sync(github_config(), sync)
        self.assertEqual(len(result.active), 1)
        self.assertEqual(catalog.forbidden_calls, [])


class TestUT15NoCrudSurface(unittest.TestCase):
    def test_no_definition_crud_methods(self) -> None:
        names = {n for n in dir(CatalogSync) if not n.startswith("_")}
        forbidden = {
            "create_connection",
            "update_connection",
            "delete_connection",
            "create_repo_definition",
            "update_repo_definition",
            "delete_repo_definition",
        }
        self.assertTrue(names.isdisjoint(forbidden))
        self.assertIn("sync", names)


class TestUT16MultipleGitHubConnections(unittest.TestCase):
    def test_two_github_connections(self) -> None:
        config = load_two_github_config()
        github = FakeGitHubDiscovery(
            {
                "gh-a": [gh_repo("org-a/a", connection_name="gh-a")],
                "gh-b": [gh_repo("org-b/b", connection_name="gh-b")],
            }
        )
        sync, _, gh, _ = make_sync(github=github)
        result = sync.sync(config)
        self.assertEqual({e.repo_identifier for e in result.active}, {"org-a/a", "org-b/b"})
        self.assertEqual(set(gh.calls), {"gh-a", "gh-b"})


class TestUT17SameFullNameDifferentConnections(unittest.TestCase):
    def test_same_full_name_distinct_connections(self) -> None:
        config = load_two_github_config()
        github = FakeGitHubDiscovery(
            {
                "gh-a": [gh_repo("my-org/svc", connection_name="gh-a")],
                "gh-b": [gh_repo("my-org/svc", connection_name="gh-b")],
            }
        )
        sync, _, _, _ = make_sync(github=github)
        result = sync.sync(config)
        self.assertEqual(len(result.active), 2)
        keys = {(e.connection_name, e.repo_identifier) for e in result.active}
        self.assertEqual(keys, {("gh-a", "my-org/svc"), ("gh-b", "my-org/svc")})


class TestUT18AbortBeforeLocalDiscovery(unittest.TestCase):
    def test_local_not_called_when_github_fails(self) -> None:
        github = FakeGitHubDiscovery(error=github_discovery_error())
        local = FakeLocalDiscovery()
        sync, _, _, loc = make_sync(github=github, local=local)
        with self.assertRaises(CatalogSyncError):
            sync.sync(mixed_config())
        self.assertEqual(loc.calls, 0)


def load_two_github_config():
    from tests.unit.catalog.sync_helpers import load_app_config, TOKEN_ENV_NAME

    return load_app_config(
        {
            "connections": {
                "gh-a": {
                    "type": "github",
                    "token": {"env": TOKEN_ENV_NAME},
                    "orgs": ["org-a"],
                    "repos": ["org-a/*"],
                    "revisions": {"branches": ["main"]},
                },
                "gh-b": {
                    "type": "github",
                    "token": {"env": TOKEN_ENV_NAME},
                    "orgs": ["org-b"],
                    "repos": ["org-b/*"],
                    "revisions": {"branches": ["main"]},
                },
            }
        }
    )


if __name__ == "__main__":
    unittest.main()
