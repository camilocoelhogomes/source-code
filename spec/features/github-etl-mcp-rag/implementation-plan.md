# Plano de implementação — github-etl-mcp-rag

| Campo | Valor |
|---|---|
| Feature ID | `github-etl-mcp-rag` |
| Versão do plano | `0.1.1` |
| Estado | `HUMAN_PLAN_APPROVAL` |
| Requisitos base | `requirements.md` v0.3.0 (aprovado 2026-07-18, commit `71ed647`) |
| Natureza | greenfield; sem código de aplicação pré-existente |
| Revisão PO | `PO_PLAN_APPROVED` em 2026-07-18 (v0.1.1); candidato aguardando aprovação humana do plano |

## 1. Arquitetura

### 1.1 Visão

Sistema local em containers com quatro superfícies:

1. **Bootstrap/config** — lê `CONFIG_PATH`, valida JSON Sourcebot-like, resolve segredos por `{ "env": "..." }`, descobre repositórios GitHub e locais.
2. **ETL de indexação** — fila limitada por workers; por repositório: snapshot `main` → elegibilidade → Zoekt → Tree-sitter → metadados SLM → PostgreSQL/Qdrant; falha parcial invalida e reinicia o repo inteiro.
3. **Consulta** — busca exata (Zoekt), semântica (embeddings/Qdrant), leitura de arquivo e árvore; compartilhada por UI e MCP.
4. **Superfícies** — UI de gestão/busca (sem editar config) e servidor MCP (somente evidências).

PostgreSQL é a fonte de verdade de catálogo, origem, estados e último commit processado.

```text
┌─────────────┐   CONFIG_PATH + volumes + env
│  Bootstrap  │──────────────────────────────────────┐
└──────┬──────┘                                      │
       │ sync catálogo                               │
       ▼                                             ▼
┌─────────────┐   jobs / progresso            ┌─────────────┐
│ PostgreSQL  │◄──────────────────────────────│ Index Worker│
└──────┬──────┘                               │  pool (env) │
       │                                      └──────┬──────┘
       │                                             │
       │         ┌──────────┬───────────┬────────────┼──────────┐
       │         ▼          ▼           ▼            ▼          ▼
       │      Zoekt    Tree-sitter   SLM abstr.   Qdrant   snapshot
       │                                                     main
       ▼
┌─────────────┐     ┌──────────┐
│ Query ports │────►│ UI + MCP │
└─────────────┘     └──────────┘
```

### 1.2 Decisões de engenharia (não alteram escopo de produto)

| ID | Decisão | Motivo |
|---|---|---|
| ENG-001 | Aplicação principal em **Python 3.12+** (API HTTP + workers + MCP SDK); UI web leve (SPA ou templates) consumindo a API. | Ecossistema maduro para MCP, Tree-sitter, embeddings/SLM e FastAPI; um runtime local. |
| ENG-002 | Compose com serviços: `app`, `postgres`, `qdrant`, `zoekt` (e runtime SLM atrás de porta abstrata). | Isola estado e índices; delivery padronizado (REQ-036). |
| ENG-003 | Defaults: `INDEX_WORKERS=2`, `QUERY_WORKERS=4` (ajustáveis por env; máximos documentados na imagem). | Leve em máquina de desenvolvedor; dúvida não bloqueante fechada para MVP. |
| ENG-004 | Horário diário: env define default no boot; preferência persistida na UI (PostgreSQL) prevalece em runtime. | Ambos exigidos (REQ-017); precedência explícita evita ambiguidade. |
| ENG-005 | Convenção de volume local padrão: `/repos` no container; URLs `file:///repos/...`. | Alinha exemplo do contrato; montagens adicionais permitidas. |
| ENG-006 | Imagem primária `linux/amd64`; `arm64` best-effort. | Dúvida de plataforma não bloqueia MVP. |
| ENG-007 | Portas (interfaces) estáveis antes dos adaptadores; MCP e UI só consomem serviços de domínio. | Reduz retrabalho quando superfícies evoluírem. |

### 1.3 Fronteiras de módulo

| Módulo | Responsabilidade | Não faz |
|---|---|---|
| `config` | Carregar/validar JSON; resolver refs de env; falha total se inválido | Descobrir repos remotos/locais |
| `sources.github` | Listar repos da org filtrando wildcards de inclusão | Indexar conteúdo |
| `sources.local` | Expandir `file://` + glob; validar Git + `main` | Mutar working tree |
| `catalog` | Sincronizar e persistir catálogo/estados no PostgreSQL | Pipeline de arquivos |
| `snapshot` | Obter commit e árvore da `main` (sem uncommitted/outras branches) | Filtrar elegibilidade |
| `eligibility` | Incluir textuais de dev; excluir CSV, imagens, `.gitignore` | Persistir índices |
| `index.zoekt` | Indexar/buscar exato | Chunks/vetores |
| `index.chunk` | Tree-sitter → chunks contextuais | Gerar prosa |
| `index.metadata` | SLM abstrato → metadados | Respostas MCP |
| `index.vector` | Persistir/consultar Qdrant | Busca exata |
| `indexing` | Orquestrar estados, fila, falha total, skip commit | UI/MCP |
| `schedule` | Agendamento diário | Editar config |
| `query` | Exact, semantic, read_file, list_tree | Narrativa |
| `mcp` | Tools aprovadas; evidências; paralelismo query | SLM narrativo |
| `ui` | Status, progresso, mensagem/horário/histórico de erro, checkbox, horário diário, buscas | CRUD de conexões/token |
| `delivery` | Dockerfile/compose/volumes/env | Lógica de domínio |

## 2. Interfaces de alto nível

Contratos lógicos (detalhamento de métodos fica no pipeline por task). Cada porta deve documentar responsabilidade e motivo da separação.

| Interface | Responsabilidade | Separação |
|---|---|---|
| `ConfigLoader` | Ler `CONFIG_PATH`, validar schema `connections`, resolver `{env}` | Isola contrato Sourcebot-like do restante |
| `SecretResolver` | Resolver nome de variável → valor; nunca logar valor | BR-008 / BR-019 |
| `GitHubRepoDiscovery` | Descobrir repos por org + wildcards de inclusão | Origem remota ≠ local |
| `LocalRepoDiscovery` | Descobrir repos em `file://` montados | Volumes e Git local |
| `CatalogRepository` | CRUD de catálogo, estados, commits, histórico, progresso | PostgreSQL como SoT (BR-001) |
| `WorkerLimiter` | Semáforos de indexação e consulta por env | BR-006 |
| `MainSnapshotProvider` | Commit e arquivos da `main` | BR-015 |
| `FileEligibilityFilter` | Elegibilidade textual / exclusões | REQ-014–015 |
| `ExactCodeIndex` | Indexar e buscar no Zoekt | DEC-002 |
| `ContextualChunker` | Chunks via Tree-sitter | DEC-003 |
| `MetadataGenerator` | Metadados via SLM abstrato (default Qwen 3B) | BR-009–010 |
| `VectorStore` | Upsert/search Qdrant | DEC-004 |
| `IndexingOrchestrator` | Fila, estados, skip, restart total em falha | BR-002–005 |
| `DailyScheduler` | Disparo diário | REQ-017 |
| `QueryService` | Exact + semantic + read + tree | Compartilhado UI/MCP |
| `McpEvidenceServer` | Tools MCP sem narrativa/SLM | DEC-008, BR-011 |
| `ManagementUiApi` | Listagem, checkbox index, progresso, erro (mensagem/horário/histórico), horário diário, buscas | BR-017 |

Estados de repositório (enum fechado, REQ-020 — sem estados extras): `não indexado` | `na fila` | `indexando` | `atualizado` | `erro`.

**Commit novo na `main` (sem estado extra):** `atualizado` só é válido quando o commit atual da `main` é igual ao último processado (BR-004). Se o tip de `main` mudar, o repositório deixa de satisfazer `atualizado` e passa a `não indexado`, tornando-se elegível a nova indexação (sob demanda ou agenda). Não existe estado `desatualizado`.

**Repo ausente da config atual (T07, sem estado extra):** o sync remove o repositório do catálogo ativo listado por UI/MCP; histórico de execuções pode permanecer no PostgreSQL. Não existe estado `indisponível`.

Etapas de progresso por arquivo (mínimo): `zoekt` | `tree_sitter` | `metadata_persisted`.

## 3. Ordem de implementação e dependências

Ordem recomendada (crítico → superfícies):

1. Fundação e contratos compartilhados  
2. Config + catálogo + workers  
3. Descoberta de origens + sync  
4. Snapshot + elegibilidade  
5. Adaptadores de pipeline (paralelos)  
6. Orquestrador de indexação + scheduler  
7. Serviços de consulta  
8. MCP e UI (paralelos)  
9. Delivery por containers  

### DAG (task → depende de)

```text
T01-project-foundation
T02-config-loader                 → T01
T03-catalog-persistence           → T01
T04-worker-limiter                → T01
T05-github-discovery              → T02
T06-local-discovery               → T02
T07-catalog-sync                  → T03, T05, T06
T08-main-snapshot                 → T01
T09-file-eligibility              → T01
T10-zoekt-adapter                 → T01
T11-treesitter-chunker            → T01
T12-slm-metadata                  → T01
T13-qdrant-vector-store           → T01
T14-indexing-orchestrator         → T04, T07, T08, T09, T10, T11, T12, T13
T15-daily-scheduler               → T14
T16-query-services                → T07, T10, T13, T08
T17-mcp-evidence-server           → T04, T16, T07
T18-management-ui                 → T14, T15, T16, T07
T19-container-delivery            → T17, T18
```

## 4. Grupos paralelos (ondas)

| Onda | Tasks paralelas | Gate |
|---|---|---|
| W0 | `T01` | Fundação |
| W1 | `T02`, `T03`, `T04` | Contratos + SoT + limites |
| W2 | `T05`, `T06` | Descoberta de origens |
| W3 | `T07`, `T08`, `T09` | Catálogo operacional + preparação de snapshot |
| W4 | `T10`, `T11`, `T12`, `T13` | Adaptadores de indexação |
| W5 | `T14` | Orquestração |
| W6 | `T15`, `T16` | Agenda + consulta |
| W7 | `T17`, `T18` | Superfícies |
| W8 | `T19` | Delivery |

**Critical path:**  
`T01 → T02 → T05/T06 → T07 → T14 → T16 → T17/T18 → T19`  
(com `T03`, `T04`, `T08`–`T13` alimentando `T14`).

## 5. Estratégia para reduzir retrabalho

1. **Contratos antes de consumidores** — schema JSON, enums de estado, portas de origem/índice/consulta travados cedo.  
2. **Um `QueryService` para UI e MCP** — evita duplicar Zoekt/Qdrant/read/tree.  
3. **Pipeline por portas** — orquestrador não importa SDKs; só interfaces (fácil mock e troca de SLM).  
4. **Falha total por repositório** — modelo de dados sem “commit parcial”; remove migrações de estado híbrido.  
5. **Config imutável em runtime** — alterações exigem restart (BR-020); UI nunca escreve conexões.  
6. **Containers por último** — após APIs estáveis; compose apenas empacota.  
7. **Segredo fora do domínio** — `SecretResolver` único; testes BDD-014 em fundação/config.  
8. **Tasks verticais testáveis** — cada task fecha um incremento com BDD + interfaces + unit + impl no implementation-pipeline.

## 6. Rastreabilidade requisito → task

| Task | REQs / BRs / DECs | BDDs |
|---|---|---|
| T01 | cobertura 95%, stack local | — (habilita demais) |
| T02 | REQ-009,039–042; BR-016–021; DEC-012 | BDD-021,022 |
| T03 | BR-001,004; dados operacionais | BDD-004,007,008 (persistência) |
| T04 | REQ-004,037; BR-006 | BDD-002,013 |
| T05 | REQ-010–011,041; BR-007,019,022; DEC-001,009,014 | BDD-001,014,019 |
| T06 | REQ-034,040; BR-013–015; DEC-010 | BDD-016–018 |
| T07 | REQ-035; BR-001,016 (remoção do catálogo ativo se ausente da config; sem estado extra) | BDD-001,016,021,023 |
| T08 | REQ-013; BR-002–004,015 | BDD-004,005,017 |
| T09 | REQ-014–015 | BDD-006 |
| T10 | DEC-002; REQ-002 | BDD-009 |
| T11 | DEC-003 | BDD-007 |
| T12 | BR-009–010; DEC-006 | BDD-007,010 |
| T13 | DEC-004; REQ-002 | BDD-010 |
| T14 | REQ-005,012,016,018–022,024; BR-002–005,014; política commit≠processado → `não indexado` | BDD-002,004,005,007,008 |
| T15 | REQ-017; ENG-004; preferência de horário persistida (sem CRUD de conexões) | BDD-003 |
| T16 | REQ-002,026–027,030 | BDD-009–012 |
| T17 | REQ-003,028–033; DEC-008; BR-011 | BDD-011–015 |
| T18 | REQ-006,012,017,020–027,035; BR-012,017; falhas só REQ-023 | BDD-002,003,007,009–010,016,023 |
| T19 | REQ-036–038; DEC-011 | BDD-020 |

## 7. Riscos e mitigações

| Risco | Mitigação na decomposição |
|---|---|
| Escala de milhares de repos / SLM pesado | Workers baixos por default; stages isolados; sem limite funcional de arquivo no MVP, mas progresso observável |
| Restart total após falha | Orquestrador único (T14) com política explícita; sem índice “meio commit” |
| Qualidade de chunks/embeddings | Portas abstratas (T11–T13) permitem trocar implementação sem refatorar UI/MCP |
| Wildcards amplos | Descoberta (T05) só inclusão; catálogo listável antes de indexar |
| Config/volume errados | Validação total em T02; erros de volume em T06 sem cadastro parcial |
| Exposição de token | SecretResolver + testes BDD-014 em T02/T05/T17/T18 |
| Heterogeneidade de máquinas | T19 documenta recursos; amd64 primário |

## 8. Migração / rollback

Greenfield: sem migração de dados legados. Rollback = não promover imagem/tag; volumes PostgreSQL/Qdrant/Zoekt são descartáveis no MVP local. Schema versionado desde T03 para evoluções futuras.

## 9. Handoff

`PO_PLAN_APPROVED` (v0.1.1). Correções da rejeição incorporadas e revalidadas: enum só REQ-020; commit novo → `não indexado`; sync remove do catálogo ativo (sem `indisponível`); UI com REQ-023 e horário diário (BDD-003) sem CRUD de conexões.

Estado atual: `HUMAN_PLAN_APPROVAL` — candidato pronto para aprovação humana do plano. Nenhuma aprovação humana do plano está registrada neste artefato.

Dúvidas de produto não bloqueantes permanecem no `requirements.md`. ENG-004 permanece sem novos estados.
