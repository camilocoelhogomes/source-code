# Unit test plan — T07-catalog-sync

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T07-catalog-sync` |
| Versão | `0.1.0` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |

## Estratégia

- Fake `GitHubRepoDiscovery` / `LocalRepoDiscovery` (injeção).
- `InMemoryCatalogRepository` (T03) como SoT de domínio.
- Spies/`RecordingCatalog` para CS-08/CS-10 (contagem de mutações).
- Sem rede, sem PG, sem filesystem real.

## Matriz

| ID | Área | Entrada | Esperado | Cenário |
|---|---|---|---|---|
| UT-01 | sync github | 2 repos discovery | 2 ativos, origin github | CS-01 |
| UT-02 | sync local | 1 repo local | ativo origin local + path | CS-02 |
| UT-03 | misto | 1 gh + 1 local | 2 ativos com conexões | CS-03 |
| UT-04 | ausência | ativo prévio fora da discovery | deactivate; state preservado | CS-05 |
| UT-05 | preservação | up_to_date + commit | inalterado após upsert | CS-06 |
| UT-06 | reativação | soft-deleted volta | active=True; state preservado | CS-07 |
| UT-07 | abort GitHub | GitHubDiscoveryError | CatalogSyncError; 0 upsert/deactivate | CS-08 |
| UT-08 | issues locais | repos + issues | sync OK; issues no result | CS-09 |
| UT-09 | não indexa | repos novos | sem mark_*/reconcile/start | CS-10 |
| UT-10 | config vazia | connections {} | desativa todos | CS-11 |
| UT-11 | REQ-020 | após sync | só 5 estados; sem indisponível | CS-12 |
| UT-12 | idempotência | sync 2× mesma discovery | mesmos ativos; state estável | — |
| UT-13 | token em erro | token conhecido + falha GH | str/repr sem token | CS-08/BDD-014 |
| UT-14 | bootstrap | run_catalog_sync | delega a sync; sem reconcile | CS-10 |
| UT-15 | superfície BDD-023 | dir(CatalogSync) | sem create/update/delete connection | CS-04 |
| UT-16 | multi github conn | 2 conexões GH | upserts de ambas | — |
| UT-17 | chave conexão | mesmo full_name, conexões distintas | 2 entradas | — |
| UT-18 | ordem abort | GH falha antes de local | local.discover não chamado | S-01 reforço |

## Extremos / corners

- Discovery github vazia + local com repos.
- Discovery com overlap de keys (não esperado entre origens distintas).
- Repo ativo em `indexing` ausente → deactivate preserva `indexing`.
- `CatalogSyncError` com `__cause__` = `GitHubDiscoveryError`.

## Evidência RED

Antes da implementação: stubs levantam `NotImplementedError` (ou imports falham até stubs). Após stubs com `NotImplementedError` em `sync`: suíte nova falha pela razão esperada (não AssertionError de comportamento verde).

```bash
python -m pytest tests/unit/catalog/test_sync.py tests/bdd/test_catalog_sync.py -q
```

## Artefatos

| Artefato | Caminho |
|---|---|
| Unitários | `tests/unit/catalog/test_sync.py` |
| BDD | `tests/bdd/test_catalog_sync.py` |
| Helpers | `tests/unit/catalog/sync_helpers.py` |
