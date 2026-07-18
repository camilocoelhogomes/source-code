"""Double injetável FakeExactCodeIndex em memória (T10).

Responsabilidade deste módulo
    Implementar a porta ``ExactCodeIndex`` sem HTTP/CLI Zoekt para BDD/unit
    e consumidores T14/T16.

Motivo da separação
    Valida contrato da porta (BDD-024 / DEC-016) sem processo Zoekt; simula
    falha tipada sob demanda via ``fail_operations``.
"""

from __future__ import annotations

from collections.abc import Sequence, Set

from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.models import ExactMatch, ExactSearchQuery, FileToIndex


class FakeExactCodeIndex:
    """Double in-memory da porta ``ExactCodeIndex``.

    Responsabilidade
        Armazenar conteúdos tip, buscar por substring exata e simular falhas
        tipadas configuráveis.

    Motivo da separação
        Testes e orquestração validam o contrato sem Zoekt real (D-T10-005).
    """

    def __init__(
        self,
        *,
        fail_operations: Set[str] | None = None,
    ) -> None:
        self._fail_operations: Set[str] = (
            fail_operations if fail_operations is not None else frozenset()
        )
        # (repository, commit, path) -> content
        self._store: dict[tuple[str, str, str], bytes] = {}

    def index(
        self,
        repository: str,
        commit: str,
        files: Sequence[FileToIndex],
    ) -> None:
        """Substitui o conjunto de paths do ``repository`` (ZOEKT-08)."""
        if "index" in self._fail_operations:
            raise ExactCodeIndexError(
                f"fake index failure for {repository}",
                operation="index",
                repository=repository,
                commit=commit,
            )

        if not files:
            return

        for file in files:
            if file.repository != repository or file.commit != commit:
                raise ExactCodeIndexError(
                    "FileToIndex diverge de repository/commit canônicos",
                    operation="index",
                    repository=repository,
                    commit=commit,
                )

        # Substituição do conjunto do repository (paths ausentes somem).
        for key in list(self._store):
            if key[0] == repository:
                del self._store[key]

        for file in files:
            self._store[(repository, commit, file.path)] = file.content

    def search(self, query: ExactSearchQuery) -> Sequence[ExactMatch]:
        """Substring exata sobre content; pattern vazio → ()."""
        if "search" in self._fail_operations:
            raise ExactCodeIndexError(
                "fake search failure",
                operation="search",
                repository=query.repository,
            )

        if query.pattern == "":
            return ()

        hits: list[ExactMatch] = []
        for (repository, commit, path), content in self._store.items():
            if query.repository is not None and repository != query.repository:
                continue
            if query.path_prefix is not None and not path.startswith(query.path_prefix):
                continue
            text = content.decode("utf-8", errors="surrogateescape")
            if query.pattern not in text:
                continue
            line_number: int | None = None
            snippet = query.pattern
            for idx, line in enumerate(text.splitlines(), start=1):
                if query.pattern in line:
                    line_number = idx
                    snippet = line
                    break
            hits.append(
                ExactMatch(
                    repository=repository,
                    path=path,
                    commit=commit,
                    snippet=snippet,
                    line_number=line_number,
                )
            )

        hits.sort(
            key=lambda m: (m.repository, m.path, m.line_number or 0, m.snippet)
        )
        return tuple(hits)

    def delete_repository(self, repository: str) -> None:
        """Remove todas as entradas do repositório; ausência = no-op."""
        if "delete" in self._fail_operations:
            raise ExactCodeIndexError(
                f"fake delete failure for {repository}",
                operation="delete",
                repository=repository,
            )

        for key in list(self._store):
            if key[0] == repository:
                del self._store[key]
