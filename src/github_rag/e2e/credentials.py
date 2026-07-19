"""Resolução de credenciais e2e HITL vs CI (T21).

Responsabilidade deste módulo
    Aplicar política DEC-020 / REQ-049 sem vazar secrets em mensagens.

Motivo da separação
    Isola credencial do launcher e da suíte Robot (I-T21-006).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from github_rag.e2e.errors import E2eCredentialError

CredentialSource = Literal["E2E_GITHUB_TOKEN", "GITHUB_TOKEN"]


@dataclass(frozen=True, slots=True)
class ResolvedE2eCredential:
    """Token resolvido para o green path e2e.

    Responsabilidade
        Carregar o valor do token e a fonte escolhida, sem serializar em logs.

    Motivo da separação
        Evita ``str`` opaco; testes BDD leem ``.token`` de forma estável.
    """

    token: str
    source: CredentialSource


def _is_ci(environ: Mapping[str, str]) -> bool:
    actions = environ.get("GITHUB_ACTIONS", "").strip().lower()
    require = environ.get("E2E_REQUIRE_E2E_TOKEN", "").strip()
    return actions in {"true", "1", "yes"} or require in {"1", "true", "yes"}


def _nonempty(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class E2eCredentialResolver:
    """Política de resolução de credencial HITL vs CI.

    Responsabilidade
        - HITL: aceitar ``E2E_GITHUB_TOKEN`` ou ``GITHUB_TOKEN`` (preferir E2E).
        - CI: exigir somente ``E2E_GITHUB_TOKEN`` não vazio.
        - Em falha: ``E2eCredentialError`` genérica (sem secret).

    Motivo da separação
        Isola DEC-020 / REQ-049 do launcher e da suíte Robot.
    """

    def resolve(
        self,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> ResolvedE2eCredential:
        env = environ if environ is not None else os.environ
        e2e_token = _nonempty(env.get("E2E_GITHUB_TOKEN"))
        github_token = _nonempty(env.get("GITHUB_TOKEN"))

        if _is_ci(env):
            if e2e_token is None:
                raise E2eCredentialError(
                    "CI e2e requires E2E_GITHUB_TOKEN "
                    "(do not use the default Actions GITHUB_TOKEN)"
                )
            return ResolvedE2eCredential(
                token=e2e_token, source="E2E_GITHUB_TOKEN"
            )

        if e2e_token is not None:
            return ResolvedE2eCredential(
                token=e2e_token, source="E2E_GITHUB_TOKEN"
            )
        if github_token is not None:
            return ResolvedE2eCredential(
                token=github_token, source="GITHUB_TOKEN"
            )
        raise E2eCredentialError(
            "e2e credential missing: set E2E_GITHUB_TOKEN or GITHUB_TOKEN"
        )
