"""Adaptador GitHub de snapshot — PyGithub tip + GitClonePort (T08).

Responsabilidade
    Tip ``main`` via PyGithub; árvore/read/diff via workspace GitPython.

Motivo da separação
    Isola API remota e clone da fachada pública (DEC-015 / D-T08-008).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from github import Auth, Github, GithubException
from github.GithubException import UnknownObjectException
from requests.exceptions import RequestException

from github_rag.catalog.models import RepoOrigin
from github_rag.snapshot.clone import GitClonePort
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    GitHubSnapshotNetworkError,
    MainBranchMissingError,
)
from github_rag.snapshot.local import LocalGitSnapshotAdapter
from github_rag.snapshot.models import (
    FirstIndexSignal,
    GitHubSnapshotSource,
    LocalSnapshotSource,
    MainSnapshot,
)

GithubFactory = Callable[[str], Any]


def _default_github(token: str) -> Github:
    return Github(auth=Auth.Token(token))


class GitHubGitSnapshotAdapter:
    """Operações de snapshot sobre origem GitHub (interno)."""

    def __init__(
        self,
        *,
        clone_port: GitClonePort,
        github_factory: GithubFactory | None = None,
    ) -> None:
        self._clone_port = clone_port
        self._github_factory = (
            github_factory if github_factory is not None else _default_github
        )
        self._local = LocalGitSnapshotAdapter()

    def get_main_tip(self, source: GitHubSnapshotSource) -> MainSnapshot:
        try:
            gh = self._github_factory(source.token)
            repo = gh.get_repo(source.full_name)
            branch = repo.get_branch("main")
            sha = branch.commit.sha
        except MainBranchMissingError:
            raise
        except UnknownObjectException as exc:
            raise MainBranchMissingError(
                f"branch main ausente em {source.full_name}"
            ) from exc
        except GithubException as exc:
            if exc.status == 404:
                raise MainBranchMissingError(
                    f"branch main ausente em {source.full_name}"
                ) from exc
            raise GitHubSnapshotNetworkError(
                f"falha na API GitHub ao obter tip de {source.full_name}"
            ) from exc
        except RequestException as exc:
            raise GitHubSnapshotNetworkError(
                f"falha de rede ao obter tip de {source.full_name}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise GitHubSnapshotNetworkError(
                f"falha ao obter tip de {source.full_name}"
            ) from exc

        return MainSnapshot(
            origin=RepoOrigin.GITHUB,
            repo_key=source.full_name,
            commit_sha=sha,
            branch="main",
        )

    def list_tree(
        self, source: GitHubSnapshotSource, *, commit_sha: str
    ) -> tuple[str, ...]:
        local = self._materialize(source, (commit_sha,))
        return self._local.list_tree(local, commit_sha=commit_sha)

    def read_file(
        self, source: GitHubSnapshotSource, *, commit_sha: str, path: str
    ) -> bytes:
        local = self._materialize(source, (commit_sha,))
        return self._local.read_file(local, commit_sha=commit_sha, path=path)

    def diff_files(
        self,
        source: GitHubSnapshotSource,
        *,
        from_commit: str | None,
        to_commit: str,
    ) -> FileDiffSet | FirstIndexSignal:
        if from_commit is None:
            return FirstIndexSignal(to_commit=to_commit)
        local = self._materialize(source, (from_commit, to_commit))
        return self._local.diff_files(
            local, from_commit=from_commit, to_commit=to_commit
        )

    def _materialize(
        self, source: GitHubSnapshotSource, shas: tuple[str, ...]
    ) -> LocalSnapshotSource:
        try:
            path = self._clone_port.ensure_commits(
                full_name=source.full_name,
                token=source.token,
                commit_shas=shas,
            )
        except (CommitNotFoundError, GitHubSnapshotNetworkError):
            raise
        except Exception as exc:  # noqa: BLE001
            raise GitHubSnapshotNetworkError(
                f"falha ao materializar {source.full_name}"
            ) from exc
        return LocalSnapshotSource(local_path=str(path))
