"""Fontes e carregamento de ``.gitignore`` (T09).

Responsabilidade deste módulo
    Expor o DTO ``GitignoreSource`` e o helper ``load_gitignore_sources`` que
    materializa ``.gitignore`` aninhados a partir de um root local.

Motivo da separação
    A porta ``FileEligibilityFilter`` é pura (sem I/O); o loader concentra
    walk/pathlib e falhas de decode, injetável via fixtures ou substituível
    quando T14 obtiver conteúdos do snapshot (D-T09-001 / D-T09-003).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitignoreSource:
    """DTO de um arquivo ``.gitignore`` já materializado.

    Responsabilidade
        Carregar o par ``(relative_dir, lines)`` consumido pela porta pura de
        elegibilidade, sem acoplar o matching a disco.

    Motivo da separação
        Testes e T14 injetam fontes em memória; o loader local é opcional.
        Distingue representação de dados do walk e do pathspec.

    Invariantes
        ``relative_dir``: ``""`` na raiz; ``"docs"`` / ``"a/b"`` aninhados;
        separador lógico ``/``; sem leading/trailing ``/`` (exceto ``""``).
        ``lines``: tupla imutável de linhas UTF-8 do arquivo.

    Erros
        Esta dataclass não levanta; loader/filter rejeitam entradas inválidas
        com ``EligibilityError``.
    """

    relative_dir: str
    lines: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "lines", tuple(self.lines))


def load_gitignore_sources(repo_root: Path) -> list[GitignoreSource]:
    """Coleta ``.gitignore`` aninhados sob ``repo_root``.

    Responsabilidade
        Percorrer o diretório (sem seguir symlinks para fora do root; sem
        descer em ``.git/``), ler cada arquivo nomeado exatamente
        ``.gitignore`` e devolver ``GitignoreSource`` com
        ``relative_dir`` do pai e linhas UTF-8.

    Motivo da separação
        I/O filesystem (BR-023) fica fora da porta; corners de aninhamento e
        ausência de gitignore são testáveis com fixtures de diretório.

    Invariantes
        Repositório sem ``.gitignore`` → lista vazia (só regras de tipo no
        filter). Ordem estável do walk. Decode UTF-8 estrito.

    Erros
        ``EligibilityError`` se ``repo_root`` inexistente/ilegível ou se algum
        ``.gitignore`` não for UTF-8 decodificável.
    """
    from github_rag.eligibility.filter import EligibilityError

    root = Path(repo_root)
    if not root.exists() or not root.is_dir():
        raise EligibilityError(
            f"repo_root inexistente ou ilegível: {root}"
        )

    sources: list[GitignoreSource] = []
    for dirpath, dirnames, filenames in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        dirnames[:] = sorted(name for name in dirnames if name != ".git")
        if ".gitignore" not in filenames:
            continue

        gitignore_path = Path(dirpath) / ".gitignore"
        try:
            text = gitignore_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise EligibilityError(
                f".gitignore não-UTF-8: {gitignore_path}"
            ) from exc
        except OSError as exc:
            raise EligibilityError(
                f".gitignore ilegível: {gitignore_path}"
            ) from exc

        rel = Path(dirpath).resolve().relative_to(root.resolve())
        relative_dir = "" if rel == Path(".") else rel.as_posix()
        sources.append(
            GitignoreSource(relative_dir=relative_dir, lines=text.splitlines())
        )

    sources.sort(key=lambda s: (s.relative_dir.count("/"), s.relative_dir))
    return sources
