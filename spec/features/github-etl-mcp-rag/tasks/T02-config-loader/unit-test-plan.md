# Plano de testes unitários — T02-config-loader

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T02-config-loader` |
| Autor | QA Engineer (candidato); corrigido por Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Interfaces base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Design base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Escopo | Testes unitários dos contratos `ConfigLoader` / `SecretResolver` / schema tipado |
| Modo | Autonomous — aprovação Architect substitui HITL |

## Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | candidato `0.1.0` → `TESTS_READY_FOR_REVIEW` | `0.1.0` | Plano + suite unitária; red demonstrado (stubs) |
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` → corrigido → `APPROVED_BY_ARCHITECT` | `0.1.0` → `0.1.1` | Ver `reviews.md` (M-UT-01..04); lacunas de extremos/redaction |

## 1. Objetivo

Verificar comportamento de carga/validação/resolução **antes** da implementação concreta (stubs `...` permanecem). A suíte deve falhar (red) nas asserções de comportamento; superfície estática de erros/Protocols pode passar.

## 2. Superfície sob teste

| Símbolo | Módulo | Tipo de verificação |
|---|---|---|
| `ConfigLoader` / `ConfigLoadError` | `github_rag.config.loader` | Comportamento de `load` |
| `EnvironSecretResolver` / `SecretResolver` / `SecretResolutionError` | `github_rag.config.secrets` | Resolução + redaction em erros |
| `AppConfig`, `GitHubConnection`, `GitConnection`, `EnvSecretRef`, `ResolvedSecret`, `Revisions` | `github_rag.config.schema` | Protocols + invariantes pós-carga |
| Re-exports | `github_rag.config` | Superfície pública |

**Fora de escopo:** descoberta de repos (T05), existência de volumes (T06), `load_settings` (T01), UI/MCP/logs.

## 3. Casos — `SecretResolver` / `EnvironSecretResolver`

| ID | Caso | Entrada | Expectativa | Contrato |
|---|---|---|---|---|
| UT-S01 | Resolve ok via mapping | nome + mapping com valor | retorna `str` não-blank | I-T02-006 |
| UT-S02 | Resolve ok via `os.environ` | `environ=None` + env preparado | lê processo | I-T02-006 |
| UT-S03 | Env ausente | chave inexistente | `SecretResolutionError`; mensagem cita nome | I-T02-006/008 |
| UT-S04 | Env blank | `""`, `" "`, `"\t"`, `"\n"` | `SecretResolutionError`; cita nome | I-T02-006 |
| UT-S05 | Nome blank | `""`, `"  "` | `SecretResolutionError` (nome inválido); **sem** valor | I-T02-006 |
| UT-S06 | Não-vazamento em erro | mapping com segredo conhecido + falha (nome blank ou outra env) | `str(exc)`/`repr(exc)` **não** contém valor do segredo | I-T02-006 / BDD-014 |
| UT-S07 | Não muta mapping | mapping mutável | inalterado após `resolve` | invariante secrets |
| UT-S08 | `SecretResolutionError` é `Exception` | — | `issubclass(..., Exception)` | §4.8 |
| UT-S09 | Idempotência | mesmo nome, duas chamadas | mesmo valor; sem efeito colateral | I-T02-006 |

## 4. Casos — `ConfigLoader.load`

| ID | Caso | Entrada | Expectativa | Contrato |
|---|---|---|---|---|
| UT-L01 | Path `None` | `load(None)` | `ConfigLoadError` (path/CONFIG_PATH ausente) | I-T02-004/005; CFG-05 |
| UT-L02 | Arquivo inexistente | Path sem arquivo | `ConfigLoadError` | CFG-06 |
| UT-L03 | Arquivo vazio | conteúdo `""` | `ConfigLoadError` (JSON inválido) | extremos |
| UT-L04 | JSON malformado | `{` / texto | `ConfigLoadError`; **sem dump integral** do conteúdo do arquivo | CFG-07 |
| UT-L05 | Sem chave `connections` | `{}` | `ConfigLoadError` | CFG-08 |
| UT-L06 | `connections` tipo errado | lista / string / null | `ConfigLoadError` | CFG-08 |
| UT-L07 | `connections: {}` | objeto vazio | `AppConfig` com mapa vazio | CFG-02; I-T02-008 |
| UT-L08 | Github+git válidos | JSON completo + env | `AppConfig` tipado completo | CFG-01 |
| UT-L09 | `type` desconhecido / ausente | `"gitlab"` / ausente / `"GITHUB"` | `ConfigLoadError` | CFG-08 |
| UT-L10 | `orgs` vazia | `[]` | `ConfigLoadError` | design §4.3 |
| UT-L11 | `orgs` item blank | `[""]` / `[" "]` | `ConfigLoadError` | design §4.3 |
| UT-L12 | `repos` vazia (válida) | `[]` + demais ok | sucesso; `repos == []` | design §4.3 |
| UT-L13 | `repos` item blank | `[""]` | `ConfigLoadError` | design §4.3 |
| UT-L14 | Wildcard em `repos` | `"org/*"` | preserva string; sem expansão | CFG-03 |
| UT-L15 | Token literal | `"token": "ghp_..."` | `ConfigLoadError`; literal **não** ecoado na mensagem | design §4.3 |
| UT-L16 | Token `env` blank | `{"env": " "}` | `ConfigLoadError` | design §4.3 |
| UT-L17 | Token formato inválido | `null` / lista / sem `env` | `ConfigLoadError` | design §4.3 |
| UT-L18 | Env ausente no processo | JSON ok, env sem var | `ConfigLoadError` cita nome | CFG-09 |
| UT-L19 | Env blank no processo | env `""`/`"  "` | `ConfigLoadError` cita nome | CFG-09 |
| UT-L20 | Sem `main` em branches | `["develop"]` | `ConfigLoadError` | CFG-12; ENG-T02-001 |
| UT-L21 | `branches` vazia | `[]` | `ConfigLoadError` | design §4.3 |
| UT-L21b | `branches` item blank | `[""]` / `["main", " "]` | `ConfigLoadError` | design §4.3 |
| UT-L22 | `file://` relativo | `file://repos`, `file://./repos` | `ConfigLoadError` | CFG-11 |
| UT-L22b | `file://` path vazio / prefixo case errado | `file://`, `FILE:///repos/*` | `ConfigLoadError` | design §4.4 |
| UT-L23 | URL sem `file://` / vazia | `https://...`, `""` | `ConfigLoadError` | CFG-11 |
| UT-L24 | `file://` POSIX absoluto | `file:///repos/*` | sucesso | CFG-04 |
| UT-L25 | `file://` Windows | `file:///C:/repos/*` | sucesso | CFG-04; I-T02-011 |
| UT-L26 | Uma inválida entre válidas | mix type inválido + env com segredo | `ConfigLoadError`; **nunca** `AppConfig` parcial; `str`/`repr` **sem** valor do token | CFG-10; BR-021; CFG-13 |
| UT-L27 | Nome conexão blank | chave `""` / `"  "` | `ConfigLoadError` | design §4.3 |
| UT-L28 | JSON parcial (campos github faltando) | sem `orgs` / `revisions` | `ConfigLoadError` | extremos |
| UT-L28b | Tipos errados em listas/revisions | `orgs`/`repos`/`branches` string/null | `ConfigLoadError` | design §4.3 |
| UT-L29 | Chaves top-level extras | `"$schema"` etc. | ignoradas; carga ok se `connections` ok | design §4.3 |
| UT-L30 | Campos desconhecidos na conexão | `"extra": 1` | ignorados; carga ok | design §4.3 |
| UT-L31 | Resolver injetado | `ConfigLoader(secret_resolver=...)` | usa injeção; não depende de `os.environ` | I-T02-003 |
| UT-L32 | Não relê `CONFIG_PATH` | env com `CONFIG_PATH` + `load(path)` explícito | usa só o `path` passado | I-T02 fronteira T01 |
| UT-L33 | Traduz `SecretResolutionError` | resolver falha | `ConfigLoadError` (não propaga `SecretResolutionError`) | I-T02-007 |
| UT-L34 | Idempotência de `load` | mesmo path, duas cargas | dois `AppConfig` equivalentes; arquivo/env intactos | invariante |
| UT-L35 | Arquivo inacessível | permissão negada (quando aplicável) | `ConfigLoadError` | design §6 |

## 5. Casos — schema / redaction

| ID | Caso | Entrada | Expectativa | Contrato |
|---|---|---|---|---|
| UT-M01 | Protocols runtime_checkable | — | `AppConfig`, `GitHubConnection`, etc. são checkable | I-T02-008 |
| UT-M02 | Instâncias pós-carga | carga ok | `isinstance` das conexões / `AppConfig` | CFG-01 |
| UT-M03 | `ResolvedSecret.get_value` | carga ok | valor == env; não-blank | I-T02-009/010 |
| UT-M04 | Redaction `ResolvedSecret` | carga ok | `str`/`repr` do secret **não** contêm valor | I-T02-009; CFG-14 |
| UT-M05 | Redaction conexão / AppConfig | carga ok | `str`/`repr` **não** contêm valor do token | CFG-14 |
| UT-M06 | Redaction em `ConfigLoadError` | falha com segredo no env | `str(exc)` sem valor; pode citar nome | CFG-13 |
| UT-M07 | `token` permanece `EnvSecretRef` | carga ok | `token.env` == nome; sem valor embutido | I-T02-010 |
| UT-M08 | `ConfigLoadError` / exports | — | subclasse `Exception`; re-exports em `__init__` | I-T02-005/014 |

## 6. Estratégia red

- Stubs: `ConfigLoader.__init__`/`load` e `EnvironSecretResolver.__init__`/`resolve` com corpo `...`.
- Chamadas comportamentais retornam `Ellipsis`/`None` ou não levantam o erro tipado esperado → asserts falham pela **razão esperada** (comportamento não implementado).
- Casos estáticos (UT-S08, UT-M01 parcial, UT-M08) podem passar com o contrato atual.

## 7. Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Plano | `spec/.../T02-config-loader/unit-test-plan.md` |
| Suite secrets | `tests/unit/config/test_secrets.py` |
| Suite loader | `tests/unit/config/test_loader.py` |
| Suite schema | `tests/unit/config/test_schema.py` |

## 8. Comandos

```bash
# Preferido (src layout + top-level para pacote tests):
PYTHONPATH=src python3 -m unittest discover -s tests/unit/config -t . -p "test_*.py" -v

# Com pytest (venv com pytest instalado):
PYTHONPATH=src python -m pytest tests/unit/config/ -q --no-cov
```

## 9. Evidência red (pré-implementação)

| Data | Comando | Resultado |
|---|---|---|
| 2026-07-18 | `PYTHONPATH=src python3 -m unittest discover -s tests/unit/config -t . -p "test_*.py"` | **RED** — `Ran 56 tests` / `FAILED (failures=87)` (subTest conta). Razão: stubs `EnvironSecretResolver.resolve` / `ConfigLoader.load` retornam `None` (corpo `...` no runtime) em vez de `str`/`AppConfig`/`ConfigLoadError`/`SecretResolutionError`. Casos estáticos (UT-S08, UT-M01, UT-M08, `ConfigLoadError` is Exception) passam. |
| 2026-07-18 | idem (pós-correção Architect v0.1.1) | **RED** — `Ran 59 tests` / `FAILED (failures=102)` (subTest conta). Stubs intactos; casos novos UT-L21b/22b/28b em red comportamental. |

Gate de cobertura ≥95% aplica-se **após** implementação. Nesta etapa o objetivo é red comportamental documentado.

## 10. Critérios de pronto (unitários)

- [x] Casos cobrem contratos, extremos, inválidos, vazios, falhas, idempotência e não-vazamento
- [x] Suites em `tests/unit/config/`
- [x] Red demonstrado (unittest; stubs sem comportamento)
- [x] Aprovação Architect (pipeline autônomo) / handoff Developer
