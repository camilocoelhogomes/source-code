"""Configuração do adaptador OpenAI-compatible (T12).

Responsabilidade deste módulo
    Declarar ``SlmClientSettings`` com default Qwen Coder 3B (DEC-006).

Motivo da separação
    Permite BR-009 (troca de modelo/provedor via settings) sem alterar
    a porta nem o orquestrador.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlmClientSettings:
    """Parâmetros do runtime OpenAI-compatible local.

    Responsabilidade
        Carregar ``base_url``, auth placeholder, modelo e timeout.

    Motivo da separação
        Settings injetáveis sem acoplar factory ao Protocol.
    """

    base_url: str
    api_key: str = "local"
    model: str = "qwen2.5-coder:3b"  # Qwen Coder 3B (DEC-006)
    timeout_seconds: float = 60.0
