# Reviews — T01-project-foundation

## Review BDD — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | Testes BDD (`bdd.md`, `tests/bdd/features/project_foundation.feature`, `tests/bdd/test_project_foundation.py`) |
| Design base | `0.2.0` aprovado (`3505880` / candidato `30272cb`) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Resultado | `CHANGES_REQUIRED` |

### Checks executados

| Check | Resultado |
|---|---|
| Leitura task / design `0.2.0` / `bdd.md` / `approvals.md` / feature / steps | OK |
| `python3 -m unittest discover -s tests/bdd -p "test_*.py" -v` | 10 falhas — todas por artefatos de fundação ausentes (red esperado) |
| Antecipação de interfaces / unitários / implementação | **Falha** — ver B-01 |
| Cobertura dos critérios de aceite + Windows first-class | Parcial — ver M-01, S-* |

### Achados

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| B-01 | `BLOCKING` | `tests/bdd/test_project_foundation.py` L246–L280; design §3 + D-T01-008 | FND-08 exige contrato de API de produção antes do gate de interfaces: `load_settings` / `get_settings` / `Settings` / `AppSettings` e atributos `INDEX_WORKERS`\|`index_workers`, `QUERY_WORKERS`\|`query_workers`, `CONFIG_PATH`\|`config_path`. Isso antecipa `interfaces.md` e amarra nomes/forma de carregamento que o Architect ainda deve definir. | Remover asserções de superfície de API. Manter FND-08 no nível de aceite observável sem fechar contrato: existência de `settings.py`, ausência de lógica de domínio (padrões já em L44–L50 / L233–L237), e verificação de defaults/`CONFIG_PATH` ausente apenas de forma não prescritiva de API (ex.: constantes/documentação no módulo **ou** adiar o exercício de carga tipada para o gate de unitários pós-interfaces). Atualizar Gherkin/`bdd.md` se o Then de “defaults” depender de API. |
| M-01 | `MAJOR` | `tests/bdd/test_project_foundation.py` L342–L344; Gherkin FND-10 L71–L72; aceite T01 (“install no venv, não no Python do sistema”) | FND-10 só exige substrings `python -m pip` e `.venv` no README. Não valida a orientação de que o fluxo padrão **não** é instalar no Python do sistema. | Reforçar asserção alinhada ao Then do Gherkin: README instrui install com interpretador do venv (`python -m pip` após activate e/ou caminho `.venv\Scripts\python.exe` / `.venv/bin/python`) e deixa explícito que isso **não** é install no Python do sistema como fluxo padrão. |
| M-02 | `MAJOR` | `tests/bdd/test_project_foundation.py` L129–L146; Gherkin FND-04 L33–L34; design D-T01-007 / §2.3 | A primeira asserção de FND-04 é fraca (basta coocorrência de “venv” + “docker\|t19\|container”). Não garante a distinção exigida: venv = **dev local** vs Docker/T19 = **entrega padronizada**. A regex de “não usa/monta” cobre só parte do cenário. | Exigir no README (asserts objetivos) (1) declaração de que a imagem/container **não monta/não usa** `.venv` do host e (2) distinção explícita venv (desenvolvimento local) × Docker/T19 (entrega padronizada), em linha com o design aprovado. |
| S-01 | `SUGGESTION` | `tests/bdd/test_project_foundation.py` L171–L196; design §2.6 | FND-06 valida diretórios placeholder e ≥1 `__init__.py` em qualquer subárvore; não exige pacote importável por fronteira (`__init__.py` em cada placeholder). | Opcional: exigir `__init__.py` (ou marcador equivalente) em cada pacote da lista `PACKAGE_PLACEHOLDERS` + raiz `github_rag`. |
| S-02 | `SUGGESTION` | Ausente nos cenários; design §2.3 / §2.10 | BDD não cobre documentação de `ExecutionPolicy` (PowerShell), fallback sem launcher `py`, nem invoke sem activate via `.venv\Scripts\python.exe` / `.venv/bin/python`. Não são bullets literais do aceite da task, mas são mitigações Windows first-class do design `0.2.0`. | Considerar cenário(s) leves de documentação README para esses fallbacks, para evitar regressão ao padrão “só Unix”. |
| S-03 | `SUGGESTION` | `tests/bdd/test_project_foundation.py` L88–L91 vs design §2.3 fluxo PowerShell | FND-01/02 aceitam `Activate.ps1` / `activate.bat` sem exigir o segmento `Scripts\` do caminho Windows documentado. | Preferir assert do caminho documentado (`.venv\Scripts\Activate.ps1` / `.venv\Scripts\activate.bat`) para paridade com o design. |

### O que está aderente (não bloqueia)

- Cenários FND-01..03 com paridade PowerShell / cmd / Unix e comandos canônicos (`py -3.12`, `python3.12`, `python -m pip install -e ".[dev]"`, `python -m pytest`).
- FND-05 `requires-python >=3.12`; FND-07 pytest + `fail_under`/`--cov-fail-under` 95 no manifesto.
- FND-06 lista de fronteiras alinhada ao design §2.6; FND-09 `.gitattributes` + pathlib / sem hardcode `\\` em settings.
- Suite executável via stdlib (`unittest`) no greenfield; 10 falhas pelas razões corretas (fundação ausente), coerente com BLK-* em `bdd.md`.
- Feature file espelha os cenários de `bdd.md`; não há código de produção nem arquivos de interface nesta etapa (exceto a **prescrição** de API em FND-08 — B-01).

### Bloqueios para aprovação

1. **B-01** — FND-08 antecipa interfaces/API de `settings` (obrigatório corrigir).
2. **M-01** — FND-10 incompleto vs aceite/Gherkin de install no venv ≠ sistema.
3. **M-02** — FND-04 incompleto vs distinção venv local × Docker/T19.

### Decisão

`CHANGES_REQUIRED` — devolver ao QA Engineer. Não aprovar BDD com achados `BLOCKING` ou `MAJOR` abertos. Após correção, nova review Architect antes do gate HITL de BDD.

---

## Resposta QA Engineer — correção BDD `0.2.0`

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Artefato corrigido | `bdd.md` v0.2.0, `tests/bdd/features/project_foundation.feature`, `tests/bdd/test_project_foundation.py` |
| Resultado solicitado | Nova review Architect |

### Resoluções por achado

| ID | Severidade | Resolução | Arquivos / trechos |
|---|---|---|---|
| B-01 | BLOCKING | Removidos import/`load_settings`/`get_settings`/`Settings`/`AppSettings` e asserts de atributos tipados. FND-08 = inspeção estática de `settings.py` (existência, nomes de env bootstrap, literais conceituais 2/4/ausente, padrões de domínio proibidos). Carga tipada/API adiados ao gate interfaces/unitários. | `TestFND08SettingsBootstrapOnly`; Gherkin/bdd FND-08 |
| M-01 | MAJOR | FND-10 exige `python -m pip install -e ".[dev]"`, situar install no venv (activate e/ou caminho completo) e regex explícita de que o fluxo padrão **não** é instalar no Python do sistema. | `TestFND10*`; Gherkin/bdd FND-10 |
| M-02 | MAJOR | Removida coocorrência fraca. Exige (1) não monta/não usa `.venv` do host e (2) venv↔desenvolvimento local + Docker/T19↔entrega. | `TestFND04*`; Gherkin/bdd FND-04 |
| S-01 | SUGGESTION | Aplicada: `__init__.py` na raiz e em cada `PACKAGE_PLACEHOLDERS`. | `TestFND06*` |
| S-02 | SUGGESTION | Aplicada de forma leve: ExecutionPolicy + `.venv\Scripts\python.exe` (FND-01); `.venv/bin/python` (FND-03). Sem cenário de produto extra. | `TestFND01*` / `TestFND03*` |
| S-03 | SUGGESTION | Aplicada: `.venv\Scripts\Activate.ps1` e `.venv\Scripts\activate.bat`. | `TestFND01*` / `TestFND02*` |

### Verificação QA pós-correção

| Check | Resultado |
|---|---|
| `python3 -m unittest discover -s tests/bdd -p "test_*.py" -v` | 10 falhas — fundação ausente (red esperado; razões alinhadas aos cenários) |
| Interfaces / unitários / produção / config criados nesta correção | Nenhum |

---

## Reavaliação BDD — Tech Lead Architect (`0.2.0`)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | BDD candidato `0.2.0` (`bdd.md`, `tests/bdd/features/project_foundation.feature`, `tests/bdd/test_project_foundation.py`) |
| Design base | `0.2.0` aprovado (`3505880` / candidato `30272cb`) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks reexecutados

| Check | Resultado |
|---|---|
| Releitura `bdd.md` v0.2.0 / feature / `test_project_foundation.py` / histórico em `reviews.md` | OK |
| `python3 -m unittest discover -s tests/bdd -p "test_*.py" -v` | 10 falhas — README/pyproject/src/settings/.gitattributes/.gitignore ausentes (red correto) |
| Antecipação de interfaces / unitários / implementação | **OK** — FND-08 só inspeção estática; sem `load_*`/`Settings`/`AppSettings` |
| Aderência design `0.2.0` (Windows first-class, venv, Docker/T19, Python 3.12+, layout, cobertura 95%, settings sem domínio, paths/EOL) | **OK** |
| Achados B-01 / M-01 / M-02 / S-01..S-03 | Todos **RESOLVED** (ver tabela) |

### Resolução dos achados anteriores

| ID | Severidade original | Status | Evidência da correção | Notas do revisor |
|---|---|---|---|---|
| B-01 | `BLOCKING` | `RESOLVED` | `test_project_foundation.py` L252–L289 (`TestFND08SettingsBootstrapOnly`); feature FND-08 L57–L64; `bdd.md` FND-08 | Removida superfície de API. Valida existência de `settings.py`, nomes `INDEX_WORKERS`/`QUERY_WORKERS`/`CONFIG_PATH`, literais conceituais 2/4, indicação de ausente/nulo, e padrões de domínio proibidos. Carga tipada adiada — alinhado a D-T01-008. |
| M-01 | `MAJOR` | `RESOLVED` | `test_project_foundation.py` L331–L363 (`TestFND10*`); feature FND-10 L72–L78 | Exige `python -m pip install -e ".[dev]"`, situar install no venv (activate e/ou caminho completo) e regex explícita de que o fluxo padrão **não** é o Python do sistema. |
| M-02 | `MAJOR` | `RESOLVED` | `test_project_foundation.py` L138–L171 (`TestFND04*`); feature FND-04 L32–L37 | Asserções objetivas: (1) não monta/usa `.venv` do host; (2) venv↔dev local; (3) Docker/T19↔entrega. Coocorrência fraca removida. |
| S-01 | `SUGGESTION` | `RESOLVED` | `test_project_foundation.py` L214–L225; feature FND-06 L48 | `__init__.py` exigido na raiz `github_rag` e em cada `PACKAGE_PLACEHOLDERS`. |
| S-02 | `SUGGESTION` | `RESOLVED` | `test_project_foundation.py` L100–L106 (FND-01), L134–L135 (FND-03); feature L13, L30 | ExecutionPolicy/RemoteSigned + `.venv\Scripts\python.exe`; invoke Unix `.venv/bin/python`. Fallback textual “sem launcher `py`” permanece opcional (não bloqueia). |
| S-03 | `SUGGESTION` | `RESOLVED` | `test_project_foundation.py` L92, L115; feature L10, L19 | Caminhos `.venv\Scripts\Activate.ps1` e `.venv\Scripts\activate.bat`. |

### Achados abertos nesta reavaliação

Nenhum `BLOCKING` ou `MAJOR`.

| ID | Severidade | Evidência | Nota | Ação |
|---|---|---|---|---|
| — | — | — | Literais `\b2\b`/`\b4\b` em FND-08 (L275–L284) são deliberadamente frouxos para não amarrar API; aceitável no gate BDD. Refinamento fica para unitários pós-interfaces. | Nenhuma — observação apenas |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD `0.2.0` aderente ao design aprovado, executável, falha pelas razões corretas no greenfield, sem antecipar interfaces/implementação. Pronto para gate HITL de aprovação humana dos testes BDD.

---

## QA Engineer — testes unitários `0.1.0` (pós `HUMAN_INTERFACES_APPROVED`)

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Artefato | `unit-test-plan.md` v0.1.0, `tests/unit/test_settings.py` |
| Interfaces base | `0.2.0` aprovadas (`41056ff`) |
| Estado | `TESTS_READY_FOR_REVIEW` |
| Produção alterada | Nenhuma — `load_settings` permanece stub `...` |

### Casos cobertos (UT-01..UT-22)

Defaults 2/4/`CONFIG_PATH=None`; env ausente/whitespace → defaults; int válido; int inválido → `SettingsBootstrapError` sem fallback; `CONFIG_PATH` POSIX/Windows drive/UNC via `Path`; environ injetado vs `None`/`os.environ`; imutabilidade do mapping; Protocol `AppSettings`; OS-agnostic; sem domínio; pathlib sem hardcode de separadores; mensagens sem jargão de shell.

### Comando

```bash
PYTHONPATH=src python3 -m unittest discover -s tests/unit -p "test_*.py" -v
```

### Resultados (red esperado)

| Métrica | Valor |
|---|---|
| testsRun | 27 |
| métodos ok | 7 (UT-01, UT-02, UT-17, UT-19×2, UT-20, UT-21) |
| métodos falhos | 20 |
| failure records (com subTest) | 35 |
| errors | 0 |

Razão dominante das falhas: `load_settings` retorna `None` (corpo `...`) — não levanta `SettingsBootstrapError` nem devolve snapshot `AppSettings`. Red correto pré-implementação.

### Cobertura

Não medida nesta etapa (stub sem implementação mensurável de carga). Gate ≥95% após implementação.

### Próximo passo

Review Architect dos unitários → HITL → implementação Developer.

---

## Review unitários — Tech Lead Architect (`0.1.0`)

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `unit-test-plan.md` v0.1.0, `tests/unit/test_settings.py` |
| Interfaces base | `0.2.0` (`HUMAN_INTERFACES_APPROVED` / registro `3b3f378` / candidato `41056ff`) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Leitura `interfaces.md` 0.2.0 / `design.md` / `unit-test-plan.md` / `settings.py` (stub) / `test_settings.py` | OK |
| `PYTHONPATH=src python3 -m unittest discover -s tests/unit -p "test_*.py" -v` | 27 tests; 7 ok; 20 falhos; 35 failure records (subTest); 0 errors |
| Red pelas razões corretas (stub `...` → `None`) | **OK** — carga tipada falha via `_assert_app_settings` (“stub sem implementação”) ou `SettingsBootstrapError not raised`; constantes/Protocol/estáticos passam |
| Aderência ao contrato (defaults, blank, erros, paths, environ, Protocol, sem domínio) | **OK** |
| Antecipação além do contrato / implementação concreta | **OK** — sem classe concreta prescrita; só `AppSettings` Protocol; stub intacto |

### Matriz de aderência (contrato × suíte)

| Área | Evidência | Veredito |
|---|---|---|
| Defaults `2` / `4` / `CONFIG_PATH→None` | UT-02..UT-04; L80–L108 | OK — I-T01-004 |
| Ausente / blank / whitespace → defaults | UT-05, UT-06 (`""`, espaços, `\t`, `\n`) | OK — I-T01-006 |
| Int válido + zero/negativo sem min/max | UT-07, UT-08, `test_ut07_zero_and_negative_*` | OK — I-T01-003/007/008 |
| Int inválido → `SettingsBootstrapError` sem fallback | UT-09..UT-10; `test_ut09_invalid_index_does_not_return_default_snapshot` | OK — I-T01-007 |
| Mensagem cita env; sem jargão de shell | UT-09/10 (`assertIn` nome); UT-11 (`SHELL_JARGON`) | OK — I-T01-015 |
| `CONFIG_PATH` POSIX / Windows drive / UNC via `Path` | UT-12..UT-14; inexistência de arquivo | OK — I-T01-005/016/009 |
| `environ` injetado vs `None`/`os.environ`; não muta mapping | UT-15..UT-17 | OK — I-T01-002/014 |
| Retorno satisfaz `AppSettings`; OS-agnostic | UT-18, UT-22 (`os.name` posix/nt) | OK — I-T01-001/014 |
| Sem domínio; pathlib sem hardcode de separador | UT-19, UT-20 | OK — I-T01-005/009 |
| Superfície estática (constantes, `Exception`) | UT-01, UT-02, UT-21 | OK |

### Achados abertos

Nenhum `BLOCKING` ou `MAJOR`.

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| S-U01 | `SUGGESTION` | `test_settings.py` L186–L187 | `assertNotIsInstance(ctx.exception, type(None))` é no-op após `assertRaises` bem-sucedido. | Remover ou substituir por assert útil (ex.: mensagem não vazia / contém razão tipada). |
| S-U02 | `SUGGESTION` | `test_settings.py` L368–L377 | Loop AST em UT-20 não aplica asserções (código morto); a proteção real está nos regex em `load_settings`. | Remover o loop inerte ou completar a verificação. |
| S-U03 | `SUGGESTION` | plano §4 vs UT-17 L285–L293 | Plano lista UT-17 como red obrigatório; o caso só verifica imutabilidade do mapping e **passa** com stub (vacuamente correto). | Ajustar plano §4 (UT-17 pode passar no stub) ou exigir também snapshot válido no mesmo teste — sem mudar o invariante. |

### O que está aderente (não bloqueia)

- Cobertura UT-01..UT-22 alinhada a `interfaces.md` 0.2.0 e ao plano.
- Paths nativos como **entrada** de teste (não hardcode de lógica no módulo sob teste).
- Sem parser/DB/secrets/min-max; sem exigir implementação concreta além do Protocol + stub.
- Red pré-implementação pelas razões corretas; produção (`settings.py`) não alterada nesta etapa.

### Bloqueios para aprovação

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — unitários suficientes e aderentes ao contrato aprovado; falham pelo stub pelas razões corretas. Pronto para gate HITL de aprovação humana dos testes unitários.

---

## Review implementação — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | Implementação T01 (`settings.py`, layout `src/github_rag`, `pyproject.toml`, README, `.gitignore`, `.gitattributes`) |
| Design base | `0.2.0` (`HUMAN_DESIGN_APPROVED`) |
| Interfaces base | `0.2.0` (`HUMAN_INTERFACES_APPROVED`) |
| BDD base | `0.2.0` (`HUMAN_BDD_APPROVED` / Architect `APPROVED_BY_ARCHITECT`) |
| Unitários base | `0.1.0` (`HUMAN_UNIT_TESTS_APPROVAL` / Architect `APPROVED_BY_ARCHITECT` / candidato `507b6ac`) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Leitura design `0.2.0` / interfaces `0.2.0` / BDD / unitários aprovados / `settings.py` / README / `pyproject.toml` / layout | OK |
| `git diff 507b6ac -- tests/` | **vazio** — testes BDD/unitários **não** alterados para passar |
| `.venv/bin/python -m pytest tests/unit tests/bdd -v` | **37 passed** (27 unit + 10 BDD); cobertura **100%**; `fail_under=95` respeitado |
| `load_settings` vs contrato I-T01-* | **OK** |
| Sem domínio (parser/JSON/DB/segredos/min-max) | **OK** |
| Windows first-class + Docker/T19 sem `.venv` do host (README + docs do módulo) | **OK** |
| Layout §2.6 + `pyproject` + coverage 95 | **OK** |

### Matriz de aderência

| Área | Evidência | Veredito |
|---|---|---|
| Constantes env + defaults `2`/`4`/`CONFIG_PATH→None` | `settings.py` L39–L92; UT-01..UT-06 | OK — I-T01-003/004/006 |
| `load_settings(environ\|None)` → `AppSettings`; não muta mapping | L212–L271; `_AppSettingsSnapshot` frozen; UT-15..UT-18 | OK — I-T01-001/002/014 |
| Int inválido → `SettingsBootstrapError` (nome + razão; sem shell) | `_load_worker` L205–L209; UT-09..UT-11 | OK — I-T01-007/015 |
| Sem min/max workers | aceita 0/negativo; UT-07 | OK — I-T01-008 |
| `CONFIG_PATH` via `pathlib` / `_NativePath`; sem I/O | L253–L258; UT-12..UT-14/UT-19 | OK — I-T01-005/009/016 |
| OS-agnostic (sem ramificar por shell/OS para defaults) | corpo sem `os.name`/activate; UT-22 | OK — I-T01-012/014 |
| Sem domínio | sem JSON/DB/secrets; FND-08 + UT-19 | OK — I-T01-009 / D-T01-006 |
| Layout placeholders + `__init__.py` | árvore `src/github_rag/...`; FND-06 | OK — D-T01-005 |
| `pyproject` Python ≥3.12; pytest-cov; `fail_under=95` | `pyproject.toml`; FND-05/FND-07 | OK — D-T01-002/004 |
| README PowerShell + cmd + Unix; Docker sem `.venv` host; install ≠ sistema | `README.md`; FND-01..04/FND-10 | OK — D-T01-003/007/009 |
| `.gitignore` `.venv/`; `.gitattributes` EOL | FND-09/FND-10 | OK — D-T01-011 |
| Testes aprovados intactos | diff `507b6ac` em `tests/` = 0 | OK |

### Achados abertos

Nenhum `BLOCKING` ou `MAJOR`.

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| S-I01 | `SUGGESTION` | `settings.py` L247–L250 | Nota de pipeline ainda descreve o gate de interfaces (“corpo após unitários”); implementação já existe. | Remover/atualizar a nota na etapa Blue (docs only). |
| S-I02 | `SUGGESTION` | `settings.py` L33, L257 | `_NativePath = type(Path())` é equivalente a `Path(...)`; indirection desnecessária. | Preferir `Path(raw)` na Blue se tocar o trecho. |
| S-I03 | `SUGGESTION` | design §2.6 vs repo | `tests/conftest.py` previsto no design; ausente. BDD não exige. | Opcional na Blue ou task futura se fixtures forem necessárias. |

### O que está aderente (não bloqueia)

- Contrato `load_settings` / `AppSettings` / `SettingsBootstrapError` implementado sem portas de domínio.
- Windows first-class no README (PowerShell, cmd, `py -3.12`, ExecutionPolicy, invoke sem activate) e Docker/T19 explícito sem `.venv` do host.
- Harness com cobertura 100% (≥95%); suíte aprovada verde sem alteração dos testes.
- Snapshot privado `_AppSettingsSnapshot` satisfaz o Protocol sem expor API de domínio.

### Bloqueios para aprovação

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — implementação aderente a design `0.2.0`, interfaces `0.2.0`, BDD e unitários aprovados. Pronto para gate HITL de aprovação humana da implementação. **Não iniciar Blue** até aprovação humana; sugestões S-I01..S-I03 podem entrar na Blue após HITL.

---

## Review Blue — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | Refatoração Blue (`refactoring.md`, `settings.py` pós B-01) |
| Metas base | B-01, B-02, B-03, B-P (`refactoring.md` passo 16) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Leitura `refactoring.md` §5 / `settings.py` / UT-22 | OK |
| B-01 (nota pipeline) | **DONE** — docstring “Implementação” (L247–L249); sem stub pendente |
| B-02 (`Path` direto) | Tentativa falhou UT-22; revertida; meta → **`WONT_APPLY`** |
| B-03 (`conftest.py`) | **DEFERRED** |
| `.venv/bin/python -m pytest tests/unit tests/bdd -q` | 37 passed; cobertura 100% |
| Microbenchmark §2.1 | typed ~11.8 ms / empty ~6.8 ms ×10k — ordem do baseline (B-P OK) |
| Testes aprovados alterados? | **Não** |

### Achados

| ID | Severidade | Evidência | Achado | Decisão |
|---|---|---|---|---|
| B-02 / S-I02 | — (meta revisada) | UT-22 L315–L330; Python 3.14 `Path` vs `os.name`; `settings.py` L33 `_NativePath` | Premissa “`_NativePath` ≡ `Path(...)`” é falsa sob mock de `os.name`: `Path` instancia `PosixPath`/`WindowsPath` e quebra igualdade exigida por I-T01-014/UT-22. | **WONT_APPLY** — manter `_NativePath = type(Path())` (classe nativa fixada no import). Sem mudança de testes. |
| — | `BLOCKING`/`MAJOR` | — | Nenhum aberto | — |

### Resolução das metas

| Meta | Status |
|---|---|
| B-01 | `APPLIED` |
| B-02 | `WONT_APPLY` (manter `_NativePath` por compatibilidade OS-agnostic / UT-22) |
| B-03 | `DEFERRED` |
| B-P | `OK` |

### Decisão

`BLUE_APPROVED_BY_ARCHITECT` — Blue concluída sem regressão de comportamento, contrato ou cobertura. Pode seguir para QA (passo 19: suites, regressão, cobertura ≥95%).

---

## QA final — validação pré-HITL de implementação

| Campo | Valor |
|---|---|
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Pré-condição | Blue `BLUE_APPROVED_BY_ARCHITECT` |
| Unitários base | `0.1.0` / candidato `507b6ac` (`HUMAN_UNIT_TESTS_APPROVED`) |
| Resultado | `VERIFICATION_PASSED` |

### Integridade dos testes aprovados

| Check | Resultado |
|---|---|
| `git diff 507b6ac -- tests/` | **vazio** (0 bytes) — BDD e unitários **não** adulterados pós-aprovação |

### Comandos executados

```bash
git diff 507b6ac -- tests/
.venv/bin/python -m pytest tests/unit -q --cov=github_rag --cov-fail-under=95
.venv/bin/python -m pytest tests/bdd -q --no-cov
.venv/bin/python -m pytest tests/ -q --cov=github_rag --cov-fail-under=95
.venv/bin/python -m pytest tests/unit tests/bdd -v --cov=github_rag --cov-report=term-missing --cov-fail-under=95
```

### Resultados

| Suite | Resultado |
|---|---|
| Unitários (`tests/unit`) | **27 passed** (36 subtests) |
| BDD (`tests/bdd`) | **10 passed** (FND-01..FND-10) |
| Regressão completa (`tests/`) | **37 passed** |

### Cobertura

| Item | Valor |
|---|---|
| `pyproject.toml` `[tool.coverage.report] fail_under` | **95** (confirmado) |
| Cobertura total (`github_rag`) | **100.00%** (44 stmts, 0 miss, 2 branches, 0 partial) |
| `settings.py` | **100%** |
| Gate `--cov-fail-under=95` | **atingido** |

### Achados

Nenhum. Sem regressão; sem adulteração de testes; cobertura ≥95%.

### Decisão

`VERIFICATION_PASSED` — pronto para **HITL de aprovação humana da implementação**.

---

## Aprovação humana — implementação + Blue

| Campo | Valor |
|---|---|
| Gate | `HUMAN_IMPLEMENTATION_APPROVAL` |
| Decisão | `APROVADO` |
| Autor | camilocoelhogomes |
| Data | 2026-07-18 |
| Commit candidato | `819204d` |
| Escopo aprovado | Implementação + refatoração Blue da T01 |

Aprovação humana explícita registrada após `BLUE_APPROVED_BY_ARCHITECT` e `VERIFICATION_PASSED`. O histórico técnico anterior permanece inalterado.
