"""Resolver zoekt-index via podman exec no container compose (T33).

Responsabilidade deste módulo
    Materializar wrapper executável referenciado por ``ZOEKT_INDEX_BIN`` e
    executar ``zoekt-index`` dentro do serviço ``zoekt`` (imagem
    ``sourcegraph/zoekt``), traduzindo paths host ↔ container.

Motivo da separação
    App e2e roda no host; CLI oficial vive na imagem zoekt (D-T33-001/002).
    Isola I/O Podman do launcher e do adaptador T10.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Callable

from github_rag.e2e.errors import E2eStackError
from github_rag.e2e.paths import COMPOSE_E2E_NAME

CommandRunner = Callable[
    [Sequence[str], Mapping[str, str]], tuple[int, str, str]
]

_DEFAULT_INDEX_BIN = "zoekt-index"
_CONTAINER_INDEX_DIR = "/data/index"
_WRAPPER_FILENAME = "zoekt-index"


def default_wrapper_dir(repo_root: Path, *, e2e: bool = False) -> Path:
    """Diretório host para script wrapper materializado."""
    name = "e2e-zoekt-index-bin" if e2e else "dev-zoekt-index-bin"
    return (repo_root / ".data" / name).resolve()


def _is_e2e_compose(compose_file: Path) -> bool:
    return compose_file.name == COMPOSE_E2E_NAME


def _explicit_index_bin(env: Mapping[str, str] | None) -> str | None:
    if env is None:
        return None
    raw = env.get("ZOEKT_INDEX_BIN", "").strip()
    if raw and raw != _DEFAULT_INDEX_BIN:
        return raw
    return None


def find_zoekt_container_id(
    compose_file: Path,
    run_command: CommandRunner,
    env: Mapping[str, str] | None = None,
) -> str:
    """Resolve CID do serviço zoekt via ``podman ps`` (filtro por nome).

    ``podman-compose`` (provider externo de ``podman compose``) não aceita
    ``ps -q <service>`` — usar filtro estável ``name=_zoekt_``.
    """
    _ = compose_file  # reservado para mensagens de erro / evolução futura
    effective = dict(os.environ)
    if env:
        effective.update({k: str(v) for k, v in env.items()})
    cmd = [
        "podman",
        "ps",
        "-q",
        "--filter",
        "name=_zoekt_",
        "--filter",
        "status=running",
    ]
    code, stdout, stderr = run_command(cmd, effective)
    if code != 0:
        raise E2eStackError.from_stderr(
            stderr or f"podman ps zoekt failed with exit {code}",
        )
    cid = stdout.strip().splitlines()[0].strip() if stdout.strip() else ""
    if not cid:
        raise E2eStackError.from_stderr(
            "zoekt container not running; ensure compose stack is up "
            "(service zoekt)",
        )
    return cid


def _parse_zoekt_index_args(args: Sequence[str]) -> tuple[str, str]:
    """Retorna ``(repository_name, tree_host_path)`` dos argv T10."""
    name = ""
    tree = ""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-index":
            i += 2
            continue
        if arg == "-name" and i + 1 < len(args):
            name = args[i + 1]
            i += 2
            continue
        tree = arg
        i += 1
    if not name or not tree:
        raise E2eStackError.from_stderr(
            f"invalid zoekt-index argv (expected -name and tree path): {list(args)!r}",
        )
    return name, tree


def exec_zoekt_index_cli(
    args: Sequence[str],
    *,
    compose_file: Path,
    run_command: CommandRunner,
    env: Mapping[str, str] | None = None,
) -> int:
    """Executa zoekt-index no container: cp árvore host, exec CLI, cleanup."""
    effective = dict(os.environ)
    if env:
        effective.update({k: str(v) for k, v in env.items()})
    name, tree_host = _parse_zoekt_index_args(args)
    cid = find_zoekt_container_id(compose_file, run_command, effective)
    tree_container = f"/tmp/zoekt-tree-{os.getpid()}"

    cp_cmd = ["podman", "cp", f"{tree_host}/.", f"{cid}:{tree_container}/"]
    cp_code, _cp_out, cp_err = run_command(cp_cmd, effective)
    if cp_code != 0:
        raise E2eStackError.from_stderr(
            cp_err or f"podman cp tree failed with exit {cp_code}",
        )

    exec_cmd = [
        "podman",
        "exec",
        cid,
        "zoekt-index",
        "-index",
        _CONTAINER_INDEX_DIR,
        "-name",
        name,
        tree_container,
    ]
    exec_code, _exec_out, exec_err = run_command(exec_cmd, effective)

    rm_cmd = ["podman", "exec", cid, "rm", "-rf", tree_container]
    run_command(rm_cmd, effective)

    return exec_code


def materialize_zoekt_index_wrapper(
    compose_file: Path,
    wrapper_dir: Path,
) -> Path:
    """Escreve script executável ``zoekt-index``; retorna path absoluto."""
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    target = wrapper_dir / _WRAPPER_FILENAME
    compose_literal = str(compose_file.resolve())
    content = f'''#!/usr/bin/env python3
"""Zoekt-index wrapper via podman exec (T33, auto-generated)."""
from __future__ import annotations

import sys
from pathlib import Path

from github_rag.e2e.zoekt_bin import exec_zoekt_index_cli, _default_run_command

_COMPOSE_FILE = Path({compose_literal!r})

if __name__ == "__main__":
    raise SystemExit(
        exec_zoekt_index_cli(
            sys.argv[1:],
            compose_file=_COMPOSE_FILE,
            run_command=_default_run_command,
        )
    )
'''
    target.write_text(content, encoding="utf-8")
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target.resolve()


def _default_run_command(
    cmd: Sequence[str], env: Mapping[str, str]
) -> tuple[int, str, str]:
    import subprocess

    completed = subprocess.run(
        list(cmd),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def resolve_zoekt_index_bin(
    repo_root: Path,
    compose_file: Path,
    *,
    run_command: CommandRunner,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve ``ZOEKT_INDEX_BIN`` para wrapper ou override explícito."""
    effective: dict[str, str] = dict(os.environ)
    if env:
        effective.update({k: str(v) for k, v in env.items()})
    explicit = _explicit_index_bin(effective)
    if explicit is not None:
        return Path(explicit).resolve()

    # Fail-fast: container must exist before materializing wrapper.
    find_zoekt_container_id(compose_file, run_command, effective)

    wrapper_dir = default_wrapper_dir(
        repo_root,
        e2e=_is_e2e_compose(compose_file),
    )
    return materialize_zoekt_index_wrapper(compose_file, wrapper_dir)
