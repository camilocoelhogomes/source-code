# Task T06 — local-discovery

| Campo | Valor |
|---|---|
| Task ID | `T06-local-discovery` |
| Feature | `github-etl-mcp-rag` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Onda | W2 |

## Objetivo

Descobrir repositórios locais declarados por conexões `type: git` com URL `file://` (inclui glob), montados no container.

## Escopo

- `LocalRepoDiscovery`: expandir glob, validar repositório Git, exigir branch `main`.
- Identificar origem como `local` e caminho montado.
- Volume ausente/inacessível ou path sem Git/`main`: erro registrado, sem indexar esses paths.
- Não indexar uncommitted nem outras branches (preparação para T08; descoberta só cataloga repos válidos).

## Fora de escopo

- Snapshot de arquivos; pipeline; UI (apenas dados para catálogo).

## Dependências

- `T02-config-loader`

## Critérios de aceite

- BDD-016, BDD-018.
- Somente paths com Git válido e `main` são retornados como candidatos.
- Erros de volume não derrubam silenciosamente outras conexões já validadas no loader (descoberta reporta falha por conexão/path).

## Arquivos prováveis

- `src/.../sources/local/discovery.py`
- `src/.../sources/local/git_fs.py`
- `tests/bdd/...`
- `tests/unit/sources/local/...`

## Rastreabilidade

- REQ-034, REQ-040; BR-013–015; DEC-010; BDD-016–018.

## Handoff

- Interface: `LocalRepoDiscovery`.
- Consumidor: `T07`.
- Convenção ENG-005: `/repos` como mount padrão documentado.
