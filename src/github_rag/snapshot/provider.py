"""Porta MainSnapshotProvider e fachada DefaultMainSnapshotProvider (T08).

Responsabilidade
    Contrato unificado tip/árvore/read/diff para T14/T16.

Motivo da separação
    Única API pública estável; despacha para adaptadores internos (D-T08-009).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from github_rag.snapshot.clone import GitClonePort, ShallowGitClonePort
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.errors import SnapshotError
from github_rag.snapshot.github import GitHubGitSnapshotAdapter
from github_rag.snapshot.local import LocalGitSnapshotAdapter
from github_rag.snapshot.models import (
    FirstIndexSignal,
    GitHubSnapshotSource,
    LocalSnapshotSource,
    MainSnapshot,
    SnapshotSource,
)

GithubFactory = Callable[[str], Any]


@runtime_checkable
class MainSnapshotProvider(Protocol):
    """Porta: tip main, árvore, leitura completa e diff de paths."""

    def get_main_tip(self, source: SnapshotSource) -> MainSnapshot: ...

    def list_tree(
        self, source: SnapshotSource, *, commit_sha: str
    ) -> tuple[str, ...]: ...

    def read_file(
        self, source: SnapshotSource, *, commit_sha: str, path: str
    ) -> bytes: ...

    def diff_files(
        self,
        source: SnapshotSource,
        *,
        from_commit: str | None,
        to_commit: str,
    ) -> FileDiffSet | FirstIndexSignal: ...


class DefaultMainSnapshotProvider:
    """Fachada pública que despacha por tipo de ``SnapshotSource``."""

    def __init__(
        self,
        *,
        clone_port: GitClonePort | None = None,
        github_factory: GithubFactory | None = None,
    ) -> None:
        self._local = LocalGitSnapshotAdapter()
        port = clone_port if clone_port is not None else ShallowGitClonePort()
        self._github = GitHubGitSnapshotAdapter(
            clone_port=port,
            github_factory=github_factory,
        )

    def get_main_tip(self, source: SnapshotSource) -> MainSnapshot:
        if isinstance(source, LocalSnapshotSource):
            return self._local.get_main_tip(source)
        if isinstance(source, GitHubSnapshotSource):
            return self._github.get_main_tip(source)
        raise TypeError(f"SnapshotSource inválido: {type(source)!r}")

    def list_tree(
        self, source: SnapshotSource, *, commit_sha: str
    ) -> tuple[str, ...]:
        if isinstance(source, LocalSnapshotSource):
            return self._local.list_tree(source, commit_sha=commit_sha)
        if isinstance(source, GitHubSnapshotSource):
            return self._github.list_tree(source, commit_sha=commit_sha)
        raise TypeError(f"SnapshotSource inválido: {type(source)!r}")

    def read_file(
        self, source: SnapshotSource, *, commit_sha: str, path: str
    ) -> bytes:
        if isinstance(source, LocalSnapshotSource):
            return self._local.read_file(source, commit_sha=commit_sha, path=path)
        if isinstance(source, GitHubSnapshotSource):
            return self._github.read_file(source, commit_sha=commit_sha, path=path)
        raise TypeError(f"SnapshotSource inválido: {type(source)!r}")

    def diff_files(
        self,
        source: SnapshotSource,
        *,
        from_commit: str | None,
        to_commit: str,
    ) -> FileDiffSet | FirstIndexSignal:
        if isinstance(source, LocalSnapshotSource):
            return self._local.diff_files(
                source, from_commit=from_commit, to_commit=to_commit
            )
        if isinstance(source, GitHubSnapshotSource):
            return self._github.diff_files(
                source, from_commit=from_commit, to_commit=to_commit
            )
        raise TypeError(f"SnapshotSource inválido: {type(source)!r}")


# SnapshotError re-export hint for callers catching invalid sources as SnapshotError
_ = SnapshotError
