# Interfaces — T27-gap-sdk-dec015-conformity

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T27-gap-sdk-dec015-conformity` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T27-gap-sdk-dec015-conformity` |
| Escopo desta etapa | Contratos de **helpers de teste** (não Protocols de produção) — a suíte consolidada, os helpers compartilhados reaproveitados/promovidos e o mapa cláusula→módulo |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Escrito e aprovado pelo próprio Architect por instrução explícita do orquestrador (modo autônomo). Sem Protocols novos em `src/`; contratos vivem só em `tests/`. |

## 1. Princípio de design desta camada

BDD-024 é uma propriedade de **conformidade de implementação** (pins + binding aos
SDKs oficiais), não um contrato de domínio novo. Por isso esta task **não** define
`Protocol`/classe em `src/github_rag/**` — as interfaces aqui são contratos de
**helpers de teste**, seguindo a convenção já estabelecida no repositório de
`tests/unit/<pacote>/helpers.py` (ex.: `tests/unit/mcp/helpers.py::MCP_PKG` +
`collect_imports`, já reaproveitado por `tests/bdd/test_management_ui.py` via
`from tests.unit.ui.helpers import ...`).

Duas decisões de contrato guiam a evitação de duplicação lógica (design §2.2):

| ID | Decisão | Motivo |
|---|---|---|
| I-T27-001 | Pins DEC-015 (`DEC015_RUNTIME_PACKAGES`, `DEC015_TREE_SITTER_GRAMMARS`, parser de `pyproject.toml`) migram de definição **local e privada** em `tests/bdd/test_container_delivery.py` para um módulo compartilhado público `tests/bdd/support/dec015_pins.py` | Hoje só existem como `_pyproject_deps`/`_dep_name` prefixados com `_` dentro de um arquivo de teste — não é o padrão do repositório (que usa `helpers.py` público) e não é seguro importar através de dois arquivos de teste distintos. Extrair para um módulo público elimina a única duplicação real do lote |
| I-T27-002 | Constantes de conformidade de import da UI (`DOMAIN_MODULES`, `FASTAPI_MODULES`, `FORBIDDEN_IN_DOMAIN`, `FORBIDDEN_HOMEMADE`) e o AST-walk de um arquivo migram de `tests/unit/ui/test_imports.py` (local) para `tests/unit/ui/helpers.py` (já existe e já é importado por `tests/bdd/test_management_ui.py`) | Alinha ao padrão já usado por `tests/unit/mcp/helpers.py::collect_imports`; remove a única outra duplicação candidata do lote |

Ambas as migrações são **refactors comportamentalmente neutros**: as suítes que já
existem (`TestCD05SdkManifest`, `TestUiImports`) passam a importar os mesmos nomes
de um novo local público, sem mudar nenhuma asserção nem resultado.

## 2. Contrato — `tests/bdd/support/dec015_pins.py` (novo, público)

```python
# tests/bdd/support/dec015_pins.py — NOVO, contrato de teste (não é API de produção)

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT: Path
"""Raiz do repositório, resolvida a partir deste arquivo.

Responsabilidade
    Âncora única de path para localizar ``pyproject.toml`` sem repetir
    ``Path(__file__).resolve().parents[N]`` em cada teste que precisa dos pins.

Motivo da separação
    Antes duplicado (implicitamente) em ``test_container_delivery.py``; um único
    ponto evita drift se a árvore de testes for reorganizada.
"""

PYPROJECT_PATH: Path
"""``REPO_ROOT / "pyproject.toml"``."""

DEC015_RUNTIME_PACKAGES: tuple[str, ...]
"""Nomes de pacote (sem versão) exigidos por DEC-015 em ``[project].dependencies``.

Responsabilidade
    Lista única/canônica dos pacotes runtime da tabela DEC-015 (inclui
    ``sqlalchemy``, ``alembic``, ``psycopg``, ``apscheduler``, ``PyGithub``,
    ``GitPython``, ``pathspec``, ``tree-sitter``, ``qdrant-client``, ``openai``,
    ``mcp``, ``fastapi``, ``uvicorn``).

Motivo da separação
    Migrada de ``tests/bdd/test_container_delivery.py`` (I-T27-001): evita duas
    fontes de verdade da mesma tabela quando `test_dec015_conformity.py` precisa
    do mesmo conjunto.
"""

DEC015_TREE_SITTER_GRAMMARS: tuple[str, ...]
"""Nomes das 9 grammars Tree-sitter pinadas (mesmo racional acima)."""

DEC015_VERSION_CONSTRAINTS: dict[str, re.Pattern[str]]
"""Pacote → regex da faixa de versão mínima esperada pela tabela DEC-015.

Responsabilidade
    Formalizar, por pacote, o que conta como "faixa de versão coerente com o
    default DEC-015" (ex.: ``sqlalchemy`` → ``r">=\\s*2"``; ``mcp`` →
    ``r">=\\s*1\\.27.*<\\s*2"``; ``apscheduler`` → ``r">=\\s*3\\.10.*<\\s*4"``).
    Não valida SemVer completo — só que a linha declara *alguma* faixa mínima
    plausível, suficiente para pegar regressões grosseiras (pin removido, `*`,
    ou major incompatível).

Motivo da separação
    Cenário novo (DEC015-01 na versão desta task); nasce aqui porque é dado, não
    comportamento — Developer/QA podem revisar/estender sem tocar em lógica de
    teste.
"""


def read_pyproject_dependencies(path: Path = PYPROJECT_PATH) -> list[str]:
    """Lê ``[project].dependencies`` de ``pyproject.toml``; levanta se ausente/vazio.

    Responsabilidade
        Único parser TOML dos testes de conformidade de manifesto.

    Motivo da separação
        Substitui ``_pyproject_deps`` privado de ``test_container_delivery.py``
        (I-T27-001) — mesma assinatura semântica, nome público.
    """
    ...


def dependency_name(spec: str) -> str:
    """Extrai o nome do pacote de uma linha de dependência (ex. ``"mcp>=1.27,<2"`` → ``"mcp"``).

    Motivo da separação
        Substitui ``_dep_name`` privado (I-T27-001); usado tanto pelo assert de
        presença (CD-05) quanto pelo assert de faixa de versão (DEC015-01).
    """
    ...


def dependency_spec(name: str, deps: list[str]) -> str:
    """Retorna a linha de dependência completa para ``name``; levanta se ausente.

    Responsabilidade
        Dar à DEC015-01 acesso à *string* completa (com faixa de versão), não só
        ao nome — o que ``dependency_name``/o assert de presença de CD-05 não
        precisavam expor antes.

    Motivo da separação
        Nova necessidade (checar faixa de versão) não existia em T19; adicionar
        aqui em vez de em ``test_container_delivery.py`` mantém CD-05 sem
        conhecer o conceito de "faixa de versão exigida" — responsabilidade de
        T27, não de T19.
    """
    ...
```

**Consumidores:**

| Consumidor | Uso |
|---|---|
| `tests/bdd/test_container_delivery.py::TestCD05SdkManifest` (refactor) | Importa `DEC015_RUNTIME_PACKAGES`, `DEC015_TREE_SITTER_GRAMMARS`, `read_pyproject_dependencies` (era `_pyproject_deps`), `dependency_name` (era `_dep_name`) — mesma asserção, mesmo resultado |
| `tests/bdd/test_dec015_conformity.py::TestDEC01PinsVersionMatrix` | Importa tudo acima + `dependency_spec` + `DEC015_VERSION_CONSTRAINTS` |
| `tests/bdd/test_dec015_conformity.py::TestDEC05TreeSitterGrammarWiring` | Importa `DEC015_TREE_SITTER_GRAMMARS` |

## 3. Contrato — promoção de helpers UI (`tests/unit/ui/helpers.py`)

```python
# tests/unit/ui/helpers.py — ADIÇÕES (arquivo já existe; ver I-T27-002)

DOMAIN_MODULES: tuple[str, ...]      # ("ports.py", "labels.py", "serialize.py", "errors.py")
FASTAPI_MODULES: tuple[str, ...]     # ("app.py", "api.py")
FORBIDDEN_IN_DOMAIN: frozenset[str]  # {"fastapi", "starlette", "uvicorn", "httpx"}
FORBIDDEN_HOMEMADE: frozenset[str]   # {"urllib", "urllib3", "aiohttp", "requests"}


def imports_of_file(path: Path) -> set[str]:
    """Nomes top-level importados (AST) por um único arquivo `.py`.

    Responsabilidade
        Mesma extração que hoje vive como ``_imports`` privado em
        ``tests/unit/ui/test_imports.py`` — promovida a público para reuso.

    Motivo da separação
        Espelha ``collect_imports`` de ``tests/unit/mcp/helpers.py`` (que opera
        sobre um diretório inteiro); UI precisa de granularidade por arquivo
        porque a regra difere por módulo (`DOMAIN_MODULES` vs `FASTAPI_MODULES`).
        Duas funções, escopos diferentes — não são a mesma responsabilidade.
    """
    ...
```

**Consumidores:**

| Consumidor | Uso |
|---|---|
| `tests/unit/ui/test_imports.py::TestUiImports` (refactor) | Importa as 4 constantes + `imports_of_file` (era `_imports`) de `tests/unit/ui/helpers.py` — mesma asserção, mesmo resultado |
| `tests/bdd/test_dec015_conformity.py::TestDEC09FastApiBinding` | Importa `UI_PKG` (já público), `FASTAPI_MODULES`, `imports_of_file` |

`tests/unit/mcp/helpers.py` **não é alterado** — já expõe `MCP_PKG`,
`FORBIDDEN_IMPORTS`, `collect_imports` publicamente; `TestDEC08McpSdkBinding`
importa direto.

## 4. Contrato — `tests/bdd/test_dec015_conformity.py` (novo)

### 4.1 `SourceConformityRule` + `assert_source_conforms`

```python
# tests/bdd/test_dec015_conformity.py — helpers internos ao módulo

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceConformityRule:
    """Regra declarativa: um arquivo de produção deve/não deve conter padrões.

    Responsabilidade
        Representar como *dado* (não como código imperativo repetido) a forma
        comum das cláusulas DEC015-02/07/10/11/12: "este módulo usa o binding
        oficial X" (``required_patterns``) "e nunca reimplementa Y"
        (``forbidden_patterns``). ``clause`` é o rótulo humano usado nas
        mensagens de falha (rastreabilidade cláusula→arquivo).

    Motivo da separação
        Sem esta abstração, 5 classes de teste repetiriam
        ``inspect.getsource`` + laço de ``assertRegex``/``assertNotRegex`` com
        só o conteúdo variando — a regra em si (não a mecânica de checagem) é
        o que QA/Developer revisam com mais frequência; separar os dois reduz
        o que muda quando uma cláusula é ajustada.
    """

    clause: str
    module_path: Path
    required_patterns: tuple[re.Pattern[str], ...]
    forbidden_patterns: tuple[re.Pattern[str], ...] = field(default_factory=tuple)


def assert_source_conforms(rule: SourceConformityRule) -> str:
    """Lê o source de ``rule.module_path`` e aplica ``rule``; retorna o source.

    Responsabilidade
        Único ponto que chama ``inspect.getsource``/``Path.read_text`` para as
        regras declarativas; mensagens de ``AssertionError`` sempre citam
        ``rule.clause`` + o padrão que faltou/apareceu indevidamente.

    Motivo da separação
        Assinatura estável e reaproveitada por 5 `TestCase` diferentes
        (DEC015-02/07/10/11/12); qualquer melhoria de mensagem de erro
        beneficia todas de uma vez.
    """
    ...
```

### 4.2 `assert_module_importable` (referências não-duplicantes)

```python
def assert_module_importable(dotted_path: str, *, clause: str) -> "ModuleType":
    """Importa ``dotted_path``; levanta ``AssertionError`` nomeando ``clause`` se falhar.

    Responsabilidade
        Prova mínima de que uma suíte de evidência **já existente** (Git/
        GitPython, pathspec, Tree-sitter, Qdrant/openai) continua presente e
        sintaticamente válida, sem reexecutar/reimplementar as asserções de
        comportamento que ela já faz.

    Motivo da separação
        É a materialização direta da regra de design "não duplicar logicamente
        evidência já provada" (design §2.2): usa o próprio mecanismo de import
        do Python como oráculo, em vez de copiar asserções de outro arquivo.
    """
    ...
```

Usado por `TestDEC03GitPythonReference`, `TestDEC04PathspecReference`,
`TestDEC06QdrantOpenAiReference` e por `TestBDD024FullTextCoverage` (§4.4).

### 4.3 `DEC015_INTEGRATION_RULES` (instâncias concretas)

```python
DEC015_INTEGRATION_RULES: tuple[SourceConformityRule, ...] = (
    SourceConformityRule(
        clause="GitHub API via PyGithub (DEC015-02)",
        module_path=SRC / "sources" / "github" / "client.py",
        required_patterns=(re.compile(r"from\s+github\s+import"),),
        forbidden_patterns=(re.compile(r"\brequests\.|\bhttpx\.|urllib\.request"),),
    ),
    SourceConformityRule(
        clause="GitHub API via PyGithub — snapshot (DEC015-02)",
        module_path=SRC / "snapshot" / "github.py",
        required_patterns=(re.compile(r"from\s+github\s+import"),),
        forbidden_patterns=(re.compile(r"\brequests\.|\bhttpx\.|urllib\.request"),),
    ),
    SourceConformityRule(
        clause="Cron via APScheduler (DEC015-07)",
        module_path=SRC / "schedule" / "scheduler.py",
        required_patterns=(re.compile(r"from\s+apscheduler\."),),
        forbidden_patterns=(),
    ),
    SourceConformityRule(
        clause="Validação cron via APScheduler (DEC015-07)",
        module_path=SRC / "schedule" / "cron_expr.py",
        required_patterns=(
            re.compile(r"from\s+apscheduler\.triggers\.cron\s+import\s+CronTrigger"),
        ),
        forbidden_patterns=(re.compile(r"def\s+_parse_cron_field|re\.compile\(r?[\"'].{0,20}\\d\{1,2\}"),),
    ),
    SourceConformityRule(
        clause="Zoekt HTTP oficial /api/search (DEC015-11 / DEC-016)",
        module_path=SRC / "index" / "zoekt" / "client.py",
        required_patterns=(
            re.compile(r"/api/search"),
            re.compile(r"urllib\.request"),
        ),
        forbidden_patterns=(re.compile(r"struct\.pack|struct\.unpack|\bmmap\b"),),
    ),
    SourceConformityRule(
        clause="Zoekt CLI oficial zoekt-index (DEC015-11 / DEC-016)",
        module_path=SRC / "index" / "zoekt" / "runner.py",
        required_patterns=(
            re.compile(r"subprocess\.run"),
        ),
        forbidden_patterns=(re.compile(r"shell\s*=\s*True"),),
    ),
    SourceConformityRule(
        clause="Zoekt adaptador não lê shard binário (DEC015-11 / DEC-016)",
        module_path=SRC / "index" / "zoekt" / "index.py",
        required_patterns=(
            re.compile(r"_DEFAULT_INDEX_BIN"),
            re.compile(r"post_search"),
        ),
        forbidden_patterns=(re.compile(r"struct\.pack|struct\.unpack|\bmmap\b|\.zoekt[\"']"),),
    ),
    SourceConformityRule(
        clause="DT-001 eliminado — GitPython sem parsing ad-hoc (DEC015-12)",
        module_path=SRC / "sources" / "local" / "git_fs.py",
        required_patterns=(re.compile(r"from\s+git\s+import\s+Repo\b|from\s+git\.repo\s+import\s+Repo\b"),),
        forbidden_patterns=(
            re.compile(r"packed-refs"),
            re.compile(r"_resolve_git_dir"),
            re.compile(r"_has_main_branch"),
        ),
    ),
)
```

**Responsabilidade da tupla:** ser a lista única e revisável de todas as regras
`SourceConformityRule` do arquivo — um `TestCase` genérico
(`TestDEC015IntegrationSourceRules`) itera `DEC015_INTEGRATION_RULES` e chama
`assert_source_conforms` por item, nomeando a falha pela `clause`.

**Motivo de ainda ter classes por cenário (DEC015-02/07/11/12) além dessa tupla:**
a tupla cobre o *quê* é checado; as classes nomeadas (`TestDEC02...`,
`TestDEC07...` etc.) existem para que `pytest -k DEC02` ou a leitura do relatório
de teste mapeiem 1:1 para o ID do cenário BDD — a tupla é o dado consumido
internamente por cada classe (cada classe filtra `DEC015_INTEGRATION_RULES` pela
sua própria `clause` ou mantém sua própria sub-tupla), não um mecanismo paralelo
de execução.

### 4.4 `BDD024_CLAUSE_MODULE_MAP`

```python
BDD024_CLAUSE_MODULE_MAP: dict[str, tuple[str, ...]] = {
    "sdk_oficial_por_integracao": (
        "tests.bdd.test_dec015_conformity",  # DEC015-01/02/05/07/08/09/10 (este módulo)
        "tests.bdd.test_local_discovery_git_sdk",  # DEC015-03
        "tests.bdd.test_file_eligibility",  # DEC015-04
        "tests.bdd.test_treesitter_chunker",  # DEC015-05 (referência)
        "tests.bdd.test_qdrant_vector_store",  # DEC015-06
    ),
    "br024_sqlalchemy_alembic_psycopg3": (
        "tests.bdd.test_dec015_conformity",  # DEC015-10
    ),
    "dec016_zoekt_adaptador_fino": (
        "tests.bdd.test_dec015_conformity",  # DEC015-11
        "tests.bdd.test_zoekt_adapter",  # Protocol/Fake — evidência complementar
    ),
    "sem_reinvencao_cliente_cli_protocolo": (
        "tests.bdd.test_dec015_conformity",  # DEC015-02/07/09/11 (asserts negativos)
    ),
    "dt001_eliminado": (
        "tests.bdd.test_dec015_conformity",  # DEC015-12
        "tests.bdd.test_local_discovery_git_sdk",  # T20-SDK-01..03 — comportamental
    ),
}
"""Mapa cláusula-de-BDD-024 → módulos de teste responsáveis.

Responsabilidade
    Dado versionado (não lógica) que torna a cobertura de BDD-024 auditável por
    leitura direta — cada chave é uma cláusula do texto (`Dado/Quando/Então/E`)
    e o valor é a lista de módulos cuja falha de import deve ser tratada como
    "a cláusula perdeu evidência".

Motivo da separação
    ``TestBDD024FullTextCoverage`` (§4.5) só percorre este dict; separar dado de
    mecanismo permite que QA/Architect revisem a completude da cobertura sem
    ler código de teste.
"""
```

### 4.5 `TestBDD024FullTextCoverage`

```python
class TestBDD024FullTextCoverage(unittest.TestCase):
    """Agregador de rastreabilidade — DEC015-13.

    Responsabilidade
        Garantir que todo módulo citado em ``BDD024_CLAUSE_MODULE_MAP`` continua
        importável; falhar nomeando cláusula + módulo se não.

    Motivo da separação
        É a única classe que conhece o mapa completo; as demais classes
        (DEC015-01..12) não precisam saber da existência umas das outras.
    """

    def test_every_clause_has_importable_evidence(self) -> None:
        for clause, modules in BDD024_CLAUSE_MODULE_MAP.items():
            for dotted in modules:
                assert_module_importable(dotted, clause=clause)
```

## 5. Mapa de classes de teste → cenário BDD

| Classe | Cenário BDD | Reaproveita |
|---|---|---|
| `TestDEC01PinsVersionMatrix` | DEC015-01 | `tests/bdd/support/dec015_pins.py` |
| `TestDEC02GitHubPyGithubBinding` | DEC015-02 | `SourceConformityRule`/`assert_source_conforms` |
| `TestDEC03GitPythonReference` | DEC015-03 | `assert_module_importable` |
| `TestDEC04PathspecReference` | DEC015-04 | `assert_module_importable` |
| `TestDEC05TreeSitterGrammarWiring` | DEC015-05 | `dec015_pins.DEC015_TREE_SITTER_GRAMMARS` + `OfficialGrammarRegistry` (produção) |
| `TestDEC06QdrantOpenAiReference` | DEC015-06 | `assert_module_importable` |
| `TestDEC07ApSchedulerBinding` | DEC015-07 | `SourceConformityRule`/`assert_source_conforms` |
| `TestDEC08McpSdkBinding` | DEC015-08 | `tests.unit.mcp.helpers` (`MCP_PKG`, `FORBIDDEN_IMPORTS`, `collect_imports`) |
| `TestDEC09FastApiBinding` | DEC015-09 | `tests.unit.ui.helpers` (`UI_PKG`, `FASTAPI_MODULES`, `imports_of_file`) |
| `TestDEC10Br024Postgres` | DEC015-10 | `SourceConformityRule`/`assert_source_conforms` + regex de URL |
| `TestDEC11Dec016ZoektRealAdapter` | DEC015-11 | `SourceConformityRule`/`assert_source_conforms` |
| `TestDEC12Dt001Elimination` | DEC015-12 | `SourceConformityRule`/`assert_source_conforms` |
| `TestBDD024FullTextCoverage` | DEC015-13 | `BDD024_CLAUSE_MODULE_MAP` + `assert_module_importable` |

DEC015-14 (consistência de auditoria) não gera classe nova — é o efeito esperado
sobre `tests/bdd/test_mvp_e2e_audit_coverage_inventory.py` e
`tests/bdd/test_mvp_e2e_audit_gap_fill_backlog.py` após a edição pontual
(design §2.5, bdd §DEC015-14).

## 6. Fora de escopo desta camada

| Item | Motivo |
|---|---|
| `Protocol`/classe nova em `src/github_rag/**` | BDD-024 é conformidade de implementação, não domínio novo (design §3) |
| Reescrever `inspect.getsource`/AST-walk já existente em outras suítes | Design §2.2 — só referência via `assert_module_importable` |
| Parser YAML/CLI real de Zoekt em produção | Fora do gap; `ZoektExactCodeIndex` já implementado (T10), só ganha prova nova |
| Rodar `alembic upgrade`/Postgres/Docker real | BR-024 provado por inspeção estática, igual ao método do inventário T01 |

## 7. Handoff

| Consumidor | Uso |
|---|---|
| QA | Escrever `unit-test-plan.md` com corner cases por `SourceConformityRule`/classe (§4.3/§5) antes do Developer implementar |
| Developer | Criar `tests/bdd/support/__init__.py` + `dec015_pins.py`; promover helpers UI; refatorar `TestCD05SdkManifest`/`TestUiImports` para importar dos novos locais (comportamento idêntico); implementar `test_dec015_conformity.py` conforme §4; editar `coverage-inventory.md` + as duas suítes de auditoria (DEC015-14) |
| Architect (Blue) | Revisar se `DEC015_INTEGRATION_RULES` cobre exatamente as cláusulas do design sem regras órfãs ou faltantes; revisar se a promoção de helpers não introduziu duplicação reversa |

Mudança que exija `Protocol` novo em `src/`, infraestrutura real (Docker/GitHub) ou
alteração de `e2e/robot/**` ⇒ `SCOPE_CHANGE_REQUIRED` (retorna à descoberta).

## 8. Estado

`APPROVED_BY_ARCHITECT` — interfaces `0.1.0` completas: I-T27-001/002 +
`dec015_pins.py` + promoção de helpers UI + `SourceConformityRule`/
`assert_source_conforms`/`assert_module_importable`/`BDD024_CLAUSE_MODULE_MAP` +
mapa de 13 classes. Sem Protocols de produção novos; sem BLOCKING/MAJOR abertos.
Prosseguir para `unit-test-plan.md` (QA).

---

**Decisão:** `APPROVED_BY_ARCHITECT`
**Data:** 2026-07-19
**Autor:** tech-lead-architect
**Versão:** v0.1.0
