"""Helpers para criar repositórios Git reais via GitPython nos testes T08."""

from __future__ import annotations

from pathlib import Path

from git import Actor, Repo


def init_repo_with_main(path: Path, *, files: dict[str, bytes] | None = None) -> str:
    """Cria repo com branch main e commit inicial; retorna SHA."""
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    # Garantir branch main desde o início
    repo.git.checkout("-b", "main")
    actor = Actor("t08", "t08@test.local")
    if files:
        for rel, content in files.items():
            target = path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            repo.index.add([rel])
    else:
        readme = path / "README.md"
        readme.write_text("init\n", encoding="utf-8")
        repo.index.add(["README.md"])
    commit = repo.index.commit("init", author=actor, committer=actor)
    return commit.hexsha


def commit_files(path: Path, files: dict[str, bytes], message: str = "change") -> str:
    """Adiciona/atualiza arquivos e cria commit na branch atual; retorna SHA."""
    repo = Repo(path)
    actor = Actor("t08", "t08@test.local")
    for rel, content in files.items():
        target = path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        repo.index.add([rel])
    commit = repo.index.commit(message, author=actor, committer=actor)
    return commit.hexsha


def delete_and_commit(path: Path, rel_paths: list[str], message: str = "delete") -> str:
    """Remove paths do índice e commita; retorna SHA."""
    repo = Repo(path)
    actor = Actor("t08", "t08@test.local")
    repo.index.remove(rel_paths, working_tree=True)
    commit = repo.index.commit(message, author=actor, committer=actor)
    return commit.hexsha


def rename_and_commit(
    path: Path, old: str, new: str, message: str = "rename"
) -> str:
    """Renomeia arquivo e commita (sem -M no diff do provider)."""
    repo = Repo(path)
    actor = Actor("t08", "t08@test.local")
    repo.index.move([old, new])
    commit = repo.index.commit(message, author=actor, committer=actor)
    return commit.hexsha
