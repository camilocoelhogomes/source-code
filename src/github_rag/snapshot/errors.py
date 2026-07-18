"""Erros tipados do módulo snapshot (T08).

Responsabilidade
    Hierarquia de falhas de snapshot sem vazar segredos (BR-008).

Motivo da separação
    Corner cases do DoD tipados; T14 trata por tipo.
"""

from __future__ import annotations


class SnapshotError(Exception):
    """Erro base de operações de snapshot da main."""


class MainBranchMissingError(SnapshotError):
    """Branch ``main`` ausente no repositório ou na API."""


class CorruptRepositoryError(SnapshotError):
    """Repositório Git inválido ou corrompido."""


class GitHubSnapshotNetworkError(SnapshotError):
    """Falha de rede/API PyGithub ou clone GitHub."""


class CommitNotFoundError(SnapshotError):
    """SHA de commit inexistente ou não materializável."""


class FileNotFoundInCommitError(SnapshotError):
    """Path ausente no commit informado."""
