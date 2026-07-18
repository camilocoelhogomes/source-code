"""Adaptador local de snapshot via GitPython (T08).

Responsabilidade
    Tip ``main``, árvore, leitura e diff sobre path local — somente GitPython.

Motivo da separação
    Isola I/O Git local da fachada pública e do adaptador GitHub (BR-023 / DEC-015).
"""

from __future__ import annotations

from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo
from git.exc import GitCommandError

from github_rag.catalog.models import RepoOrigin
from github_rag.snapshot.diff import FileDiffSet
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    CorruptRepositoryError,
    FileNotFoundInCommitError,
    MainBranchMissingError,
    SnapshotError,
)
from github_rag.snapshot.models import (
    FirstIndexSignal,
    LocalSnapshotSource,
    MainSnapshot,
)


class LocalGitSnapshotAdapter:
    """Operações de snapshot sobre repositório local (interno)."""

    def get_main_tip(self, source: LocalSnapshotSource) -> MainSnapshot:
        repo = _open_repo(source.local_path)
        commit = _main_commit(repo)
        return MainSnapshot(
            origin=RepoOrigin.LOCAL,
            repo_key=str(Path(source.local_path).resolve()),
            commit_sha=commit.hexsha,
            branch="main",
        )

    def list_tree(self, source: LocalSnapshotSource, *, commit_sha: str) -> tuple[str, ...]:
        repo = _open_repo(source.local_path)
        commit = _resolve_commit(repo, commit_sha)
        return _list_paths(commit)

    def read_file(
        self, source: LocalSnapshotSource, *, commit_sha: str, path: str
    ) -> bytes:
        repo = _open_repo(source.local_path)
        commit = _resolve_commit(repo, commit_sha)
        return _read_blob(commit, path)

    def diff_files(
        self,
        source: LocalSnapshotSource,
        *,
        from_commit: str | None,
        to_commit: str,
    ) -> FileDiffSet | FirstIndexSignal:
        if from_commit is None:
            return FirstIndexSignal(to_commit=to_commit)
        repo = _open_repo(source.local_path)
        _resolve_commit(repo, from_commit)
        _resolve_commit(repo, to_commit)
        return _diff_name_status(repo, from_commit, to_commit)


def _open_repo(local_path: str) -> Repo:
    try:
        return Repo(local_path)
    except (InvalidGitRepositoryError, NoSuchPathError) as exc:
        raise CorruptRepositoryError(
            f"repositório Git inválido ou inacessível: {local_path}"
        ) from exc
    except Exception as exc:  # noqa: BLE001 — mapeia falhas estruturais GitPython
        raise CorruptRepositoryError(
            f"repositório Git corrompido ou ilegível: {local_path}"
        ) from exc


def _main_commit(repo: Repo):
    try:
        return repo.heads.main.commit
    except Exception as exc:  # noqa: BLE001 — GitPython varia o tipo da falha
        if _has_main_head(repo):
            raise CorruptRepositoryError("falha ao resolver tip da main") from exc
        raise MainBranchMissingError("branch main ausente") from exc


def _has_main_head(repo: Repo) -> bool:
    try:
        return any(h.name == "main" for h in repo.heads)
    except Exception:  # noqa: BLE001
        return False


def _resolve_commit(repo: Repo, commit_sha: str):
    try:
        return repo.commit(commit_sha)
    except Exception as exc:  # noqa: BLE001 — BadName/ValueError/GitCommandError etc.
        raise CommitNotFoundError(f"commit não encontrado: {commit_sha}") from exc


def _list_paths(commit) -> tuple[str, ...]:
    paths: list[str] = []
    for blob in commit.tree.traverse():
        # blobs only
        if getattr(blob, "type", None) == "blob":
            paths.append(blob.path.replace("\\", "/"))
    return tuple(sorted(paths))


def _read_blob(commit, path: str) -> bytes:
    posix = path.replace("\\", "/")
    try:
        blob = commit.tree / posix
    except KeyError as exc:
        raise FileNotFoundInCommitError(
            f"arquivo ausente no commit: {posix}"
        ) from exc
    if getattr(blob, "type", None) != "blob":
        raise FileNotFoundInCommitError(f"path não é arquivo: {posix}")
    return blob.data_stream.read()


def _diff_name_status(repo: Repo, from_commit: str, to_commit: str) -> FileDiffSet:
    """Diff sem rename detection (-M off): R → deleted + added via name-status."""
    try:
        # --no-renames garante deleted+added em vez de R100
        output = repo.git.diff(
            from_commit, to_commit, "--name-status", "--no-renames"
        )
    except GitCommandError as exc:
        raise SnapshotError("falha ao calcular diff entre commits") from exc

    added: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("A") and len(parts) >= 2:
            added.append(parts[1].replace("\\", "/"))
        elif status.startswith("M") and len(parts) >= 2:
            modified.append(parts[1].replace("\\", "/"))
        elif status.startswith("D") and len(parts) >= 2:
            deleted.append(parts[1].replace("\\", "/"))
        elif status.startswith("R") and len(parts) >= 3:
            # fallback se --no-renames for ignorado
            deleted.append(parts[1].replace("\\", "/"))
            added.append(parts[2].replace("\\", "/"))

    return FileDiffSet(
        added=tuple(sorted(set(added))),
        modified=tuple(sorted(set(modified))),
        deleted=tuple(sorted(set(deleted))),
    )


# Re-export Repo for structural test U-L12 / MS-10
__all__ = ["LocalGitSnapshotAdapter", "Repo"]
