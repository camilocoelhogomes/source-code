# Requisitos — `zoekt-index` disponível para app no host (e2e launcher)

## Identificação

| Campo | Valor |
|---|---|
| Feature ID | `github-etl-mcp-rag` |
| Artefato | `requirements-e2e-zoekt-index-host` |
| Versão | `0.1.0` |
| Estado | `PENDING_HUMAN_APPROVAL` |
| Origem | loop e2e W1 — `spec/features/mvp-local-e2e-green/runs/e2e-run-20260719-r3.md` (commit `d70fdab`) |
| Rastreabilidade | `REQ-ZIH-*`, `BR-ZIH-*`, `BDD-ZIH-001` → BDD-002–008, BDD-017; `I-T10-009`, `DEC-015`; `ROBOT-02` (`e2e/robot/catalog_indexing.robot`) |
| Task alvo (proposta) | `T33-fix-e2e-zoekt-index-host-cli` |

## Problema

Após merge de T22 (PR#29), a stack e2e completa fases **compose** e **healthy**; o serviço `zoekt` (`sourcegraph/zoekt:latest`) sobe e expõe `zoekt-webserver` em `:6070`. O launcher e2e (`python -m github_rag.e2e`) inicia o **delivery no host** (`python -m github_rag.delivery`) com `ZOEKT_INDEX_DIR` apontando para `.data/e2e-zoekt-index` (bind mount compartilhado com o container zoekt).

Na indexação, `ZoektExactCodeIndex` (`SubprocessZoektIndexRunner`, **I-T10-009**) invoca o binário `zoekt-index` no **PATH do host**. O binário **não existe** no host de desenvolvimento → `FileNotFoundError`:

```text
index CLI falhou bin='zoekt-index' para <repo>@<commit>: FileNotFoundError
```

Repositórios ficam em estado `erro`; indexação não materializa shards em `ZOEKT_INDEX_DIR`; buscas exact/semantic retornam **400** por índice vazio/ausente.

**Evidência:** run W1 r3 — exit **18**; `catalog_indexing` **2/10**; `ui` **1/3**; `mcp` **3/6**; falha principal **F-W1-007**.

**Causa raiz observada:** modelo e2e “infra em compose + app no host” compartilha diretório de índice via volume, mas **não** disponibiliza o CLI `zoekt-index` no runtime do host — distinto do escopo T22 (entrypoint/saúde do container zoekt).

## Objetivos

- **REQ-ZIH-001:** Garantir que, no fluxo e2e com delivery no host, a invocação de indexação Zoekt (`zoekt-index` / override `ZOEKT_INDEX_BIN`) conclua com sucesso para snapshots elegíveis.
- **REQ-ZIH-002:** Restaurar prova e2e de `catalog_indexing`: cenários BDD ligados à indexação deixam de falhar por `FileNotFoundError` em `zoekt-index` **sem alterar** `e2e/robot/**`.
- **REQ-ZIH-003:** Desbloquear efeitos downstream observáveis: repositórios alcançam estado `atualizado`; buscas exact (UI/MCP) deixam de retornar **400** por ausência de índice quando pré-condições de BDD-009/011 forem satisfeitas.
- **REQ-ZIH-004:** Preservar contrato T10: materialização de árvore + CLI oficial zoekt; `ZOEKT_URL` continua apontando para webserver em `:6070`; sem segredos em logs de indexação.

## Fora de escopo

- Qualquer mudança em **`e2e/robot/**`** (suítes, resources, keywords, tags, asserts).
- Correção de entrypoint/`tini` do serviço zoekt no compose (**T22** — concluída).
- Expansão de cobertura integral BDD-003/005/006/017 (**T24**).
- Fail-fast env loader (**T28/T29**), imagem local (**T30**), `/healthz` mount (**T31**), `robot` venv (**T32**).
- Instalação global permanente de zoekt no SO do desenvolvedor fora do contrato e2e documentado (solução deve ser reproduzível pelo launcher/runbook e2e).
- Refatoração ampla do adapter Zoekt além do necessário para o fluxo host+compose e2e.

## Classificação produto / tooling-e2e

| ID | Superfície | Classificação | Motivo |
|---|---|---|---|
| F-W1-007 | `catalog_indexing` / indexação Zoekt | **`produto`** | Pipeline de indexação (**DEC-015**, **I-T10-009**) falha em runtime real quando app roda no host; viola BDD-002–008, BDD-017 |
| F-W1-009 | `ui` / `mcp` — search 400 | consequência de F-W1-007 | Índice ausente; **não** exige task separada se F-W1-007 fechar |
| F-W1-008 | `catalog_indexing` — fixture/estado `error` | misto | Pode incluir efeito colateral de F-W1-007; reavaliar pós-fix |
| — | `tooling-e2e` / wiring launcher | **`tooling-e2e`** | Launcher e2e deve garantir pré-condição de CLI ou equivalente documentado para modelo host+compose |

## Regra de negócio

- **BR-ZIH-001:** Quando o delivery executa no host com `ZOEKT_INDEX_DIR` e `ZOEKT_URL` configurados (modelo e2e/dev), a etapa Zoekt de indexação **deve** conseguir executar o binário de indexação configurado (`ZOEKT_INDEX_BIN`, default `zoekt-index`) e escrever shards legíveis pelo `zoekt-webserver` no diretório compartilhado, antes de marcar repositório como `atualizado`.

## Cenários BDD (rastreabilidade `catalog_indexing`)

### BDD-ZIH-001 — Indexação Zoekt conclui com app no host (rastreia BDD-002 / ROBOT-02)

**Dado** stack e2e healthy (compose infra + delivery host em `:8080`)  
**E** repositório elegível selecionado para indexação  
**E** `ZOEKT_INDEX_DIR` compartilhado com serviço zoekt  
**Quando** a indexação for disparada (UI ou pipeline)  
**Então** `zoekt-index` (ou binário configurado) executa **sem** `FileNotFoundError`  
**E** o repositório transita para `atualizado`  
**E** shards existem em `ZOEKT_INDEX_DIR` consumíveis por `GET/POST` em `ZOEKT_URL`

| BDD pai | Cenário Robot existente (inalterado) | Assert observável |
|---|---|---|
| BDD-002 | `BDD-002 Index Reference Repo Until Updated` | estado `atualizado`; sem histórico `index CLI falhou` |
| BDD-003 | `BDD-003 Scheduler Cron Fires And Indexes Stale Local` | tick indexa repo stale |
| BDD-004 | `BDD-004 Reindex When Already Updated Stays Updated` | idempotência |
| BDD-005 | `BDD-005 Tip Change Updates Last Processed Commit` | novo commit processado |
| BDD-006 | `BDD-006 Eligibility Include And Exclude Paths` | paths elegíveis indexados |
| BDD-006 | `BDD-006 Exact Search Finds Python Or Markdown Smoke` | busca exact encontra marker |
| BDD-007 | (progresso durante indexação) | percentual/etapa avança sem erro Zoekt CLI |
| BDD-008 | `BDD-008 Invalid Index Request Is Explicit Error` | erro explícito ≠ FileNotFound zoekt-index |
| BDD-017 | `BDD-017 Main Only Other Branch And Uncommitted Absent` | marker main indexado |

**Efeitos downstream (não editar suítes):**

| BDD pai | Superfície | Dependência |
|---|---|---|
| BDD-009 | `ui` | índice populado → busca exact ≠ 400 |
| BDD-011 | `mcp` | `search_code` retorna hits |

## Critérios de aceite mensuráveis

1. **CA-ZIH-01:** Com stack e2e healthy e delivery host running, disparo de indexação de repo de referência **não** registra `FileNotFoundError` para `zoekt-index` no histórico UI/MCP.
2. **CA-ZIH-02:** Após indexação bem-sucedida, `catalog_indexing.robot` — cenários BDD-002, BDD-004, BDD-005, BDD-006 (ambos), BDD-017 passam **sem** alteração em `e2e/robot/**` (baseline run r3: **2/10** → meta **≥8/10** nesta superfície, excluindo falhas não relacionadas a F-W1-008).
3. **CA-ZIH-03:** `POST /api/search` (exact) contra `ZOEKT_URL` retorna resultados para query conhecida pós-indexação smoke (não 400 por índice ausente).
4. **CA-ZIH-04:** `.venv/bin/python -m github_rag.e2e` exit code **≠ 18** por falhas dominantes de F-W1-007; fases compose/healthy permanecem ok.
5. **CA-ZIH-05:** Runbook `e2e/README.md` documenta pré-requisito ou mecanismo automático do launcher para disponibilidade de `zoekt-index` no fluxo host+compose (paridade com doc de compose provider T22).
6. **CA-ZIH-06:** Testes unitários cobrem wiring host/CLI (runner, env `ZOEKT_INDEX_BIN`, launcher ou factory); cobertura do projeto ≥ 95%.

## Métricas de sucesso

- `catalog_indexing`: de **2/10** (run r3) para **≥8/10** no rerun W1 pós-fix, com F-W1-007 ausente do log.
- Tempo até primeiro repo `atualizado` após start e2e: ≤ **300s** (alinhado a timeouts existentes em `catalog_indexing.robot`).
- Zero ocorrências de `bin='zoekt-index' ... FileNotFoundError` em `e2e/results/output.xml` do run de validação.

## Dependências e deduplicação

- **Depende de:** T22 (zoekt container healthy), T21 (launcher e2e), T10 (adapter zoekt-index).
- **Não duplica T22:** T22 corrigiu saúde do serviço zoekt no compose; **não** cobre CLI no host.
- **Evidência T22 atualizada:** ver § Pós-merge em `tasks/T22-fix-tooling-e2e-compose-zoekt.md`.
- **Task proposta:** `T33-fix-e2e-zoekt-index-host-cli` — ownership no pipeline pai `github-etl-mcp-rag`.

## Aprovação humana

- **Estado atual:** `PENDING_HUMAN_APPROVAL` — aguardando revisão e aprovação explícita antes de plano/implementação T33.
