"""Porta de clone/materialização GitHub (T08).

Responsabilidade
    Garantir workspace local contendo os SHAs pedidos (GitPython).

Motivo da separação
    Isola rede/clone dos contratos de domínio; mockável nos testes (D-T08-005).
"""

from __future__ import annotations

import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable
from urllib.parse import quote

from git import Repo
from git.exc import GitCommandError

from github_rag.snapshot.errors import (
    CommitNotFoundError,
    GitHubSnapshotNetworkError,
)


@runtime_checkable
class GitClonePort(Protocol):
    """Materializa workspace Git com os commits necessários."""

    def ensure_commits(
        self,
        *,
        full_name: str,
        token: str,
        commit_shas: Sequence[str],
    ) -> Path:
        """Retorna path de workspace contendo todos os SHAs pedidos."""
        ...


class ShallowGitClonePort:
    """Clone via GitPython com fetch dos SHAs; credencial efêmera."""

    def __init__(self, *, work_root: Path | None = None) -> None:
        self._work_root = work_root

    def ensure_commits(
        self,
        *,
        full_name: str,
        token: str,
        commit_shas: Sequence[str],
    ) -> Path:
        if not full_name or "/" not in full_name:
            raise GitHubSnapshotNetworkError("full_name GitHub inválido")

        shas = tuple(dict.fromkeys(commit_shas))  # unique, preserve order
        root = self._work_root or Path(tempfile.mkdtemp(prefix="github_rag_clone_"))
        target = root / full_name.replace("/", "_")
        # URL com token efêmero — não deve ser persistida pelo caller após uso
        encoded = quote(token, safe="")
        url = f"https://x-access-token:{encoded}@github.com/{full_name}.git"

        try:
            if target.exists() and (target / ".git").exists():
                repo = Repo(target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                repo = Repo.clone_from(
                    url,
                    str(target),
                    multi_options=["--no-checkout"],
                    filter="blob:none",
                )
            # Remove remote URL com credencial
            with repo.config_writer() as cw:
                if cw.has_section('remote "origin"'):
                    cw.set('remote "origin"', "url", f"https://github.com/{full_name}.git")

            for sha in shas:
                if _has_commit(repo, sha):
                    continue
                try:
                    repo.git.fetch("origin", sha)
                except GitCommandError as exc:
                    raise CommitNotFoundError(
                        f"commit não encontrado: {sha}"
                    ) from exc
                if not _has_commit(repo, sha):
                    raise CommitNotFoundError(f"commit não encontrado: {sha}")
        except CommitNotFoundError:
            raise
        except Exception as exc:  # noqa: BLE001
            # Nunca incluir token na mensagem
            raise GitHubSnapshotNetworkError(
                f"falha ao clonar ou materializar {full_name}"
            ) from exc

        return target


def _has_commit(repo: Repo, sha: str) -> bool:
    try:
        repo.commit(sha)
        return True
    except Exception:  # noqa: BLE001
        return False
