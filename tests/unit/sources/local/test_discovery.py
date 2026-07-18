"""Testes unitários de LocalRepoDiscovery (T06)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from github_rag.catalog.models import RepoOrigin
from github_rag.config.schema import _AppConfig, _GitConnection, _Revisions
from github_rag.sources.local.discovery import LocalRepoDiscovery
from github_rag.sources.local.git_fs import (
    GitFilesystemInspector,
    ParsedFileUrl,
    RepoInspection,
)


def _git_conn(url: str) -> _GitConnection:
    return _GitConnection(url=url, revisions=_Revisions(branches=("main",)))


class TestLocalRepoDiscovery(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.mount = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_discover_connection_happy_glob(self) -> None:
        repo = self.mount / "svc"
        repo.mkdir()
        inspector = mock.create_autospec(GitFilesystemInspector, instance=True)
        inspector.parse_file_url.return_value = ParsedFileUrl(self.mount, "*")
        inspector.is_accessible.return_value = True
        inspector.expand_candidates.return_value = [repo]
        inspector.inspect_repo.return_value = RepoInspection(True, True)

        discovery = LocalRepoDiscovery(inspector)
        result = discovery.discover_connection("local", _git_conn("file:///mnt/*"))

        self.assertEqual(len(result.repos), 1)
        self.assertEqual(result.repos[0].origin, RepoOrigin.LOCAL)
        self.assertEqual(result.repos[0].repo_identifier, "svc")

    def test_inaccessible_base_yields_issue(self) -> None:
        inspector = mock.create_autospec(GitFilesystemInspector, instance=True)
        inspector.parse_file_url.return_value = ParsedFileUrl(Path("/missing"), "*")
        inspector.is_accessible.return_value = False

        result = LocalRepoDiscovery(inspector).discover_connection(
            "local", _git_conn("file:///missing/*")
        )
        self.assertEqual(result.repos, ())
        self.assertEqual(len(result.issues), 1)

    def test_invalid_path_issue_valid_remains(self) -> None:
        good = self.mount / "good"
        bad = self.mount / "bad"
        inspector = mock.create_autospec(GitFilesystemInspector, instance=True)
        inspector.parse_file_url.return_value = ParsedFileUrl(self.mount, "*")
        inspector.is_accessible.return_value = True
        inspector.expand_candidates.return_value = [good, bad]

        def inspect(path: Path) -> RepoInspection:
            if path == good:
                return RepoInspection(True, True)
            return RepoInspection(False, False, reason="not a git repository")

        inspector.inspect_repo.side_effect = inspect

        result = LocalRepoDiscovery(inspector).discover_connection(
            "local", _git_conn("file:///mnt/*")
        )
        self.assertEqual(len(result.repos), 1)
        self.assertEqual(len(result.issues), 1)

    def test_discover_multiple_git_connections(self) -> None:
        config = _AppConfig(
            connections={
                "a": _git_conn("file:///a/*"),
                "b": _git_conn("file:///b/*"),
            }
        )
        discovery = LocalRepoDiscovery()
        with mock.patch.object(
            discovery,
            "discover_connection",
            side_effect=[
                type("R", (), {"repos": (), "issues": ()})(),
                type(
                    "R",
                    (),
                    {
                        "repos": (
                            type(
                                "Repo",
                                (),
                                {
                                    "connection_name": "b",
                                    "origin": RepoOrigin.LOCAL,
                                    "local_path": "/b/x",
                                    "repo_identifier": "x",
                                },
                            )(),
                        ),
                        "issues": (),
                    },
                )(),
            ],
        ) as mocked:
            result = discovery.discover(config)
            self.assertEqual(mocked.call_count, 2)
            self.assertEqual(len(result.repos), 1)

    def test_discover_ignores_github(self) -> None:
        from github_rag.config.schema import (
            _EnvSecretRef,
            _GitHubConnection,
            _ResolvedSecret,
        )

        gh = _GitHubConnection(
            orgs=("o",),
            repos=(),
            token=_EnvSecretRef(env="T"),
            secret=_ResolvedSecret("t"),
            revisions=_Revisions(branches=("main",)),
        )
        config = _AppConfig(connections={"gh": gh, "loc": _git_conn("file:///x")})
        discovery = LocalRepoDiscovery()
        with mock.patch.object(
            discovery, "discover_connection", return_value=mock.Mock(repos=(), issues=())
        ) as mocked:
            discovery.discover(config)
            mocked.assert_called_once()
            self.assertEqual(mocked.call_args[0][0], "loc")

    def test_uses_injected_inspector_default(self) -> None:
        inspector = GitFilesystemInspector()
        discovery = LocalRepoDiscovery(inspector)
        self.assertIs(discovery._inspector, inspector)

    def test_discover_connection_invalid_url_issue(self) -> None:
        result = LocalRepoDiscovery().discover_connection(
            "local", _git_conn("https://not-file/x")
        )
        self.assertEqual(result.repos, ())
        self.assertEqual(len(result.issues), 1)

    def test_discover_connection_empty_glob_match_issue(self) -> None:
        empty = self.mount / "empty"
        empty.mkdir()
        url = f"file://{empty.resolve().as_posix()}/*"
        result = LocalRepoDiscovery().discover_connection("local", _git_conn(url))
        self.assertEqual(result.repos, ())
        self.assertTrue(any("no matching" in i.message for i in result.issues))


if __name__ == "__main__":
    unittest.main()
