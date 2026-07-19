# Unit Test Plan — T25-gap-negative-integral

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T25-gap-negative-integral` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Matriz

| ID | Caso | Extremo / corner | Contrato | Cenário BDD |
|---|---|---|---|---|
| UT-I01 | store vazio → `issues=[]` | estado vazio | I-T25-001/003 | NEG-02 |
| UT-I02 | `replace` + list round-trip | snapshot imutável | I-T25-002 | NEG-02 |
| UT-I03 | `replace` sobrescreve (não acumula) | idempotência | I-T25-002 | NEG-02 |
| UT-I04 | `GET /api/catalog/issues` serializa campos | contrato JSON | I-T25-003 | NEG-02 |
| UT-I05 | resposta issues sem token | segurança | I-T25-008 | NEG-02 |
| UT-I06 | `create_app` sem store → lista vazia | compat T18 | I-T25-004 | NEG-02 |
| UT-D01 | boot popula store com local_issues | integração wire | I-T25-006 | NEG-02 |
| UT-D02 | boot CONFIG_PATH inválido: exit 1, sync=0, sem leak | fail-fast | I-T25-008 | NEG-03 |
| UT-P01 | probe `bdd008` exit 0 no happy path induzido | indução | I-T25-007 | NEG-01 |
| UT-P02 | probe `bdd022` exit 0 (fail-fast ok) | indução | I-T25-007 | NEG-03 |
| UT-P03 | probe argv inválido → exit ≠ 0 | entrada inválida | I-T25-007 | — |
| UT-P04 | probe stdout nunca contém secret | concorrência N/A | I-T25-008 | NEG-01/03 |

## 2. BDD executável (espelho)

| Arquivo | Cenários |
|---|---|
| `tests/bdd/test_negative_integral.py` | NEG-01, NEG-02, NEG-03 |
| `e2e/robot/negative.robot` | tags bdd008/bdd018/bdd022 (Camada B) |

## 3. Evidência de falha pré-implementação

Antes do código de produto, os novos testes devem falhar por:

- `ImportError` / `AttributeError` de `CatalogIssueStore` / `InMemoryCatalogIssueStore` / rota `/api/catalog/issues`;
- `negative_probes` módulo ausente;
- runtime não populando store.

Comando: `python -m pytest tests/bdd/test_negative_integral.py tests/unit/ui/test_catalog_issues.py tests/unit/e2e/test_negative_probes.py -q`
