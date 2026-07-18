"""DTOs imutáveis do snapshot da main (T08).

Responsabilidade
    Formas de dados de origem, tip e sinais de primeiro index.

Motivo da separação
    Separar contratos de dados da I/O Git e da orquestração (T14).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from github_rag.catalog.models import RepoOrigin


class FileChangeKind(str, Enum):
    """Tipo de mudança de path entre dois commits (ENG-012)."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass(frozen=True)
class LocalSnapshotSource:
    """Origem local: path absoluto do repositório Git."""

    local_path: str


@dataclass(frozen=True)
class GitHubSnapshotSource:
    """Origem GitHub: ``owner/repo`` + token em memória (BR-008)."""

    full_name: str
    token: str


SnapshotSource = LocalSnapshotSource | GitHubSnapshotSource


@dataclass(frozen=True)
class MainSnapshot:
    """Snapshot imutável do tip da branch ``main``."""

    origin: RepoOrigin
    repo_key: str
    commit_sha: str
    branch: str


@dataclass(frozen=True)
class FirstIndexSignal:
    """Sinal de primeiro index: sem ``from_commit`` (D-T08-003)."""

    to_commit: str
