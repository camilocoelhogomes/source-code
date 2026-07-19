# Orquestrador status — onda T31

| Campo | Valor |
|---|---|
| Data | 2026-07-19 |
| Onda | 1 (T31) |

| Task | Branch | PR | Status | Cobertura |
|---|---|---|---|---|
| T31-fix-healthz-static-mount-order | `feature/...-T31-...` | #42 | MERGED | 95.96% |

## Re-run W1 pós T31

| Métrica | Valor |
|---|---|
| exit (sem PATH venv) | `1` — `FileNotFoundError: robot` |
| exit (PATH=.venv/bin) | `33` — fase robot |
| healthy | **ok** (T31 corrigiu) |
| Robot | 1/34 pass; 33 fail — `IF $e2e != ${EMPTY}` SyntaxError em `common.resource:64` |

## Bloqueios

1. **T32** (produto/tooling-e2e): launcher deve invocar `robot` do venv — dedup T22 não cobre.
2. **Gate humano Robot**: corrigir `$e2e != ${EMPTY}` → `$e2e != $EMPTY` em `e2e/robot/resources/common.resource` (RF 7.x).

