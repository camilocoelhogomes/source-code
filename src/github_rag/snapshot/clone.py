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
        encoded = quote(token, safe="")
        auth_url = f"https://x-access-token:{encoded}@github.com/{full_name}.git"
        clean_url = f"https://github.com/{full_name}.git"
        repo: Repo | None = None

        try:
            if target.exists() and (target / ".git").exists():
                repo = Repo(target)
                _set_origin_url(repo, auth_url)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                # Sem filter=blob:none: read_file precisa do conteúdo completo (D-T08-004).
                repo = Repo.clone_from(
                    auth_url,
                    str(target),
                    multi_options=["--no-checkout"],
                )

            for sha in shas:
                if _has_commit(repo, sha):
                    continue
                try:
                    # Fetch com auth ainda presente (antes do scrub).
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
        finally:
            # BR-008: nunca persistir remote com token após a operação.
            if repo is not None:
                try:
                    _set_origin_url(repo, clean_url)
                except Exception:  # noqa: BLE001
                    pass
            elif target.exists() and (target / ".git").exists():
                try:
                    _set_origin_url(Repo(target), clean_url)
                except Exception:  # noqa: BLE001
                    pass

        return target


def _set_origin_url(repo: Repo, url: str) -> None:
    """Atualiza URL do remote origin sem vazar falhas de config ao caller."""
    try:
        repo.remotes.origin.set_url(url)
    except Exception:  # noqa: BLE001
        with repo.config_writer() as cw:
            if cw.has_section('remote "origin"'):
                cw.set('remote "origin"', "url", url)


def _has_commit(repo: Repo, sha: str) -> bool:
    try:
        repo.commit(sha)
        return True
    except Exception:  # noqa: BLE001
        return False
