# Requisitos — Documentação, CI/CD, e2e Robot e release

## Identificação

- **Feature ID:** `docs-cicd-e2e-release`
- **Versão:** 0.1.0
- **Estado:** `ENGINEERING_REFINEMENT`
- **Natureza:** feature nova de qualidade, documentação e entrega contínua; não altera o domínio do MVP.
- **Dependência obrigatória:** task `T19-container-delivery` da feature `github-etl-mcp-rag` (Dockerfile, imagens base e os 3 composes com testes passando).
- **Rastreabilidade:** requisitos `REQ-*`, regras `BR-*`, decisões `DEC-*` e cenários `BDD-*` deste documento.
- **Aprovação humana (requisitos 0.1.0):** `aprovado` em 2026-07-18 por `camilocoelhogomes` (commit candidato `ae1941ebd43ca97ef6d77a55004847f4af4d72db`).

## Problema

Ao final da primeira fase (MVP `github-etl-mcp-rag`), o repositório ainda não possui:

1. uma suíte e2e que trave o comportamento dos componentes do MVP em stack real;
2. uma esteira GitHub Actions que impeça merge na `main` sem unitários, BDD e e2e;
3. release automático (semver + imagem pública GHCR) após merge;
4. documentação em inglês voltada ao usuário final e a contribuidores.

Sem isso, regressões do MVP podem chegar à `main`, a distribuição fica informal e o onboarding do usuário/contribuidor permanece em português e misturado com detalhes de desenvolvimento.

## Objetivos

- **REQ-001:** Garantir, via Robot Framework, testes e2e que travem os fluxos funcionais do MVP (`github-etl-mcp-rag`, BDD-001–BDD-024 aplicáveis a runtime) sobre a stack iniciada com Podman e o compose e2e entregue por T19.
- **REQ-002:** Executar na esteira GitHub Actions, em todo PR destinado à `main`, os testes unitários, BDD e e2e Robot; esses checks devem ser obrigatórios para o merge.
- **REQ-003:** Após merge na `main`, realizar bump semver automático em `pyproject.toml`, publicar imagem em GHCR e atualizar tags `latest` + versão.
- **REQ-004:** Disponibilizar documentação em inglês: README orientado ao usuário final; `docs/` com features do produto e seção de contribuidores; CHANGELOG em inglês.
- **REQ-005:** Consumir os artefatos de container de T19 (Dockerfile/imagem e os 3 composes) sem reivindicar ownership exclusivo deles; esta feature é dona da esteira, do Robot e2e, das docs e do release.

## Personas

- **Usuário final / operador local:** sobe o produto com o compose de usuário apontando para a imagem pública GHCR e segue o README.
- **Contribuidor:** roda a stack de desenvolvimento com Podman, executa testes e segue `docs/contributing`.
- **Mantenedor / revisores de PR:** confiam nos required checks da esteira para autorizar merge na `main`.
- **Release automation:** após merge, versiona e publica a imagem consumível pelo compose de usuário.

## Escopo funcional

### Dependência e consumo de T19

- **REQ-006:** Esta feature só pode ser considerada pronta após T19 entregar, com testes passando:
  - Dockerfile / capacidade de build da imagem do produto;
  - `docker-compose.yml` (usuário final, apontando para imagem pública);
  - `docker-compose.e2e.yml` (stack e2e);
  - `docker-compose.dev.yml` (desenvolvimento).
- **REQ-007:** A esteira e o Robot devem usar `docker-compose.e2e.yml` (e Podman) para subir a stack e2e; não duplicar ownership dos 3 composes.

### Testes e2e (Robot Framework)

- **REQ-008:** Introduzir suíte Robot Framework que exercite, em ambiente de stack real, os comportamentos do MVP cobertos pelos cenários BDD da feature `github-etl-mcp-rag` (BDD-001 a BDD-024) na medida em que forem observáveis via UI, MCP, healthchecks e efeitos de indexação/busca.
- **REQ-009:** O e2e deve usar integração real com GitHub: token/credenciais via variáveis de ambiente / secrets da esteira GitHub Actions.
- **REQ-010:** O repositório de referência para a integração GitHub no e2e é **este próprio repositório** (`github_rag`).
- **REQ-011:** Podman é o runtime obrigatório para iniciar a stack e2e no CI e na documentação de contribuidores (linha opensource).

### CI — gate de PR

- **REQ-012:** Workflow de CI em PRs para `main` deve, nesta ordem lógica de qualidade:
  1. testes unitários;
  2. testes BDD do projeto;
  3. subir a stack e2e com Podman + `docker-compose.e2e.yml`;
  4. executar a suíte Robot Framework e2e.
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
- **REQ-020:** Criar pasta `docs/` em inglês documentando as features do produto e uma subseção/área de contribuidores (`docs/contributing` ou equivalente) com instruções para rodar localmente com Podman, testes unitários/BDD e e2e.
- **REQ-021:** Conteúdo de desenvolvimento atualmente no README (venv, pytest, etc.) deve migrar para a documentação de contribuidores; o README deixa de ser o hub principal de setup de desenvolvimento.
- **REQ-022:** Não alterar arquivos em `spec/`.

## Fora de escopo

- Alterar o **código principal** da aplicação (domínio, adapters de negócio, UI/MCP além do necessário para wiring de CI/docs/testes externos).
- Ownership ou reescrita dos 3 composes e Dockerfile de T19 (exceto ajustes mínimos de consumo pela esteira/docs/release, se inevitáveis e justificados no plano).
- Alterar documentação em `spec/`.
- Deploy em cloud gerenciada, orquestradores além de compose local, multi-cloud.
- Self-hosted runners ou podman machine obrigatória.
- Assinatura de imagens, SBOM, provenance avançada (não exigidos neste MVP de CI/CD).
- Tradução de artefatos fora de README, CHANGELOG e `docs/`.
- Expandir o domínio funcional do MVP (novas tools MCP, novos estados de indexação, etc.).

## Fluxo principal

1. Contribuidor abre PR para `main`.
2. GitHub Actions em `ubuntu-latest` executa unitários e BDD.
3. A esteira sobe a stack com Podman e `docker-compose.e2e.yml` (artefato T19).
4. Robot Framework executa e2e com token GitHub da esteira, usando este repositório como referência.
5. Se todos os checks passarem, o PR pode ser mesclado (required checks).
6. Após merge na `main`, o workflow de release calcula bump semver (Conventional Commits, fallback patch), atualiza `pyproject.toml`, publica imagem no GHCR (`latest` + versão).
7. Usuário final segue o README em inglês e sobe o produto com `docker-compose.yml` apontando para a imagem pública.

## Fluxos alternativos e erros

- Unitários ou BDD falham no PR: check falha; merge bloqueado; e2e pode não ser necessário se a esteira curto-circuitar após falha (aceitável desde que o merge permaneça bloqueado).
- Stack e2e não sobe (Podman/compose/deps): e2e falha; merge bloqueado.
- Token GitHub ausente ou inválido na esteira: e2e que depende de GitHub real falha de forma explícita; merge bloqueado.
- Robot detecta regressão de fluxo MVP: e2e falha; merge bloqueado.
- Release pós-merge: se build/push GHCR falhar, a publicação da versão/imagem fica em estado de falha observável no Actions (sem publicar tag parcial enganosa como sucesso).
- Commits sem Conventional Commits no intervalo de release: aplica bump **patch**.

## Dados e integrações

| Dado / integração | Uso |
|---|---|
| Secrets/vars da esteira (token GitHub) | Autenticação real no e2e contra este repositório |
| `pyproject.toml` → `version` | Fonte da verdade do semver |
| GHCR `ghcr.io/<owner>/<repo>` | Registro público da imagem |
| Podman + compose e2e (T19) | Runtime da suíte Robot |
| GitHub Actions `ubuntu-latest` | Runner CI/CD |
| Robot Framework | Automação e2e |

## Regras de negócio / qualidade

- **BR-001:** Merge na `main` exige required checks: unitários + BDD + e2e Robot.
- **BR-002:** PR nunca publica imagem nem altera versão.
- **BR-003:** Release (bump + GHCR) ocorre somente após merge na `main`.
- **BR-004:** Semver segue Conventional Commits com fallback patch; fonte da verdade é `pyproject.toml`.
- **BR-005:** Imagem publicada deve ter tags `latest` e a versão semver correspondente ao bump.
- **BR-006:** Podman é obrigatório no CI e na doc de contribuidores para a stack containerizada.
- **BR-007:** E2e usa GitHub real (não mock de API GitHub) e este repositório como referência.
- **BR-008:** Esta feature não altera o código principal do produto; foco em CI/CD, testes e2e externos, docs e release.
- **BR-009:** Os 3 composes são entregues por T19; esta feature os consome.
- **BR-010:** Documentação de produto/contribuição entregue por esta feature fica em inglês; `spec/` permanece intocado.

## Decisões

| ID | Decisão | Motivo |
|---|---|---|
| DEC-001 | Gate no PR (required checks), não pós-merge como único controle de qualidade | Impede regressão antes do merge |
| DEC-002 | Release (bump + GHCR) só após merge na `main` | Separa validação de publicação |
| DEC-003 | Conventional Commits + fallback patch | Versionamento previsível com default seguro |
| DEC-004 | GHCR com tags `latest` + versão | Padrão de consumo de imagem pública |
| DEC-005 | Podman em `ubuntu-latest` | Opensource; sem self-hosted |
| DEC-006 | E2e com GitHub real + este repo | Trava integração verdadeira do MVP |
| DEC-007 | Ownership: T19 = composes/Dockerfile; esta feature = esteira + Robot + docs + release | Evita retrabalho e conflito de escopo |
| DEC-008 | Não mexer em `spec/` nem no código principal | Feature de qualidade/entrega, não de domínio |

## Restrições

- Depende de T19 concluída (composes + imagem + testes passando).
- Cobertura mínima do projeto permanece 95% para a suíte unitária/BDD existente; a suíte Robot é gate adicional de e2e.
- Runner: `ubuntu-latest` com Podman.
- Secrets de GitHub necessários para e2e devem existir na esteira; sem eles o e2e não pode passar.
- Compatibilidade documental: README usuário final; contribuidores em `docs/`.

## Segurança relevante

- Token GitHub da esteira é segredo: não pode ser logado pelo Robot, workflows ou artefatos publicados.
- Imagem e docs públicas não devem embutir tokens, `.env` reais ou credenciais.
- Workflows devem usar secrets do GitHub Actions, não valores commitados.

## Compatibilidade

- CI: Linux `ubuntu-latest` + Podman.
- Usuário final: consome imagem GHCR via compose de usuário (T19), tipicamente com Podman ou Docker Compose compatível — a **doc de contribuidores/CI** exige Podman; o README de usuário descreve o uso do compose público.
- Documentação e CHANGELOG em inglês como padrão do repositório após esta feature.

## Métricas de sucesso

- PR para `main` não mescla sem unitários + BDD + e2e Robot verdes.
- Após merge elegível, existe nova versão em `pyproject.toml` e imagem correspondente em GHCR (`latest` + versão).
- Usuário consegue seguir o README em inglês e subir o produto pelo compose de usuário apontando para GHCR.
- Contribuidor consegue seguir `docs/contributing` (Podman, testes, e2e).
- Suíte Robot falha se algum fluxo MVP coberto regressar na stack e2e.

## Critérios de aceite BDD

### BDD-001 — Bloquear merge sem testes verdes

**Dado** um PR aberto contra `main`  
**Quando** unitários, BDD ou e2e Robot falharem na esteira  
**Então** o required check correspondente deve falhar  
**E** o merge na `main` deve permanecer bloqueado.

### BDD-002 — PR não publica release

**Dado** um PR aberto contra `main` com todos os testes passando  
**Quando** a esteira de PR concluir com sucesso  
**Então** nenhuma imagem nova deve ser publicada no GHCR como release desse PR  
**E** a versão em `pyproject.toml` não deve ser alterada pelo workflow de PR.

### BDD-003 — Subir stack e2e com Podman

**Dado** os artefatos de T19 disponíveis (`docker-compose.e2e.yml` e imagem/build necessários)  
**E** Podman disponível no runner `ubuntu-latest`  
**Quando** a esteira de PR executar a fase e2e  
**Então** a stack definida em `docker-compose.e2e.yml` deve subir expondo as portas necessárias  
**E** o Robot Framework deve conseguir alcançar os endpoints/serviços do MVP.

### BDD-004 — E2e trava fluxos do MVP com GitHub real

**Dado** um token GitHub válido configurado como secret/variável da esteira  
**E** este repositório como referência de integração  
**Quando** a suíte Robot Framework e2e for executada sobre a stack  
**Então** os fluxos observáveis do MVP (`github-etl-mcp-rag` BDD-001–BDD-024 aplicáveis a runtime) devem ser validados  
**E** uma regressão nesses fluxos deve falhar a suíte e bloquear o merge.

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
**E** instruções de desenvolvimento/execução local com Podman e testes devem estar em `docs/` (não como foco principal do README)  
**E** `spec/` não deve ter sido alterado por esta feature.

### BDD-008 — Fallback patch sem Conventional Commits

**Dado** um merge na `main` cujo intervalo de commits não contém prefixos Conventional Commits aplicáveis  
**Quando** o workflow de release calcular o bump  
**Então** a versão em `pyproject.toml` deve avançar um **patch**.

## Riscos

- T19 atrasada ou incompleta bloqueia esta feature (dependência dura dos composes).
- E2e com GitHub real aumenta flakiness (rate limit, rede, permissões do token).
- Suíte Robot que tente cobrir BDD-015 (Discovery humano no Cursor) pode ser apenas parcial/automatizável via tools MCP — validação narrativa humana permanece fora.
- Tempo de CI pode crescer significativamente ao subir stack completa + indexação real.
- Publicação GHCR exige permissões `packages: write` e visibilidade correta do pacote.
- “Não mexer no código principal” pode conflitar com pequenos hooks de health/version se não forem previstos em T19; o plano deve evitar mudanças de domínio.

## Dúvidas não bloqueantes (refinamento técnico)

- Nome exato do secret do token GitHub na esteira (`GITHUB_TOKEN` vs secret dedicado com escopos).
- Estratégia de commit do bump (`pyproject.toml`) no workflow de release (bot commit vs tag-only) — detalhar no plano do Principal Engineer sem mudar a regra de semver.
- Granularidade dos arquivos `.robot` por fluxo MVP vs suíte monolítica.
- Timeout e política de retry do e2e sob rate limit da API GitHub.
- Se BDD-015 (coerência narrativa no Cursor) permanece validação humana e fora do Robot (premissa: sim; Robot cobre capacidade das tools/fluxos observáveis).

## Matriz resumida de rastreabilidade

| Objetivo | Requisitos/regras | Cenários |
|---|---|---|
| Gate de PR com unitários, BDD e e2e | REQ-002, REQ-012–014, BR-001–002 | BDD-001, BDD-002 |
| Stack e2e Podman + Robot no MVP | REQ-001, REQ-006–011, BR-006–007, BR-009, DEC-005–007 | BDD-003, BDD-004 |
| Release semver + GHCR pós-merge | REQ-003, REQ-015–017, BR-003–005, DEC-002–004 | BDD-005, BDD-006, BDD-008 |
| Docs inglês usuário + contribuidores | REQ-004, REQ-018–022, BR-010, DEC-008 | BDD-007 |
| Sem alteração de domínio/`spec/` | REQ-005, REQ-022, BR-008–010, DEC-007–008 | BDD-007 |

## Premissas

- T19 entrega os 3 composes nomeados e a imagem buildável antes ou como pré-requisito desta feature.
- “Todos os fluxos desenvolvidos na feature anterior” = cobertura e2e alinhada aos BDD-001–BDD-024 do MVP, na medida automatizável em stack (exceto validação humana exclusiva de narrativa Discovery no Cursor).
- `<owner>/<repo>` do GHCR corresponde ao owner/repositório GitHub deste projeto.
