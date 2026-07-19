# Interfaces — T33-fix-e2e-zoekt-index-host-bin

| Campo | Valor |
|---|---|
| Task | `T33-fix-e2e-zoekt-index-host-bin` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |

## I-T33-001 — `github_rag.e2e.zoekt_bin`

```python
CommandRunner = Callable[[Sequence[str], Mapping[str, str]], tuple[int, str, str]]

def default_wrapper_dir(repo_root: Path, *, e2e: bool = False) -> Path:
    """Diretório host para script wrapper materializado (.data/*-zoekt-index-bin)."""

def find_zoekt_container_id(
    compose_file: Path,
    run_command: CommandRunner,
    env: Mapping[str, str] | None = None,
) -> str:
    """Resolve CID do serviço zoekt via ``podman compose ps -q zoekt``.

    Responsabilidade: descobrir container pós-up para exec/cp.
    Motivo da separação: mockável; launcher não conhece argv podman.
    """

def exec_zoekt_index_cli(
    args: Sequence[str],
    *,
    compose_file: Path,
    run_command: CommandRunner,
    env: Mapping[str, str] | None = None,
) -> int:
    """Executa zoekt-index no container: cp árvore host, exec CLI, cleanup.

    Responsabilidade: bridge host PATH → binário na imagem sourcegraph/zoekt.
    Motivo da separação: único lugar que traduz paths host/container (D-T33-002).
    """

def materialize_zoekt_index_wrapper(
    compose_file: Path,
    wrapper_dir: Path,
) -> Path:
    """Escreve script executável ``zoekt-index``; retorna path absoluto."""

def resolve_zoekt_index_bin(
    repo_root: Path,
    compose_file: Path,
    *,
    run_command: CommandRunner,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve ``ZOEKT_INDEX_BIN`` para wrapper ou override explícito (D-T33-003)."""
```

## I-T33-002 — `build_host_delivery_env` (delta)

Parâmetro opcional `zoekt_index_bin: str | None`. Quando presente, define `ZOEKT_INDEX_BIN` no env merged.

## I-T33-003 — `PodmanE2eStackLauncher` (delta)

`_start_host_app` invoca `resolve_zoekt_index_bin` após compose up; propaga via `build_host_delivery_env`.

## Reuso congelado

- `ZoektExactCodeIndex.from_environ` — lê `ZOEKT_INDEX_BIN` (T10, D-T33-004).
- `SubprocessZoektIndexRunner` — invoca argv[0] como executável (T10).
