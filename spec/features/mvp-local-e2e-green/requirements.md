# Requisitos — MVP local verde (e2e + imagem pré-buildada + loop autônomo)

## Identificação

- **Feature ID:** `mvp-local-e2e-green`
- **Versão:** 0.1.0
- **Estado:** `APPROVED`
- **Natureza:** feature filha / delta operacional de entrega do MVP local. Orquestra execução e2e, abertura de tasks de correção, imagem local pré-buildada e merge automático quando a prova Robot estiver verde. Não redefine comportamento de produto além do necessário para fechar gaps detectados pelo e2e.
- **Feature pai / destino das tasks de bug:** `github-etl-mcp-rag`
- **Feature irmã / contexto:** `mvp-e2e-audit-hardening` (já `APPROVED`; inventário e auditoria)
- **Dependências:**
  - `github-etl-mcp-rag` requisitos 0.5.0 (REQ-043–052, BDD-001–024, BDD-026–028);
  - tasks abertas T22–T27 (gaps) e ownership T19 (composes/Dockerfile) + T21 (Robot, `python -m github_rag.e2e`);
  - skill `autonomous-implementation-orchestrator` para implementação autônoma das tasks geradas.
- **Rastreabilidade:** requisitos `REQ-*`, regras `BR-*`, decisões `DEC-*` e cenários `BDD-*` deste documento.
- **Aprovação (requisitos 0.1.0):** `APPROVED` em 2026-07-19 por `operador` — gate HITL dispensado explicitamente pelo operador (aprovação implícita autorizada).

## Justificativa do feature-id

Escolhido **`mvp-local-e2e-green`** porque o resultado desejado é objetivo e observável: **MVP rodando localmente com todos os testes de negócio (Robot) verdes**, usando **imagem local pré-buildada** referenciada por `docker-compose.yml`, com **loop autônomo de correção** até estabilizar. Diferencia-se de `mvp-e2e-audit-hardening` (auditoria/inventário) e de `docs-cicd-e2e-release` (CI/release).

## Problema

O MVP possui suíte Robot e tasks de gap (T22–T27), mas o ambiente local ainda não garante: (a) green path e2e estável via `python -m github_rag.e2e`, (b) conversão automática de falhas em trabalho de correção, (c) imagem local reutilizável sem `build` a cada `compose up`, (d) encerramento automático quando a prova Robot passa.

## Objetivos

- **REQ-001:** Executar a prova e2e local canônica via `python -m github_rag.e2e` (Podman + stack real + GitHub real do repositório de referência), conforme `e2e/README.md`.
- **REQ-002:** Considerar “testes de negócio” a suíte Robot MVP green path (`health`, `catalog_indexing`, `ui`, `ui_browser`, `mcp`, `negative`), com `--exclude bdd015` (BDD-015 permanece fora do Robot).
- **REQ-003:** Para **cada falha** observável (cenário Robot, suíte, boot/compose, launcher ou assert de negócio), gerar **nova task de implementação** em `spec/features/github-etl-mcp-rag/tasks/` classificada como correção de bug/gap (`produto` | `flakiness` | `gap-teste` | `tooling-e2e`).
- **REQ-004:** Após gerar ou atualizar tasks com falhas pendentes, executar **handoff automático** para `autonomous-implementation-orchestrator` (sem gate HITL intermediário; Architect aprova etapas do pipeline por task).
- **REQ-005:** Repetir o ciclo **rodar e2e → tasks por falha → orquestrador → merge** até a prova Robot estar **100% verde** no ambiente local preparado.
- **REQ-006:** Entregar imagem de container **local pré-buildada e taggeada** (`github-rag:local`, plataforma `linux/amd64`), produzida a partir do `Dockerfile` do projeto, **sem** depender de rebuild implícito a cada subida do stack end-user.
- **REQ-007:** Alterar `docker-compose.yml` (ownership T19) para referenciar a imagem local taggeada (`image: github-rag:local`) em vez de `build:` como caminho padrão de subida; rebuild da imagem ocorre apenas por comando explícito documentado (ex.: `docker build -t github-rag:local .`).
- **REQ-008:** Quando a prova Robot (`python -m github_rag.e2e`) concluir com **exit code 0** e artefatos em `e2e/results/` consistentes com sucesso, **aprovação do teste Robot é suficiente** para **merge automático na `main`** dos PRs das tasks deste ciclo (sem gate humano adicional de revisão).
- **REQ-009:** Manter `.env` local não versionado com token GitHub válido para o repo de referência (`camilocoelhogomes/source-code` / remoto do projeto); nunca commitar segredos.
- **REQ-010:** Respeitar e consumir tasks de gap já abertas (T22–T27) antes ou em paralelo às novas tasks geradas por falhas runtime; não duplicar task para o mesmo achado já rastreado.

## Personas

- **Operador local:** prepara Podman, `.env`, deps e2e (`pip install -e ".[e2e]"`, `rfbrowser init`), dispara o loop ou delega ao orquestrador.
- **Orquestrador principal:** executa e2e, parseia falhas, abre/atualiza tasks, invoca `autonomous-implementation-orchestrator`, monitora PRs e dispara merge automático quando Robot verde.
- **Engenharia (via tasks no pai):** corrige produto/tooling/imagem conforme tasks geradas ou T22–T27.

## Escopo funcional

### Execução e2e local

- **REQ-011:** Entrypoint canônico: `python -m github_rag.e2e` (`DefaultRobotMvpSuite` + launcher Podman).
- **REQ-012:** Pré-requisitos documentados em `e2e/README.md`: Podman + compose provider, `.env`, deps e2e, `rfbrowser init`.
- **REQ-013:** Registrar resultado observável por execução: exit code, suítes/cenários falhos, paths de artefatos Robot em `e2e/results/` (gitignored).
- **REQ-014:** Falha de token, stack, timeout ou rate limit deve ser classificada e virar task (não abortar o loop sem registro).

### Geração de tasks por falha

- **REQ-015:** Uma falha distinta → ao menos uma task em `github-etl-mcp-rag`, agrupada por superfície: `health` | `catalog_indexing` | `ui` | `mcp` | `negative` | `tooling-e2e` | `container-delivery`.
- **REQ-016:** Cada task nova deve incluir: evidência da falha (comando, cenário Robot, log sanitizado), classificação do achado, critério de aceite ligado ao cenário BDD do pai quando aplicável, estado inicial `READY_FOR_IMPLEMENTATION`.
- **REQ-017:** Reexecução e2e após merge de task deve confirmar correção; falha residual gera nova task ou reabertura documentada.

### Handoff autônomo

- **REQ-018:** Ao detectar tasks `READY_FOR_IMPLEMENTATION` (novas ou T22–T27 pendentes), invocar `autonomous-implementation-orchestrator` com plano/handoff mínimo: `feature-id` destino, lista de `task-id`, dependências e critério de parada (Robot verde).
- **REQ-019:** Cada task implementada em branch `feature/github-etl-mcp-rag-<task-id>` (ou empilhada conforme dependências do plano); cobertura ≥ 95% herdada do pipeline autônomo.
- **REQ-020:** O orquestrador **não** exige aprovação humana intermediária; substituída pela aprovação do Architect em cada etapa da task.

### Imagem local e compose end-user

- **REQ-021:** Tag canônica local: `github-rag:local` (`linux/amd64`).
- **REQ-022:** Comando de build explícito documentado (ex.: `docker build --platform linux/amd64 -t github-rag:local .` ou equivalente Podman).
- **REQ-023:** `docker-compose.yml` usa `image: github-rag:local` no serviço `app`; remoção ou override opcional de `build:` para evitar rebuild silencioso no fluxo padrão `docker compose up`.
- **REQ-024:** Subida end-user com imagem pré-buildada: `docker compose up -d` (sem `--build`) deve funcionar quando `github-rag:local` existir localmente.
- **REQ-025:** Alterações de compose/imagem permanecem compatíveis com `docker-compose.e2e.yml` e `docker-compose.dev.yml` (T19); e2e canônico continua Podman + modelo descrito em `e2e/README.md`.

### Merge automático na main

- **REQ-026:** Após Robot verde local, merge automático na `main` dos PRs abertos das tasks do ciclo, **sem force push**, na ordem de dependências documentada.
- **REQ-027:** Robot verde = exit 0 de `python -m github_rag.e2e` + suites REQ-002 passando; pytest unitário/BDD do projeto deve permanecer verde nas branches mergeadas (gate do pipeline autônomo).
- **REQ-028:** Se merge automático falhar (conflito, CI remota, regressão pós-merge), registrar bloqueio e gerar task `tooling-e2e` ou reexecutar ciclo; não declarar MVP local entregue.

## Regras de negócio

- **BR-001:** Critério de “MVP local entregue” = Robot green path 100% verde + `docker compose up -d` (sem rebuild) com `github-rag:local` + `/healthz` OK.
- **BR-002:** Toda falha e2e vira task no pai — não se ignora flakiness nem falha de tooling.
- **BR-003:** BDD-015 permanece fora do Robot e fora do critério de merge automático.
- **BR-004:** Segredos nunca versionados; redaction em logs/artefatos Robot.
- **BR-005:** Não duplicar task se T22–T27 já cobrem o mesmo achado; atualizar task existente com nova evidência.
- **BR-006:** Merge automático só após Robot verde **local** na execução de validação final do ciclo (não apenas CI remota).
- **BR-007:** Imagem local deve ser rebuildada explicitamente após merges que alterem código da app containerizada.
- **BR-008:** Ownership Robot (T21) e composes (T19) permanecem no pai; esta feature orquestra e exige deltas via tasks, não forks paralelos de suíte.

## Fluxo principal

1. Operador prepara ambiente local (`.env`, Podman, deps e2e, `rfbrowser init`).
2. Build explícito da imagem `github-rag:local` (se ausente ou após merges).
3. Executar `python -m github_rag.e2e`.
4. Se falhar: registrar evidência → criar/atualizar tasks no pai → handoff `autonomous-implementation-orchestrator`.
5. Orquestrador implementa tasks (T22–T27 + novas), abre PRs, Architect aprova etapas.
6. Após merges das tasks do ciclo: rebuild imagem se necessário → reexecutar passo 3.
7. Quando Robot verde: merge automático remanescente (se houver) → validação final e2e → declarar MVP local entregue.

## Fluxos alternativos e erros

- Token ausente/inválido: falha explícita; task `tooling-e2e`/credencial; operador corrige `.env`.
- Imagem local ausente: `docker compose up` falha; operador executa build explícito (REQ-022).
- Task falha no pipeline autônomo: registrar, não bloquear tasks independentes; reexecutar e2e quando onda aplicável concluir.
- Conflito de merge automático: pausar merge auto; task `tooling-e2e`; operador notificado.
- Rate limit/timeout GitHub: classificar `flakiness`; task com retry/timeout; loop continua.

## Dados e integrações

- Config e2e: `e2e/fixtures/config.e2e.json`, volumes `e2e/fixtures/repos`.
- GitHub real (repo de referência do projeto).
- Stack: Podman/Docker, PostgreSQL, Zoekt, Qdrant, SLM (Ollama).
- Superfícies: UI `:8080`, MCP `:8001`, `/healthz`.
- Imagem: `github-rag:local` referenciada em `docker-compose.yml`.

## Restrições e compatibilidade

- Plataforma primária `linux/amd64` (ENG-006).
- ENG-009: nunca montar `.venv` do host no container app.
- Cobertura ≥ 95% nas tasks de correção (herdado).
- Não transferir ownership da suíte Robot para outra feature.
- `docker-compose.dev.yml` permanece modelo infra-only + app no host para iteração; delta de imagem foca `docker-compose.yml` end-user.

## Segurança

- Token só em `.env` local / env exportado; nunca commit.
- Artefatos Robot e logs de falha sanitizados (sem PAT).
- Merge automático proibido de force push na `main`.

## Métricas de sucesso

- `python -m github_rag.e2e` exit 0 no ambiente local preparado.
- Todas as suítes REQ-002 verdes (exc. BDD-015).
- `docker compose up -d` sem `--build` sobe stack end-user com `github-rag:local`.
- Tasks de falha rastreadas e fechadas (incl. T22–T27 quando aplicável).
- PRs do ciclo mergeados na `main` sem gate humano adicional pós-Robot verde.

## Fora de escopo

- Redefinir requisitos funcionais do produto além do necessário para corrigir falhas e2e.
- Automatizar BDD-015 (Discovery narrativa no Cursor).
- Publicação GHCR / release (`docs-cicd-e2e-release`) como gate desta feature.
- Mock da API GitHub.
- Substituir revisão humana em features que **não** sejam correções deste loop e2e.
- Auditoria documental de cobertura BDD integral (permanece em `mvp-e2e-audit-hardening`).
- Hot-reload de `./src` no compose end-user (permanece em `docker-compose.dev.yml`).

## Decisões

- **DEC-001:** Feature filha `mvp-local-e2e-green`; tasks de bug/gap em `github-etl-mcp-rag`.
- **DEC-002:** Entrypoint e2e canônico = `python -m github_rag.e2e`.
- **DEC-003:** Cada falha e2e gera (ou atualiza) task de implementação no pai.
- **DEC-004:** Handoff automático para `autonomous-implementation-orchestrator` sem HITL intermediário.
- **DEC-005:** Robot verde local = critério suficiente para merge automático na `main` (operador dispensou gate humano de merge).
- **DEC-006:** Tag de imagem local canônica = `github-rag:local`; `docker-compose.yml` referencia `image`, não `build` no fluxo padrão.
- **DEC-007:** Rebuild de imagem apenas por comando explícito, não por `compose up` implícito.
- **DEC-008:** Consumir T22–T27 existentes; evitar duplicação de backlog.
- **DEC-009:** BDD-015 excluído do critério de verde e merge auto.
- **DEC-010:** Aprovação de requisitos 0.1.0 pelo operador em 2026-07-19 sem gate HITL formal.

## Critérios de aceite BDD

### BDD-001 — Execução e2e local canônica

**Dado** Podman disponível, `.env` válido e deps e2e instaladas  
**Quando** o operador executar `python -m github_rag.e2e`  
**Então** a stack sobe e a suíte Robot green path (REQ-002) é exercitada  
**E** o exit code e artefatos em `e2e/results/` ficam registrados.

### BDD-002 — Task por falha

**Dado** uma execução e2e com ao menos um cenário/suíte falho  
**Quando** o loop processar o resultado  
**Então** deve existir task em `github-etl-mcp-rag` com evidência sanitizada e classificação do achado  
**E** a task inicia em `READY_FOR_IMPLEMENTATION`  
**E** achados já cobertos por T22–T27 são atualizados, não duplicados.

### BDD-003 — Handoff autônomo

**Dado** tasks pendentes de correção (novas ou T22–T27)  
**Quando** o orquestrador principal concluir o registro das falhas  
**Então** invoca `autonomous-implementation-orchestrator` automaticamente  
**E** cada task segue pipeline autônomo com aprovação do Architect.

### BDD-004 — Loop até verde

**Dado** falhas corrigidas via tasks mergeadas  
**Quando** a imagem local for rebuildada se necessário e o e2e for reexecutado  
**Então** o ciclo repete até `python -m github_rag.e2e` retornar exit 0  
**E** nenhum cenário da suíte REQ-002 permanece falho.

### BDD-005 — Imagem local pré-buildada

**Dado** o `Dockerfile` do projeto  
**Quando** o operador executar o build explícito documentado  
**Então** a imagem `github-rag:local` existe localmente (`linux/amd64`)  
**E** contém o entrypoint `python -m github_rag.delivery`.

### BDD-006 — Compose end-user sem rebuild

**Dado** a imagem `github-rag:local` presente  
**E** `docker-compose.yml` referenciando `image: github-rag:local`  
**Quando** o operador executar `docker compose up -d` sem `--build`  
**Então** o serviço `app` sobe usando a imagem local  
**E** `GET /healthz` responde sucesso após healthy.

### BDD-007 — Merge automático pós-Robot verde

**Dado** PRs abertos das tasks do ciclo de correção  
**E** validação final `python -m github_rag.e2e` com exit 0  
**Quando** o orquestrador executar merge automático  
**Então** os PRs elegíveis são mergeados na `main` sem force push  
**E** nenhum gate humano adicional de revisão é exigido além do Robot verde.

### BDD-008 — Segredos fora do git

**Dado** preparação do ambiente local  
**Quando** tokens e `.env` forem usados  
**Então** nenhum segredo é commitado  
**E** evidências de falha/sucesso permanecem sanitizadas.

## Riscos

- Flakiness com GitHub real pode oscilar entre verde/vermelho; mitigação = tasks `tooling-e2e` + reexecução.
- Merge automático sem revisão humana aumenta risco de regressão; mitigação = Robot verde local obrigatório + pytest ≥ 95% no pipeline autônomo.
- Imagem desatualizada após merge parcial; mitigação = BR-007 rebuild explícito pós-merge.
- Conflitos na `main` podem bloquear merge auto; mitigação = task tooling + rebase documentado.

## Rastreabilidade (resumo)

| Valor | REQ | BDD |
|---|---|---|
| Rodar e2e local | REQ-001, 011–014 | BDD-001 |
| Gerar tasks por falha | REQ-003, 015–017; BR-002, BR-005 | BDD-002 |
| Handoff autônomo | REQ-004, 018–020 | BDD-003 |
| Loop até verde | REQ-005, 017 | BDD-004 |
| Imagem local taggeada | REQ-006, 021–022 | BDD-005 |
| Compose aponta imagem | REQ-007, 023–025 | BDD-006 |
| Merge auto Robot verde | REQ-008, 026–028; BR-006 | BDD-007 |
| Sem secrets no git | REQ-009; BR-004 | BDD-008 |
