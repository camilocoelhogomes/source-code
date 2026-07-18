"""Resolução de segredos por nome de variável de ambiente (T02).

Responsabilidade deste módulo
    Declarar a porta ``SecretResolver`` e o erro tipado
    ``SecretResolutionError``. Resolver nome → valor sem embutir o valor em
    mensagens de erro ou logs.

Motivo da separação
    Isolar a política BR-008 / BR-019 / BDD-014 do parser JSON e do I/O de
    arquivo. O loader traduz falhas deste módulo em ``ConfigLoadError``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Protocol, runtime_checkable


class SecretResolutionError(Exception):
    """Falha ao resolver uma variável de ambiente para segredo.

    Responsabilidade
        Sinalizar nome inválido/blank ou env ausente/blank citando somente o
        nome da variável — nunca o valor.

    Motivo da separação
        Distinguir erro de resolução de erro de schema/I/O; o ``ConfigLoader``
        traduz este tipo em ``ConfigLoadError`` na API pública de ``load``.
    """


@runtime_checkable
class SecretResolver(Protocol):
    """Porta: nome de env → valor string não-blank.

    Responsabilidade
        Resolver referências ``EnvSecretRef.env`` contra o ambiente (ou
        ``Mapping`` injetável na implementação concreta).

    Motivo da separação
        Concentra redaction e acesso a env fora do schema e do loader;
        permite testes unitários com mapping injetável.
    """

    def resolve(self, env_name: str) -> str:
        """Resolve ``env_name`` → valor.

        Invariantes
            Nome não-blank; valor presente e não-blank.
        Erros
            ``SecretResolutionError`` citando o nome; nunca o valor.
        """
        ...


class EnvironSecretResolver:
    """Implementação default de ``SecretResolver`` baseada em environ.

    Responsabilidade
        Ler ``os.environ`` ou um ``Mapping`` injetado no construtor.

    Motivo da separação
        Implementação concreta default do ``ConfigLoader``; mapping injetável
        isola testes do ``os.environ`` do processo.
    """

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        """``environ is None`` ⇒ ambiente do processo."""
        self._environ = os.environ if environ is None else environ

    def resolve(self, env_name: str) -> str:
        """Resolve a env sem expor valores em mensagens de falha."""
        if not isinstance(env_name, str) or not env_name.strip():
            raise SecretResolutionError("nome de variável de ambiente inválido")

        value = self._environ.get(env_name)
        if not isinstance(value, str) or not value.strip():
            raise SecretResolutionError(
                f"variável de ambiente {env_name!r} ausente ou vazia"
            )
        return value
