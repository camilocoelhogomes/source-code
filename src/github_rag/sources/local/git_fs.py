"""Inspeção de filesystem Git para descoberta local (T06 + T20 GitPython)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote, urlparse

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError


@dataclass(frozen=True)
class ParsedFileUrl:
    """URL ``file://`` parseada em base e padrão glob opcional."""

    base_path: Path
    glob_pattern: str | None


@dataclass(frozen=True)
class RepoInspection:
    """Resultado da inspeção Git mínima de um diretório."""

    is_git_repo: bool
    has_main_branch: bool
    reason: str | None = None

    @property
    def is_valid_candidate(self) -> bool:
        return self.is_git_repo and self.has_main_branch


class GitFilesystemInspector:
    """Parse de URL ``file://``, glob e validação Git sem mutar working tree.

    Responsabilidade
        Concentrar I/O de filesystem e inspeção Git (GitPython) da branch ``main``.

    Motivo da separação
        Permite mock/injeção nos testes sem stubar ``LocalRepoDiscovery``;
        confina o SDK ao adaptador (ENG-013 / DEC-015).
    """

    def parse_file_url(self, url: str) -> ParsedFileUrl:
        """Separa path base absoluto e glob da URL declarada."""
        parsed = urlparse(url)
        if parsed.scheme != "file":
            msg = f"unsupported file URL scheme: {parsed.scheme!r}"
            raise ValueError(msg)

        raw_path = unquote(parsed.path or "")
        if not raw_path:
            msg = "file URL path is empty"
            raise ValueError(msg)

        glob_pattern: str | None = None
        base_raw = raw_path

        if "*" in raw_path:
            star_index = raw_path.index("*")
            prefix = raw_path[:star_index]
            suffix = raw_path[star_index:]
            glob_pattern = suffix.lstrip("/") or "*"
            base_raw = prefix.rstrip("/") or "/"

        base_path = _to_native_path(base_raw)
        if not _is_absolute_file_path(base_path, base_raw):
            msg = f"file URL path is not absolute: {url!r}"
            raise ValueError(msg)

        return ParsedFileUrl(base_path=base_path, glob_pattern=glob_pattern)

    def is_accessible(self, path: Path) -> bool:
        """True se path existe e é legível."""
        return path.exists() and os.access(path, os.R_OK)

    def expand_candidates(self, base: Path, pattern: str | None) -> Sequence[Path]:
        """Expande glob ou retorna candidato único."""
        if pattern is None:
            return (base,)

        if not base.is_dir():
            return ()

        glob_target = pattern if pattern.startswith("*") else f"*/{pattern}"
        if glob_target == "*":
            glob_target = "*"

        return tuple(
            sorted(
                (p for p in base.glob(glob_target) if p.is_dir()),
                key=lambda item: item.as_posix(),
            )
        )

    def inspect_repo(self, path: Path) -> RepoInspection:
        """Valida repositório Git e presença de branch ``main`` via GitPython."""
        if not path.is_dir():
            return RepoInspection(
                is_git_repo=False,
                has_main_branch=False,
                reason="not a directory",
            )

        try:
            with Repo(path) as repo:
                # Paridade T06: mounts locais são worktrees; bare não é candidato.
                if repo.bare:
                    return RepoInspection(
                        is_git_repo=False,
                        has_main_branch=False,
                        reason="not a git repository",
                    )
                if "main" not in repo.heads:
                    return RepoInspection(
                        is_git_repo=True,
                        has_main_branch=False,
                        reason="main branch not found",
                    )
                return RepoInspection(is_git_repo=True, has_main_branch=True)
        except (InvalidGitRepositoryError, NoSuchPathError):
            return RepoInspection(
                is_git_repo=False,
                has_main_branch=False,
                reason="not a git repository",
            )


def _to_native_path(raw: str) -> Path:
    """Converte path de URL file:// para ``Path`` nativo."""
    if re.match(r"^/[A-Za-z]:", raw):
        # file:///C:/repos → C:/repos (forma Windows validada em T02)
        return Path(raw[1:])
    if os.name == "nt" and re.match(r"^[A-Za-z]:", raw):
        return Path(raw)
    return Path(raw)


def _is_absolute_file_path(path: Path, raw: str) -> bool:
    if path.is_absolute():
        return True
    return bool(re.match(r"^[A-Za-z]:", str(path)) or re.match(r"^/[A-Za-z]:", raw))
