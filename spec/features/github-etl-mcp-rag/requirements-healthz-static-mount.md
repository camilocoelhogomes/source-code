# Requisitos — `/healthz` acessível com mount estático em `/`

## Identificação

| Campo | Valor |
|---|---|
| Feature ID | `github-etl-mcp-rag` |
| Artefato | `requirements-healthz-static-mount` |
| Versão | `0.1.0` |
| Estado | `READY_FOR_PO_REVIEW` |
| Origem | loop e2e Robot pós-merge T28/T29 — `spec/features/mvp-local-e2e-green/runs/e2e-run-20260719-w2.md` |
| Rastreabilidade | `REQ-HSM-*`, `BR-HSM-*`, `BDD-HSM-001` → `BDD-020`, `I-T19-007`, `CD-01`, `ROBOT-01` (`e2e/robot/health.robot`) |
| Task alvo (proposta) | `T31-fix-healthz-static-mount-order` |

## Problema

Após boot bem-sucedido do delivery host (`python -m github_rag.delivery`), Uvicorn escuta em `:8080`, `GET /` e `GET /docs` respondem **200**, mas `GET /healthz` responde **404 Not Found**.

O launcher e2e (`PodmanE2eStackLauncher.wait_healthy`) faz poll de `http://127.0.0.1:8080/healthz` por ~600s sem alcançar `status=ok`; o run termina com **exit 3** na fase `healthy` (~624s). A suíte Robot **não executa** (`health.robot` / demais suítes ficam bloqueadas).

**Causa raiz observada:** `register_health_routes` é invocado em `runtime._materialize_surfaces` **depois** de `StaticFiles` montado em `/` em `ui/app.create_app`. O mount em `/` intercepta `/healthz` antes da rota FastAPI, devolvendo 404.

**Evidência:** run W1 pós T28/T29 (`d4aab4b`); delivery host **running**; infra compose dev ok.

## Objetivos

- **REQ-HSM-001:** Garantir que `GET /healthz` responda conforme contrato **I-T19-007** após boot completo com UI e MCP prontos.
- **REQ-HSM-002:** Restaurar a prova e2e: fase `healthy` do launcher conclui com sucesso e desbloqueia execução Robot (incl. `BDD-020` em `health.robot`) **sem alterar** `e2e/robot/**`.
- **REQ-HSM-003:** Preservar serviço da UI estática em `/` (`GET /` e `GET /docs` continuam **200** após a correção).
- **REQ-HSM-004:** Manter payload canônico e ausência de segredos em `/healthz` (sem regressão de T19).

## Fora de escopo

- Qualquer mudança em **`e2e/robot/**`** (suítes, resources, keywords, tags).
- Alteração do contrato JSON de `/healthz` (`status`, `ui`, `mcp` — **I-T19-007**).
- Refatoração ampla de routing UI além do necessário para expor `/healthz`.
- Fail-fast do launcher quando delivery crash (T29 — escopo distinto).
- Tooling compose/zoekt (T22), env loader (T28/T29), imagem local (T30).
- Novos endpoints de health ou mudança de porta (`8080` / `8001`).

## Classificação produto

| ID | Superfície | Classificação | Motivo |
|---|---|---|---|
| F-W1-001 | `health` / boot delivery | **`produto`** | Rota de health do produto inacessível em runtime real; viola **I-T19-007** e bloqueia MVP |
| F-W1-002 | `tooling-e2e` / timeout launcher | efeito colateral | Consequência de F-W1-001; **não** exige mudança em `e2e/robot/**` |

## Regra de negócio

- **BR-HSM-001:** Após `DefaultContainerRuntime.boot()` concluir com sucesso, a superfície ASGI exposta na porta UI **deve** atender `GET /healthz` com HTTP 200 e corpo `{ "status": "ok", "ui": "ready", "mcp": "ready" }` antes de qualquer consumidor externo (compose healthcheck, launcher e2e, Robot) considerar a stack saudável.

## Cenário BDD

### BDD-HSM-001 — `/healthz` alcançável com UI estática montada (rastreia BDD-020 / I-T19-007)

**Dado** stack local com delivery host boot ok (equivalente a `docker-compose.dev.yml` + `python -m github_rag.delivery`)  
**E** Uvicorn escutando em `http://127.0.0.1:8080`  
**Quando** o cliente HTTP faz `GET /healthz`  
**Então** a resposta é HTTP **200**  
**E** o corpo JSON contém exatamente `status=ok`, `ui=ready`, `mcp=ready`  
**E** o corpo **não** contém tokens ou segredos  

**Rastreabilidade Robot (sem editar suíte):**

| Artefato existente | Assert observável |
|---|---|
| `e2e/robot/health.robot` — `BDD-020 Healthz Reports Ui And Mcp Ready` | `Wait Until Healthz Ok` + `Get Healthz` → 200; `status`/`ui`/`mcp` |
| `e2e/robot/resources/common.resource` — `Get Healthz` | `GET .../healthz` `expected_status=200` |
| **I-T19-007** | Contrato canônico de payload |
| **CD-01** (T19 BDD) | Boot ok → `/healthz` 200 ui+mcp ready |

## Critérios de aceite mensuráveis

1. **CA-HSM-01:** Com delivery host running pós-boot (~≤120s após start), `curl -sf http://127.0.0.1:8080/healthz` retorna exit 0 e JSON com `status=ok`, `ui=ready`, `mcp=ready`.
2. **CA-HSM-02:** No mesmo processo, `GET /` e `GET /docs` continuam HTTP **200** (regressão zero na UI estática).
3. **CA-HSM-03:** `.venv/bin/python -m github_rag.e2e` completa fase `healthy` sem timeout; exit code ≠ 3 por `healthz timeout`.
4. **CA-HSM-04:** Robot executa `health.robot` / `BDD-020` **verde** usando artefatos **inalterados** em `e2e/robot/**`.
5. **CA-HSM-05:** Testes unitários/BDD de delivery cobrem ordem de registro/mount (rota `/healthz` não interceptada por `StaticFiles` em `/`); cobertura do projeto ≥ 95%.
6. **CA-HSM-06:** Body de `/healthz` contém **somente** chaves `status`, `ui`, `mcp`; nenhum valor de token ou segredo (**I-T19-007** / UT-H04).

## Métricas de sucesso

- Tempo até primeiro `GET /healthz` 200 após boot: ≤ **120s** (alinhado a `Wait Until Healthz Ok timeout=120` em `health.robot`).
- Run e2e completo: fase `healthy` ok + suítes Robot executadas (não skip por timeout de health).

## Dependências e deduplicação

- **Não duplica:** T22 (zoekt), T28/T29 (env/fail-fast), T30 (imagem local) — nenhum cobre ordem `StaticFiles` vs `register_health_routes`.
- **Desbloqueia:** loop `mvp-local-e2e-green`, prova **REQ-047** / **BDD-020**, compose healthcheck `/healthz` (T19 manifesto).

## Aprovação humana

- **Estado atual:** `READY_FOR_PO_REVIEW` — aguardando revisão e aprovação explícita antes de `PENDING_HUMAN_APPROVAL` → plano/task T31.
