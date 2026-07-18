# Reviews — T02-config-loader

## Review Design — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` v0.1.0 (candidato) → v0.2.0 (corrigido) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Modo | Autonomous pipeline (aprovação Architect substitui HITL) |
| Resultado inicial | `CHANGES_REQUIRED` |
| Resultado final | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Leitura `T02-config-loader.md`, `requirements.md` (REQ-009,039–042; BR-016–022; BDD-021/022/014), `implementation-plan.md` | OK |
| Cruzamento com T01 (`AppSettings.config_path: Path \| None`, sem I/O) | OK |
| Escopo vs fora de escopo (sem descoberta / sem I/O GitHub) | OK após correção §3.1 |
| Completude de regras de schema / erros / segredo | OK após correção §4.3–4.4 / §6 |

### Achados (sobre v0.1.0)

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| M-01 | `MAJOR` | `design.md` v0.1.0 §13; BDD-021; plano T02↔BDD-021 e T07↔BDD-021 | Design afirmava cobrir BDD-021 integralmente, mas BDD-021 inclui descoberta/identificação de origem — fora do escopo T02. Risco de overscape no BDD ou aceite incompleto. | Explicitar cobertura parcial: T02 = carregar conexões tipadas; descoberta/origem = T05/T06/T07. |
| M-02 | `MAJOR` | `design.md` v0.1.0 §4.3; REQ-010; contrato exemplo | Regras de validação incompletas: não definia se `orgs`/`branches` vazios são inválidos, se `repos` vazio é permitido, se `connections: {}` é válido, nem tratamento de chaves extras. | Tabela de regras obrigatórias (§4.3): `orgs` não-vazio; `repos` pode ser vazio; `{}` válido; extras top-level ignorados. |
| M-03 | `MAJOR` | `design.md` v0.1.0 §4.4; T01 Windows first-class; REQ-040 | `file://` “absoluto” sem formas aceitas (POSIX vs Windows `file:///C:/...`) nem exemplos de rejeição de path relativo. | Especificar formas POSIX/Windows aceitas e rejeições (§4.4). |
| M-04 | `MAJOR` | `design.md` v0.1.0 §4.3 (“alinhado a REQ-013”) | Exigir `"main"` em `branches` atribuído a REQ-013; REQ-013 regula indexação, não o schema do JSON. | Renomear como ENG-T02-001 (decisão de engenharia do loader MVP). |
| M-05 | `MAJOR` | `design.md` v0.1.0 §3 fluxo vs §8; handoff T01 | Fluxo dizia “ler bytes”; §8 `read_text`; não deixava explícito que o path vem de `AppSettings.config_path` sem reler env. | Unificar I/O em `read_text`+`json.loads`; input = `AppSettings.config_path`. |
| S-01 | `SUGGESTION` | `design.md` v0.1.0 §10 | Fail-fast único; BR-021 só exige não aplicar parcial. | Aceitar fail-fast **ou** validação completa sem montar `AppConfig` — documentado em §6 v0.2.0. |

### O que já estava aderente (v0.1.0)

- Separação `schema` / `SecretResolver` / `ConfigLoader` alinhada ao plano §1.3 / §2.
- Fail total sem cadastro parcial (BR-021); token só via `{ "env" }` (REQ-041); wildcards só inclusão (BR-022).
- Sem descoberta GitHub/disco além do arquivo; stdlib only; rollback greenfield.
- Política de redaction em erros/`repr` para BDD-014 parcial.

### Correções aplicadas pelo Architect (v0.2.0)

| ID | Resolução |
|---|---|
| M-01 | §3.1 matriz BDD parcial; rastreabilidade `BDD-021 (parcial)`. |
| M-02 | §4.3 tabela de regras (`orgs`, `repos`, `branches`, `{}`, extras). |
| M-03 | §4.4 formas `file://` POSIX/Windows + rejeições. |
| M-04 | ENG-T02-001; REQ-013 não citato como fonte da regra de schema. |
| M-05 | Fluxo + §4.1/`§5` usam `AppSettings.config_path` + `read_text`. |
| S-01 | §6 permite fail-fast ou validação agregada sem retorno parcial. |

### Bloqueios abertos

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.2.0 apto para o gate BDD. Próximo artefato: `bdd.md` (sem implementação).

---

## Review BDD — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` v0.1.0 + `tests/bdd/test_config_loader.py` + `tests/bdd/features/config_loader.feature` |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Modo | Autonomous pipeline (aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Cobertura design §3.1: BDD-021 parcial, BDD-022, BDD-014 parcial | OK — CFG-01..14 |
| Sem overscape (descoberta/UI/container) | OK |
| Given/When/Then mapeados a `TestCFG*` | OK |
| Imports esperados de `github_rag.config` | OK |
| Sem fixar injeção `ConfigLoader(environ=)` antes de interfaces | OK — `patch.dict(os.environ)` |
| Sem `interfaces.md` / implementação do loader | OK |
| Red esperado | OK — `PYTHONPATH=src python3 -m unittest ... test_config_loader.py` → 17 errors `ImportError: cannot import name 'AppConfig'` |

### Achados

| ID | Severidade | Evidência | Achado | Correção |
|---|---|---|---|---|
| — | — | — | Nenhum BLOCKING/MAJOR | — |
| S-01 | `SUGGESTION` | design §4.2 blank env | Candidato inicial cobria só env ausente | Aceito e aplicado: `test_blank_token_env_raises_*` em CFG-09 |

### Bloqueios abertos

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — BDD v0.1.0 apto para o gate de interfaces. Sem implementação nesta etapa.

---

## Review Interfaces — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `interfaces.md` v0.1.0 + stubs `src/github_rag/config/{schema,secrets,loader,__init__}.py` |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Modo | Autonomous pipeline (aprovação Architect substitui HITL) |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Cobertura design §4: ConfigLoader, SecretResolver, modelos, erros | OK |
| Responsabilidade + motivo da separação em cada tipo | OK |
| Alinhamento BDD imports (`AppConfig`, `ConfigLoadError`, `ConfigLoader`, `GitConnection`, `GitHubConnection`) | OK |
| Fronteira T01 (`config_path` injetado; sem reler env bootstrap) | OK — I-T02 / §1 |
| BR-021 sem retorno parcial; redaction BDD-014 | OK — I-T02-005/009/007 |
| `SecretResolutionError` + tradução para `ConfigLoadError` | OK — I-T02-006/007 |
| Stubs sem lógica real (sem `json.loads`/I/O/resolve) | OK |
| Estilo T01 (Protocol/`...` + docstrings) | OK |

### Achados

| ID | Severidade | Evidência | Achado | Correção |
|---|---|---|---|---|
| — | — | — | Nenhum BLOCKING/MAJOR | — |
| S-01 | `SUGGESTION` | BDD usa `isinstance(AppConfig)` | Protocols `@runtime_checkable` bastam no gate; implementação Developer deve fornecer classes concretas compatíveis | Aceito — documentado em §5; Developer entrega dataclasses/concretos pós unitários |

### Bloqueios abertos

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces v0.1.0 aptas para o gate de testes unitários (QA). Sem implementação real do loader nesta etapa.

---

## Review Unit Tests — QA Engineer (candidato)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Artefato | `unit-test-plan.md` v0.1.0 + `tests/unit/config/{test_loader,test_secrets,test_schema,helpers}.py` |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Modo | Autonomous pipeline (sem HITL intermediário) |
| Resultado | `TESTS_READY_FOR_REVIEW` |

### Cobertura de casos

| Área | IDs | Extremos notáveis |
|---|---|---|
| Secrets | UT-S01..S09 | env blank, nome blank, não-vazamento, idempotência, não muta mapping |
| Loader | UT-L01..L35 | path None, arquivo vazio, JSON parcial, type desconhecido, orgs vazia, repos vazia (válida), token literal, file:// relativo/Windows, sem parcial, injeção resolver |
| Schema / redaction | UT-M01..M08 | Protocols, `get_value`, str/repr sem token, `EnvSecretRef` |

### Evidência red

```text
PYTHONPATH=src python3 -m unittest discover -s tests/unit/config -t . -p "test_*.py"
Ran 56 tests in ~0.04s
FAILED (failures=87)
```

Razão esperada: stubs `load`/`resolve` retornam `None` (corpo `...`) em vez do comportamento tipado.

### Decisão

`TESTS_READY_FOR_REVIEW` — sem commit; sem implementação de produção; aguarda review Architect / handoff Developer.

---

## Review Unit Tests — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` v0.1.0 → v0.1.1 + `tests/unit/config/*` |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Modo | Autonomous pipeline (aprovação Architect substitui HITL) |
| Resultado inicial | `CHANGES_REQUIRED` |
| Resultado final | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Cobertura contratos I-T02-003..014 / CFG-01..14 | OK após correção |
| Extremos: path None, arquivo vazio, JSON parcial, types errados, blanks | OK após M-UT-01/03 |
| Redaction segredo em erros / str/repr / L26 com conexão válida+ inválida | OK após M-UT-02/04 |
| Falha total sem AppConfig parcial (BR-021 / UT-L26) | OK |
| Stubs sem lógica de produção; suíte em RED | OK — confirmado |
| Cruzamento plan ↔ testes executáveis | OK após v0.1.1 |

### Achados (sobre v0.1.0 / suite inicial)

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| M-UT-01 | `MAJOR` | design §4.3 / interfaces §4.3: branches itens não-blank; plan UT-L21 só `[]` | Ausência de caso para item blank em `branches` (`[""]`, `["main", " "]`) | UT-L21b + teste correspondente |
| M-UT-02 | `MAJOR` | CFG-13 / UT-L26; `test_loader.py` L26 sem assert de redaction | Mix conexão válida (token resolvível) + inválida não assertava ausência do valor em `str`/`repr` do `ConfigLoadError` | Assert `SECRET_TOKEN_VALUE not in str/repr(exc)` em UT-L26 |
| M-UT-03 | `MAJOR` | design §4.4 path vazio + prefixo case-sensitive; plan UT-L22 só relativo | Sem caso para `file://` (path vazio) nem `FILE://...` (case) | UT-L22b |
| M-UT-04 | `MAJOR` | CFG-07 / design §6 “sem dump integral”; UT-L04 só checava `SECRET_TOKEN_VALUE` (ausente no arquivo) | Asserção de dump fraca — não garantia ausência do conteúdo integral do arquivo | Assert conteúdo poison completo ausente de `str`/`repr` |
| S-UT-01 | `SUGGESTION` | design §4.3 listas obrigatórias | Tipos errados (`orgs`/`repos`/`branches` string/null) só parcialmente cobertos via campos ausentes | Aceito e aplicado: UT-L28b |
| S-UT-02 | `SUGGESTION` | `_assert_raises_load_error` | Tratava só `Ellipsis`, não `None` (mensagem red menos clara) | Aceito e aplicado |

### Correções aplicadas pelo Architect (v0.1.1)

| ID | Resolução |
|---|---|
| M-UT-01 | `test_ut_l21b_blank_branch_items_rejected` + linha no plan |
| M-UT-02 | Redaction em `test_ut_l26_no_partial_config_on_one_invalid` |
| M-UT-03 | `test_ut_l22b_empty_or_case_invalid_file_url_rejected` |
| M-UT-04 | UT-L04 exige ausência do dump integral (`poison`) |
| S-UT-01 | `test_ut_l28b_wrong_types_for_list_fields` |
| S-UT-02 | Helper trata `None`/`Ellipsis` de forma uniforme |

### Evidência red (pós-correção)

```text
PYTHONPATH=src python3 -m unittest discover -s tests/unit/config -t . -p "test_*.py"
Ran 59 tests in ~0.05s
FAILED (failures=102)
```

Razão: stubs `load`/`resolve` intactos (corpo `...` → `None`); sem implementação de produção.

### Bloqueios abertos

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — unit-test-plan v0.1.1 + suites aptos para handoff Developer. Sem implementação de produção nesta etapa; suíte permanece RED.
