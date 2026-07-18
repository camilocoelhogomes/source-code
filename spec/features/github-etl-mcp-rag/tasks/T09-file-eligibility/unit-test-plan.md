# Unit test plan — T09-file-eligibility

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T09-file-eligibility` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |
| Versão | `0.1.0` |
| Interfaces base | `APPROVED_BY_ARCHITECT` (`0.1.0`) |
| Design base | `APPROVED_BY_ARCHITECT` (`0.1.0`) |
| BDD base | `APPROVED_BY_ARCHITECT` (`0.1.0`) |
| Branch | `feature/github-etl-mcp-rag-T09-file-eligibility` |
| Rastreabilidade | I-T09-001..008; D-T09-001..006; REQ-014/015/019; BR-023; DEC-015 |

## Objetivo

Cobrir contratos, extremos, corner cases, entradas inválidas, estados vazios e
falhas da porta `FileEligibilityFilter`, do loader `load_gitignore_sources` e
das regras de denylist **antes** da implementação completa (TDD: red → green).

## Arquivo de testes

`tests/unit/eligibility/test_file_eligibility.py`

## Matriz de casos

| ID | Cenário | Tipo | Expectativa |
|---|---|---|---|
| U-01 | Path absoluto (`/abs/x.py`) | inválido | `EligibilityError`; mensagem cita o path |
| U-02 | Path com escape `..` (`../outside.py`) | inválido | `EligibilityError`; mensagem cita o path |
| U-03 | Path vazio (`""`) | inválido | `EligibilityError` |
| U-04 | Path `"."` / `"./"` | inválido | `EligibilityError` (não são arquivos elegíveis) |
| U-05 | `gitignore_sources == []` | estado vazio | só denylist CSV/imagens; textuais incluídos |
| U-06 | Gitignore aninhado (`""` + `"docs"`) | corner | `*.tmp` em docs e `node_modules/` excluídos |
| U-07 | Negação `!` na mesma fonte | corner | `*.log` exclui; `!keep.log` re-inclui |
| U-08 | CSV case-insensitive (`report.CSV`) | contrato | excluído |
| U-09 | Imagens case-insensitive (`.PNG`, `.JPEG`, `.svg`) | contrato | excluídas |
| U-10 | Sem extensão (`Makefile`, `Dockerfile`, `LICENSE`) | contrato | incluídos (D-T09-005) |
| U-11 | Sem extensão sob dir gitignored | corner | `node_modules/pkg` excluído via ignore |
| U-12 | Duplicatas na entrada | contrato | colapsa mantendo a primeira; ordem estável |
| U-13 | Normalização `\` → `/` | contrato | `src\\App.java` → elegível como `src/App.java` |
| U-14 | Ordem estável de elegíveis | contrato | subset na ordem de entrada |
| U-15 | `load_gitignore_sources` root inexistente | falha | `EligibilityError` |
| U-16 | Loader não desce em `.git/` | contrato | `.gitignore` dentro de `.git/` ignorado |
| U-17 | Loader aninhado: estrutura de fontes | contrato | `relative_dir` `""` e `"docs"` + linhas corretas |
| U-18 | Repo sem nenhum `.gitignore` | estado vazio | `load_gitignore_sources` → `[]` |
| U-19 | Assinatura `filter` sem params de tamanho | contrato | sem `size`/`max_bytes`/`max_size` |
| U-20 | Paths “grandes” sem cap | contrato | incluídos; filtro não rejeita por volume |
| U-21 | Idempotência: duas chamadas iguais | contrato | mesmo resultado |
| U-22 | `isinstance(impl, FileEligibilityFilter)` | contrato | Protocol runtime |
| U-23 | `CSV_DENYLIST` / `IMAGE_DENYLIST` fechadas | contrato | `.csv` + set D-T09-004; `include_extensionless=True` |
| U-24 | `.gitignore` não-UTF-8 no loader | falha | `EligibilityError` |

## Cobertura obrigatória (checklist do pedido)

| Tema | Casos |
|---|---|
| Absolutos / `..` / vazios → `EligibilityError` | U-01..U-04 |
| Sem gitignore | U-05, U-18 |
| Gitignore aninhado + negação `!` | U-06, U-07 |
| CSV/imagens case-insensitive | U-08, U-09 |
| Sem extensão include | U-10, U-11 |
| Duplicatas colapsadas | U-12 |
| Normalização `\` → `/` | U-13 |
| `load_gitignore_sources`: root inexistente, skip `.git/`, nested | U-15..U-17 |
| Ausência de size checks/caps | U-19, U-20 |
| Idempotência / ordem estável | U-14, U-21 |

## Demonstração red

Antes da implementação completa (stubs com `NotImplementedError`):

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/eligibility/test_file_eligibility.py -q --tb=line --no-cov
```

Falhas esperadas: `NotImplementedError` em `PathspecFileEligibilityFilter.filter`
e `load_gitignore_sources` (stubs). Casos de constantes/`inspect.signature`/
Protocol podem passar sem implementação.

Evidência red (2026-07-18): **21 failed, 3 passed** (U-19, U-22, U-23).

## Fora de escopo dos unitários

- Caps futuros / sniffing binário por conteúdo
- `.git/info/exclude` e excludes globais
- Indexação, UI, orquestração T14
- Cenários BDD ELIG-01..07 (já em `tests/bdd/test_file_eligibility.py`)
