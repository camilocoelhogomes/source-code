"""Erro tipado da porta ExactCodeIndex (T10).

Responsabilidade deste módulo
    Declarar ``ExactCodeIndexError`` para falhas de indexação/busca/limpeza.

Motivo da separação
    Distinto de erros HTTP/subprocess crus; T14 trata um tipo estável
    (D-T10-004) sem acoplar a urllib/CLI.
"""

from __future__ import annotations


class ExactCodeIndexError(Exception):
    """Falha tipada de indexação, busca ou limpeza Zoekt.

    Responsabilidade
        Sinalizar falha de etapa Zoekt para T14 marcar erro e reiniciar o
        repositório; ``operation`` discrimina ``index`` / ``search`` / ``delete``.

    Motivo da separação
        Callers tratam um tipo estável sem depender de HTTP/subprocess
        (D-T10-004); mensagens não devem conter tokens/segredos.
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str,
        repository: str | None = None,
        commit: str | None = None,
    ) -> None:
        super().__init__(message)
        self._operation = operation
        self._repository = repository
        self._commit = commit

    @property
    def operation(self) -> str:
        """Operação que falhou: ``index`` | ``search`` | ``delete``."""
        return self._operation

    @property
    def repository(self) -> str | None:
        """Repositório associado à falha, se houver."""
        return self._repository

    @property
    def commit(self) -> str | None:
        """Commit associado à falha, se houver."""
        return self._commit
