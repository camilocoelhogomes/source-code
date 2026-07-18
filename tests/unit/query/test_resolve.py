"""Unit — resolve de catálogo/commit (T16 / UT-Z02)."""

from __future__ import annotations

import unittest

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin
from github_rag.query.errors import (
    QueryCommitUnavailableError,
    QueryRepositoryNotFoundError,
    QueryValidationError,
)
from github_rag.query.fake import FakeSnapshotSourceResolver
from github_rag.query.resolve import resolve_browse_commit, resolve_catalog_entry
from github_rag.snapshot.models import LocalSnapshotSource


class TestResolve(unittest.TestCase):
    def test_resolve_by_key_and_id(self) -> None:
        catalog = InMemoryCatalogRepository()
        entry = catalog.upsert_repository(
            connection_name="gh",
            origin=RepoOrigin.LOCAL,
            repo_identifier="local/api",
            local_path="/repos/api",
        )
        found = resolve_catalog_entry(
            catalog,
            repo_key="local/api",
            repository_id=None,
            require_scope=True,
        )
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.id, entry.id)

        found_id = resolve_catalog_entry(
            catalog,
            repo_key=None,
            repository_id=entry.id,
            require_scope=True,
        )
        self.assertEqual(found_id.id, entry.id)

    def test_multi_repo_none(self) -> None:
        catalog = InMemoryCatalogRepository()
        self.assertIsNone(
            resolve_catalog_entry(
                catalog,
                repo_key=None,
                repository_id=None,
                require_scope=False,
            )
        )
        with self.assertRaises(QueryValidationError):
            resolve_catalog_entry(
                catalog,
                repo_key=None,
                repository_id=None,
                require_scope=True,
            )

    def test_browse_commit(self) -> None:
        catalog = InMemoryCatalogRepository()
        entry = catalog.upsert_repository(
            connection_name="gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/api",
            github_org="acme",
        )
        with self.assertRaises(QueryCommitUnavailableError):
            resolve_browse_commit(entry, commit_sha=None)
        self.assertEqual(
            resolve_browse_commit(entry, commit_sha="deadbeef"), "deadbeef"
        )

        catalog.mark_queued(entry.id)
        catalog.mark_indexing(entry.id)
        updated = catalog.mark_updated(entry.id, "abc123")
        self.assertEqual(
            resolve_browse_commit(updated, commit_sha=None), "abc123"
        )

    def test_inactive_and_missing(self) -> None:
        catalog = InMemoryCatalogRepository()
        entry = catalog.upsert_repository(
            connection_name="gh",
            origin=RepoOrigin.GITHUB,
            repo_identifier="acme/api",
            github_org="acme",
        )
        catalog.deactivate_repository(entry.id)
        with self.assertRaises(QueryRepositoryNotFoundError):
            resolve_catalog_entry(
                catalog,
                repo_key=None,
                repository_id=entry.id,
                require_scope=True,
            )
        with self.assertRaises(QueryRepositoryNotFoundError):
            resolve_catalog_entry(
                catalog,
                repo_key="acme/api",
                repository_id=None,
                require_scope=True,
            )

    def test_fake_resolver(self) -> None:
        catalog = InMemoryCatalogRepository()
        entry = catalog.upsert_repository(
            connection_name="local",
            origin=RepoOrigin.LOCAL,
            repo_identifier="local/api",
            local_path="/repos/api",
        )
        source = FakeSnapshotSourceResolver().resolve(entry)
        self.assertIsInstance(source, LocalSnapshotSource)
        assert isinstance(source, LocalSnapshotSource)
        self.assertEqual(source.local_path, "/repos/api")


if __name__ == "__main__":
    unittest.main()
