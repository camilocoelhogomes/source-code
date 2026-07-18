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
from pathlib import PurePosixPath
from typing import Protocol, runtime_checkable

import pathspec
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from github_rag.eligibility.gitignore import GitignoreSource
from github_rag.eligibility.rules import (
    DEFAULT_ELIGIBILITY_RULES,
    EligibilityRules,
)

# Referência explícita ao motor OSS (D-T09-002 / BDD-024 / ELIG-06).
_ = (pathspec, GitWildMatchPattern)


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
        ``EligibilityError`` conforme design §2.5.
    """

    def __init__(self, rules: EligibilityRules | None = None) -> None:
        self._rules = rules if rules is not None else DEFAULT_ELIGIBILITY_RULES

    def filter(
        self,
        paths: Sequence[str],
        gitignore_sources: Sequence[GitignoreSource],
    ) -> list[str]:
        """Filtra paths elegíveis.

        Responsabilidade: ver ``FileEligibilityFilter.filter``.
        Motivo da separação: implementação concreta distinta do Protocol.
        Invariantes / Erros: ver classe.
        """
        result: list[str] = []
        seen: set[str] = set()
        for raw in paths:
            normalized = _normalize_path(raw)
            if normalized in seen:
                continue
            seen.add(normalized)
            if _is_ignored(normalized, gitignore_sources):
                continue
            if _is_denied_by_extension(normalized, self._rules):
                continue
            result.append(normalized)
        return result


def _normalize_path(path: str) -> str:
    """Normaliza separadores e valida path relativo ao root do snapshot."""
    if path == "":
        raise EligibilityError("path vazio não é elegível")

    normalized = path.replace("\\", "/")

    if normalized in (".", "./"):
        raise EligibilityError(f"path inválido (não é arquivo): {path}")

    if normalized.startswith("/") or _is_windows_absolute(normalized):
        raise EligibilityError(f"path absoluto não permitido: {path}")

    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    depth = 0
    cleaned: list[str] = []
    for part in parts:
        if part == "..":
            depth -= 1
            if depth < 0:
                raise EligibilityError(
                    f"path com escape '..' fora do root: {path}"
                )
            if cleaned:
                cleaned.pop()
            continue
        depth += 1
        cleaned.append(part)

    if not cleaned:
        raise EligibilityError(f"path inválido (não é arquivo): {path}")

    return "/".join(cleaned)


def _is_windows_absolute(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"


def _is_source_applicable(relative_dir: str, path: str) -> bool:
    if relative_dir == "":
        return True
    return path == relative_dir or path.startswith(relative_dir + "/")


def _path_relative_to_source(path: str, relative_dir: str) -> str:
    if relative_dir == "":
        return path
    prefix = relative_dir + "/"
    if path.startswith(prefix):
        return path[len(prefix) :]
    return ""


def _source_depth(relative_dir: str) -> tuple[int, str]:
    if relative_dir == "":
        return (0, "")
    return (relative_dir.count("/") + 1, relative_dir)


def _is_ignored(
    path: str,
    gitignore_sources: Sequence[GitignoreSource],
) -> bool:
    """Last-match wins entre fontes aplicáveis (D-T09-003 / I-T09-008)."""
    applicable = [
        source
        for source in gitignore_sources
        if _is_source_applicable(source.relative_dir, path)
    ]
    applicable.sort(key=lambda s: _source_depth(s.relative_dir))

    ignored = False
    for source in applicable:
        rel = _path_relative_to_source(path, source.relative_dir)
        if rel == "" and source.relative_dir != "":
            continue
        spec = PathSpec.from_lines("gitwildmatch", source.lines)
        for pattern in spec.patterns:
            if pattern.include is None:
                continue
            if pattern.match_file(rel) is not None:
                ignored = bool(pattern.include)
    return ignored


def _is_denied_by_extension(path: str, rules: EligibilityRules) -> bool:
    suffix = PurePosixPath(path).suffix.lower()
    if not suffix:
        return not rules.include_extensionless
    if suffix in {ext.lower() for ext in rules.csv_extensions}:
        return True
    if suffix in {ext.lower() for ext in rules.image_extensions}:
        return True
    return False
