"""Adaptador ZoektExactCodeIndex — porta ExactCodeIndex via CLI/HTTP oficiais (T10).

Responsabilidade deste módulo
    Mapear modelos de domínio ↔ CLI ``zoekt-index`` e HTTP ``POST /api/search``,
    mantendo mapa mínimo ``repository → last_commit``.

Motivo da separação
    Único lugar que conhece query language Zoekt, flags ``-index``,
    materialização de árvore e JSON ``FileMatches`` (D-T10-002 / DEC-016).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from github_rag.index.zoekt.client import HttpZoektSearchTransport, ZoektSearchTransport
from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.models import ExactMatch, ExactSearchQuery, FileToIndex
from github_rag.index.zoekt.runner import SubprocessZoektIndexRunner, ZoektIndexRunner

_DEFAULT_ZOEKT_URL = "http://127.0.0.1:6070"
_DEFAULT_INDEX_BIN = "zoekt-index"
_DEFAULT_GIT_INDEX_BIN = "zoekt-git-index"
_STDERR_TRUNCATE = 500


def _repo_slug(repository: str) -> str:
    return repository.replace("/", "_")


def _escape_literal_pattern(pattern: str) -> str:
    """Escape literal Zoekt: ``content:"…"`` com aspas internas escapadas."""
    escaped = pattern.replace("\\", "\\\\").replace('"', '\\"')
    return f'content:"{escaped}"'


def _build_query_string(query: ExactSearchQuery) -> str:
    parts = [_escape_literal_pattern(query.pattern)]
    if query.repository:
        parts.append(f"repo:{query.repository}")
    if query.path_prefix:
        parts.append(f"file:{query.path_prefix}")
    return " ".join(parts)


def _snippet_from_fragments(fragments: Sequence[Mapping[str, Any]]) -> str:
    parts: list[str] = []
    for frag in fragments:
        pre = str(frag.get("Pre", "") or "")
        match = str(frag.get("Match", "") or "")
        post = str(frag.get("Post", "") or "")
        parts.append(f"{pre}{match}{post}")
    return "".join(parts)


def _normalize_posix_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("/")


class ZoektExactCodeIndex:
    """Implementação default da porta ``ExactCodeIndex`` sobre Zoekt oficial.

    Responsabilidade
        Indexar via CLI, buscar via HTTP JSON e limpar artefatos por associação
        de nome no ``index_dir``.

    Motivo da separação
        Único ponto que conhece mapeamento Zoekt; T14/T16 usam só a porta.
    """

    def __init__(
        self,
        *,
        search: ZoektSearchTransport,
        indexer: ZoektIndexRunner,
        index_dir: str | Path,
        index_bin: str = _DEFAULT_INDEX_BIN,
        git_index_bin: str = _DEFAULT_GIT_INDEX_BIN,
        git_workdir: str | Path | None = None,
    ) -> None:
        self._search = search
        self._indexer = indexer
        self._index_dir = Path(index_dir)
        self._index_bin = index_bin
        # Reservados para otimização opcional zoekt-git-index (D-T10-001).
        self._git_index_bin = git_index_bin
        self._git_workdir = Path(git_workdir) if git_workdir is not None else None
        self._last_commit: dict[str, str] = {}

    @classmethod
    def from_environ(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        search: ZoektSearchTransport | None = None,
        indexer: ZoektIndexRunner | None = None,
    ) -> ZoektExactCodeIndex:
        """Factory local a partir de envs ``ZOEKT_*`` (D-T10-007)."""
        env = environ if environ is not None else os.environ
        base_url = env.get("ZOEKT_URL", _DEFAULT_ZOEKT_URL)
        index_dir = env.get("ZOEKT_INDEX_DIR", "/data/index")
        index_bin = env.get("ZOEKT_INDEX_BIN", _DEFAULT_INDEX_BIN)
        git_index_bin = env.get("ZOEKT_GIT_INDEX_BIN", _DEFAULT_GIT_INDEX_BIN)
        transport = search if search is not None else HttpZoektSearchTransport(
            base_url=base_url
        )
        runner = indexer if indexer is not None else SubprocessZoektIndexRunner()
        return cls(
            search=transport,
            indexer=runner,
            index_dir=index_dir,
            index_bin=index_bin,
            git_index_bin=git_index_bin,
        )

    def index(
        self,
        repository: str,
        commit: str,
        files: Sequence[FileToIndex],
    ) -> None:
        """Materializa árvore tip e invoca CLI oficial; ``files`` vazio = no-op."""
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

        # MVP: materializa content + zoekt-index (otimização git_workdir fora do Protocol).
        self._index_via_tree(repository, commit, files)
        self._last_commit[repository] = commit

    def _index_via_tree(
        self,
        repository: str,
        commit: str,
        files: Sequence[FileToIndex],
    ) -> None:
        tree_root = Path(tempfile.mkdtemp(prefix="zoekt-tree-"))
        try:
            for file in files:
                rel = _normalize_posix_path(file.path)
                dest = tree_root.joinpath(*rel.split("/"))
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(file.content)

            argv = [
                self._index_bin,
                "-index",
                str(self._index_dir),
                "-name",
                repository,
                str(tree_root),
            ]
            self._run_indexer(argv, repository=repository, commit=commit)
        finally:
            shutil.rmtree(tree_root, ignore_errors=True)

    def _run_indexer(
        self,
        argv: Sequence[str],
        *,
        repository: str,
        commit: str,
    ) -> None:
        try:
            result = self._indexer.run(argv)
        except Exception as exc:
            raise ExactCodeIndexError(
                f"index CLI falhou bin={argv[0]!r} para {repository}@{commit}: "
                f"{type(exc).__name__}",
                operation="index",
                repository=repository,
                commit=commit,
            ) from exc

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "")[:_STDERR_TRUNCATE]
            raise ExactCodeIndexError(
                f"index CLI exit={result.returncode} para {repository}@{commit}: "
                f"{detail}",
                operation="index",
                repository=repository,
                commit=commit,
            )

    def search(self, query: ExactSearchQuery) -> Sequence[ExactMatch]:
        """Busca literal via HTTP oficial; pattern vazio → ()."""
        if query.pattern == "":
            return ()

        opts: dict[str, Any] = {"NumContextLines": query.context_lines}
        if query.max_matches is not None:
            opts["TotalMaxMatchCount"] = query.max_matches

        try:
            response = self._search.post_search(
                {"Q": _build_query_string(query), "Opts": opts}
            )
        except Exception as exc:
            raise ExactCodeIndexError(
                f"search transport falhou: {type(exc).__name__}",
                operation="search",
                repository=query.repository,
            ) from exc

        matches = self._map_file_matches(response)
        ordered = sorted(
            matches,
            key=lambda m: (m.repository, m.path, m.line_number or 0, m.snippet),
        )
        return tuple(ordered)

    def _map_file_matches(self, response: Mapping[str, Any]) -> list[ExactMatch]:
        result = response.get("Result") or {}
        out: list[ExactMatch] = []
        for fm in result.get("FileMatches") or []:
            path = str(fm.get("FileName") or "")
            repository = str(fm.get("Repository") or "")
            commit = str(fm.get("Version") or fm.get("Commit") or "") or (
                self._last_commit.get(repository, "")
            )
            for match in fm.get("Matches") or []:
                line_raw = match.get("LineNumber")
                line_val = int(line_raw) if line_raw is not None else None
                snippet = _snippet_from_fragments(match.get("Fragments") or [])
                out.append(
                    ExactMatch(
                        repository=repository,
                        path=path,
                        commit=commit,
                        snippet=snippet,
                        line_number=line_val,
                    )
                )
        return out

    def delete_repository(self, repository: str) -> None:
        """Remove artefatos associados ao nome do repo; ausência = no-op."""
        slug = _repo_slug(repository)
        try:
            entries = list(self._index_dir.iterdir())
        except FileNotFoundError:
            self._last_commit.pop(repository, None)
            return
        except OSError as exc:
            raise ExactCodeIndexError(
                f"delete falhou para {repository}: {type(exc).__name__}",
                operation="delete",
                repository=repository,
            ) from exc

        try:
            for path in entries:
                if slug in path.name and path.is_file():
                    path.unlink(missing_ok=True)
        except OSError as exc:
            raise ExactCodeIndexError(
                f"delete falhou para {repository}: {type(exc).__name__}",
                operation="delete",
                repository=repository,
            ) from exc

        self._last_commit.pop(repository, None)
