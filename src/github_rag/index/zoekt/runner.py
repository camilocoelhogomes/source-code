"""Invocador CLI oficial zoekt-index / zoekt-git-index (T10).

Responsabilidade deste módulo
    Declarar ``ZoektIndexRunResult``, ``ZoektIndexRunner`` e
    ``SubprocessZoektIndexRunner``.

Motivo da separação
    Isola ``subprocess``/PATH; mockável; não interpreta formato de shard
    (D-T10-002 / DEC-016).
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ZoektIndexRunResult:
    """Resultado tipado de uma invocação CLI Zoekt.

    Responsabilidade
        Carregar exit code + saídas capturadas sem acoplar a
        ``CompletedProcess``.

    Motivo da separação
        Porta mockável e estável; adaptador monta ``ExactCodeIndexError`` a
        partir destes campos.
    """

    returncode: int
    stdout: str
    stderr: str


@runtime_checkable
class ZoektIndexRunner(Protocol):
    """Porta fina: executar argv da CLI oficial de indexação.

    Responsabilidade
        Executar ``zoekt-index`` / ``zoekt-git-index`` e devolver exit + saídas.

    Motivo da separação
        Isola subprocess/PATH; a porta de domínio envelopa falhas
        (D-T10-002).
    """

    def run(self, argv: Sequence[str]) -> ZoektIndexRunResult:
        """Executa ``argv`` (lista, nunca shell string)."""
        ...


class SubprocessZoektIndexRunner:
    """Implementação via ``subprocess.run`` (sem shell).

    Responsabilidade
        Invocar binário oficial com lista de args e capturar stdout/stderr.

    Motivo da separação
        Implementação concreta injetável; testes usam fake do Protocol.
    """

    def __init__(self, *, timeout_seconds: float = 600.0) -> None:
        self._timeout_seconds = timeout_seconds

    def run(self, argv: Sequence[str]) -> ZoektIndexRunResult:
        """Executa argv; propaga ``FileNotFoundError``/timeout para envelopar."""
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            timeout=self._timeout_seconds,
            shell=False,
            check=False,
        )
        return ZoektIndexRunResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
