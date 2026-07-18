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
