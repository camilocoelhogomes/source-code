# Plano de testes unitários — T01-project-foundation

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T01-project-foundation` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `HUMAN_UNIT_TESTS_APPROVED` |
| Versão | `0.1.0` |
| Interfaces base | `0.2.0` (`HUMAN_INTERFACES_APPROVED` / candidato `41056ff`) |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Escopo | Somente testes unitários dos contratos `AppSettings` / `load_settings` / `SettingsBootstrapError` |

## Histórico de aprovação

| Data | Autor | Decisão | Versão / Commit candidato | Observações |
|---|---|---|---|---|
| 2026-07-18 | camilocoelhogomes | `HUMAN_UNIT_TESTS_APPROVED` | `0.1.0` / `507b6ac` | Testes unitários T01 aprovados explicitamente. |

## 1. Objetivo

Verificar o comportamento do bootstrap de settings **antes** da implementação concreta de `load_settings` (stub `...` permanece). A suíte deve falhar (red) nas asserções de carga tipada pela ausência de implementação; constantes e superfície de contrato podem passar.

## 2. Superfície sob teste

| Símbolo | Módulo | Tipo de verificação |
|---|---|---|
| `ENV_*` / `DEFAULT_*` | `github_rag.settings` | Constantes de contrato |
| `AppSettings` | `github_rag.settings` | Protocol `runtime_checkable` |
| `SettingsBootstrapError` | `github_rag.settings` | Subclasse de `Exception` |
| `load_settings` | `github_rag.settings` | Comportamento (red até implementação) |

**Fora de escopo:** parser JSON, DB, secrets, min/max workers, existência de arquivo em `CONFIG_PATH`, pyproject/README/layout completo.

## 3. Casos

| ID | Caso | Entrada | Expectativa | Contrato |
|---|---|---|---|---|
| UT-01 | Constantes de env | — | `ENV_INDEX_WORKERS`/`ENV_QUERY_WORKERS`/`ENV_CONFIG_PATH` literais corretos | I-T01-003 |
| UT-02 | Defaults literais | — | `DEFAULT_INDEX_WORKERS==2`, `DEFAULT_QUERY_WORKERS==4` | I-T01-004 |
| UT-03 | Defaults via `load_settings({})` | mapping vazio | `index_workers=2`, `query_workers=4`, `config_path=None` | I-T01-004/006 |
| UT-04 | Env ausente (chave inexistente) | mapping sem as três chaves | mesmos defaults | I-T01-006 |
| UT-05 | Whitespace-only workers | `"  "`, `"\t"`, `"\n"` | defaults `2`/`4` | I-T01-006 |
| UT-06 | Whitespace-only `CONFIG_PATH` | `"   "` | `config_path is None` | I-T01-006 |
| UT-07 | Int válido | `"8"`, `"16"` | ints tipados | I-T01-003 |
| UT-08 | Int com espaços | `" 3 "` | `int` após strip implícito do contrato (blank vs valor) — valor não-blank conversível | I-T01-007 |
| UT-09 | `INDEX_WORKERS` inválido | `"abc"`, `"2.5"`, `""` já coberto por blank | `SettingsBootstrapError`; mensagem cita `INDEX_WORKERS`; **sem** fallback para `2` | I-T01-007/015 |
| UT-10 | `QUERY_WORKERS` inválido | `"xyz"` | `SettingsBootstrapError`; mensagem cita `QUERY_WORKERS` | I-T01-007/015 |
| UT-11 | Erro sem jargão de shell | int inválido | mensagem **não** contém Activate.ps1 / activate.bat / source / bin/activate / Scripts / PowerShell / cmd / bash | I-T01-015 |
| UT-12 | `CONFIG_PATH` POSIX | `"/etc/app/config.json"` | `isinstance(..., Path)` e equivale a `Path(valor)` | I-T01-005/016 |
| UT-13 | `CONFIG_PATH` Windows drive | `"C:\\Users\\dev\\config.json"` | `Path(valor)` nativo; sem hardcode de separador no módulo | I-T01-005/016 |
| UT-14 | `CONFIG_PATH` UNC | `"\\\\server\\share\\config.json"` | `Path(valor)` | I-T01-016 |
| UT-15 | `environ` injetado | mapping custom | lê só o mapping; não depende de `os.environ` real | I-T01-002/014 |
| UT-16 | `environ is None` | `None` + `os.environ` preparado | usa ambiente do processo | I-T01-014 |
| UT-17 | Não muta mapping | mapping mutável | mapping inalterado após chamada | invariante interfaces §4.3 |
| UT-18 | Retorno satisfaz `AppSettings` | carga ok | `isinstance(result, AppSettings)` | I-T01-001 |
| UT-19 | Sem domínio | inspeção estática + carga | sem `json.loads`, Sourcebot, DB, `SecretResolver` no módulo; carga não abre arquivo | I-T01-009 |
| UT-20 | Paths via pathlib | AST/fonte de `settings.py` | usa `pathlib`/`Path`; sem literais de lógica com só `\` ou só `/` hardcoded para montar path | I-T01-005 / FND-09 |
| UT-21 | `SettingsBootstrapError` é `Exception` | — | `issubclass(..., Exception)` | §4.4 |
| UT-22 | OS-agnostic | mesma entrada de workers em qualquer OS | mesma semântica; sem ramificar por `os.name` no contrato sob teste | I-T01-014 |

## 4. Estratégia red

- `load_settings` permanece stub (`...`) até aprovação HITL dos unitários + implementação.
- Casos UT-03..UT-18 e UT-22 **devem falhar** enquanto o stub não implementa leitura/conversão/snapshot.
- UT-01, UT-02, UT-19 (estático parcial), UT-20 (estático), UT-21 podem passar com o contrato atual.

## 5. Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Plano | `spec/.../T01-project-foundation/unit-test-plan.md` |
| Suite | `tests/unit/test_settings.py` |

## 6. Comandos

```bash
# Greenfield (stdlib; PYTHONPATH para src layout):
PYTHONPATH=src python3 -m unittest discover -s tests/unit -p "test_*.py" -v

# Após fundação (venv ativo):
python -m pytest tests/unit -q
```

## 7. Cobertura

Gate de cobertura ≥95% aplica-se **após** implementação do corpo de `load_settings`. Nesta etapa o objetivo é red comportamental documentado, não threshold de coverage.
