"""Porta pública da UI de gestão (T18).

Responsabilidade deste módulo
    Declarar ``ManagementUiApi`` (Protocol).

Motivo da separação
    T19/testes programam contra a porta; domínio não importa FastAPI
    (I-T18-001 / ENG-007 / ENG-013).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ManagementUiApi(Protocol):
    """Superfície HTTP+static de gestão e busca.

    Responsabilidade
        Expor FastAPI com listagem, indexação sob demanda, progresso,
        histórico de falhas, cron e buscas — sem CRUD de config/token.

    Motivo da separação
        Isola ENG-001/BR-017 da orquestração e dos índices (ENG-007).
    """

    def build(self) -> Any:
        """Monta a aplicação ASGI (``fastapi.FastAPI``) pronta para servir.

        Responsabilidade: registrar rotas /api e static.
        Motivo da separação: composition root vs handlers.
        Retorno tipado como ``Any`` neste módulo para não importar FastAPI
        (ENG-013 / I-T18 domain modules); a implementação concreta devolve FastAPI.
        """
        ...
