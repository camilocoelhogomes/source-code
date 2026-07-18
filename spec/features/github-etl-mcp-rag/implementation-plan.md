# Plano de implementação — github-etl-mcp-rag

| Campo | Valor |
|---|---|
| Feature ID | `github-etl-mcp-rag` |
| Versão do plano | `0.1.6` |
| Estado | `PO_PLAN_APPROVED` |
| Requisitos base | `requirements.md` v0.4.0 (aprovado 2026-07-18, commit `7747a27`) |
| Natureza | delta sobre v0.1.5 — conformidade SDK OSS / ORM (BR-023–024, DEC-015–016, BDD-024, DT-001) |
| Revisão humana (plano anterior) | plano v0.1.5 aprovado em 2026-07-18 por `camilocoelhogomes` (commit candidato `bfc9189`) |
| Revisão PO | `PO_PLAN_APPROVED` em 2026-07-18 — rastreabilidade BR-023–024, DEC-015–016, BDD-024, DT-001 ok; T20 cobre dívida sem mudar BDD-016/018; T03 só confirma ORM; sem explosão de escopo. Aguardando `HUMAN_PLAN_APPROVAL`. |

## 1. Arquitetura

### 1.1 Visão

Sistema local em containers com quatro superfícies:

1. **Bootstrap/config** — lê `CONFIG_PATH`, valida JSON Sourcebot-like, resolve segredos por `{ "env": "..." }`, descobre repositórios GitHub e locais, sincroniza o catálogo PostgreSQL e, **no startup do container**, reconcilia indexação (tip `main` × último commit processado) enfileirando o que não estiver `atualizado` (ENG-011).
2. **ETL de indexação** — fila limitada por workers; por repositório: snapshot `main` → (se reindex) arquivos **modificados no commit** reindexados **por arquivo inteiro** → elegibilidade → Zoekt (busca exata) **e** RAG: **Tree-sitter produz cada chunk semântico** → **SLM local gera metadados contextuais para cada chunk** → **Qdrant persiste vetor + payload (chunk + metadados)**; falha parcial invalida e reinicia o repo inteiro.
3. **Consulta** — busca exata (Zoekt), semântica (embeddings/Qdrant com payload dos chunks Tree-sitter + metadados SLM), leitura de arquivo e árvore; compartilhada por UI e MCP.
4. **Superfícies** — UI de gestão/busca (sem editar config) e servidor MCP (somente evidências).

PostgreSQL é a fonte de verdade de catálogo, origem, estados e último commit processado (acesso **somente** via SQLAlchemy 2.x + Alembic + psycopg3 — BR-024 / T03).

```text
┌─────────────┐   CONFIG_PATH + volumes + env
│  Bootstrap  │──────────────────────────────────────┐
└──────┬──────┘                                      │
       │ sync catálogo                               │
       ▼                                             ▼
┌─────────────┐   jobs / progresso            ┌─────────────┐
│ PostgreSQL  │◄──────────────────────────────│ Index Worker│
│ (SQLAlchemy)│                               │  pool (env) │
└──────┬──────┘                               └──────┬──────┘
       │                                      │
       │                    ┌────────────────────────┤
       │                    ▼                        ▼
       │                 Zoekt                 snapshot main
       │           (adaptador fino API/CLI)          │
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
| ENG-013 | **SDKs / clientes oficiais (DEC-015)** confinados aos **adaptadores**. Defaults: PyGithub (GitHub), GitPython (Git), pathspec (`.gitignore`), `tree-sitter` + grammars, `qdrant-client`, cliente OpenAI-compatible (`openai`) para SLM/embeddings, APScheduler (ou cron maduro equivalente), SDK oficial `mcp`, FastAPI (UI API). Substituição só por outro SDK OSS de mercado equivalente documentado — nunca cliente caseiro (BR-023). | BR-023, DEC-015, BDD-024. |
| ENG-014 | **Zoekt (DEC-016):** adaptador fino sobre API HTTP e/ou CLI **oficial** do Zoekt; sem reinventar formato de índice nem protocolo. | DEC-016; ausência de SDK Python maduro. |
| ENG-015 | **PostgreSQL (BR-024):** catálogo exclusivamente via **SQLAlchemy 2.x** + **Alembic** + **psycopg3** (T03 já alinhado). Proibido SQL ad hoc paralelo fora do ORM/migrations para o catálogo. | BR-024, BDD-024. |
| ENG-016 | **DT-001:** inspeção Git ad-hoc de T06 migra para GitPython na task `T20-refactor-local-discovery-git-sdk`, preservando contrato e BDD-016/018. | BR-023, DEC-015, BDD-024. |

### 1.3 Fronteiras de módulo

| Módulo | Responsabilidade | Não faz |
|---|---|---|
| `config` | Carregar/validar JSON; resolver refs de env; falha total se inválido | Descobrir repos remotos/locais |
| `sources.github` | Listar repos da org filtrando wildcards (adaptador **PyGithub**) | Indexar conteúdo |
| `sources.local` | Expandir `file://` + glob; validar Git + `main` (**GitPython** após T20) | Mutar working tree |
| `catalog` | Sincronizar e persistir catálogo/estados no PostgreSQL (**SQLAlchemy**) | Pipeline de arquivos |
| `snapshot` | Obter tip `main`, árvore e **diff de arquivos** entre commits (**GitPython**) | Filtrar elegibilidade; orquestrar fila |
| `eligibility` | Incluir textuais de dev; excluir CSV, imagens, `.gitignore` (**pathspec**) | Persistir índices |
| `index.zoekt` | Adaptador fino API/CLI oficial Zoekt | Chunks semânticos / RAG; cliente inventado |
| `index.chunk` | Tree-sitter oficial → **única** fonte de chunks semânticos/RAG | Chunking por tamanho/linhas; prosa; SLM; Qdrant |
| `index.metadata` | SLM local via cliente OpenAI-compatible → metadados **por cada** chunk | Respostas MCP; inventar chunks |
| `index.vector` | Qdrant via `qdrant-client`: vetor + payload | Busca exata; gerar chunks |
| `indexing` | Orquestrar via **portas**; sem importar SDKs de integração | UI/MCP |
| `schedule` | Agendamento cron via **APScheduler** (ou equivalente maduro) | Editar config / CRUD conexões |
| `query` | Exact, semantic, read_file, list_tree via portas existentes | Narrativa; client paralelo ad-hoc |
| `mcp` | Tools aprovadas via SDK oficial **`mcp`** | SLM narrativo |
| `ui` | API **FastAPI** + frontend; status, progresso, cron, buscas | CRUD de conexões/token |
| `delivery` | Dockerfile/compose; deps/SDKs das tasks nas imagens | Lógica de domínio |

## 2. Interfaces de alto nível

Contratos lógicos (detalhamento de métodos fica no pipeline por task). Cada porta deve documentar responsabilidade e motivo da separação.

| Interface | Responsabilidade | Separação |
|---|---|---|
| `ConfigLoader` | Ler `CONFIG_PATH`, validar schema `connections`, resolver `{env}` | Isola contrato Sourcebot-like do restante |
| `SecretResolver` | Resolver nome de variável → valor; nunca logar valor | BR-008 / BR-019 |
| `GitHubRepoDiscovery` | Descobrir repos por org + wildcards (impl: PyGithub) | Origem remota ≠ local |
| `LocalRepoDiscovery` | Descobrir repos em `file://` montados (impl: GitPython após T20) | Volumes e Git local |
| `CatalogRepository` | CRUD de catálogo via SQLAlchemy/Alembic/psycopg3 | PostgreSQL como SoT (BR-001, BR-024) |
| `WorkerLimiter` | Semáforos de indexação e consulta por env | BR-006 |
| `MainSnapshotProvider` | Tip `main`, árvore e diff (impl: GitPython) | BR-015; ENG-012 |
| `FileEligibilityFilter` | Elegibilidade; `.gitignore` via pathspec | REQ-014–015 |
| `ExactCodeIndex` | Adaptador fino Zoekt API/CLI oficial | DEC-002, DEC-016 |
| `ContextualChunker` | Chunks semânticos via `tree-sitter` + grammars | Isola qualidade estrutural |
| `MetadataGenerator` | Metadados SLM via cliente `openai` (OpenAI-compatible) | Metadados ≠ embeddings ≠ prosa MCP |
| `VectorStore` | Qdrant via `qdrant-client` | Não redefine a unidade de chunk |
| `IndexingOrchestrator` | Só portas; Zoekt + Tree-sitter → SLM → Qdrant; startup reconcile; reindex arquivo inteiro | BR-002–005; ENG-011–013 |
| `DailyScheduler` | Cron via APScheduler (ou equivalente maduro) | REQ-017; ENG-010; DEC-015 |
| `QueryService` | Exact + semantic + read + tree (reutiliza portas; sem client paralelo) | Compartilhado UI/MCP |
| `McpEvidenceServer` | Tools MCP via SDK `mcp`; sem narrativa/SLM | DEC-008, BR-011 |
| `ManagementUiApi` | Listagem, checkbox, progresso, cron, buscas (FastAPI) | BR-017; ENG-001 |

Estados de repositório (enum fechado, REQ-020 — sem estados extras): `não indexado` | `na fila` | `indexando` | `atualizado` | `erro`.

**Commit novo na `main` (sem estado extra):** `atualizado` só é válido quando o commit atual da `main` é igual ao último processado (BR-004). Se o tip de `main` mudar, o repositório deixa de satisfazer `atualizado` e passa a `não indexado`, tornando-se elegível a nova indexação (sob demanda ou agenda). Não existe estado `desatualizado`.

**Repo ausente da config atual (T07, sem estado extra):** o sync remove o repositório do catálogo ativo listado por UI/MCP; histórico de execuções pode permanecer no PostgreSQL. Não existe estado `indisponível`.

Etapas de progresso por arquivo (mínimo): `zoekt` | `tree_sitter` | `metadata_persisted` (metadados SLM por chunk + persistência Qdrant; REQ-022).

## 3. Ordem de implementação e dependências

Ordem recomendada (crítico → superfícies):

1. Fundação e contratos compartilhados  
2. Config + catálogo + workers  
3. Descoberta de origens + sync  
4. Snapshot + elegibilidade (+ refactor GitPython da descoberta local)  
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
T20-refactor-local-discovery-git-sdk → T06
T10-zoekt-adapter                 → T01
T11-treesitter-chunker            → T01
T12-slm-metadata                  → T11
T13-qdrant-vector-store           → T11
T14-indexing-orchestrator         → T04, T07, T08, T09, T10, T11, T12, T13
T15-daily-scheduler               → T14
T16-query-services                → T07, T10, T13, T08
T17-mcp-evidence-server           → T04, T16, T07
T18-management-ui                 → T14, T15, T16, T07
T19-container-delivery            → T17, T18, T20
```

**Sequência RAG no orquestrador (T14):** para cada arquivo da leva (inteiro se modificado) → `ContextualChunker` → para cada chunk `MetadataGenerator` → `VectorStore.upsert` (vetor + payload). Boot: sync catálogo → startup reconcile → fila.

**Nota T03:** já conforme BR-024 / ENG-015 (SQLAlchemy 2.x + Alembic + psycopg3); sem mudança de escopo nesta revisão — apenas confirmação de conformidade ORM.

**Nota T20:** refactor de conformidade (DT-001); não altera contrato de `LocalRepoDiscovery` nem BDD-016/018; pode rodar cedo em paralelo após T06; T19 depende de T20 para fechar BDD-024 na entrega.

## 4. Grupos paralelos (ondas)

| Onda | Tasks paralelas | Gate |
|---|---|---|
| W0 | `T01` | Fundação + venv de desenvolvimento |
| W1 | `T02`, `T03`, `T04` | Contratos + SoT (ORM) + limites |
| W2 | `T05`, `T06` | Descoberta de origens |
| W3 | `T07`, `T08`, `T09`, `T20` | Catálogo + snapshot/elegibilidade + **refactor GitPython (DT-001)** |
| W4 | `T10`; após `T11`: `T12` ∥ `T13` | Zoekt (adaptador fino); contratos RAG após Tree-sitter |
| W5 | `T14` | Orquestração (só portas; Tree-sitter→SLM→Qdrant) |
| W6 | `T15`, `T16` | Agenda (APScheduler) + consulta (sem client paralelo) |
| W7 | `T17`, `T18` | Superfícies (SDK `mcp` + FastAPI) |
| W8 | `T19` | Delivery (deps/SDKs das tasks + T20 fechada) |

**Critical path:**  
`T01 → T02 → T05/T06 → T07 → T14 → T16 → T17/T18 → T19`  
(com `T03`, `T04`, `T08`–`T13` alimentando `T14`; `T20` após `T06` em W3, paralelo ao path crítico, e gate de conformidade em `T19`).

## 5. Estratégia para reduzir retrabalho

1. **Contratos antes de consumidores** — schema JSON, enums de estado, portas de origem/índice/consulta travados cedo.  
2. **Um `QueryService` para UI e MCP** — evita duplicar Zoekt/Qdrant/read/tree; sem client paralelo ad-hoc.  
3. **Pipeline por portas** — orquestrador (**T14**) **não importa SDKs** de integração; só interfaces (fácil mock e troca de SLM). SDKs ficam **somente nos adaptadores** (ENG-013).  
4. **RAG fixo Tree-sitter→SLM→Qdrant** — evita retrabalho de chunking genérico e garante metadados por chunk no payload.  
5. **Falha total por repositório** — modelo de dados sem “commit parcial”; remove migrações de estado híbrido.  
6. **Config imutável em runtime** — alterações exigem restart (BR-020); UI nunca escreve conexões.  
7. **Containers por último** — após APIs estáveis; compose apenas empacota deps/SDKs já escolhidos.  
8. **Segredo fora do domínio** — `SecretResolver` único; testes BDD-014 em fundação/config.  
9. **Tasks verticais testáveis** — cada task fecha um incremento com BDD + interfaces + unit + impl no implementation-pipeline.  
10. **Conformidade SDK cedo** — defaults DEC-015 nas tasks de adaptador; T20 elimina DT-001 sem mudar contrato de descoberta local.

## 6. Rastreabilidade requisito → task

| Task | REQs / BRs / DECs | BDDs |
|---|---|---|
| T01 | cobertura 95%; stack local; **venv** obrigatório para deps de dev (ENG-009) | — (habilita demais) |
| T02 | REQ-009,039–042; BR-016–021; DEC-012 | BDD-021,022 |
| T03 | BR-001,004,**024**; SQLAlchemy 2.x + Alembic + psycopg3; ENG-015 | BDD-004,007,008 (persistência); BDD-024 (ORM) |
| T04 | REQ-004,037; BR-006 | BDD-002,013 |
| T05 | REQ-010–011,041; BR-007,019,022,**023**; DEC-001,009,014,**015**; **PyGithub** | BDD-001,014,019; BDD-024 |
| T06 | REQ-034,040; BR-013–015; DEC-010; **DT-001** → T20 | BDD-016–018 |
| T07 | REQ-035; BR-001,016; handoff para startup reconcile | BDD-001,016,021,023 |
| T08 | REQ-013; BR-002–004,015,**023**; DEC-015; **GitPython**; ENG-012 | BDD-004,005,017; BDD-024 |
| T09 | REQ-014–015; BR-023; DEC-015; **pathspec** (GitWildMatch) | BDD-006; BDD-024 |
| T10 | DEC-002,**016**; REQ-002; adaptador fino API/CLI oficial Zoekt | BDD-009; BDD-024 |
| T11 | DEC-003,**015**; **`tree-sitter` + grammars oficiais** | BDD-007; BDD-024 |
| T12 | BR-009–010,**023**; DEC-006,**015**; cliente **`openai`** (OpenAI-compatible) | BDD-007,010; BDD-024 |
| T13 | DEC-004,**015**; **`qdrant-client`** (+ embedder via SDK) | BDD-010; BDD-024 |
| T14 | REQ-005,012,016,018–022,024; BR-002–005,014,**023**; **só portas**; ENG-011–013 | BDD-002,004,005,007,008 |
| T15 | REQ-017; ENG-004,010; DEC-015; **APScheduler** (ou equivalente maduro) | BDD-003; BDD-024 |
| T16 | REQ-002,026–027,030; reutiliza portas T10/T13/T08; **sem client paralelo ad-hoc** | BDD-009–012; BDD-024 |
| T17 | REQ-003,028–033; DEC-008,**015**; SDK oficial **`mcp`** | BDD-011–015; BDD-024 |
| T18 | REQ-006,012,017,020–027,035; BR-012,017; **FastAPI** (ENG-001) | BDD-002,003,007,009–010,016,023; BDD-024 |
| T19 | REQ-036–038; DEC-011; ENG-011; deps/SDKs das tasks (incl. T20) nas imagens | BDD-020; BDD-024 |
| T20 | BR-023; DEC-015; **DT-001**; migrar inspeção Git T06 → **GitPython** | BDD-016,018 (preservar); BDD-024 |

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
| Integração sem SDK (DT-001) | T20 migra T06 para GitPython; ENG-013/014 nas tasks de adaptador; gate T19 |

## 8. Migração / rollback

Greenfield: sem migração de dados legados. Rollback = não promover imagem/tag; volumes PostgreSQL/Qdrant/Zoekt são descartáveis no MVP local. Schema versionado desde T03 para evoluções futuras.

**T20:** refactor interno de adaptação Git; rollback = reverter a task/PR; contrato de descoberta e catálogo permanecem estáveis.

## 9. Handoff

Candidato **v0.1.6** — `PO_PLAN_APPROVED` (2026-07-18). Delta sobre v0.1.5:

- ENG-013–016 alinhados a BR-023–024, DEC-015–016, BDD-024.
- Tasks T05–T19 com SDK/ORM explícitos; T03 confirmado ORM (sem refactor).
- Nova task `T20-refactor-local-discovery-git-sdk` (DT-001) em W3 (paralela após T06); T19 depende de T20; BDD-016/018 preservados.
- Estratégia anti-retrabalho: SDKs só nos adaptadores; T14 não importa SDKs.

Próximo gate: aprovação humana do plano (`HUMAN_PLAN_APPROVAL`). Não há aprovação humana inventada neste candidato.
