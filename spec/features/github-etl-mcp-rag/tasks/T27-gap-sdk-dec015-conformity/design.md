# Design — T27-gap-sdk-dec015-conformity

| Campo | Valor |
|---|---|
| Task ID | `T27-gap-sdk-dec015-conformity` |
| Feature | `github-etl-mcp-rag` |
| Versão | `v0.1.0` |
| Autor | `tech-lead-architect` |
| Data | 2026-07-19 |
| Branch | `feature/github-etl-mcp-rag-T27-gap-sdk-dec015-conformity` |

## 1. Contexto

BDD-024 (`requirements.md` §BDD-024) exige que GitHub, Git, `.gitignore`, Tree-sitter,
Qdrant, SLM/embeddings, cron, MCP, API HTTP da UI e PostgreSQL usem o SDK/cliente
oficial listado em DEC-015 (tabela §DEC-015), que o PostgreSQL do catálogo use
SQLAlchemy 2.x + Alembic + psycopg3 (BR-024), que o Zoekt seja um adaptador fino
sobre API/CLI oficial (DEC-016), que nenhuma integração reinvente cliente/CLI/
protocolo, e que a dívida DT-001 (parsing ad-hoc de `.git` em `T06-local-discovery`)
esteja eliminada.

`coverage-inventory.md` (T01 da feature filha `mvp-e2e-audit-hardening`) classifica
BDD-024 como `lacuna`, motivo: *"Smoke Robot ≠ conformidade integral DEC-015/BR-024
em todas as integrações"*. A evidência hoje é real, mas fragmentada e desigual entre
integrações:

| Integração DEC-015 | Evidência hoje | Nível |
|---|---|---|
| Git local (GitPython) / DT-001 | `tests/bdd/test_local_discovery_git_sdk.py` (T20-SDK-01..03) | BDD, explícito |
| `.gitignore` (pathspec) | `tests/bdd/test_file_eligibility.py` (ELIG-06) | BDD, explícito |
| Tree-sitter | `tests/bdd/test_treesitter_chunker.py` (TS-10) | BDD, explícito |
| Qdrant + embeddings OpenAI-compatible | `tests/bdd/test_qdrant_vector_store.py` (VS-05/06) | BDD, explícito |
| Zoekt (DEC-016) | `tests/bdd/test_zoekt_adapter.py` (ZOEKT-04) | BDD, mas só prova o **Fake**/Protocol — não prova que o adaptador **real** (`ZoektExactCodeIndex`) é fino sobre CLI/HTTP oficiais |
| Pins DEC-015 no manifesto | `tests/bdd/test_container_delivery.py` (CD-05) | BDD, presença no `pyproject.toml`; sem checagem de faixa de versão por linha da tabela |
| GitHub API (PyGithub) | `tests/unit/sources/github/test_client.py`, `tests/unit/snapshot/test_github*.py` | Unit, sem framing BDD-024 |
| Cron (APScheduler) | `tests/unit/schedule/test_scheduler.py`, `test_eng013.py` | Unit, sem framing BDD-024 |
| MCP (SDK `mcp`) | `tests/unit/mcp/test_imports.py` (UT-X02) | Unit, sem framing BDD-024 |
| API HTTP da UI (FastAPI) | `tests/unit/ui/test_imports.py` | Unit, sem framing BDD-024 |
| PostgreSQL (BR-024: SQLAlchemy 2.x + Alembic + psycopg3) | `tests/unit/delivery/test_wiring.py`, `tests/integration/test_postgres_catalog_repository.py` (requer Docker, `skip` sem ele) | Unit/integration parcial; sem checagem explícita de versão SQLAlchemy 2.x / driver psycopg3 na URL |

Não existe um único artefato executável que, ao passar, comprove o **texto integral**
de BDD-024 — cada cláusula está espalhada e algumas (Zoekt real, PyGithub, APScheduler,
MCP, FastAPI, driver psycopg3) não têm evidência com esse framing em `tests/bdd/`.

Achado adicional relevante para a decisão de aprovação: a review Architect de
`T01-coverage-inventory` (`spec/features/mvp-e2e-audit-hardening/tasks/T01-coverage-inventory/reviews.md`,
achado M-01) fixou a denylist anti-parcial (BDD-003/006/013/024 → `lacuna`)
explicitamente como piso **na ausência de regra explícita de prova integral**:
*"não podem ser `coberto-integral` sem regra explícita de prova integral"*. T27 é
exatamente essa regra explícita para BDD-024 — a mudança de status não contradiz
T01; realiza a condição que T01 previu.

## 2. Solução

Consolidar, no pai (`github-etl-mcp-rag`), uma suíte única `tests/bdd/test_dec015_conformity.py`
que:

1. Cobre por inspeção estática (sem infraestrutura real — consistente com o método
   já usado pelo inventário T01) cada linha da tabela DEC-015, BR-024 e DEC-016, com
   uma classe de teste por integração e nomenclatura rastreável (`DEC015-01`..`DEC015-12`).
2. Para integrações que **já** têm evidência BDD-024 explícita e substantiva
   (Git/GitPython, pathspec, Tree-sitter, Qdrant/openai, pins no manifesto), **não
   duplica a lógica de asserção** — referencia essas suítes por docstring/comentário
   e importa constantes/helpers já existentes quando aplicável (evita re-derivar AST
   walk, listas de pacotes etc.), acrescentando só o que ainda falta (ex.: faixa de
   versão por linha DEC-015, não apenas presença do nome do pacote).
3. Preenche as lacunas reais de framing/produção ainda não provadas como BDD-024:
   - **PyGithub** — binding nas duas superfícies de produção (`sources/github/client.py`,
     `snapshot/github.py`) + ausência de cliente HTTP caseiro para a API GitHub.
   - **APScheduler** — binding em `schedule/scheduler.py` / `schedule/cron_expr.py` +
     ausência de parser de cron manual.
   - **MCP oficial** — binding em `mcp/server.py` via `mcp.server.fastmcp.FastMCP`,
     framed como evidência BDD-024 (reaproveita `MCP_PKG`/`collect_imports` de
     `tests/unit/mcp/helpers.py`, sem reescrever o AST walk).
   - **FastAPI** — binding em `ui/app.py` / `ui/api.py`, framed como BDD-024
     (reaproveita constantes de `tests/unit/ui/test_imports.py` via import direto).
   - **BR-024 integral** — SQLAlchemy 2.x (`sqlalchemy>=2` + API 2.0: `DeclarativeBase`/
     `Session`, não `declarative_base()` legado) + Alembic (`run_alembic_upgrade`
     chama `alembic.command.upgrade`, não DDL manual) + psycopg3 (driver
     `postgresql+psycopg://`, nunca `+psycopg2://`), unindo `catalog/postgres/*`,
     `schedule/postgres.py` e `delivery/wiring.py` numa única prova.
   - **DEC-016 no adaptador real** — `ZoektExactCodeIndex`/`HttpZoektSearchTransport`/
     `SubprocessZoektIndexRunner` usam CLI (`zoekt-index`) e HTTP (`/api/search`)
     oficiais, sem reimplementar formato de shard/protocolo (o teste BDD atual só
     prova o Fake/Protocol — este é o gap mais substantivo do lote).
   - **DT-001** — cláusula final de BDD-024 (eliminação da dívida) citada
     explicitamente, com uma asserção mínima e direta sobre `sources/local/git_fs.py`
     (não a suíte completa de T20, que permanece a fonte de verdade comportamental).
4. Uma classe final `TestBDD024FullTextCoverage` mapeia cada cláusula do texto de
   BDD-024 (`Dado/Quando/Então/E/E/E`) para o(s) módulo(s) de teste responsável(is)
   e falha se qualquer módulo referenciado não existir/não importar — dando
   rastreabilidade de "todas as cláusulas têm dono" num único ponto de entrada.
5. Atualizar `coverage-inventory.md` (linha BDD-024: `status=coberto-integral`,
   `evidencia_pytest` apontando para a suíte nova + as já existentes,
   `nota_parcial_t21=n/a`, `motivo_lacuna=—`) e, como consequência necessária de
   coerência do próprio artefato de auditoria da feature filha, ajustar as duas
   regras de regressão que hoje fixam BDD-024 como lacuna permanente:
   - `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` — remover `"BDD-024"` de
     `T21_KNOWN_PARTIAL_OR_SMOKE` (mantendo 003/006/013 intocados).
   - `tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py` — remover `"BDD-024"` de
     `EXPECTED_LACUNA_BDDS` (mantendo `DENYLIST_PARTIAL` intocado, pois T27 continua
     citado no backlog como task que fechou a lacuna).

   Este ajuste é estritamente documental/evidência (nenhum `src/github_rag/**`,
   `e2e/robot/**` ou compose da feature filha é tocado) e implementa a exceção que a
   própria review de T01 previu. Ver §9 (Riscos) para o tratamento formal deste
   cross-feature touch.
6. Robot: **sem alteração**. `e2e/robot/mcp.robot` (tag `bdd024`) continua provando
   que as tools MCP aprovadas estão disponíveis em runtime — isso é evidência de
   comportamento observável, complementar e não substituível pela prova de
   conformidade de SDK, que é uma propriedade de implementação verificável por
   inspeção estática (mesmo método do inventário T01). Pins DEC-015 não exigem
   GitHub real nem stack e2e.

## 3. Componentes

| Componente | Arquivo | Tipo | Responsabilidade |
|---|---|---|---|
| Suíte consolidada BDD-024 | `tests/bdd/test_dec015_conformity.py` | novo | Ponto único de prova integral de BDD-024/DEC-015/BR-024/DEC-016/DT-001 |
| Ajuste de auditoria (status) | `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md` | edição | Linha BDD-024 → `coberto-integral` |
| Ajuste de regressão (auditoria) | `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` | edição pontual | Remove BDD-024 da denylist anti-parcial (exceção prevista por T01) |
| Ajuste de regressão (auditoria) | `tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py` | edição pontual | Remove BDD-024 do conjunto fixo de lacunas esperadas |

Nenhum componente de produção (`src/github_rag/**`) é alterado — T27 é só
teste/evidência/documentação, conforme escopo e handoff da task.

## 4. Fluxo

```
pytest tests/bdd/test_dec015_conformity.py
  ├─ DEC015-01 PinsMatrix           → lê pyproject.toml (reusa DEC015_RUNTIME_PACKAGES/
  │                                    DEC015_TREE_SITTER_GRAMMARS/_pyproject_deps/_dep_name
  │                                    de test_container_delivery) + checa faixa de versão
  ├─ DEC015-02 GitHubPyGithub       → inspect.getsource(client.py, snapshot/github.py)
  ├─ DEC015-03 GitPythonRef         → referência a test_local_discovery_git_sdk (DT-001)
  ├─ DEC015-04 PathspecRef          → referência a test_file_eligibility (ELIG-06)
  ├─ DEC015-05 TreeSitterRef        → referência a test_treesitter_chunker (TS-10)
  ├─ DEC015-06 QdrantOpenAIRef      → referência a test_qdrant_vector_store (VS-05/06)
  ├─ DEC015-07 APScheduler         → inspect.getsource(scheduler.py, cron_expr.py)
  ├─ DEC015-08 McpSdk               → collect_imports(MCP_PKG) via helper unit/mcp
  ├─ DEC015-09 FastApiUi            → import de helper unit/ui/test_imports
  ├─ DEC015-10 Br024Postgres        → inspect.getsource(models.py, wiring.py) + regex URL
  ├─ DEC015-11 Dec016ZoektReal      → inspect.getsource(index.py, client.py, runner.py)
  ├─ DEC015-12 Dt001Elimination     → inspect.getsource(git_fs.py) — zero parsing ad-hoc
  └─ TestBDD024FullTextCoverage     → mapa cláusula → módulo; importlib.import_module por item
       → falha cedo (import error) se algum módulo referenciado desaparecer
```

Todos os testes rodam sem GitHub real, sem Docker/Zoekt/Qdrant real e sem Robot —
100% inspeção estática/import, herdando o método já validado pelo inventário T01.

## 5. Dados

Não há dados de runtime novos. Os "dados" de entrada dos testes são:
- `pyproject.toml` (`[project.dependencies]`) — fonte única dos pins.
- Código-fonte de produção (`src/github_rag/**`) — lido via `inspect.getsource`/AST,
  nunca executado contra infraestrutura real.
- `coverage-inventory.md` — matriz markdown; edição de uma linha (BDD-024), sem
  alterar schema/colunas (evita quebrar `INV-05` e `INV-06`).

## 6. Erros

| Cenário | Comportamento esperado do teste |
|---|---|
| Pacote DEC-015 removido/rebaixado no `pyproject.toml` | `DEC015-01` falha citando o pacote e a linha da tabela |
| Produção volta a usar cliente HTTP caseiro (ex.: `requests`/`urllib` direto para GitHub/Qdrant/OpenAI) | teste da integração correspondente falha (assert de ausência de import banido) |
| Alembic é chamado por DDL manual em vez de `command.upgrade` | `DEC015-10` falha |
| `DATABASE_URL`/engine usa `postgresql+psycopg2://` | `DEC015-10` falha (driver errado = não é psycopg3) |
| Zoekt real volta a manipular formato de shard binário/protocolo próprio | `DEC015-11` falha (assert de ausência de manipulação binária de índice) |
| `git_fs.py` reintroduz parsing de `packed-refs`/`_resolve_git_dir` | `DEC015-12` falha (regressão DT-001) |
| Algum módulo BDD referenciado for removido/renomeado sem atualizar o mapa | `TestBDD024FullTextCoverage` falha no `import_module`, evitando lacuna silenciosa |

Nenhum destes testes lança segredo em mensagem de falha — todas as asserções operam
sobre fonte/estrutura, nunca sobre valores de `.env`/tokens.

## 7. Segurança

- Sem tokens, credenciais ou GitHub real em qualquer teste novo (consistente com
  REQ-048/BR-028).
- Nenhuma alteração em `.env.example`, composes ou segredos.
- A checagem de driver PostgreSQL (`psycopg` vs `psycopg2`) usa apenas strings de
  exemplo/fixture já presentes nos testes existentes (`postgresql+psycopg://u:p@...`),
  nunca URLs reais.

## 8. Compatibilidade

- Não altera contrato/comportamento de nenhuma classe de produção; é puramente
  aditivo em `tests/`.
- Não altera `e2e/robot/**`, composes, `Dockerfile` nem `src/github_rag/**`
  (conforme handoff/escopo do task file).
- A cobertura de linhas de produção (`--cov=github_rag`, `fail_under=95`) não piora
  — testes novos só leem/inspecionam módulos já exercitados; se algum trecho
  passar a ser importado por um teste novo que antes não era coberto, a cobertura
  só pode subir ou ficar igual.
- As duas edições em testes da feature filha (`test_mvp_e2e_audit_coverage_inventory.py`,
  `test_mvp_e2e_audit_gap_fill_backlog.py`) são puramente subtrativas em conjuntos
  fixos (`T21_KNOWN_PARTIAL_OR_SMOKE`, `EXPECTED_LACUNA_BDDS`) — não alteram schema,
  não afetam BDD-003/006/013/demais linhas, e preservam 100% das demais asserções
  dessas suítes.

## 9. Observabilidade

- Nenhum log/métrica de produto novo (task é só teste/documentação).
- Rastreabilidade textual: `TestBDD024FullTextCoverage` funciona como "mapa vivo"
  entre o texto de BDD-024 e os módulos de prova — falha explícita e nomeada por
  cláusula se um módulo referenciado desaparecer, servindo de guarda de regressão
  para futuras refatorações dessas integrações.
- `coverage-inventory.md` atualizado passa a apontar exatamente para
  `tests/bdd/test_dec015_conformity.py` como evidência primária consolidada,
  facilitando auditorias futuras (ex.: eventual T-fechamento do MVP).

## 10. Riscos

| Risco | Severidade | Mitigação |
|---|---|---|
| Editar testes de regressão de uma feature filha já fechada (`CLOSURE_READY` em T07) pode ser lido como reabertura de escopo fora de `github-etl-mcp-rag` | Média | Escopo estritamente limitado a remover BDD-024 de dois conjuntos fixos que a própria review de T01 (M-01) previu como piso condicional ("sem regra explícita de prova integral"); nenhuma linha de produto/robot/compose da filha é tocada; decisão registrada e justificada neste design com citação da review de origem |
| Suíte nova cai em duplicação lógica real (não apenas referência) com as suítes já existentes, aumentando manutenção | Média | Design exige que, para integrações já providas com framing BDD-024 (Git/pathspec/Tree-sitter/Qdrant/pins), a suíte nova só referencie/importe, sem reimplementar as asserções de comportamento já cobertas — Developer/QA devem revisar isso explicitamente na etapa Blue |
| Falso positivo: assert de "ausência de import banido" via `inspect.getsource`/AST pode não capturar import indireto (ex.: `importlib.import_module("requests")`) | Baixa | Mesmo padrão de risco já aceito pelas suítes homólogas existentes (UI/MCP `FORBIDDEN_IMPORTS`); não é uma regressão introduzida por T27 |
| `ZoektExactCodeIndex` (DEC-016) pode evoluir e passar a manipular bytes de shard sem que a nova asserção detecte (assert é por ausência de padrões conhecidos, não allowlist positiva) | Baixa | Registrar no teste o racional (comentário) e literals esperados (`zoekt-index`, `/api/search`) como allowlist positiva além da checagem negativa |
| Ambiente de execução do design (worktree) não tem `pytest` instalado (sem venv) — testes não foram executados localmente nesta etapa | Média | Escopo desta etapa é design; Developer deve criar/usar `.venv` com `pip install -e .[dev]` e rodar `pytest tests/bdd/test_dec015_conformity.py tests/bdd/test_mvp_e2e_audit_coverage_inventory.py tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py -q` como primeiro gate antes do restante da suíte completa |

## 11. Rollback

- Toda a mudança está isolada em `tests/**` e em uma linha de `coverage-inventory.md`
  — revert de um único commit (ou `git checkout` dos 4 arquivos) restaura o estado
  anterior sem qualquer efeito em produção, robot ou composes.
- Se a review de QA/Architect concluir que o cross-feature touch (§10, risco 1) não
  deve ocorrer nesta task, a alternativa de rollback parcial é: manter
  `coverage-inventory.md` com `status=lacuna` e `T21_KNOWN_PARTIAL_OR_SMOKE`/
  `EXPECTED_LACUNA_BDDS` inalterados, e a nova suíte `test_dec015_conformity.py`
  passa a ser apenas evidência adicional referenciada em `nota_parcial_t21` (sem
  fechar formalmente a lacuna no inventário) — decisão explícita a registrar em
  `approvals.md` desta task.

## 12. Critérios de aceite mapeados

- BDD-024 (texto integral) → `tests/bdd/test_dec015_conformity.py` (12 classes +
  `TestBDD024FullTextCoverage`) + suítes referenciadas.
- BR-024 → `DEC015-10`.
- DEC-016 → `DEC015-11` (adaptador real, não só Fake).
- DT-001 → `DEC015-12` + regressão preservada em `test_local_discovery_git_sdk.py`.
- Sem secrets versionados → §7.
- Implementação no pipeline do pai → todos os arquivos ficam em
  `github-etl-mcp-rag`/`tests/**`; os dois ajustes pontuais em testes da filha são
  tratados como consequência documentada de auditoria, não como implementação de
  feature filha.

---

**Decisão:** `APPROVED_BY_ARCHITECT`
**Data:** 2026-07-19
**Autor:** tech-lead-architect
**Versão:** v0.1.0
