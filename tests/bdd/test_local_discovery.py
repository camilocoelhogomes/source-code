"""
BDD executável — T06-local-discovery.

Valida BDD-016, BDD-018 e isolamento de falhas por conexão conforme design 0.1.0.

Execução:
    python -m pytest tests/bdd/test_local_discovery.py -q
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from github_rag.catalog.models import RepoOrigin
from github_rag.config.schema import _AppConfig, _GitConnection, _Revisions
from github_rag.sources.local.discovery import LocalRepoDiscovery


def _git_connection(url: str) -> _GitConnection:
    return _GitConnection(
        url=url,
        revisions=_Revisions(branches=("main",)),
    )


def _init_git_repo(path: Path, *, with_main: bool = True, branch: str = "main") -> None:
    """Cria repositório Git mínimo em filesystem para testes."""
    path.mkdir(parents=True, exist_ok=True)
    git_dir = path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")
    if with_main:
        ref_dir = git_dir / "refs" / "heads"
        ref_dir.mkdir(parents=True)
        (ref_dir / branch).write_text("deadbeef" * 5 + "\n", encoding="utf-8")


def _file_url(path: Path) -> str:
    return f"file://{path.resolve().as_posix()}"


class TestLocalDiscoveryBdd(unittest.TestCase):
    """Cenários LOC-01..06."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.mount = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_loc01_discover_valid_local_repos_with_main(self) -> None:
        """LOC-01 / BDD-016: repos locais válidos com origem local."""
        _init_git_repo(self.mount / "service-a")
        _init_git_repo(self.mount / "service-b")

        config = _AppConfig(
            connections={
                "local-microservices": _git_connection(f"{_file_url(self.mount)}/*"),
            }
        )
        result = LocalRepoDiscovery().discover(config)

        self.assertEqual(len(result.repos), 2)
        for repo in result.repos:
            self.assertEqual(repo.connection_name, "local-microservices")
            self.assertEqual(repo.origin, RepoOrigin.LOCAL)
            self.assertTrue(Path(repo.local_path).is_dir())
            self.assertIn(repo.repo_identifier, {"service-a", "service-b"})
        self.assertEqual(result.issues, ())

    def test_loc02_skip_non_git_and_missing_main(self) -> None:
        """LOC-02: somente Git válido + main; issues para inválidos."""
        _init_git_repo(self.mount / "valid")
        (self.mount / "plain-dir").mkdir()
        _init_git_repo(self.mount / "no-main", with_main=False)

        config = _AppConfig(
            connections={"local": _git_connection(f"{_file_url(self.mount)}/*")}
        )
        result = LocalRepoDiscovery().discover(config)

        self.assertEqual(len(result.repos), 1)
        self.assertEqual(result.repos[0].repo_identifier, "valid")
        self.assertGreaterEqual(len(result.issues), 2)

    def test_loc03_inaccessible_volume_registers_error(self) -> None:
        """LOC-03 / BDD-018: volume ausente → sem repos + issue."""
        missing = self.mount / "missing-volume"
        config = _AppConfig(
            connections={"local": _git_connection(f"{_file_url(missing)}/*")}
        )
        result = LocalRepoDiscovery().discover(config)

        self.assertEqual(result.repos, ())
        self.assertEqual(len(result.issues), 1)
        issue = result.issues[0]
        self.assertEqual(issue.connection_name, "local")
        self.assertIn("inaccessible", issue.message.lower())

    def test_loc04_failure_isolated_per_connection(self) -> None:
        """LOC-04: conexão ruim não impede conexão boa."""
        good_mount = self.mount / "good"
        good_mount.mkdir()
        _init_git_repo(good_mount / "repo")

        bad_mount = self.mount / "bad-missing"

        config = _AppConfig(
            connections={
                "bad": _git_connection(f"{_file_url(bad_mount)}/*"),
                "good": _git_connection(f"{_file_url(good_mount)}/*"),
            }
        )
        result = LocalRepoDiscovery().discover(config)

        self.assertEqual(len(result.repos), 1)
        self.assertEqual(result.repos[0].connection_name, "good")
        self.assertTrue(any(i.connection_name == "bad" for i in result.issues))

    def test_loc05_single_repo_without_glob(self) -> None:
        """LOC-05: URL file:// sem glob apontando para um repo."""
        repo_path = self.mount / "single-repo"
        _init_git_repo(repo_path)

        config = _AppConfig(
            connections={"local": _git_connection(_file_url(repo_path))}
        )
        result = LocalRepoDiscovery().discover(config)

        self.assertEqual(len(result.repos), 1)
        self.assertEqual(result.repos[0].repo_identifier, "single-repo")

    def test_loc06_github_connections_ignored(self) -> None:
        """LOC-06: somente type git é processado."""
        from github_rag.config.schema import (
            _EnvSecretRef,
            _GitHubConnection,
            _ResolvedSecret,
        )

        _init_git_repo(self.mount / "local-repo")
        github = _GitHubConnection(
            orgs=("org",),
            repos=("*",),
            token=_EnvSecretRef(env="GITHUB_TOKEN"),
            secret=_ResolvedSecret("token"),
            revisions=_Revisions(branches=("main",)),
        )
        config = _AppConfig(
            connections={
                "github-ms": github,
                "local-ms": _git_connection(f"{_file_url(self.mount)}/*"),
            }
        )
        result = LocalRepoDiscovery().discover(config)

        self.assertEqual(len(result.repos), 1)
        self.assertEqual(result.repos[0].connection_name, "local-ms")


if __name__ == "__main__":
    unittest.main()
