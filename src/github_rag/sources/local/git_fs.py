"""Inspeção de filesystem Git para descoberta local (T06)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote, urlparse


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
        Concentrar I/O de filesystem e heurística Git (``.git``, ref ``main``).

    Motivo da separação
        Permite mock/injeção nos testes sem stubar ``LocalRepoDiscovery``.
    """

    def parse_file_url(self, url: str) -> ParsedFileUrl:
        """Separa path base absoluto e glob da URL declarada."""
        raise NotImplementedError

    def is_accessible(self, path: Path) -> bool:
        """True se path existe e é legível."""
        raise NotImplementedError

    def expand_candidates(self, base: Path, pattern: str | None) -> Sequence[Path]:
        """Expande glob ou retorna candidato único."""
        raise NotImplementedError

    def inspect_repo(self, path: Path) -> RepoInspection:
        """Valida repositório Git e presença de branch ``main``."""
        raise NotImplementedError
