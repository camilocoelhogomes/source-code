# Plano de implementação — github-etl-mcp-rag

| Campo | Valor |
|---|---|
| Feature ID | `github-etl-mcp-rag` |
| Versão do plano | `0.1.5` |
| Estado | `READY_FOR_IMPLEMENTATION` |
| Requisitos base | `requirements.md` v0.3.0 (aprovado 2026-07-18, commit `71ed647`) |
| Natureza | greenfield; sem código de aplicação pré-existente |
| Revisão humana | plano v0.1.5 aprovado em 2026-07-18 por `camilocoelhogomes` (commit candidato `bfc9189`) |
| Revisão PO | `PO_PLAN_APPROVED` em 2026-07-18 (v0.1.5) |

## 1. Arquitetura

### 1.1 Visão

Sistema local em containers com quatro superfícies:

1. **Bootstrap/config** — lê `CONFIG_PATH`, valida JSON Sourcebot-like, resolve segredos por `{ "env": "..." }`, descobre repositórios GitHub e locais, sincroniza o catálogo PostgreSQL e, **no startup do container**, reconcilia indexação (tip `main` × último commit processado) enfileirando o que não estiver `atualizado` (ENG-011).
2. **ETL de indexação** — fila limitada por workers; por repositório: snapshot `main` → (se reindex) arquivos **modificados no commit** reindexados **por arquivo inteiro** → elegibilidade → Zoekt (busca exata) **e** RAG: **Tree-sitter produz cada chunk semântico** → **SLM local gera metadados contextuais para cada chunk** → **Qdrant persiste vetor + payload (chunk + metadados)**; falha parcial invalida e reinicia o repo inteiro.
3. **Consulta** — busca exata (Zoekt), semântica (embeddings/Qdrant com payload dos chunks Tree-sitter + metadados SLM), leitura de arquivo e árvore; compartilhada por UI e MCP.
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
       │                    ┌────────────────────────┤
       │                    ▼                        ▼
       │                 Zoekt                 snapshot main
       │              (busca exata)                  │
       │                                             ▼
       │                              ┌──────────────────────────┐
       │                              │ RAG semântico (obrigatório)│
       │                              │ Tree-sitter → chunk        │
       │                              │      ↓                     │
       │                              │ SLM local → metadados      │
       │                              │   (por cada chunk)         │
       │                              │      ↓                     │
       │                              │ Qdrant ← vetor + payload   │
       │                              └──────────────────────────┘
       ▼
┌─────────────┐     ┌──────────┐
│ Query ports │────►│ UI + MCP │
└─────────────┘     └──────────┘
```

### 1.1.1 Fluxo RAG semântico (obrigatório)

Unidade de chunk semântico/RAG = **somente** chunk contextual produzido pelo **Tree-sitter** (DEC-003). **Proibido** usar chunking genérico por tamanho, janela ou linhas como fonte dos chunks semânticos.

Fluxo por arquivo elegível no pipeline de indexação:

1. Tree-sitter → produz N chunks contextuais  
2. Para **cada** chunk: SLM local (abstrata; default Qwen Coder 3B) → metadados contextuais (BR-010, DEC-006)  
3. Para **cada** chunk enriquecido: embedding + persistência no **Qdrant** (vetor + payload com texto/localização do chunk Tree-sitter **e** metadados gerados pela SLM) (DEC-004)

Zoekt permanece o caminho de busca exata e **não** substitui Tree-sitter/SLM/Qdrant no RAG.

### 1.1.2 Startup reconcile e reindexação por arquivo (obrigatório)

**Startup (ENG-011):** após config válida + sync do catálogo, para cada repo ativo: obter tip `main` e comparar com `last_processed_commit` / estado no PostgreSQL. Se não estiver `atualizado` (tip ≠ processado ou estado `não indexado`/`erro`), transicionar para `não indexado` quando aplicável e **enfileirar** indexação. Estados somente REQ-020.

**Arquivo modificado (ENG-012):** diff entre último commit processado e tip `main`. Paths adicionados/modificados elegíveis → reindexar o **arquivo inteiro** no tip (não delta/hunk como unidade). Paths removidos → limpar índices daquele path. Primeiro index → todos os elegíveis. Falha parcial → restart do **repositório inteiro** (BR-005).
### 1.2 Decisões de engenharia (não alteram escopo de produto)

| ID | Decisão | Motivo |
|---|---|---|
| ENG-001 | Aplicação principal em **Python 3.12+** (API HTTP + workers + MCP SDK); UI web leve (SPA ou templates) consumindo a API. | Ecossistema maduro para MCP, Tree-sitter, embeddings/SLM e FastAPI; um runtime local. |
| ENG-009 | Desenvolvimento local usa **`python -m venv`** (padrão `.venv/`) para instalar e isolar dependências; README documenta create/activate/install/test. Delivery por containers (T19) instala deps na imagem e **não** monta/usa o `.venv` do host. | Feedback humano no candidato `7d6f14a`; alinha REQ-007 (local) com REQ-036 (containers) sem conflito. |
| ENG-002 | Compose com serviços: `app`, `postgres`, `qdrant`, `zoekt` (e runtime SLM atrás de porta abstrata). | Isola estado e índices; delivery padronizado (REQ-036). |
| ENG-003 | Defaults: `INDEX_WORKERS=2`, `QUERY_WORKERS=4` (ajustáveis por env; máximos documentados na imagem). | Leve em máquina de desenvolvedor; dúvida não bloqueante fechada para MVP. |
| ENG-004 | Agenda por **cron**: env (`INDEX_CRON` ou nome fixado no design) define default no boot; preferência de expressão cron persistida na UI (PostgreSQL) prevalece em runtime. | REQ-017 + BDD-003; feedback humano `e22a2a7`. |
| ENG-010 | Configuração do scheduler = **expressão cron** (UI e env). “Uma vez ao dia” de REQ-017 é caso especial de cron; permite também N vezes/dia, horário a horário, etc., sem segundo modelo de config. | Facilita configuração; não contradiz o valor do requisito. |
| ENG-005 | Convenção de volume local padrão: `/repos` no container; URLs `file:///repos/...`. | Alinha exemplo do contrato; montagens adicionais permitidas. |
| ENG-006 | Imagem primária `linux/amd64`; `arm64` best-effort. | Dúvida de plataforma não bloqueia MVP. |
| ENG-007 | Portas (interfaces) estáveis antes dos adaptadores; MCP e UI só consomem serviços de domínio. | Reduz retrabalho quando superfícies evoluírem. |
| ENG-008 | Chunks semânticos **somente** via Tree-sitter; SLM **obrigatória por chunk** antes do upsert Qdrant. | DEC-003, BR-010, DEC-006; qualidade do RAG; feedback humano no candidato `0166f97`. |
| ENG-011 | **Startup do container:** após config + sync do catálogo, comparar tip `main` × estado/último commit no PostgreSQL e enfileirar indexação dos repos que não estejam `atualizado` (tip ≠ processado → `não indexado` + fila). Sem estados extras. | Feedback humano `f6272ef`; alinha BR-002–004 ao boot. |
| ENG-012 | **Reindexação por arquivo modificado:** arquivos alterados entre último commit processado e tip `main` são reindexados **por arquivo inteiro** (não só delta/hunk). Removidos saem dos índices. | Feedback humano `f6272ef`; qualidade e consistência Zoekt/RAG. |

### 1.3 Fronteiras de módulo

| Módulo | Responsabilidade | Não faz |
|---|---|---|
| `config` | Carregar/validar JSON; resolver refs de env; falha total se inválido | Descobrir repos remotos/locais |
| `sources.github` | Listar repos da org filtrando wildcards de inclusão | Indexar conteúdo |
| `sources.local` | Expandir `file://` + glob; validar Git + `main` | Mutar working tree |
| `catalog` | Sincronizar e persistir catálogo/estados no PostgreSQL | Pipeline de arquivos |
| `snapshot` | Obter tip `main`, árvore e **diff de arquivos** entre commits | Filtrar elegibilidade; orquestrar fila |
| `eligibility` | Incluir textuais de dev; excluir CSV, imagens, `.gitignore` | Persistir índices |
| `index.zoekt` | Indexar/buscar exato (arquivo completo na reindexação) | Chunks semânticos / RAG |
| `index.chunk` | Tree-sitter → **única** fonte de chunks semânticos/RAG (sobre arquivo inteiro) | Chunking por tamanho/linhas; prosa; SLM; Qdrant |
| `index.metadata` | SLM local → metadados **por cada** chunk Tree-sitter | Respostas MCP; inventar chunks |
| `index.vector` | Qdrant: vetor + payload (chunk Tree-sitter + metadados SLM) | Busca exata; gerar chunks |
| `indexing` | Orquestrar estados, fila, falha total, skip commit, **startup reconcile**, reindex por arquivo inteiro | UI/MCP |
| `schedule` | Agendamento por expressão cron | Editar config / CRUD conexões |
| `query` | Exact, semantic, read_file, list_tree | Narrativa |
| `mcp` | Tools aprovadas; evidências; paralelismo query | SLM narrativo |
| `ui` | Status, progresso, mensagem/horário/histórico de erro, checkbox, **cron** do scheduler, buscas | CRUD de conexões/token |
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
| `MainSnapshotProvider` | Tip `main`, árvore e diff de arquivos entre commits | BR-015; ENG-012 |
| `FileEligibilityFilter` | Elegibilidade textual / exclusões | REQ-014–015 |
| `ExactCodeIndex` | Indexar e buscar no Zoekt | DEC-002 |
| `ContextualChunker` | Produzir a **única** unidade de chunk semântico/RAG via Tree-sitter (DEC-003). Não chunka por tamanho/linhas. | Isola qualidade estrutural do código |
| `MetadataGenerator` | Gerar metadados contextuais via SLM local **para cada** chunk Tree-sitter (BR-009–010, DEC-006; default Qwen 3B) | Metadados ≠ embeddings ≠ prosa MCP |
| `VectorStore` | Persistir/consultar no Qdrant: vetor + payload com chunk Tree-sitter e metadados SLM (DEC-004) | Não redefine a unidade de chunk |
| `IndexingOrchestrator` | Zoekt + Tree-sitter → SLM(por chunk) → Qdrant; estados REQ-020; skip; restart total; **startup reconcile**; reindex **arquivo inteiro** se modificado | BR-002–005; REQ-022; ENG-011–012 |
| `DailyScheduler` | Disparo conforme expressão cron (UI/env; diário = caso especial) | REQ-017; ENG-010 |
| `QueryService` | Exact + semantic + read + tree | Compartilhado UI/MCP |
| `McpEvidenceServer` | Tools MCP sem narrativa/SLM | DEC-008, BR-011 |
| `ManagementUiApi` | Listagem, checkbox index, progresso, erro (mensagem/horário/histórico), **edição de cron**, buscas | BR-017 |

Estados de repositório (enum fechado, REQ-020 — sem estados extras): `não indexado` | `na fila` | `indexando` | `atualizado` | `erro`.

**Commit novo na `main` (sem estado extra):** `atualizado` só é válido quando o commit atual da `main` é igual ao último processado (BR-004). Se o tip de `main` mudar, o repositório deixa de satisfazer `atualizado` e passa a `não indexado`, tornando-se elegível a nova indexação (sob demanda ou agenda). Não existe estado `desatualizado`.

**Repo ausente da config atual (T07, sem estado extra):** o sync remove o repositório do catálogo ativo listado por UI/MCP; histórico de execuções pode permanecer no PostgreSQL. Não existe estado `indisponível`.

Etapas de progresso por arquivo (mínimo): `zoekt` | `tree_sitter` | `metadata_persisted` (metadados SLM por chunk + persistência Qdrant; REQ-022).

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
T12-slm-metadata                  → T11
T13-qdrant-vector-store           → T11
T14-indexing-orchestrator         → T04, T07, T08, T09, T10, T11, T12, T13
T15-daily-scheduler               → T14
T16-query-services                → T07, T10, T13, T08
T17-mcp-evidence-server           → T04, T16, T07
T18-management-ui                 → T14, T15, T16, T07
T19-container-delivery            → T17, T18
```

**Sequência RAG no orquestrador (T14):** para cada arquivo da leva (inteiro se modificado) → `ContextualChunker` → para cada chunk `MetadataGenerator` → `VectorStore.upsert` (vetor + payload). Boot: sync catálogo → startup reconcile → fila.

## 4. Grupos paralelos (ondas)

| Onda | Tasks paralelas | Gate |
|---|---|---|
| W0 | `T01` | Fundação + venv de desenvolvimento |
| W1 | `T02`, `T03`, `T04` | Contratos + SoT + limites |
| W2 | `T05`, `T06` | Descoberta de origens |
| W3 | `T07`, `T08`, `T09` | Catálogo operacional + preparação de snapshot |
| W4 | `T10`; após `T11`: `T12` ∥ `T13` | Zoekt paralelo; contratos RAG após Tree-sitter |
| W5 | `T14` | Orquestração (sequência Tree-sitter→SLM→Qdrant) |
| W6 | `T15`, `T16` | Agenda (cron) + consulta |
| W7 | `T17`, `T18` | Superfícies |
| W8 | `T19` | Delivery |

**Critical path:**  
`T01 → T02 → T05/T06 → T07 → T14 → T16 → T17/T18 → T19`  
(com `T03`, `T04`, `T08`–`T13` alimentando `T14`).

## 5. Estratégia para reduzir retrabalho

1. **Contratos antes de consumidores** — schema JSON, enums de estado, portas de origem/índice/consulta travados cedo.  
2. **Um `QueryService` para UI e MCP** — evita duplicar Zoekt/Qdrant/read/tree.  
3. **Pipeline por portas** — orquestrador não importa SDKs; só interfaces (fácil mock e troca de SLM).  
4. **RAG fixo Tree-sitter→SLM→Qdrant** — evita retrabalho de chunking genérico e garante metadados por chunk no payload.  
5. **Falha total por repositório** — modelo de dados sem “commit parcial”; remove migrações de estado híbrido.  
6. **Config imutável em runtime** — alterações exigem restart (BR-020); UI nunca escreve conexões.  
7. **Containers por último** — após APIs estáveis; compose apenas empacota.  
8. **Segredo fora do domínio** — `SecretResolver` único; testes BDD-014 em fundação/config.  
9. **Tasks verticais testáveis** — cada task fecha um incremento com BDD + interfaces + unit + impl no implementation-pipeline.

## 6. Rastreabilidade requisito → task

| Task | REQs / BRs / DECs | BDDs |
|---|---|---|
| T01 | cobertura 95%; stack local; **venv** obrigatório para deps de dev (ENG-009) | — (habilita demais) |
| T02 | REQ-009,039–042; BR-016–021; DEC-012 | BDD-021,022 |
| T03 | BR-001,004; dados operacionais; leitura para startup reconcile | BDD-004,007,008 (persistência) |
| T04 | REQ-004,037; BR-006 | BDD-002,013 |
| T05 | REQ-010–011,041; BR-007,019,022; DEC-001,009,014 | BDD-001,014,019 |
| T06 | REQ-034,040; BR-013–015; DEC-010 | BDD-016–018 |
| T07 | REQ-035; BR-001,016; handoff para startup reconcile | BDD-001,016,021,023 |
| T08 | REQ-013; BR-002–004,015; diff de arquivos entre commits (ENG-012) | BDD-004,005,017 |
| T09 | REQ-014–015 | BDD-006 |
| T10 | DEC-002; REQ-002 | BDD-009 |
| T11 | DEC-003; única fonte de chunk semântico/RAG | BDD-007 |
| T12 | BR-009–010; DEC-006; metadados **por cada** chunk Tree-sitter | BDD-007,010 |
| T13 | DEC-004; REQ-002; payload = chunk Tree-sitter + metadados SLM | BDD-010 |
| T14 | REQ-005,012,016,018–022,024; BR-002–005,014; Tree-sitter→SLM→Qdrant; ENG-011 startup; ENG-012 arquivo inteiro | BDD-002,004,005,007,008 |
| T15 | REQ-017 via cron (ENG-010); ENG-004; preferência cron persistida (sem CRUD conexões) | BDD-003 (cron UI/env) |
| T16 | REQ-002,026–027,030 | BDD-009–012 |
| T17 | REQ-003,028–033; DEC-008; BR-011 | BDD-011–015 |
| T18 | REQ-006,012,017,020–027,035; BR-012,017; falhas só REQ-023; UI configura **cron** | BDD-002,003,007,009–010,016,023 |
| T19 | REQ-036–038; DEC-011; boot dispara ENG-011 | BDD-020 |

## 7. Riscos e mitigações

| Risco | Mitigação na decomposição |
|---|---|
| Escala de milhares de repos / SLM pesado | Workers baixos por default; stages isolados; sem limite funcional de arquivo no MVP, mas progresso observável |
| Restart total após falha | Orquestrador único (T14) com política explícita; sem índice “meio commit” |
| Qualidade de chunks/embeddings | Chunks **só** Tree-sitter (DEC-003); SLM por chunk (BR-010); sem chunking genérico; portas T11–T13 estáveis |
| Wildcards amplos | Descoberta (T05) só inclusão; catálogo listável antes de indexar |
| Config/volume errados | Validação total em T02; erros de volume em T06 sem cadastro parcial |
| Exposição de token | SecretResolver + testes BDD-014 em T02/T05/T17/T18 |
| Heterogeneidade de máquinas | T19 documenta recursos; amd64 primário |

## 8. Migração / rollback

Greenfield: sem migração de dados legados. Rollback = não promover imagem/tag; volumes PostgreSQL/Qdrant/Zoekt são descartáveis no MVP local. Schema versionado desde T03 para evoluções futuras.

## 9. Handoff

`PO_PLAN_APPROVED` (v0.1.5). Validado:

- ENG-011: startup compara tip `main` × PostgreSQL e enfileira o que não estiver `atualizado` (T03/T07/T14/T19).
- ENG-012: arquivos modificados reindexados por arquivo inteiro (T08/T14).
- Sem regressão: cron; venv; Tree-sitter→SLM→Qdrant; REQ-020.

Estado atual: `READY_FOR_IMPLEMENTATION` — plano aprovado; tasks `T01`–`T19` prontas para o pipeline de implementação.
