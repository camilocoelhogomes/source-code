"""Porta e implementação de elegibilidade de arquivos (T09).

Responsabilidade deste módulo
    Expor a porta ``FileEligibilityFilter``, o erro tipado
    ``EligibilityError`` e a implementação ``PathspecFileEligibilityFilter``
    baseada em pathspec GitWildMatch + regras de tipo.

Motivo da separação
    Isolar o contrato puro (paths + fontes já materializadas) do loader de
    disco e das denylists, permitindo T14 e testes injetarem inputs sem I/O
    (D-T09-001 / D-T09-002).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import pathspec
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from github_rag.eligibility.rules import (
    DEFAULT_ELIGIBILITY_RULES,
    EligibilityRules,
)

if TYPE_CHECKING:
    from github_rag.eligibility.gitignore import GitignoreSource

# Referência explícita ao motor OSS (D-T09-002 / BDD-024 / ELIG-06).
# A implementação completa usará PathSpec.from_lines("gitwildmatch", lines).
_ = (pathspec, PathSpec, GitWildMatchPattern)


class EligibilityError(Exception):
    """Falha de entrada na porta ou no loader de elegibilidade.

    Responsabilidade
        Sinalizar paths inválidos (absoluto, escape ``..``, vazio),
        ``repo_root`` inexistente no loader, ou ``.gitignore`` ilegível /
        não-UTF-8 — fail-fast sem silenciar.

    Motivo da separação
        Distinguir erros de elegibilidade (T09) de settings (T01), discovery
        (T05/T06) e catalog (T03); T14 pode mapear para falha de repositório.

    Invariantes
        Mensagem cita o path/root ofensivo; sem conteúdo de arquivo nem
        segredos.

    Erros
        Esta classe **é** o tipo de erro.
    """


@runtime_checkable
class FileEligibilityFilter(Protocol):
    """Porta pura de filtragem de arquivos elegíveis à indexação.

    Responsabilidade
        Receber paths relativos do snapshot e fontes de ``.gitignore`` já
        materializadas; devolver o subset elegível (textuais de
        desenvolvimento; excluir CSV, imagens e paths ignorados).

    Motivo da separação
        Contrato estável para o orquestrador (T14) sem acoplar a disco,
        pathspec concreto ou constantes de extensão — D-T09-001.

    Invariantes
        - Sem I/O na porta; sem parâmetros de tamanho (D-T09-006 / REQ-019).
        - Paths lógicos com ``/``; ordem estável; duplicatas colapsadas na
          primeira ocorrência.
        - ``gitignore_sources=[]`` válido (só regras de tipo).

    Erros
        ``EligibilityError`` para path absoluto, com ``..`` que escape o
        root, ou path vazio.
    """

    def filter(
        self,
        paths: Sequence[str],
        gitignore_sources: Sequence[GitignoreSource],
    ) -> list[str]:
        """Filtra paths elegíveis.

        Responsabilidade: aplicar ignore (pathspec) e denylists; preservar
        ordem de entrada.
        Motivo da separação: única API pública da porta (sem size/max_bytes).
        Invariantes: retorno é subset ordenado de ``paths`` (1ª ocorrência).
        Erros: ``EligibilityError`` em entrada inválida.
        """
        ...


class PathspecFileEligibilityFilter:
    """Implementação de ``FileEligibilityFilter`` com pathspec + rules.

    Responsabilidade
        Materializar o contrato com matching GitWildMatch via biblioteca
        ``pathspec`` e exclusão por denylist CSV/imagens (D-T09-002..005).

    Motivo da separação
        Isola o SDK OSS e a política de tipo da porta Protocol, permitindo
        mocks em T14 e inspeção BDD-024 de que não há parser caseiro.

    Invariantes
        Usa ``PathSpec`` / ``GitWildMatchPattern`` (gitwildmatch); last-match
        wins entre fontes aplicáveis; denylist após ignore; sem caps de
        tamanho.

    Erros
        ``EligibilityError`` conforme design §2.5; stub atual levanta
        ``NotImplementedError`` até a implementação pós unit-test-plan.
    """

    def __init__(self, rules: EligibilityRules | None = None) -> None:
        self._rules = rules if rules is not None else DEFAULT_ELIGIBILITY_RULES

    def filter(
        self,
        paths: Sequence[str],
        gitignore_sources: Sequence[GitignoreSource],
    ) -> list[str]:
        """Filtra paths elegíveis (stub — comportamento na etapa de implementação).

        Responsabilidade: ver ``FileEligibilityFilter.filter``.
        Motivo da separação: implementação concreta distinta do Protocol.
        Invariantes / Erros: ver classe; stub → ``NotImplementedError``.
        """
        raise NotImplementedError(
            "PathspecFileEligibilityFilter.filter: "
            "implementação após unit-test-plan (T09)"
        )
