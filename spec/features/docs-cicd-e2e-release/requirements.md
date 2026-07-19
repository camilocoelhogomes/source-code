# Requisitos — Documentação, CI/CD, e2e (consumo) e release

## Identificação

- **Feature ID:** `docs-cicd-e2e-release`
- **Versão:** 0.2.0
- **Estado:** `ENGINEERING_REFINEMENT`
- **Natureza:** delta de redução de escopo — remove ownership da suíte Robot (passa a `github-etl-mcp-rag` / T21); mantém CI, docs EN e release GHCR consumindo T19+T21.
- **Dependência obrigatória:**
  - `github-etl-mcp-rag` / `T19-container-delivery` (Dockerfile + 3 composes com testes passando);
  - `github-etl-mcp-rag` / `T21-mvp-e2e-robot` (suíte Robot e2e entregue e verde na prova do MVP).
- **Rastreabilidade:** requisitos `REQ-*`, regras `BR-*`, decisões `DEC-*` e cenários `BDD-*` deste documento.
- **Aprovação humana (requisitos 0.1.0):** `aprovado` em 2026-07-18 por `camilocoelhogomes` (commit candidato `ae1941ebd43ca97ef6d77a55004847f4af4d72db`).
- **Aprovação humana (plano 0.1.1):** `aprovo` em 2026-07-18 por `camilocoelhogomes` (commit candidato `8d0f84b64a6a03fab361b072ac02e456dd7e92ca`); tasks T01–T07 estavam em `READY_FOR_IMPLEMENTATION` sob 0.1.x — **plano deve ser refeito** sob 0.2.0 (T04 deixa de criar a suíte).
- **Aprovação humana (requisitos 0.2.0):** `aprovo` em 2026-07-18 por `camilocoelhogomes` (commit candidato `37f7def0ecacabcb079feaec780016735fefc9fd`).
- **Histórico deste delta:** `0.1.0` → `0.2.0` — ownership Robot → T21; REQ-001/005/008–011 e DEC-007 reescritos; T04 reduzida a consumo/integração na esteira.

## Problema

Ao final da primeira fase (MVP `github-etl-mcp-rag`), o repositório ainda não possui:

1. uma esteira GitHub Actions que impeça merge na `main` sem unitários, BDD e e2e (suíte entregue por T21);
2. release automático (semver + imagem pública GHCR) após merge;
3. documentação em inglês voltada ao usuário final e a contribuidores.

A prova Robot/e2e do MVP em si é responsabilidade de `github-etl-mcp-rag` / T21 (requisitos MVP 0.5.0); esta feature **não** recria essa suíte.

## Objetivos

- **REQ-001:** Na esteira, **invocar** a suíte Robot Framework entregue por `github-etl-mcp-rag` / T21 sobre a stack iniciada com Podman e `docker-compose.e2e.yml` (T19), sem reinventar nem duplicar a ownership da suíte.
- **REQ-002:** Executar na esteira GitHub Actions, em todo PR destinado à `main`, os testes unitários, BDD e e2e Robot (suíte T21); esses checks devem ser obrigatórios para o merge.
- **REQ-003:** Após merge na `main`, realizar bump semver automático em `pyproject.toml`, publicar imagem em GHCR e atualizar tags `latest` + versão.
- **REQ-004:** Disponibilizar documentação em inglês: README orientado ao usuário final; `docs/` com features do produto e seção de contribuidores; CHANGELOG em inglês.
- **REQ-005:** Consumir artefatos de `github-etl-mcp-rag`: Dockerfile/imagem e os 3 composes (T19) + suíte Robot (T21). Esta feature é dona da **esteira**, das **docs EN** e do **release** — **não** da suíte Robot.

## Personas

- **Usuário final / operador local:** sobe o produto com o compose de usuário apontando para a imagem pública GHCR e segue o README.
- **Contribuidor:** roda a stack de desenvolvimento com Podman, executa testes (incluindo e2e T21 documentado) e segue `docs/contributing`.
- **Mantenedor / revisores de PR:** confiam nos required checks da esteira para autorizar merge na `main`.
- **Release automation:** após merge, versiona e publica a imagem consumível pelo compose de usuário.

## Escopo funcional

### Dependência e consumo de T19 + T21

- **REQ-006:** Esta feature só pode ser considerada pronta após:
  - T19 entregar, com testes passando: Dockerfile; `docker-compose.yml`; `docker-compose.e2e.yml`; `docker-compose.dev.yml`;
  - T21 entregar a suíte Robot e2e (prova MVP) reutilizável pela esteira.
- **REQ-007:** A esteira deve usar `docker-compose.e2e.yml` (Podman) para subir a stack e2e e executar a suíte Robot de T21; não duplicar ownership dos 3 composes nem da suíte.

### Testes e2e (consumo da suíte T21)

- **REQ-008:** ~~Introduzir~~ **Consumir** a suíte Robot Framework de T21; não criar suíte paralela sob ownership desta feature.
- **REQ-009:** O job e2e da esteira deve usar integração real com GitHub via secrets (`E2E_GITHUB_TOKEN`), alinhado ao contrato de credenciais do MVP 0.5.0.
- **REQ-010:** O repositório de referência permanece o deste projeto (definido em T21 / MVP).
- **REQ-011:** Podman é o runtime obrigatório para iniciar a stack e2e no CI e na documentação de contribuidores.

### CI — gate de PR

- **REQ-012:** Workflow de CI em PRs para `main` deve, nesta ordem lógica de qualidade:
  1. testes unitários;
  2. testes BDD do projeto;
  3. subir a stack e2e com Podman + `docker-compose.e2e.yml`;
  4. executar a suíte Robot Framework de T21.
- **REQ-013:** Falha em qualquer etapa do REQ-012 deve impedir o merge (required checks).
- **REQ-014:** O workflow de PR **não** deve publicar imagem no GHCR nem alterar versão em `pyproject.toml`.

### Release — pós-merge na `main`

- **REQ-015:** Após merge na `main`, workflow de release deve:
  1. calcular o próximo semver a partir de Conventional Commits;
  2. atualizar a versão em `pyproject.toml` (fonte da verdade);
  3. buildar e publicar a imagem em `ghcr.io/<owner>/<repo>` com tags `latest` e a versão semver;
  4. garantir que o compose de usuário (`docker-compose.yml` de T19) continue apontando para essa imagem pública de forma utilizável.
- **REQ-016:** Regra de bump: `fix` → patch; `feat` → minor; `BREAKING CHANGE` / `!` → major; **fallback padrão = patch** quando não houver prefixo Conventional Commits aplicável.
- **REQ-017:** Runner dos workflows: `ubuntu-latest` com Podman (sem self-hosted / sem exigir podman machine).

### Documentação

- **REQ-018:** Traduzir `README.md` e `CHANGELOG.md` para inglês.
- **REQ-019:** O README deve ser página de usuário final (como obter a imagem, configurar, subir com o compose de usuário, variáveis essenciais, uso básico UI/MCP).
- **REQ-020:** Criar pasta `docs/` em inglês documentando as features do produto e uma subseção/área de contribuidores (`docs/contributing` ou equivalente) com instruções para rodar localmente com Podman, testes unitários/BDD e e2e (apontando para a suíte T21).
- **REQ-021:** Conteúdo de desenvolvimento atualmente no README (venv, pytest, etc.) deve migrar para a documentação de contribuidores; o README deixa de ser o hub principal de setup de desenvolvimento.
- **REQ-022:** Não alterar arquivos em `spec/` (exceto artefatos desta feature sob `spec/features/docs-cicd-e2e-release/`).

## Fora de escopo

- Criar ou ser dona da suíte Robot Framework (ownership = T21 / `github-etl-mcp-rag`).
- Alterar o **código principal** da aplicação (domínio, adapters de negócio, UI/MCP além do necessário para wiring de CI/docs).
- Ownership ou reescrita dos 3 composes e Dockerfile de T19 (exceto ajustes mínimos de consumo pela esteira/docs/release, se inevitáveis e justificados no plano).
- Alterar documentação em `spec/` fora desta feature.
- Deploy em cloud gerenciada, orquestradores além de compose local, multi-cloud.
- Self-hosted runners ou podman machine obrigatória.
- Assinatura de imagens, SBOM, provenance avançada (não exigidos neste MVP de CI/CD).
- Tradução de artefatos fora de README, CHANGELOG e `docs/`.
- Expandir o domínio funcional do MVP (novas tools MCP, novos estados de indexação, etc.).
- Declarar o MVP do produto entregue (isso é gate de T19+T21 em `github-etl-mcp-rag`).

## Fluxo principal

1. Contribuidor abre PR para `main`.
2. GitHub Actions em `ubuntu-latest` executa unitários e BDD.
3. A esteira sobe a stack com Podman e `docker-compose.e2e.yml` (artefato T19).
4. A esteira executa a suíte Robot de T21 com token GitHub da esteira.
5. Se todos os checks passarem, o PR pode ser mesclado (required checks).
6. Após merge na `main`, o workflow de release calcula bump semver (Conventional Commits, fallback patch), atualiza `pyproject.toml`, publica imagem no GHCR (`latest` + versão).
7. Usuário final segue o README em inglês e sobe o produto com `docker-compose.yml` apontando para a imagem pública.

## Fluxos alternativos e erros

- Unitários ou BDD falham no PR: check falha; merge bloqueado; e2e pode não ser necessário se a esteira curto-circuitar após falha (aceitável desde que o merge permaneça bloqueado).
- Stack e2e não sobe (Podman/compose/deps): e2e falha; merge bloqueado.
- Token GitHub ausente ou inválido na esteira: e2e que depende de GitHub real falha de forma explícita; merge bloqueado.
- Suíte Robot (T21) detecta regressão: e2e falha; merge bloqueado.
- Release pós-merge: se build/push GHCR falhar, a publicação da versão/imagem fica em estado de falha observável no Actions (sem publicar tag parcial enganosa como sucesso).
- Commits sem Conventional Commits no intervalo de release: aplica bump **patch**.

## Dados e integrações

| Dado / integração | Uso |
|---|---|
| Secrets/vars da esteira (`E2E_GITHUB_TOKEN`) | Autenticação real no e2e contra este repositório |
| `pyproject.toml` → `version` | Fonte da verdade do semver |
| GHCR `ghcr.io/<owner>/<repo>` | Registro público da imagem |
| Podman + compose e2e (T19) | Runtime da stack |
| Suíte Robot (T21) | Automação e2e consumida |
| GitHub Actions `ubuntu-latest` | Runner CI/CD |

## Regras de negócio / qualidade

- **BR-001:** Merge na `main` exige required checks: unitários + BDD + e2e Robot (suíte T21).
- **BR-002:** PR nunca publica imagem nem altera versão.
- **BR-003:** Release (bump + GHCR) ocorre somente após merge na `main`.
- **BR-004:** Semver segue Conventional Commits com fallback patch; fonte da verdade é `pyproject.toml`.
- **BR-005:** Imagem publicada deve ter tags `latest` e a versão semver correspondente ao bump.
- **BR-006:** Podman é obrigatório no CI e na doc de contribuidores para a stack containerizada.
- **BR-007:** E2e usa GitHub real (contrato T21) e este repositório como referência.
- **BR-008:** Esta feature não altera o código principal do produto; foco em CI/CD, docs e release (e wiring para invocar T21).
- **BR-009:** Os 3 composes são entregues por T19; a suíte Robot por T21; esta feature os consome.
- **BR-010:** Documentação de produto/contribuição entregue por esta feature fica em inglês; `spec/` permanece intocado fora desta feature.
- **BR-011:** É proibido criar suíte Robot duplicada sob esta feature.

## Decisões

| ID | Decisão | Motivo |
|---|---|---|
| DEC-001 | Gate no PR (required checks), não pós-merge como único controle de qualidade | Impede regressão antes do merge |
| DEC-002 | Release (bump + GHCR) só após merge na `main` | Separa validação de publicação |
| DEC-003 | Conventional Commits + fallback patch | Versionamento previsível com default seguro |
| DEC-004 | GHCR com tags `latest` + versão | Padrão de consumo de imagem pública |
| DEC-005 | Podman em `ubuntu-latest` | Opensource; sem self-hosted |
| DEC-006 | E2e com GitHub real + este repo | Trava integração verdadeira do MVP (definida em T21) |
| DEC-007 | Ownership: T19 = composes/Dockerfile; **T21 = Robot e2e**; esta feature = esteira + docs + release (consome T19+T21) | Evita duplicação; alinha ao MVP 0.5.0 |
| DEC-008 | Não mexer em `spec/` (fora desta feature) nem no código principal | Feature de qualidade/entrega, não de domínio |
| DEC-009 | Task T04 (0.1.x) deixa de “introduzir” a suíte; plano 0.2.x deve redistribuir para consumo/invocação de T21 | Resposta humana: reduzir Robot duplicado |

## Restrições

- Depende de T19 e T21 concluídas (composes + suíte Robot + testes passando).
- Cobertura mínima do projeto permanece 95% para a suíte unitária/BDD existente; a suíte Robot (T21) é gate adicional de e2e na esteira.
- Runner: `ubuntu-latest` com Podman.
- Secrets de GitHub necessários para e2e devem existir na esteira; sem eles o e2e não pode passar.
- Compatibilidade documental: README usuário final; contribuidores em `docs/`.

## Segurança relevante

- Token GitHub da esteira é segredo: não pode ser logado pelos workflows, pela invocação do Robot ou artefatos publicados.
- Imagem e docs públicas não devem embutir tokens, `.env` reais ou credenciais.
- Workflows devem usar secrets do GitHub Actions, não valores commitados.

## Compatibilidade

- CI: Linux `ubuntu-latest` + Podman.
- Usuário final: consome imagem GHCR via compose de usuário (T19), tipicamente com Podman ou Docker Compose compatível — a **doc de contribuidores/CI** exige Podman; o README de usuário descreve o uso do compose público.
- Documentação e CHANGELOG em inglês como padrão do repositório após esta feature.

## Métricas de sucesso

- PR para `main` não mescla sem unitários + BDD + e2e Robot (T21) verdes.
- Após merge elegível, existe nova versão em `pyproject.toml` e imagem correspondente em GHCR (`latest` + versão).
- Usuário consegue seguir o README em inglês e subir o produto pelo compose de usuário apontando para GHCR.
- Contribuidor consegue seguir `docs/contributing` (Podman, testes, e2e T21).
- Não existe segunda suíte Robot sob ownership desta feature.

## Critérios de aceite BDD

### BDD-001 — Bloquear merge sem testes verdes

**Dado** um PR aberto contra `main`  
**Quando** unitários, BDD ou e2e Robot (suíte T21) falharem na esteira  
**Então** o required check correspondente deve falhar  
**E** o merge na `main` deve permanecer bloqueado.

### BDD-002 — PR não publica release

**Dado** um PR aberto contra `main` com todos os testes passando  
**Quando** a esteira de PR concluir com sucesso  
**Então** nenhuma imagem nova deve ser publicada no GHCR como release desse PR  
**E** a versão em `pyproject.toml` não deve ser alterada pelo workflow de PR.

### BDD-003 — Subir stack e2e com Podman e invocar suíte T21

**Dado** os artefatos de T19 (`docker-compose.e2e.yml` e imagem/build) e a suíte Robot de T21  
**E** Podman disponível no runner `ubuntu-latest`  
**Quando** a esteira de PR executar a fase e2e  
**Então** a stack definida em `docker-compose.e2e.yml` deve subir expondo as portas necessárias  
**E** a esteira deve executar a suíte Robot de T21 (sem suíte duplicada desta feature).

### BDD-004 — E2e da esteira falha se a suíte T21 falhar

**Dado** um token GitHub válido configurado como secret da esteira (`E2E_GITHUB_TOKEN`)  
**Quando** a suíte Robot de T21 for executada pela esteira  
**Então** regressão detectada pela suíte deve falhar o check e2e e bloquear o merge.

### BDD-005 — Release pós-merge com semver e GHCR

**Dado** um merge na `main` após checks verdes  
**Quando** o workflow de release executar  
**Então** a versão em `pyproject.toml` deve ser bumpada conforme Conventional Commits (`fix`→patch, `feat`→minor, `BREAKING`→major) com fallback patch  
**E** a imagem deve ser publicada em `ghcr.io/<owner>/<repo>` com tags `latest` e a versão bumpada.

### BDD-006 — Compose de usuário aponta para imagem pública

**Dado** uma versão publicada no GHCR  
**Quando** um usuário final seguir o README e usar `docker-compose.yml` (T19)  
**Então** o compose deve referenciar a imagem pública do repositório  
**E** o produto (UI e MCP) deve ficar disponível para uso local com a configuração documentada.

### BDD-007 — Documentação em inglês para usuário e contribuidor

**Dado** a entrega desta feature  
**Quando** um usuário abrir `README.md` e um contribuidor abrir `docs/` (incluindo contributing)  
**Então** README e CHANGELOG devem estar em inglês  
**E** o README deve ser orientado ao usuário final  
**E** instruções de desenvolvimento/execução local com Podman e testes (incluindo e2e T21) devem estar em `docs/`  
**E** `spec/` não deve ter sido alterado por esta feature fora dos próprios artefatos.

### BDD-008 — Fallback patch sem Conventional Commits

**Dado** um merge na `main` cujo intervalo de commits não contém prefixos Conventional Commits aplicáveis  
**Quando** o workflow de release calcular o bump  
**Então** a versão em `pyproject.toml` deve avançar um **patch**.

### BDD-009 — Sem suíte Robot duplicada

**Dado** o repositório após esta feature  
**Quando** ownership da automação e2e for inspecionado  
**Então** a suíte Robot canônica deve ser a de T21 / `github-etl-mcp-rag`  
**E** esta feature não deve manter uma segunda suíte Robot paralela.

## Riscos

- T19 ou T21 atrasadas bloqueiam esta feature.
- E2e com GitHub real aumenta flakiness (rate limit, rede, permissões do token).
- Tempo de CI pode crescer ao subir stack completa + indexação real.
- Publicação GHCR exige permissões `packages: write` e visibilidade correta do pacote.
- Plano 0.1.1 / T04–T05 precisam ser reescritos no ENGINEERING_REFINEMENT para refletir consumo de T21.

## Dúvidas não bloqueantes (refinamento técnico)

- Estratégia de commit do bump (`pyproject.toml`) no workflow de release (bot commit vs tag-only).
- Nomes estáveis dos required checks na branch protection.
- Timeout do job e2e na esteira (alinhar a T21).

## Matriz resumida de rastreabilidade

| Objetivo | Requisitos/regras | Cenários |
|---|---|---|
| Gate de PR com unitários, BDD e e2e (T21) | REQ-002, REQ-012–014, BR-001–002 | BDD-001, BDD-002, BDD-004 |
| Consumir stack T19 + suíte T21 | REQ-001, REQ-006–011, BR-006–007, BR-009, BR-011, DEC-005–007, DEC-009 | BDD-003, BDD-009 |
| Release semver + GHCR pós-merge | REQ-003, REQ-015–017, BR-003–005, DEC-002–004 | BDD-005, BDD-006, BDD-008 |
| Docs inglês usuário + contribuidores | REQ-004, REQ-018–022, BR-010, DEC-008 | BDD-007 |
| Sem ownership Robot nesta feature | REQ-005, REQ-008, BR-011, DEC-007, DEC-009 | BDD-009 |

## Premissas

- T19 entrega os 3 composes e a imagem buildável; T21 entrega a suíte Robot e prova o MVP.
- Requisitos `github-etl-mcp-rag` 0.5.0 aprovados definem o contrato e2e (BDD-001–024 observáveis, Podman, credenciais).
- `<owner>/<repo>` do GHCR corresponde ao owner/repositório GitHub deste projeto.
- Implementação desta feature permanece adiada/sequenciada após T19+T21 conforme dependências; plano 0.1.1 fica obsoleto até reaprovação pós-0.2.0.
