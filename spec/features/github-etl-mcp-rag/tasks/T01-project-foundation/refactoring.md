# Refactoring Blue — T01-project-foundation

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T01-project-foundation` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Etapa | Passo 18 — review Architect pós-Developer |
| Estado | `BLUE_APPROVED_BY_ARCHITECT` |
| Implementação | `APPROVED_BY_ARCHITECT` (reviews.md) |

## 1. Escopo Blue

Permitido: simplificar código/docs sem alterar comportamento, contratos (`interfaces.md` 0.2.0) nem escopo da task.

Proibido: mudar semântica de `load_settings`, defaults, erros, layout de pacotes, testes aprovados, ou antecipar domínio T02+.

## 2. Baseline (evidência)

| Métrica | Valor | Como reproduzir |
|---|---|---|
| Suite | 37 passed (27 unit + 10 BDD), 36 subtests | `.venv/bin/python -m pytest tests/unit tests/bdd -q` |
| Cobertura | 100% (44 stmts, 2 branches; `fail_under=95`) | mesmo comando (pytest-cov via `pyproject.toml`) |
| `settings.py` | 271 linhas / ~11 KB; 44 stmts mensuráveis | `wc -l` / coverage |
| `load_settings` (env tipado) ×10 000 | min ≈ 11.7 ms / mean ≈ 11.8 ms | `timeit` no venv (ver §2.1) |
| `load_settings({})` ×10 000 | min ≈ 6.7 ms / mean ≈ 6.7 ms | idem |
| `tests/conftest.py` | ausente | `ls tests/conftest.py` |

### 2.1 Comando de microbenchmark (baseline)

```bash
.venv/bin/python -c "
import timeit
setup = '''
from github_rag.settings import load_settings
env = {'INDEX_WORKERS': '8', 'QUERY_WORKERS': '16', 'CONFIG_PATH': '/tmp/cfg.json'}
'''
print('typed', timeit.repeat('load_settings(env)', setup=setup, number=10000, repeat=5))
print('empty', timeit.repeat('load_settings({})', setup=setup, number=10000, repeat=5))
"
```

Host da medição: darwin / Python 3.14.6 (`.venv`). Valores são ordem de grandeza.

## 3. Análise — complexidade e performance

### 3.1 Performance

**Nenhum gargalo de performance comprovado.** Guardrail B-P atendido (mesma ordem de grandeza pós-Blue).

### 3.2 Complexidade / candidatas (estado final)

| ID | Veredito Blue | Motivo |
|---|---|---|
| S-I01 / B-01 | `APPLIED` | Nota de pipeline obsoleta substituída por “Implementação” (snapshot existente). |
| S-I02 / B-02 | `WONT_APPLY` (meta revisada) | `_NativePath = type(Path())` **não** é equivalente a `Path(...)` sob UT-22 / I-T01-014 no Python 3.14. Ver §4.1. |
| S-I03 / B-03 | `DEFERRED` | Opcional; sem benefício funcional nesta task. |

## 4. Metas Blue (revisadas)

| ID | Meta | Critério de pronto | Status |
|---|---|---|---|
| B-01 | Remover/atualizar nota de pipeline obsoleta | Docstring sem stub pendente | **DONE** |
| B-02 | ~~Eliminar `_NativePath`~~ → **manter `_NativePath`** | UT-22 + I-T01-014 verdes sem alterar testes; tipagem continua via pathlib | **WONT_APPLY** (revisão Architect) |
| B-03 | `tests/conftest.py` opcional | — | **DEFERRED** |
| B-P | Sem regressão material de microbenchmark | Ordem de grandeza ≈ baseline | **OK** |

### 4.1 Revisão da meta B-02 (Architect)

Evidência (Python 3.14.6 / darwin):

- `Path(str)` consulta `os.name` em tempo de construção e instancia `PosixPath` ou `WindowsPath`.
- UT-22 (`test_ut22_same_semantics_regardless_of_os_name`) faz `mock.patch("os.name", …)` com `"posix"` e `"nt"` e exige `results[0].config_path == results[1].config_path` (I-T01-014: semântica idêntica independente de `os.name`).
- Com `Path(raw)` sob o mock: `PosixPath(...) != WindowsPath(...)` (falha UT-22). Em alguns hosts, instanciar `WindowsPath` fora do Windows levanta `UnsupportedOperation`.
- `_NativePath = type(Path())` fixa a subclasse nativa do **host no import**; a tipagem permanece pathlib (`isinstance(..., Path)`), sem hardcode de separador e **sem ramificar** o resultado pela simulação de `os.name` — alinhado a I-T01-014 e ao teste aprovado.

Conclusão: a sugestão S-I02 partia de premissa incorreta (“equivalente a `Path(...)`”). Manter `_NativePath` é a solução correta **sem** alterar testes aprovados nem o contrato. Alternativas (ex.: `PurePath`) mudariam o tipo exposto (`Path | None` no Protocol) e sairiam do escopo Blue.

### Invariantes pós-Blue (obrigatórios)

- `.venv/bin/python -m pytest tests/unit tests/bdd -q` → 37 passed — **OK**
- Cobertura ≥ 95% — **100% OK**
- Testes aprovados intactos — **OK**
- Contrato/defaults/erros inalterados — **OK**

## 5. Resultados pós-Developer + decisão Architect

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Mudanças | B-01 aplicada. B-02 tentada, falhou UT-22, revertida; meta revisada para `WONT_APPLY`. B-03 deferred. |
| Suite (Architect recheck) | 37 passed, 36 subtests |
| Cobertura | 100% (44 stmts, 2 branches) |
| Benchmark §2.1 (Architect) | typed ×10k: min 11,78 ms / mean 11,85 ms; empty ×10k: min 6,77 ms / mean 6,84 ms — mesma ordem do baseline |
| B-01 / B-02 / B-03 | B-01 `APPLIED`; B-02 `WONT_APPLY`; B-03 `DEFERRED` |
| Review Architect | **`BLUE_APPROVED_BY_ARCHITECT`** |

## 6. Decisão Blue (passo 18)

| Pergunta | Resposta |
|---|---|
| Blue aprovada? | **Sim** — `BLUE_APPROVED_BY_ARCHITECT` |
| Trabalho Blue restante para Developer? | **Não** |
| Pode seguir para QA (cobertura/regressão)? | **Sim** (passo 19) |
| Mudança de escopo / reabrir unitários? | **Não** — testes e contrato preservados |
