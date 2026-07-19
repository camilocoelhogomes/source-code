"""Porta pública do lifecycle de entrega (T19).

Responsabilidade deste módulo
    Declarar ``ContainerRuntime`` — Protocol do composition root do container.

Motivo da separação
    Isola o entrypoint testável do Dockerfile dos adaptadores de domínio
    (T07/T14/T17/T18) sem importar SDKs de superfície (ENG-013 / I-T19-002).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ContainerRuntime(Protocol):
    """Lifecycle de processo do container (composition root).

    Responsabilidade
        Orquestrar o boot ordenado até superfícies UI/MCP prontas ou falha fatal
        com SystemExit(1), sem aplicar configuração parcial.

    Motivo da separação
        Isola o entrypoint testável do Dockerfile (CMD ``python -m github_rag.delivery``)
        dos adaptadores de domínio (T07/T14/T17/T18). Permite doubles de wiring
        nos testes sem subir compose (I-T19-002 / D-T19-002).
    """

    def boot(self) -> None:
        """Executa o boot ordenado até superfícies prontas ou falha fatal.

        Responsabilidade
            Percorrer a ordem I-T19-005; em sucesso bind UI/MCP; em falha
            pré-bind levantar ``SystemExit(1)`` (I-T19-006).

        Motivo da separação
            Único método da porta — callers (``__main__``, testes) não conhecem
            stages internos nem factories.

        Erros
            ``SystemExit(1)`` para falhas de settings/config/infra/sync (e
            equivalentes tipados encapsulados). Não faz bind em falha.
        """
        ...
