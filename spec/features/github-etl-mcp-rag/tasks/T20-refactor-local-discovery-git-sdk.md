# Task T20 — refactor-local-discovery-git-sdk

| Campo | Valor |
|---|---|
| Task ID | `T20-refactor-local-discovery-git-sdk` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Onda | W3 |
| Plano | candidato v0.1.6 (`PENDING_PO_REVIEW`) |

## Objetivo

Eliminar a dívida **DT-001**: migrar a inspeção Git ad-hoc de `T06-local-discovery` (`.git` / `refs` / `packed-refs`) para **GitPython**, cumprindo BR-023 / DEC-015 / BDD-024, sem alterar o contrato de descoberta nem o comportamento de produto.

## Escopo

- Substituir leitura ad-hoc de refs/`packed-refs` por **GitPython** no adaptador de descoberta local.
- Preservar interface `LocalRepoDiscovery` e critérios BDD-016 e BDD-018 (mesmos resultados/erros observáveis).
- Stdlib para I/O genérico (`pathlib`, parse `file://`) permanece permitido; Git de serviço não.
- Não expandir escopo de produto; refactor de conformidade apenas.

## Fora de escopo

- Snapshot/diff (T08); sync de catálogo (T07); UI; mudanças em wildcards/glob além do necessário ao adaptador.

## Dependências

- `T06-local-discovery` (entregue / contrato estável)

## Critérios de aceite

- BDD-016 e BDD-018 continuam válidos sem alteração de intenção.
- Nenhuma inspeção ad-hoc de `.git`/refs/`packed-refs` permanece no caminho de produção da descoberta local.
- Integração Git local usa GitPython (DEC-015); contribui a BDD-024 / eliminação de DT-001.
- Corner cases já cobertos em T06 (volume ausente, sem `main`, bare/corrupt) preservados via testes existentes + regressão unitária do adaptador.

## Arquivos prováveis

- `src/.../sources/local/discovery.py` (ou adaptador Git)
- `src/.../sources/local/git_fs.py` (substituir/remover parse ad-hoc)
- `tests/unit/sources/local/...`
- `tests/bdd/...` (regressão BDD-016/018)

## Rastreabilidade

- BR-023; DEC-015; DT-001; BDD-016, BDD-018; BDD-024.

## Handoff

- Contrato `LocalRepoDiscovery` inalterado para `T07` e consumidores.
- Gate de entrega: `T19` depende desta task para fechar BDD-024.
- Rollback: reverter PR da task; comportamento de produto permanece o de T06.
