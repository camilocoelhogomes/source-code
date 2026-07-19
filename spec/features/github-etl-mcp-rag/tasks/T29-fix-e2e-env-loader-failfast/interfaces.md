# Interfaces — T29 fix-e2e-env-loader-failfast

| Campo | Valor |
|---|---|
| Estado | `APPROVED_BY_ARCHITECT` |

## I-T29-001 — `parse_dotenv_text`

```python
def parse_dotenv_text(text: str) -> dict[str, str]:
    """Parse conteúdo estilo .env sem interpretação shell.

    Responsabilidade
        Converter linhas KEY=VALUE em dict; ignorar comentários/vazias.

    Motivo da separação
        Valores com espaços (INDEX_CRON) quebram ``source .env``; parser
        puro é testável e reutilizável fora do entrypoint.
    """
```

## I-T29-002 — `load_dotenv_file`

```python
def load_dotenv_file(
    path: Path | str,
    *,
    override: bool = False,
    environ: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
    """Carrega .env em os.environ (best-effort se arquivo ausente).

    Responsabilidade
        I/O de arquivo + merge em environ; não sobrescreve chaves existentes
        por default (override=False).

    Motivo da separação
        Entrypoint fino; testes injetam ``environ`` fake sem disco.
    """
```

## I-T29-003 — `_check_host_app_exited` (launcher interno)

```python
def _check_host_app_exited(self) -> None:
    """Levanta E2eStackError se processo host exitou.

    Responsabilidade
        Fail-fast com stderr sanitizado; chamado no início e no loop poll.

    Motivo da separação
        Evita duplicar lógica poll+stderr+redaction; cobre exit durante wait.
    """
```

## I-T29-004 — Entrypoint `__main__`

```python
def main() -> None:
    """Carrega .env via loader Python e executa run_mvp_e2e()."""
```

## Reuso (sem mudança de Protocol)

| Interface T21 | Mudança |
|---|---|
| `E2eStackLauncher.wait_healthy` | Comportamento interno apenas |
| `PodmanE2eStackLauncher` | + helper fail-fast |

## Aprovação

| Gate | Decisão | Autor | Data |
|---|---|---|---|
| Architect interfaces review | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 |
