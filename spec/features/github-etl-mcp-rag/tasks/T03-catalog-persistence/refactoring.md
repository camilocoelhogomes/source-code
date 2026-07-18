# Refatoração (Blue) — T03-catalog-persistence

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T03-catalog-persistence` |
| Autor | Tech Lead Architect (modo REVIEW/Blue) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T03-catalog-persistence` |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

## 1. Objetivo da etapa Blue

Após aprovação técnica da implementação (gate IMPLEMENTATION), identificar
complexidade desnecessária e gargalos de performance **com evidência**, definir
metas e registrar baseline e resultados. Sem otimização especulativa: toda
alegação de performance exige comparação reproduzível antes/depois com testes
verdes.

## 2. Baseline reproduzível (antes)

Comando (workspace T03 sem `.venv` próprio — usa o venv canônico):

```bash
PYTHONPATH=src /Users/camilocoelhogomes/projects/github_rag/.venv/bin/python \
  -m pytest -p no:cacheprovider -q
```

Resultado (2026-07-18):

```
137 passed, 1 skipped, 92 subtests passed in 0.15s
Required test coverage of 95.0% reached. Total coverage: 98.71%
```

| Métrica | Valor baseline |
|---|---|
| Testes | 137 passed, 1 skipped (integração, sem Docker), 92 subtests |
| Tempo da suíte | ~0.15 s |
| Cobertura total | 98.71% (`fail_under=95`) |
| `catalog/memory.py` | 97% (ramos 116, 251 defensivos/inalcançáveis pela API) |
| `catalog/postgres/*` | `omit` (I/O só exercível com PG real; paridade via `integration`) |

## 3. Análise de complexidade e gargalos (com evidência)

| Item | Evidência | Avaliação | Meta Blue |
|---|---|---|---|
| `upsert_repository` (fake) varre repos O(n) | `memory.py` L136–140 | Fake de domínio/teste; catálogo pequeno; fora do caminho de produção (produção usa adaptador PG indexado) | Nenhuma |
| `list_active_catalog` (fake) filtro O(n) | `memory.py` L173–174 | Leitura de catálogo pequeno; adaptador PG usa `WHERE active` com índice parcial | Nenhuma |
| Adaptador PG | `postgres/repository.py` — `session.get` por PK e `select` com índices únicos (`ux_catalog_repository_active_identity`, `ux_file_processing_execution_path`) | Acesso indexado; sem gargalo comprovado | Nenhuma |
| Duplicação fake × adaptador (`_STAGE_FIELD`, `_now`, `_close_current_execution`, reconcile) | `memory.py` vs `postgres/repository.py` | Duplicação **intencional** para paridade da porta (design §3.3). Deduplicar borraria a fronteira hexagonal; ganho não medido | Nenhuma (otimização especulativa recusada) |

## 4. Conclusão

Complexidade adequada ao escopo da camada de persistência. **Nenhum gargalo de
performance comprovado por medição.** As oportunidades de simplificação
observadas são especulativas e conflitam com a separação hexagonal aprovada, não
devendo ser exigidas na etapa Blue.

Testes verdes e baseline reproduzível registrados acima. Como não há gargalo
comprovado nem meta Blue, o resultado é `BLUE_APPROVED_BY_ARCHITECT`.

## 5. Achados remanescentes (SUGGESTION, gates futuros — ver `reviews.md`)

- M-1: `current_execution_id` como FK no design vs `Integer` simples na implementação (evitar FK circular).
- M-2: ramo "tip ausente" do reconcile inalcançável pela API pública (branch defensivo; U-1).
- M-3: `current_execution_id` não é limpo ao fechar execução (sem impacto funcional).
