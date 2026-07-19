# Design — T22-fix-tooling-e2e-compose-zoekt

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T22-fix-tooling-e2e-compose-zoekt` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` |
| Base | `main` (task aberta por auditoria filha `mvp-e2e-audit-hardening` / T05) |
| Rastreabilidade | F-T04-001, F-T04-002, F-T04-003; ENG-010; REQ-043–044; DEC-011, DEC-017–018; T10 (contrato Zoekt); T19 (composes); T21 (`python -m github_rag.e2e`) |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Fix tooling e2e: pré-req compose provider (F-T04-001); comando `zoekt-webserver` sob `tini` (F-T04-002); alinhamento nos 3 composes; F-T04-003 como consequência. Evidência runtime validada. |

## 1. Contexto

A prova canônica MVP (`python -m github_rag.e2e`, T21) depende de:

1. provider Compose resolvível no host (Podman + `podman-compose` ou equivalente);
2. stack `docker-compose.e2e.yml` com serviços `postgres`, `qdrant`, `zoekt`, `slm`, `app` saudáveis o suficiente para `depends_on` + wait healthy;
3. suíte Robot green path (excluindo BDD-015).

A auditoria filha `mvp-e2e-audit-hardening` / T04 registrou falha de tooling (exit `3`) **antes** de exercitar Robot. Ownership do fix é do pai (`github-etl-mcp-rag` / esta task) — ENG-010: a filha **não** implementa correção.

Arquitetura Zoekt já consolidada em T10/T19:

- **Indexação:** CLI `zoekt-index` no container `app`, escrevendo shards em volume compartilhado (`ZOEKT_INDEX_DIR=/data/index`).
- **Busca:** HTTP oficial `POST /api/search` no `zoekt-webserver` com `-rpc`, base `ZOEKT_URL=http://zoekt:6070`.
- Serviço compose `zoekt` só precisa do **webserver** lendo o volume; não precisa indexar.

## 2. Problema

| ID | Classificação | Sintoma | Impacto |
|---|---|---|---|
| F-T04-001 | `flakiness` / pré-req host | `looking up compose provider failed` (`docker-compose` / `podman-compose` ausentes no PATH) | Fase `compose` falha antes do up |
| F-T04-002 | `produto` (manifesto compose) | `sourcegraph/zoekt:latest`: ENTRYPOINT=`["/sbin/tini","--"]`, CMD=null → `tini` imprime help e **exit 1** | Container zoekt `Exited (1)`; `app` fica `Created`; wait hang |
| F-T04-003 | consequência de F-T04-002 | Fases `healthy` / `robot` skip | Green path não executa |

Evidência runtime (já validada fora desta task):

```text
# Quebrado (status quo nos 3 composes):
image: sourcegraph/zoekt:latest
# sem command → tini sem filho → exit 1

# Fix validado:
tini -- zoekt-webserver -index /data/index -rpc
→ HTTP 200 em /healthz na :6070
```

Os três composes (`docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml`) declaram o mesmo serviço `zoekt` sem `command`/`entrypoint` — o bug é compartilhado.

Documentação atual (`e2e/README.md`, `docs/runbook-local.md`) menciona Podman/`podman compose` mas **não** lista pré-req explícito de binário provider no PATH (mitigação F-T04-001).

## 3. Solução proposta

### 3.1 Correção do serviço `zoekt` (F-T04-002)

Em **todos** os composes que definem `zoekt` com `sourcegraph/zoekt:latest` (ou pin equivalente), definir processo filho do `tini`:

```yaml
zoekt:
  image: sourcegraph/zoekt:latest
  command: ["zoekt-webserver", "-index", "/data/index", "-rpc"]
  # ENTRYPOINT da imagem permanece ["/sbin/tini","--"] →
  # processo efetivo: tini -- zoekt-webserver -index /data/index -rpc
  volumes:
    - <volume_zoekt>:/data/index
  environment:
    ZOEKT_INDEX_DIR: /data/index
  ports:
    - "6070:6070"
  healthcheck:
    test:
      [
        "CMD-SHELL",
        "wget -qO- http://127.0.0.1:6070/healthz >/dev/null || curl -fsS http://127.0.0.1:6070/healthz >/dev/null",
      ]
    interval: 5s
    timeout: 5s
    retries: 12
    start_period: 15s
```

Notas de implementação:

- Preferir `command:` (argv JSON) sem sobrescrever `entrypoint`, preservando `tini` como init (reaping/sinais).
- Flags alinhadas a T10: `-index /data/index` + `-rpc` (API JSON `/api/search`).
- Healthcheck opcional mas **recomendado**; se a imagem não tiver `wget`/`curl`, usar probe equivalente disponível na imagem ou documentar fallback `service_started` + wait do launcher T21 no `ZOEKT_URL/healthz`. Decisão final na implementação deve manter prova: HTTP 200 em `/healthz`.
- `app.depends_on.zoekt` pode evoluir de `service_started` para `service_healthy` **somente se** healthcheck for confiável nos três composes; caso contrário manter `service_started` e deixar o wait de T21 (`E2eStackLauncher`) cobrir readiness do app (que já depende de Zoekt indiretamente via indexação/busca).

### 3.2 Pré-requisito compose provider (F-T04-001)

Documentar de forma explícita e acionável em:

- `e2e/README.md`
- `docs/runbook-local.md`

Conteúdo mínimo:

| Pré-req | Nota |
|---|---|
| Podman instalado e machine running (macOS) | `podman info` ok |
| Provider Compose no PATH | `podman-compose` **ou** plugin/`docker-compose` resolvível por `podman compose` |
| Comando de verificação | `command -v podman-compose` (ou equivalente) + `podman compose version` |
| Instalação tipica (Homebrew) | `brew install podman-compose` (exemplo; não pin de versão obrigatório no design) |

Não é alteração de domínio Python: falha de provider continua exit tooling (`E2eStackError` / exit `3`); a mitigação é documentação + checklist operacional.

### 3.3 Fechamento de F-T04-003

Não há task/código separado: após F-T04-002 corrigido e pré-reqs atendidos,

1. `podman compose -f docker-compose.e2e.yml up -d --build` completa sem zoekt exit 1;
2. wait healthy do T21 alcança `/healthz` do app;
3. Robot green path **executa** (pass/fail de cenário de produto = evidência nova, fora do aceite de tooling desta task).

### 3.4 Testes (padrão T19)

Gate de testes desta task = **manifesto/delivery** (sem expandir Robot; sem `compose up` real no pytest unitário, alinhado REQ-044 / DEC-017):

| Tipo | Escopo |
|---|---|
| Manifesto | Nos 3 YAML: serviço `zoekt` com `command` contendo `zoekt-webserver`, `-index`, `/data/index`, `-rpc` |
| Docs | Assertes leves ou checklist BDD de que README/runbook mencionam pré-req provider |
| Runtime | Validação HITL/`python -m github_rag.e2e` pós-implementação (prova operacional; não substitui unitários) |

Cobertura mínima do projeto permanece ≥ 95%; novos testes de manifesto devem entrar no suite existente `tests/unit/delivery/` (ou equivalente T19).

## 4. Componentes

| ID | Componente | Responsabilidade | Motivo da separação |
|---|---|---|---|
| C-T22-01 | `docker-compose.e2e.yml` → `zoekt` | Stack prova T21/CI; comando webserver saudável | Ownership runtime e2e; isola volumes `e2e_*` |
| C-T22-02 | `docker-compose.yml` → `zoekt` | Entrega end-user; mesmo fix | Evita regressão em stack pública com o mesmo bug |
| C-T22-03 | `docker-compose.dev.yml` → `zoekt` | Dev local; mesmo fix | Paridade de manifesto entre os 3 papéis REQ-043 |
| C-T22-04 | `e2e/README.md` | Pré-reqs Podman + provider + comando canônico | Superfície do operador e2e (F-T04-001) |
| C-T22-05 | `docs/runbook-local.md` | Pré-reqs nas três audiências compose | Runbook único não deixa e2e como único lugar documentado |
| C-T22-06 | Testes manifesto (T19) | Travas de regressão do `command` zoekt | Detecta remoção acidental do argv sem subir stack |

**Fora desta task (não componentes):**

- `src/github_rag/**` domínio ETL/RAG/MCP
- expansão `e2e/robot/**` / browser
- declaração de MVP entregue

## 5. Fluxo

```text
Operador / CI
  │
  ├─(pré-req) Podman + compose provider no PATH          # F-T04-001
  │
  └─ python -m github_rag.e2e  (T21)
       │
       ├─ resolve credencial
       ├─ podman compose -f docker-compose.e2e.yml up -d --build
       │     postgres healthy
       │     qdrant / slm started
       │     zoekt: tini -- zoekt-webserver -index /data/index -rpc
       │           → :6070/healthz = 200                     # F-T04-002
       │     app depends_on → boot delivery → /healthz
       ├─ wait healthy                                       # fecha F-T04-003
       ├─ robot --exclude bdd015 …                           # executa (aceite tooling)
       └─ compose down
```

Fluxo de indexação/busca (inalterado, T10):

```text
app: zoekt-index -index /data/index <tree>  →  volume compartilhado
cliente: POST http://zoekt:6070/api/search   →  webserver -rpc
```

## 6. Dados

| Artefato | Persistência | Notas |
|---|---|---|
| Volume índice Zoekt | named volume (`e2e_zoekt_index` / `zoekt_index` / `dev_zoekt_index`) | Compartilhado app↔zoekt; sem secrets |
| Config e2e | `HOST_CONFIG` / fixtures T21 | Sem mudança nesta task |
| Credenciais | `.env` / `E2E_GITHUB_TOKEN` | Sem versionar; fora do diff de compose zoekt |
| Docs | markdown no repo | Única superfície de dados “nova” para F-T04-001 |

Nenhum schema de domínio, migração ou payload MCP/UI.

## 7. Erros

| Situação | Comportamento esperado | Superfície |
|---|---|---|
| Provider Compose ausente | Falha imediata com mensagem acionável; docs apontam instalação | F-T04-001 / T21 launcher |
| `command` zoekt omitido/errado | Container exit 1; stack failure exit `3`; manifesto deve falhar no CI unitário | F-T04-002 |
| Webserver sem `-rpc` | `/api/search` indisponível; falhas de busca em Robot (produto) — prevenido pelo manifesto | T10 contrato |
| Volume índice vazio | Webserver sobe healthy; buscas vazias até app indexar — comportamento T10, não bug T22 | — |
| Healthcheck probe sem binário na imagem | Implementação escolhe probe disponível ou mantém `service_started` + wait T21; não bloquear fix do `command` | risco R-T22-02 |

## 8. Segurança

- Nenhum segredo em compose/docs; tokens continuam via env (DEC-020 / T21).
- Não logar tokens em README/runbook (apenas nomes de variáveis).
- Imagem Zoekt de origem inalterada (`sourcegraph/zoekt`); só argv do processo.
- Portas host `6070` já expostas — sem abertura nova de superfície além do status quo T19.

## 9. Compatibilidade

| Aspecto | Decisão |
|---|---|
| Três composes REQ-043 | Mesmo `command` zoekt nos três (D-T22-002) |
| T10 `ExactCodeIndex` / HTTP | Mantém `-rpc` + `/data/index` |
| T19 delivery / Dockerfile | Sem mudança obrigatória de imagem app; binário `zoekt-index` no app permanece |
| T21 launcher | Sem mudança de contrato; consome compose corrigido |
| Feature filha | Sem implementação de fix (ENG-010) |
| Pin de tag `latest` | Aceito no status quo; pin de digest/versão fica SUGGESTION (não bloqueia T22) |

## 10. Observabilidade

| Sinal | Onde |
|---|---|
| Log container zoekt | Sem help do `tini`; processo webserver ativo |
| `GET :6070/healthz` | HTTP 200 |
| Fases T21 | `compose` ok → `healthy` ok → `robot` executa |
| Manifesto CI | Falha se `command` zoekt regressar |

## 11. Riscos

| ID | Risco | Severidade | Mitigação |
|---|---|---|---|
| R-T22-01 | Tag `latest` muda layout/ENTRYPOINT | Aberta (baixa) | Manifesto + revalidar `/healthz`; SUGGESTION pin futuro |
| R-T22-02 | Healthcheck sem `curl`/`wget` na imagem | Aberta (baixa) | Probe alternativo ou `service_started` + wait T21 |
| R-T22-03 | Podman vs Docker CLI divergem em `command`+`entrypoint` | Baixa | Preferir argv JSON; validar com Podman (canônico T21) |
| R-T22-04 | Robot falha por produto após tooling verde | Fora de escopo | Nova task por superfície (T23+); não bloqueia aceite T22 |
| R-T22-05 | Docs desatualizados só em um arquivo | Baixa | Alterar README e2e **e** runbook |

## 12. Rollback

1. Reverter commits que alteram os 3 composes + docs + testes manifesto.
2. Stack volta ao estado quebrado conhecido (zoekt exit 1) — aceitável só se hotfix alternativo (imagem/pin) for adotado.
3. Sem migração de dados; volumes de índice podem ser recriados (`compose down -v` se necessário).

## 13. Decisões

| ID | Decisão | Motivo |
|---|---|---|
| D-T22-001 | Corrigir via `command: ["zoekt-webserver", "-index", "/data/index", "-rpc"]` preservando ENTRYPOINT `tini` | Evidência runtime: `tini -- zoekt-webserver …` → `/healthz` 200; CMD null era a causa do exit 1 |
| D-T22-002 | Aplicar o mesmo fix em `docker-compose.e2e.yml`, `docker-compose.yml` e `docker-compose.dev.yml` | Serviço zoekt idêntico e quebrado nos três; evita paridade falsa |
| D-T22-003 | Serviço zoekt = só webserver; indexação permanece no `app` via `zoekt-index` | Contrato T10; volume compartilhado |
| D-T22-004 | Documentar pré-req Podman + compose provider em `e2e/README.md` e `docs/runbook-local.md` | Mitiga F-T04-001 sem código de domínio |
| D-T22-005 | F-T04-003 não gera task/código próprio | Consequência direta de F-T04-002 + pré-reqs |
| D-T22-006 | Gate de teste = manifesto/docs (padrão T19); prova runtime via T21 pós-fix | REQ-044 / DEC-017; sem expandir Robot |
| D-T22-007 | Sem alteração de domínio `src/github_rag/**` nem suítes Robot nesta task | Escopo tooling-e2e; ENG-010 |
| D-T22-008 | Aceite tooling: Robot green path **executa**; pass/fail de cenário de produto não bloqueia T22 | Critério da task; lacunas → tasks posteriores |

## 14. Rastreabilidade F-T04-*

| Evidência | Tratamento nesta task | Critério de done |
|---|---|---|
| F-T04-001 | Docs + verificação de pré-req provider | Com provider instalado, lookup não falha por PATH |
| F-T04-002 | `command` zoekt nos 3 composes + health/prova `/healthz` | Container não exit 1 por `tini` help |
| F-T04-003 | Consequência | `python -m github_rag.e2e` passa compose/healthy e **inicia** Robot |

## 15. Fora de escopo

- Expandir Robot / browser (auditoria T06 / tasks T23+).
- Declarar MVP entregue.
- ETL/RAG/MCP de domínio não relacionados ao bootstrap e2e.
- Implementação na feature filha `mvp-e2e-audit-hardening`.
- Pin obrigatório de digest da imagem Zoekt (apenas SUGGESTION).

## 16. Critérios de aceite (design → implementação)

1. Pré-reqs documentados (F-T04-001).
2. Zoekt sobe sem exit 1 por entrypoint/`tini` inválido nos composes alinhados (F-T04-002).
3. `python -m github_rag.e2e` ultrapassa compose/healthy; Robot green path executa (F-T04-003).
4. Nenhum segredo versionado.
5. Testes manifesto verdes; cobertura projeto ≥ 95%.
6. Ownership no pipeline do pai.

## 17. Próximos artefatos do pipeline

1. BDD (cenários manifesto + docs + aceite tooling) — QA.
2. Interfaces/contratos de manifesto (se houver porta nova; provável só critérios M-T22-* sobre YAML/docs).
3. Unitários / manifesto tests — QA.
4. Implementação Developer nos arquivos listados.
5. Review Architect + Blue se aplicável.

## 18. Estado

`APPROVED_BY_ARCHITECT` — design `0.1.0` completo, sem BLOCKING/MAJOR abertos. Riscos R-T22-01/02 permanecem residuais documentados, não bloqueiam implementação.
