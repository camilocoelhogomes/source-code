"""
BDD executável — T20 conformidade GitPython (DT-001 / BDD-024 parcial).

Cenários T20-SDK-01..03. Regressão BDD-016/018 permanece em
tests/bdd/test_local_discovery.py.

Execução:
    python -m pytest tests/bdd/test_local_discovery_git_sdk.py -q
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from git import Repo

from github_rag.config.schema import _AppConfig, _GitConnection, _Revisions
from github_rag.sources.local import git_fs
from github_rag.sources.local.discovery import LocalRepoDiscovery
from github_rag.sources.local.git_fs import GitFilesystemInspector


def _git_connection(url: str) -> _GitConnection:
    return _GitConnection(
        url=url,
        revisions=_Revisions(branches=("main",)),
    )


def _file_url(path: Path) -> str:
    return f"file://{path.resolve().as_posix()}"


def _init_real_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    (path / "README").write_text("ok", encoding="utf-8")
    repo.index.add(["README"])
    repo.index.commit("init")
    if "main" not in repo.heads:
        repo.create_head("main")
    repo.heads.main.checkout()
    repo.close()


class TestLocalDiscoveryGitSdkBdd(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.mount = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_t20_sdk01_production_uses_gitpython_no_adhoc_parse(self) -> None:
        """T20-SDK-01: GitPython + zero parse ad-hoc; bare rejeitado."""
        source = inspect.getsource(git_fs)
        self.assertRegex(
            source,
            r"from\s+git\s+import\s+Repo\b|from\s+git\.repo\s+import\s+Repo\b",
            msg="production must import GitPython Repo (not only RepoInspection)",
        )
        self.assertRegex(source, r"with\s+Repo\s*\(")
        self.assertNotIn("packed-refs", source)
        self.assertNotIn("_resolve_git_dir", source)
        self.assertNotIn("_has_main_branch", source)

        _init_real_repo(self.mount / "svc")
        bare = self.mount / "bare.git"
        with Repo(self.mount / "svc") as donor:
            donor.clone(bare, bare=True)

        inspector = GitFilesystemInspector()
        self.assertTrue(inspector.inspect_repo(self.mount / "svc").is_valid_candidate)
        bare_result = inspector.inspect_repo(bare)
        self.assertFalse(bare_result.is_valid_candidate)
        self.assertEqual(bare_result.reason, "not a git repository")

        config = _AppConfig(
            connections={"local": _git_connection(f"{_file_url(self.mount)}/*")}
        )
        result = LocalRepoDiscovery().discover(config)
        ids = {r.repo_identifier for r in result.repos}
        self.assertIn("svc", ids)
        self.assertNotIn("bare.git", ids)

    def test_t20_sdk02_main_only_in_packed_refs(self) -> None:
        """T20-SDK-02: main só em packed-refs via SDK."""
        repo_path = self.mount / "packed"
        _init_real_repo(repo_path)
        main_ref = repo_path / ".git" / "refs" / "heads" / "main"
        sha = main_ref.read_text(encoding="utf-8").strip()
        packed = repo_path / ".git" / "packed-refs"
        packed.write_text(
            f"# pack-refs with: peeled fully-peeled\n{sha} refs/heads/main\n",
            encoding="utf-8",
        )
        main_ref.unlink()

        result = GitFilesystemInspector().inspect_repo(repo_path)
        self.assertTrue(result.is_valid_candidate)

    def test_t20_sdk03_gitdir_file(self) -> None:
        """T20-SDK-03: worktree com .git file (gitdir)."""
        donor = self.mount / "donor"
        _init_real_repo(donor)
        work = self.mount / "linked"
        work.mkdir()
        actual = self.mount / "actual.git"
        import shutil

        shutil.copytree(donor / ".git", actual)
        (work / ".git").write_text(f"gitdir: {actual.resolve()}\n", encoding="utf-8")

        result = GitFilesystemInspector().inspect_repo(work)
        self.assertTrue(result.is_valid_candidate)


if __name__ == "__main__":
    unittest.main()
