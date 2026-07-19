# Task T33 — fix-e2e-zoekt-index-host-bin

| Campo | Valor |
|---|---|
| Task ID | `T33-fix-e2e-zoekt-index-host-bin` |
| Feature | `github-etl-mcp-rag` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Revisão PO | `PENDING_PO_REVIEW` |
| Superfície | `tooling-e2e` + `catalog_indexing` (wiring host) |
| Origem | `mvp-local-e2e-green` run r3 (`F-W1-007`) |
| Evidência | `spec/features/mvp-local-e2e-green/runs/e2e-run-20260719-r3.md` |
| Dependência | T22 **mergeado** (zoekt webserver saudável); T10 (`ZoektExactCodeIndex` / `ZOEKT_INDEX_BIN`) |

## Classificação

| ID | Classificação | Motivo |
|---|---|---|
| F-W1-007 | `produto` (wiring e2e host) | App no host invoca `zoekt-index` via PATH; binário ausente no host → `FileNotFoundError`; webserver zoekt OK pós-T22 |
| F-W1-008..010 | consequência / gap | Não cobertos por T33 — tasks/gaps separados |

## Objetivo

Garantir que o app e2e rodando no **host** (`python -m github_rag.delivery` via launcher T21) consiga indexar shards Zoekt no volume compartilhado (`ZOEKT_INDEX_DIR` / bind `ZOEKT_INDEX_HOST`) **sem** exigir instalação manual de `zoekt-index` no PATH do operador.

## Evidência (sanitizada) — run r3

Run `e2e-run-20260719-r3.md` (commit `7ed791a`, pós T22/T31):

| Check | Resultado |
|---|---|
| compose / healthy | **ok** |
| robot | 16/34 pass |
| catalog_indexing | 2/10 |
| Detalhe repo #1 | `index CLI falhou bin='zoekt-index' … FileNotFoundError` |
| ui / mcp search | 400 (provável efeito colateral de índice vazio — fora do aceite T33) |

Causa raiz: `build_host_delivery_env` define `ZOEKT_URL` e `ZOEKT_INDEX_DIR` mas **não** resolve `ZOEKT_INDEX_BIN`; `ZoektExactCodeIndex.from_environ` usa default `"zoekt-index"` no PATH do host.

Contrato T22/T10: indexação permanece no app; serviço compose `zoekt` = só webserver. T22 corrigiu webserver; **não** wiring do CLI no host.

## Escopo

- Resolver binário de indexação para fluxo e2e host (superfícies prováveis):
  - `src/github_rag/e2e/host_env.py` — injetar `ZOEKT_INDEX_BIN` (e opcionalmente `ZOEKT_GIT_INDEX_BIN`) no env do app host;
  - `src/github_rag/e2e/launcher.py` — descobrir container/serviço zoekt pós-`compose up` e materializar wrapper ou path absoluto;
  - helper e2e (novo módulo sob `github_rag/e2e/`) — resolver exec via `podman exec` no serviço `zoekt` do projeto `github-rag-e2e`, **ou** script wrapper temporário no repo (`.data/e2e-zoekt-index-bin/`) invocado por `ZOEKT_INDEX_BIN`;
  - reutilizar `SubprocessZoektIndexRunner` / contrato T10 — **sem** alterar formato de índice ou HTTP search.
- Testes unitários e2e/host_env + launcher (UT-P08): mock de resolução de bin; assert env contém `ZOEKT_INDEX_BIN` não-default quando zoekt container disponível; corner case container ausente → erro claro (fail-fast).
- Documentar em `e2e/README.md`: operador **não** precisa instalar `zoekt-index` no host quando stack e2e está up.

## Fora de escopo

- Alterar serviço compose `zoekt` para incluir indexação sidecar permanente (T22 congelou webserver-only).
- Fix de cenários Robot/catalog restantes (F-W1-008 fixture repo, F-W1-009 search 400, F-W1-010 timeout ui_browser) — abrir tasks/gaps dedicados se persistirem pós-T33.
- Instalar zoekt via brew/apt como pré-req obrigatório (mitigação documental apenas como fallback explícito).
- T32 (`robot` venv executable) — task paralela distinta.

## Decisões propostas (Architect)

| ID | Decisão | Motivo |
|---|---|---|
| D-T33-001 | Preferir `podman exec` no container `zoekt` (imagem `sourcegraph/zoekt`) materializando wrapper em path host referenciado por `ZOEKT_INDEX_BIN` | Binário oficial já presente na imagem; evita duplicar toolchain no host; alinha DEC-016 |
| D-T33-002 | Volume bind `ZOEKT_INDEX_HOST` ↔ `/data/index` permanece canônico; `-index` da CLI usa mesmo path **dentro** do exec | Paridade T10/T22 |
| D-T33-003 | Fallback: `ZOEKT_INDEX_BIN` explícito no `.env` do operador se resolver falhar | Escape hatch dev; não bloqueia CI local |
| D-T33-004 | Não alterar `ZoektExactCodeIndex` semantics além do env já suportado (`ZOEKT_INDEX_BIN`) | T10 estável |

## Critérios de aceite

- [ ] Com stack e2e up e app host booted, indexação de fixture local não falha por `FileNotFoundError: zoekt-index`.
- [ ] Shards aparecem em `.data/e2e-zoekt-index` (ou `ZOEKT_INDEX_HOST` configurado) após index bem-sucedida.
- [ ] `build_host_delivery_env` / launcher propagam `ZOEKT_INDEX_BIN` resolvido no fluxo `python -m github_rag.e2e`.
- [ ] Testes unitários cobrem resolução + env merge; cobertura ≥ 95% nos módulos alterados.
- [ ] Sem segredos versionados; wrapper/exec não loga tokens.
- [ ] Re-run manual: catalog_indexing deixa de falhar **somente** por ausência de binário (pass/fail de cenário produto restante ≠ bloqueio T33).

## Arquivos prováveis

- `src/github_rag/e2e/host_env.py`
- `src/github_rag/e2e/launcher.py`
- `src/github_rag/e2e/zoekt_bin.py` (ou nome equivalente — resolver wrapper)
- `tests/unit/e2e/test_host_env.py`
- `tests/unit/e2e/test_zoekt_bin_resolver.py` (novo)
- `e2e/README.md`

## Dependências

| Tipo | Task | Motivo |
|---|---|---|
| Hard | T22 (mergeado) | webserver zoekt + volume `/data/index` saudáveis |
| Hard | T10 | `ZOEKT_INDEX_BIN`, `SubprocessZoektIndexRunner` |
| Soft | T21 | launcher host app + compose e2e |
| Paralelo | T32 | robot venv — não bloqueia implementação T33 |

## Rastreabilidade

| Artefato | Referência |
|---|---|
| Falha | F-W1-007 |
| Run | `e2e-run-20260719-r3.md` |
| Contrato index | T10 `from_environ`, I-T10-009 |
| Contrato compose | T22 D-T22-003 (app indexa; zoekt serve) |

## Handoff

- Ownership: pipeline `github-etl-mcp-rag` (esta task).
- T22 **não** reabrir — escopo webserver concluído; F-W1-007 é delta pós-merge.
