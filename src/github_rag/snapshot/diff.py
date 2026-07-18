"""Diff de paths entre commits (T08 / ENG-012).

Responsabilidade
    Agregar paths adicionados/modificados/removidos sem conteúdo.

Motivo da separação
    Diff independe de elegibilidade (T09) e de leitura de arquivo.
"""

from __future__ import annotations

from dataclasses import dataclass

from github_rag.snapshot.models import FileChangeKind


@dataclass(frozen=True)
class FileDiff:
    """Mudança de um path entre dois commits."""

    path: str
    change: FileChangeKind


@dataclass(frozen=True)
class FileDiffSet:
    """Conjunto de paths alterados (renome = deleted + added)."""

    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]
