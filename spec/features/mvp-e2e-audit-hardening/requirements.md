# Requisitos — Auditoria e hardening da prova e2e do MVP

## Identificação

- **Feature ID:** `mvp-e2e-audit-hardening`
- **Versão:** 0.1.0
- **Estado:** `APPROVED`
- **Natureza:** feature filha / delta operacional sobre a prova e2e do MVP já especificado em `github-etl-mcp-rag` (0.5.0 / T21). Não redefine o produto; audita cobertura, executa provas e gera tasks de correção e lacuna **dentro** de `github-etl-mcp-rag`.
- **Feature pai / destino das tasks:** `github-etl-mcp-rag`
- **Dependências:**
  - `github-etl-mcp-rag` requisitos 0.5.0 (REQ-043–052, BDD-001–024, BDD-026–028);
  - artefatos T19 (`docker-compose.e2e.yml` + empacotamento) e T21 (`e2e/robot/**`, `python -m github_rag.e2e`).
- **Rastreabilidade:** requisitos `REQ-*`, regras `BR-*`, decisões `DEC-*` e cenários `BDD-*` deste documento.
- **Aprovação humana (requisitos 0.1.0):** `aprovado` em 2026-07-18 por `humano` (commit candidato `c460bd5`).

## Justificativa do feature-id

Escolhido **`mvp-e2e-audit-hardening`** (feature filha clara) em vez de incrementar `github-etl-mcp-rag` 0.5.0 porque:

1. o trabalho é de **auditoria + execução + abertura de tasks**, não de novo comportamento de produto;
2. o produto MVP e a ownership T21 permanecem em `github-etl-mcp-rag`;
3. bugs de produto, flakiness e lacunas de teste resultantes **viram tasks novas dentro de `github-etl-mcp-rag`**, mantendo rastreabilidade sem misturar processo de auditoria com REQ funcionais do ETL/RAG/MCP.

## Problema

A suíte Robot e os contratos T21 existem, mas ainda não há garantia de que (a) cobrem o MVP **integral** (BDD-001–024, não só fatias “parciais” DEC-019/T21), (b) a prova automática em stack real passa, e (c) falhas/lacunas viram trabalho rastreável de correção no feature pai.

## Objetivos

- **REQ-001:** Auditar a suíte Robot (`e2e/robot/**`) e o green path canônico contra o texto integral de BDD-001–024 de `github-etl-mcp-rag` (exceto BDD-015, que permanece validação humana fora do Robot).
- **REQ-002:** Executar automaticamente a prova e2e via `python -m github_rag.e2e` (Podman + `docker-compose.e2e.yml` + GitHub real do repositório de referência).
- **REQ-003:** Executar a suíte pytest do projeto relativa a **todas as tasks** de `github-etl-mcp-rag` (unitários + BDD de contrato), além da prova Robot em stack real.
- **REQ-004:** Criar/usar `.env` local **não versionado** (a partir de `.env.example`) com token GitHub válido para `camilocoelhogomes/source-code`; nunca commitá-lo.
- **REQ-005:** Transformar todo achado (bug de produto, flakiness, gap de cobertura ou assert fraco do Robot) em **task(s) de correção/lacuna** em `spec/features/github-etl-mcp-rag/tasks/`, agrupadas por superfície.
- **REQ-006:** Ordem obrigatória: (1) rodar green path atual e abrir tasks do que falhar; (2) depois fechar lacunas de teste (cobertura integral + browser na UI).
- **REQ-007:** Validação de UI do MVP na prova e2e deve incluir interação via **browser** (API HTTP sozinha não basta para declarar cobertura de fluxos UI).

## Personas

- **Operador HITL / mantenedor:** gera token GitHub, preenche `.env` local, sobe Podman e dispara a prova.
- **Product Owner / orquestração:** valida escopo MVP integral e que tasks abertas cobrem falhas e lacunas.
- **Engenharia (via tasks no pai):** corrige produto e fortalece a suíte Robot conforme tasks abertas.

## Escopo funcional

### Auditoria de cobertura (MVP integral)

- **REQ-008:** Produzir inventário BDD-001–024 × evidência na suíte (caso Robot, keyword browser, contrato pytest ou **lacuna explícita**).
- **REQ-009:** Marcar como lacuna qualquer BDD cujo assert atual seja só parcial/API-smoke quando o critério integral exigir mais (ex.: exclusão de arquivos, progresso por arquivo, falha parcial → `erro`+histórico, paralelismo sob limite, checkbox/fluxo UI no browser).
- **REQ-010:** BDD-015 permanece fora do Robot e fora desta auditoria automatizada.

### Preparação de ambiente

- **REQ-011:** Garantir existência de `.env` na raiz do repositório (não versionado), com pelo menos token para o fluxo GitHub (`GITHUB_TOKEN` e/ou `E2E_GITHUB_TOKEN`) e demais vars canônicas alinhadas a REQ-049 do pai / `.env.example`.
- **REQ-012:** Runtime da prova: **Podman** + `docker-compose.e2e.yml`; repositório de referência: `camilocoelhogomes/source-code`.
- **REQ-013:** Entrypoint canônico da prova Robot: `python -m github_rag.e2e`.

### Execução (run-first)

- **REQ-014:** Na fase 1, executar pytest (todas as tasks do pai) e em seguida (ou no fluxo canônico) a prova Robot green path atual **sem** expandir antes a cobertura integral.
- **REQ-015:** Registrar resultado observável: verde / falha por cenário ou suíte, com artefatos em `e2e/results/` quando aplicável (já gitignored).

### Abertura de tasks no feature pai

- **REQ-016:** Para cada falha ou lacuna, criar task em `github-etl-mcp-rag` agrupada por superfície:
  - `health` / boot / compose;
  - `catalog_indexing`;
  - `ui` (inclui browser);
  - `mcp`;
  - `negative` / config inválida;
  - `tooling-e2e` (flakiness, timeouts, asserts fracos, credenciais, launcher).
- **REQ-017:** Cada task deve classificar o achado como: `produto` | `flakiness` | `gap-teste` | `assert-fraco` (ou combinação documentada).
- **REQ-018:** Tasks de lacuna cobrem adição/fortalecimento de testes (Robot/browser/contratos) até o critério integral BDD-001–024 (exceto 015).

### Fase gap-fill (depois do run)

- **REQ-019:** Somente após a fase run-first e a abertura das tasks de falha, planejar/executar (via tasks no pai) o fechamento das lacunas de cobertura integral e browser UI.

## Regras de negócio

- **BR-001:** Critério de cobertura desta feature = texto integral BDD-001–024 do pai; fatias “parciais” de T21/DEC-019 **não** bastam para declarar auditoria concluída.
- **BR-002:** Ownership da suíte Robot permanece em `github-etl-mcp-rag` / T21; esta feature não cria suíte paralela sob outro dono.
- **BR-003:** Ownership dos 3 composes/Dockerfile permanece em T19; consumo apenas.
- **BR-004:** Segredos nunca versionados; `.env` real fora do git; fixtures sem PAT em claro.
- **BR-005:** Todo achado vira task no pai — não se descarta flakiness nem gap como “fora”.
- **BR-006:** Agrupamento de tasks é por superfície (REQ-016), não necessariamente 1:1 por cenário BDD.
- **BR-007:** Ordem run-first → tasks de falha → gap-fill é obrigatória (REQ-006).
- **BR-008:** UI MVP exige prova com browser além de APIs.
- **BR-009:** `docs-cicd-e2e-release` não é dona desta auditoria nem das tasks de correção; apenas permanece consumidora futura da suíte T21.

## Fluxo principal

1. Operador gera token GitHub com acesso a `camilocoelhogomes/source-code` e cria `.env` local a partir de `.env.example` (sem commit).
2. Auditoria documental: inventário BDD-001–024 × suíte atual → lacunas listadas.
3. Fase run-first: pytest (todas as tasks do pai) + `python -m github_rag.e2e`.
4. Achados de falha → tasks em `github-etl-mcp-rag` por superfície.
5. Fase gap-fill: tasks de lacuna (cobertura integral + browser UI) no mesmo feature pai.
6. Encerramento desta feature quando inventário, execuções e tasks estiverem registrados e aprováveis.

## Fluxos alternativos e erros

- Token ausente/inválido: prova falha de forma explícita; vira task `tooling-e2e` / credencial se o comportamento diverge do contrato T21; operador deve corrigir `.env` para reexecutar.
- Stack não sobe (Podman/compose): falha explícita; task por superfície `health`/compose.
- Rate limit GitHub / timeout: classificar `flakiness` e abrir task `tooling-e2e` (retry/timeout), sem ignorar.
- Pytest vermelho em task já entregue: task de `produto` ou teste regressivo na superfície correspondente.
- Lacuna sem falha runtime: ainda assim task `gap-teste` (fase 2).

## Dados e integrações

- Config e2e: `e2e/fixtures/config.e2e.json` + volumes `e2e/fixtures/repos`.
- GitHub real (sem mock) para o repo de referência.
- Stack: Podman, PostgreSQL, Zoekt, Qdrant, SLM/OpenAI-compatible conforme compose e2e.
- Superfícies: UI `:8080` (API + browser), MCP `:8001`, `/healthz`.

## Restrições e compatibilidade

- Não implementar correções de produto nesta feature sem passar pelo pipeline de tasks do pai.
- Não versionar `.env` nem tokens.
- Não automatizar BDD-015.
- Não transferir ownership Robot para `docs-cicd-e2e-release`.
- Cobertura unitária/BDD do projeto permanece ≥ 95% nas tasks de correção do pai (herdado).

## Segurança

- Token só em env local / secrets CI; redaction em logs e artefatos Robot (alinhado BDD-014/027 do pai).
- Keywords/browser não devem capturar ou persistir segredos em screenshots/logs commitáveis.

## Métricas de sucesso

- Inventário BDD-001–024 (exc. 015) completo com status coberto / lacuna.
- Pytest (todas as tasks) e `python -m github_rag.e2e` executados e resultados registrados.
- Toda falha e toda lacuna refletida em task(s) no pai, agrupadas por superfície.
- Plano de gap-fill (browser + asserts integrais) documentado em tasks após o run-first.

## Fora de escopo

- Redefinir requisitos funcionais do produto ETL/RAG/MCP além do necessário para apontar bugs.
- Implementar as correções nesta feature (isso ocorre nas tasks abertas em `github-etl-mcp-rag`).
- Esteira GitHub Actions, docs EN, release GHCR (`docs-cicd-e2e-release`).
- Mock da API GitHub.
- Automatizar narrativa Discovery no Cursor (BDD-015).
- Declarar MVP entregue sem T19+T21 verdes no critério do pai (esta feature só produz evidência e backlog de correção/lacuna).

## Decisões

- **DEC-001:** Feature filha `mvp-e2e-audit-hardening`; tasks de resultado em `github-etl-mcp-rag`.
- **DEC-002:** Critério de auditoria = BDD-001–024 **integral** (não parcial T21).
- **DEC-003:** UI exige browser.
- **DEC-004:** Execução canônica = `python -m github_rag.e2e` + pytest de todas as tasks do pai.
- **DEC-005:** `.env` local HITL não versionado; token gerado pelo operador para o repo de referência.
- **DEC-006:** Achados: produto + flakiness + gap + assert fraco → todos viram tasks.
- **DEC-007:** Granularidade de tasks = por superfície.
- **DEC-008:** Ordem = run-first, depois gap-fill.

## Dúvidas resolvidas

| # | Pergunta | Resposta humana |
|---|---|---|
| 1 | Critério MVP parcial T21 vs integral? | Integral BDD-001–024 |
| 2 | Gaps viram tasks? | Sim, tasks de lacuna de teste |
| 3 | UI só API? | Não — browser obrigatório |
| 4 | Como executar / credenciais? | `python -m github_rag.e2e`; criar `.env` local; Podman + token para `camilocoelhogomes/source-code` |
| 5 | Flakiness/gap viram task? | Sim, ambos |
| 6 | Granularidade? | Agrupar por superfície |
| 7 | O que rodar? | pytest de todas as tasks + Robot stack real |
| 8 | Ordem? | Rodar green path primeiro; depois fechar lacunas |

## Critérios de aceite BDD

### BDD-001 — Auditoria de cobertura MVP integral

**Dado** os cenários BDD-001–024 de `github-etl-mcp-rag` (exceto BDD-015)  
**E** a suíte Robot/T21 atual em `e2e/`  
**Quando** a auditoria de cobertura for concluída  
**Então** cada BDD deve estar classificado como coberto integralmente ou como lacuna explícita  
**E** fatias parciais existentes não podem ser aceitas como cobertura integral sem task de lacuna.

### BDD-002 — Preparação de `.env` local não versionado

**Dado** `.env.example` na raiz  
**Quando** o operador preparar o ambiente HITL  
**Então** deve existir `.env` local com token válido para `camilocoelhogomes/source-code`  
**E** `.env` permanece fora do versionamento  
**E** nenhum segredo é commitado.

### BDD-003 — Execução automática do green path (run-first)

**Dado** Podman disponível e `.env` válido  
**Quando** for executado `python -m github_rag.e2e` na fase run-first  
**Então** a stack e2e sobe e a suíte Robot green path atual é exercitada  
**E** o resultado (sucesso ou falha por cenário/suíte) fica registrado de forma observável.

### BDD-004 — Execução pytest de todas as tasks do pai

**Dado** o ambiente de testes do projeto  
**Quando** a fase run-first executar pytest  
**Então** os testes unitários/BDD de **todas as tasks** de `github-etl-mcp-rag` são executados  
**E** falhas geram achados para abertura de tasks no pai.

### BDD-005 — Tasks de falha agrupadas por superfície

**Dado** falhas na fase run-first (produto, flakiness, assert fraco ou tooling)  
**Quando** os achados forem convertidos em trabalho  
**Então** devem existir tasks em `github-etl-mcp-rag` agrupadas por superfície (REQ-016)  
**E** cada task declara a classificação do achado (REQ-017).

### BDD-006 — UI com browser na cobertura integral

**Dado** fluxos UI do MVP (listagem, seleção/indexação, busca, estados)  
**Quando** as tasks de lacuna/gap-fill forem especificadas  
**Então** a prova exigida inclui automação via browser  
**E** cobertura apenas por API não encerra a lacuna de UI.

### BDD-007 — Ordem run-first depois gap-fill

**Dado** o início desta feature  
**Quando** o plano for executado  
**Então** a execução do green path e a abertura de tasks de falha ocorrem antes  
**E** o fechamento de lacunas de teste (cobertura integral + browser) ocorre depois  
**E** não se bloqueia o run-first para primeiro expandir a suíte.

### BDD-008 — Lacunas viram tasks mesmo sem falha runtime

**Dado** inventário com BDD integral não coberto e green path possivelmente verde  
**Quando** a fase gap-fill for planejada  
**Então** ainda assim são abertas tasks `gap-teste` no pai  
**E** a auditoria não pode ser encerrada só com “green path passou”.

## Riscos

- Prova com GitHub real: rate limit e flakiness aumentam ruído; mitigação = tasks `tooling-e2e` + retries já previstos na suíte.
- Expandir para browser aumenta custo/tempo da suíte; fica na fase gap-fill via tasks.
- Escopo integral pode gerar muitas lacunas frente ao T21 parcial; agrupamento por superfície evita explosão de tasks.
- Token HITL depende do operador; sem token a prova não autentica o MVP.

## Rastreabilidade (resumo)

| Valor | REQ | BDD |
|---|---|---|
| Auditar MVP integral | REQ-001, 008–010; BR-001 | BDD-001, BDD-008 |
| Rodar prova automática + pytest | REQ-002–004, 011–015 | BDD-002–004 |
| Tasks no pai por superfície | REQ-005, 016–018; BR-005–006 | BDD-005 |
| Browser na UI | REQ-007; BR-008 | BDD-006 |
| Ordem run-first → gap-fill | REQ-006, 019; BR-007 | BDD-007 |
| Sem secrets no git | REQ-004, 011; BR-004 | BDD-002 |
