"""Erros tipados do pacote e2e (T21).

Responsabilidade deste módulo
    Sinalizar falhas de credencial vs stack com mensagens sem secrets.

Motivo da separação
    Distingue política DEC-020 de falhas Podman/compose (I-T21-007/008).
"""

from __future__ import annotations

import re
from collections.abc import Sequence

_GHP_PATTERN = re.compile(r"ghp_[A-Za-z0-9_]{10,}")


def _redact(raw: str, secrets: Sequence[str] | None) -> str:
    text = raw if raw is not None else ""
    for secret in secrets or ():
        if secret:
            text = text.replace(secret, "***")
    return _GHP_PATTERN.sub("ghp_***", text)


class E2eCredentialError(Exception):
    """Credencial e2e ausente ou inválida para o ambiente (HITL/CI).

    Responsabilidade
        Sinalizar falha explícita de política DEC-020 / REQ-049 antes de subir stack.
        ``str(self)`` NUNCA contém o valor do token.

    Motivo da separação
        Distingue falha de auth/política de falha de runtime Podman/compose.
    """


class E2eStackError(Exception):
    """Falha ao subir, aguardar healthy ou derrubar a stack e2e.

    Responsabilidade
        Expor erro de runtime (compose/Podman/health) com mensagem segura
        (stderr truncado, sem token).

    Motivo da separação
        Isola I/O de infraestrutura das asserções Robot e da política de credencial.
    """

    @classmethod
    def from_stderr(
        cls,
        raw: str,
        *,
        secrets: Sequence[str] | None = None,
    ) -> E2eStackError:
        """Constrói instância redigindo secrets e padrões ``ghp_``."""
        cleaned = _redact(raw or "", secrets).strip()
        if not cleaned:
            cleaned = "e2e stack command failed"
        # Truncate noisy compose dumps
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000] + "…"
        return cls(cleaned)
