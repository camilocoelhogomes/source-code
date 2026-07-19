# BDD — T22-fix-tooling-e2e-compose-zoekt

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T22-fix-tooling-e2e-compose-zoekt` |
| Autor | QA Engineer |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Execução | `tests/bdd/test_e2e_compose_zoekt_fix.py` (manifesto compose + docs; sem `compose up` / Robot) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Cenários EZ-01..EZ-05; gate manifesto/docs (padrão T19); red até `command` zoekt + docs pré-req. |
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Review: F-T04-001/002/003 + D-T22-*; padrão T19; sem BLOCKING/MAJOR. Modo autônomo. |

## Convenções

- Gate desta camada = **manifesto YAML + documentação** (D-T22-006 / REQ-044 / DEC-017), alinhado a T19.
- **Não** expandir suíte Robot; **não** exigir `podman compose up` / `docker compose up` real neste pytest.
- Aceite de **runtime** (F-T04-003: fases compose → healthy → Robot green path **executa**) fica documentado nos cenários e é prova operacional pós-implementação via `python -m github_rag.e2e` (T21) — fora do assert unitário desta camada.
- Sem secrets em asserts; tokens só como nomes de variáveis (`GITHUB_TOKEN`, `E2E_GITHUB_TOKEN`).
- Composes cobertos: `docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml`.

---

## EZ-01 — Pré-req compose provider documentado (F-T04-001)

**Dado** os artefatos operacionais `e2e/README.md` e `docs/runbook-local.md`  
**Quando** o operador consultar pré-requisitos para subir a prova e2e / stack local  
**Então** ambos documentam de forma explícita o pré-requisito de **provider Compose no PATH** (`podman-compose` e/ou `docker-compose` / plugin resolvível por `podman compose`)  
**E** há comando de verificação acionável (ex.: `command -v podman-compose` e/ou `podman compose version`)  
**E** há orientação de instalação tipica (ex.: `brew install podman-compose` ou equivalente)  
**E** com esses pré-reqs atendidos no host, a falha `looking up compose provider failed` deixa de ser o bloqueio esperado (aceite operacional F-T04-001)

**Camada pytest:** asserts de texto/docs — sem subir stack.

---

## EZ-02 — Serviço zoekt declara command do webserver nos três composes (F-T04-002)

**Dado** `docker-compose.yml`, `docker-compose.e2e.yml` e `docker-compose.dev.yml`  
**Quando** inspecionar o serviço `zoekt` em cada arquivo  
**Então** existe `command` (argv do filho do ENTRYPOINT `tini`) contendo `zoekt-webserver`, `-index`, `/data/index` e `-rpc`  
**E** o serviço **não** depende apenas do ENTRYPOINT/`tini` sem CMD (status quo quebrado: `tini` help → exit 1)  
**E** o volume de índice permanece montado em `/data/index`  
**E** nenhum segredo é introduzido no bloco do serviço

**Camada pytest:** leitura de manifesto — sem `compose up`.

**Aceite runtime (fora do pytest desta camada):** com o `command` correto, `tini -- zoekt-webserver -index /data/index -rpc` mantém o container vivo e `GET :6070/healthz` → HTTP 200.

---

## EZ-03 — Paridade do fix zoekt entre papéis de compose (F-T04-002 / D-T22-002)

**Dado** os três composes REQ-043 (user, e2e, dev)  
**Quando** comparar o `command` do serviço `zoekt`  
**Então** os três declaram o mesmo argv efetivo do webserver (`zoekt-webserver` + `-index /data/index` + `-rpc`)  
**E** não há compose “esquecido” sem o fix (evita paridade falsa)

**Camada pytest:** manifesto nos três arquivos.

---

## EZ-04 — Tooling e2e ultrapassa compose/healthy e inicia Robot (F-T04-003)

**Dado** pré-reqs de provider atendidos (EZ-01) e manifesto zoekt corrigido nos composes (EZ-02/EZ-03)  
**Quando** o operador/CI executar a prova canônica `python -m github_rag.e2e` (T21)  
**Então** a fase `compose` completa sem zoekt `Exited (1)` por `tini` sem filho  
**E** a fase `healthy` alcança readiness do app (`/healthz`)  
**E** a fase `robot` do green path **é iniciada** (não skip por tooling)  
**E** pass/fail de cenário de produto Robot **não** bloqueia o aceite de tooling desta task (D-T22-008)

**Camada pytest desta task:** cenário rastreável + pré-condições de manifesto/docs (EZ-01..EZ-03) como gate CI; **sem** `compose up` nem execução Robot neste arquivo.

**Prova operacional:** HITL / `python -m github_rag.e2e` após implementação do Developer.

---

## EZ-05 — Artefatos de tooling sem secrets versionados

**Dado** os três composes, `e2e/README.md` e `docs/runbook-local.md`  
**Quando** inspecionar conteúdo versionado  
**Então** não há PAT/`ghp_` embutido  
**E** credenciais continuam apenas como nomes de variáveis de ambiente

**Camada pytest:** asserts negativos de segredo.

---

## Rastreabilidade

| Cenário | Critério | Evidência auditoria | Gate pytest |
|---|---|---|---|
| EZ-01 | F-T04-001 | provider ausente no PATH | docs |
| EZ-02 | F-T04-002 | zoekt exit 1 / tini help | manifesto `command` |
| EZ-03 | F-T04-002 / D-T22-002 | bug nos 3 composes | paridade manifesto |
| EZ-04 | F-T04-003 | healthy/robot skip | docs do aceite + pré-condições EZ-01..03; runtime = T21 |
| EZ-05 | aceite “sem secrets” | — | negativos |

## Execução

```bash
python -m pytest tests/bdd/test_e2e_compose_zoekt_fix.py -q
```

Estado esperado **antes** da implementação Developer: **FAIL** (command zoekt ausente; docs sem pré-req provider).  
Estado esperado **depois** da implementação: **PASS** nesta camada; runtime T21 validado operacionalmente.
