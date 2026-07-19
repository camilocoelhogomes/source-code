# BDD — T25-gap-negative-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T25-gap-negative-integral` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Rastreabilidade | BDD-008, BDD-018, BDD-022; design T25 D-T25-001..005 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Escopo dos cenários

Cobertura **integral** do texto dos BDD-008/018/022 do pai. Asserts na superfície API/delivery/probes; browser visual = residual T23.

| ID | BDD pai | Superfície |
|---|---|---|
| NEG-01 | BDD-008 | UI API + orquestrador (indução controlada) |
| NEG-02 | BDD-018 | Discovery/sync + `GET /api/catalog/issues` (+ Robot live) |
| NEG-03 | BDD-022 | Delivery boot `CONFIG_PATH` inválido (+ Robot probe) |
| NEG-04 | regressão | Payload index vazio / unknown id (mantém negative.robot atual) |

## 2. Cenários

### NEG-01 — Falha parcial com histórico e reindex total (BDD-008)

**Dado** um repositório enfileirado cuja indexação processa parte dos arquivos  
**E** uma porta do pipeline (ex. vector store) falha após progresso parcial  
**Quando** a execução terminar com erro  
**Então** `GET /api/repos/{id}` expõe `state=error` e `state_label=erro`  
**E** `GET /api/repos/{id}/executions` lista execução `failed` com `error_message` e `error_at` não nulos  
**E** o histórico retém a falha entre tentativas  
**Quando** a falha for removida e uma nova indexação for disparada  
**Então** ocorre restart total (wipe/delete do índice do repositório)  
**E** o repositório alcança `state=up_to_date`  
**E** nenhum corpo de resposta contém valor de token

**Arquivos:** `tests/bdd/test_negative_integral.py`; probe `bdd008`; Robot tag `bdd008`.

### NEG-02 — Volume local ausente registra erro na UI API (BDD-018)

**Dado** uma conexão local cujo volume/path está ausente ou inacessível  
**E** (opcional) outra conexão local válida  
**Quando** o sync/discovery executar  
**Então** nenhum repositório do volume ausente é indexado/listado como ativo dessa conexão  
**E** `GET /api/catalog/issues` contém issue com `connection_name`, `path` e `message` tipada (ex. inaccessible)  
**E** a resposta não contém valor de token  
**E** conexões válidas permanecem utilizáveis

**Arquivos:** `tests/bdd/test_negative_integral.py`; Robot `negative.robot` tag `bdd018`; fixture `config.e2e.json`.

### NEG-03 — CONFIG_PATH inválido fail-fast sem parcial nem leak (BDD-022)

**Dado** `CONFIG_PATH` ausente, blank, arquivo inexistente ou JSON malformado  
**E** variável de token presente no ambiente (para provar anti-leak)  
**Quando** o container/boot iniciar (`DefaultContainerRuntime.boot` / entrypoint)  
**Então** o processo termina com exit code `1`  
**E** sync, reconcile, scheduler.start e bind UI/MCP **não** são invocados  
**E** stdout/stderr/logs não contêm o valor do token

**Arquivos:** `tests/bdd/test_negative_integral.py` (+ regressão CD-03); probe `bdd022`; Robot tag `bdd022`.

### NEG-04 — Regressão: rejeição de index inválido (não substitui NEG-03)

**Dado** stack UI saudável  
**Quando** `POST /api/repos/index` com `repository_ids` vazio ou id desconhecido  
**Então** status ≥ 400  
**E** catálogo não muda de tamanho no caso unknown id  
**E** resposta sem token

**Arquivos:** `e2e/robot/negative.robot` (casos existentes).

## 3. Mapeamento

| Cenário | Critério aceite T25 | Design |
|---|---|---|
| NEG-01 | texto integral BDD-008 | D-T25-002 |
| NEG-02 | texto integral BDD-018 | D-T25-001/005 |
| NEG-03 | texto integral BDD-022 | D-T25-003 |
| NEG-04 | sem secrets; regressão | §3.4 design |

## 4. Política de evidência

- Green path Robot inclui `negative` (T21).
- Probe Process é indução controlada determinística (não soft-pass).
- Sem secrets em artefatos Robot (`e2e/results/` gitignored).
