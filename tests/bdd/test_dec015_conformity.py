"""
BDD executável — T27-gap-sdk-dec015-conformity.

Prova integral de BDD-024 (`requirements.md` §BDD-024), DEC-015 (tabela de
SDKs oficiais), BR-024 (PostgreSQL via SQLAlchemy 2.x + Alembic + psycopg3),
DEC-016 (Zoekt como adaptador fino) e eliminação de DT-001, consolidada num
único ponto de entrada.

Cenários: DEC015-01..13 — ver
    spec/features/github-etl-mcp-rag/tasks/T27-gap-sdk-dec015-conformity/bdd.md

Método: 100% inspeção estática (`Path.read_text`/AST/`tomllib`) +
`importlib.import_module`. Nenhum GitHub real, Docker, Zoekt/Qdrant real ou
Robot é necessário — mesmo método já validado pelo inventário T01. Para
integrações já providas com evidência BDD-024 explícita em suítes existentes
(Git/GitPython, pathspec, Tree-sitter, Qdrant/openai), este módulo apenas
referencia essas suítes (`assert_module_importable`) em vez de duplicar a
lógica de asserção já provada (design §2.2).

Execução:
    python -m pytest tests/bdd/test_dec015_conformity.py -q
"""

from __future__ import annotations

import inspect
import re
import tempfile
import unittest
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from tests.bdd.support.dec015_pins import (
    DEC015_RUNTIME_PACKAGES,
    DEC015_TREE_SITTER_GRAMMARS,
    DEC015_VERSION_CONSTRAINTS,
    REPO_ROOT,
    dependency_name,
    dependency_spec,
    read_pyproject_dependencies,
)

SRC = REPO_ROOT / "src" / "github_rag"


# ---------------------------------------------------------------------------
# Helpers internos do módulo (interfaces.md §4.1/§4.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceConformityRule:
    """Regra declarativa: um arquivo de produção deve/não deve conter padrões.

    Responsabilidade
        Representar como *dado* (não como código imperativo repetido) a
        forma comum das cláusulas DEC015-02/07/10/11/12: "este módulo usa o
        binding oficial X" (``required_patterns``) "e nunca reimplementa Y"
        (``forbidden_patterns``). ``clause`` é o rótulo humano usado nas
        mensagens de falha (rastreabilidade cláusula→arquivo).

    Motivo da separação
        Sem esta abstração, 5 classes de teste repetiriam
        ``inspect.getsource``/``Path.read_text`` + laço de
        ``assertRegex``/``assertNotRegex`` com só o conteúdo variando — a
        regra em si (não a mecânica de checagem) é o que QA/Developer
        revisam com mais frequência; separar os dois reduz o que muda
        quando uma cláusula é ajustada.
    """

    clause: str
    module_path: Path
    required_patterns: tuple[re.Pattern[str], ...]
    forbidden_patterns: tuple[re.Pattern[str], ...] = field(default_factory=tuple)


def assert_source_conforms(rule: SourceConformityRule) -> str:
    """Lê o source de ``rule.module_path`` e aplica ``rule``; retorna o source.

    Responsabilidade
        Único ponto que lê o arquivo para as regras declarativas; mensagens
        de ``AssertionError`` sempre citam ``rule.clause`` + o padrão que
        faltou/apareceu indevidamente.

    Motivo da separação
        Assinatura estável e reaproveitada por várias ``TestCase`` diferentes
        (DEC015-02/07/11/12); qualquer melhoria de mensagem de erro
        beneficia todas de uma vez.
    """
    if not rule.module_path.is_file():
        raise AssertionError(
            f"{rule.clause}: módulo de produção ausente: {rule.module_path}"
        )
    source = rule.module_path.read_text(encoding="utf-8")
    for pattern in rule.required_patterns:
        if not pattern.search(source):
            raise AssertionError(
                f"{rule.clause}: padrão obrigatório ausente "
                f"({pattern.pattern!r}) em {rule.module_path}"
            )
    for pattern in rule.forbidden_patterns:
        if pattern.search(source):
            raise AssertionError(
                f"{rule.clause}: padrão banido encontrado "
                f"({pattern.pattern!r}) em {rule.module_path}"
            )
    return source


def assert_module_importable(dotted_path: str, *, clause: str) -> ModuleType:
    """Importa ``dotted_path``; levanta ``AssertionError`` nomeando ``clause`` se falhar.

    Responsabilidade
        Prova mínima de que uma suíte de evidência **já existente** (Git/
        GitPython, pathspec, Tree-sitter, Qdrant/openai) continua presente e
        sintaticamente válida, sem reexecutar/reimplementar as asserções de
        comportamento que ela já faz.

    Motivo da separação
        É a materialização direta da regra de design "não duplicar
        logicamente evidência já provada" (design §2.2): usa o próprio
        mecanismo de import do Python como oráculo, em vez de copiar
        asserções de outro arquivo.
    """
    if not isinstance(dotted_path, str) or not dotted_path.strip():
        raise AssertionError(f"{clause}: dotted_path inválido: {dotted_path!r}")
    try:
        return importlib.import_module(dotted_path)
    except Exception as exc:  # noqa: BLE001 — qualquer falha de import é lacuna
        raise AssertionError(
            f"{clause}: módulo de evidência não importável: {dotted_path} "
            f"({type(exc).__name__}: {exc})"
        ) from exc


# ---------------------------------------------------------------------------
# DEC015_INTEGRATION_RULES (interfaces.md §4.3)
# ---------------------------------------------------------------------------

_HOMEMADE_HTTP_CALL_RE = re.compile(
    r"\brequests\.(get|post|put|patch|delete|head|options|Session)\s*\("
    r"|\bhttpx\.(get|post|put|patch|delete|Client)\s*\("
    r"|urllib\.request"
)
"""Chamada HTTP caseira real — distingue de ``requests.exceptions.RequestException``.

Importar tipos de exceção de ``requests``/``httpx`` para traduzir falhas de
transporte do SDK oficial (PyGithub já usa ``requests`` internamente) não é
"reinventar cliente HTTP" — só invocar verbos/`Session`/`urllib.request`
diretamente é.
"""

DEC015_INTEGRATION_RULES: tuple[SourceConformityRule, ...] = (
    SourceConformityRule(
        clause="GitHub API via PyGithub (DEC015-02)",
        module_path=SRC / "sources" / "github" / "client.py",
        required_patterns=(re.compile(r"from\s+github\s+import"),),
        # Nota: `requests.exceptions.RequestException` é permitido — traduz
        # falha de transporte do PyGithub sem chamar a API caseiramente. O
        # que é banido é a chamada HTTP direta (verbo/Session/urllib).
        forbidden_patterns=(_HOMEMADE_HTTP_CALL_RE,),
    ),
    SourceConformityRule(
        clause="GitHub API via PyGithub — snapshot (DEC015-02)",
        module_path=SRC / "snapshot" / "github.py",
        required_patterns=(re.compile(r"from\s+github\s+import"),),
        forbidden_patterns=(_HOMEMADE_HTTP_CALL_RE,),
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
        forbidden_patterns=(
            re.compile(r"def\s+_parse_cron_field|re\.compile\(r?[\"'].{0,20}\\d\{1,2\}"),
        ),
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
        required_patterns=(re.compile(r"subprocess\.run"),),
        forbidden_patterns=(re.compile(r"shell\s*=\s*True"),),
    ),
    SourceConformityRule(
        clause="Zoekt adaptador não lê shard binário (DEC015-11 / DEC-016)",
        module_path=SRC / "index" / "zoekt" / "index.py",
        required_patterns=(
            re.compile(r"_DEFAULT_INDEX_BIN"),
            re.compile(r"post_search"),
        ),
        forbidden_patterns=(
            re.compile(r"struct\.pack|struct\.unpack|\bmmap\b|\.zoekt[\"']"),
        ),
    ),
    SourceConformityRule(
        clause="DT-001 eliminado — GitPython sem parsing ad-hoc (DEC015-12)",
        module_path=SRC / "sources" / "local" / "git_fs.py",
        required_patterns=(
            re.compile(r"from\s+git\s+import\s+Repo\b|from\s+git\.repo\s+import\s+Repo\b"),
        ),
        forbidden_patterns=(
            re.compile(r"packed-refs"),
            re.compile(r"_resolve_git_dir"),
            re.compile(r"_has_main_branch"),
        ),
    ),
)


def _rules_matching(needle: str) -> tuple[SourceConformityRule, ...]:
    return tuple(rule for rule in DEC015_INTEGRATION_RULES if needle in rule.clause)


# ---------------------------------------------------------------------------
# BDD024_CLAUSE_MODULE_MAP (interfaces.md §4.4)
# ---------------------------------------------------------------------------

BDD024_CLAUSE_MODULE_MAP: dict[str, tuple[str, ...]] = {
    "sdk_oficial_por_integracao": (
        "tests.bdd.test_dec015_conformity",
        "tests.bdd.test_local_discovery_git_sdk",
        "tests.bdd.test_file_eligibility",
        "tests.bdd.test_treesitter_chunker",
        "tests.bdd.test_qdrant_vector_store",
    ),
    "br024_sqlalchemy_alembic_psycopg3": (
        "tests.bdd.test_dec015_conformity",
    ),
    "dec016_zoekt_adaptador_fino": (
        "tests.bdd.test_dec015_conformity",
        "tests.bdd.test_zoekt_adapter",
    ),
    "sem_reinvencao_cliente_cli_protocolo": (
        "tests.bdd.test_dec015_conformity",
    ),
    "dt001_eliminado": (
        "tests.bdd.test_dec015_conformity",
        "tests.bdd.test_local_discovery_git_sdk",
    ),
}
"""Mapa cláusula-de-BDD-024 → módulos de teste responsáveis.

Responsabilidade
    Dado versionado (não lógica) que torna a cobertura de BDD-024 auditável
    por leitura direta — cada chave é uma cláusula do texto
    (`Dado/Quando/Então/E`) e o valor é a lista de módulos cuja falha de
    import deve ser tratada como "a cláusula perdeu evidência".

Motivo da separação
    ``TestBDD024FullTextCoverage`` só percorre este dict; separar dado de
    mecanismo permite que QA/Architect revisem a completude da cobertura
    sem ler código de teste.
"""


# ---------------------------------------------------------------------------
# DEC015-01 — Matriz de pins DEC-015 no manifesto (faixa de versão)
# ---------------------------------------------------------------------------


class TestDEC01PinsVersionMatrix(unittest.TestCase):
    """DEC015-01 — pins DEC-015 presentes + faixa de versão coerente."""

    def test_all_dec015_packages_present_in_pyproject(self) -> None:
        deps = read_pyproject_dependencies()
        names = {dependency_name(d) for d in deps}
        missing = [p for p in DEC015_RUNTIME_PACKAGES if p not in names]
        self.assertEqual(missing, [], f"deps runtime ausentes: {missing}")
        missing_grammars = [g for g in DEC015_TREE_SITTER_GRAMMARS if g not in names]
        self.assertEqual(
            missing_grammars, [], f"grammars ausentes no pyproject: {missing_grammars}"
        )

    def test_all_dec015_packages_declare_a_version_range(self) -> None:
        deps = read_pyproject_dependencies()
        offenders: list[str] = []
        for package in (*DEC015_RUNTIME_PACKAGES, *DEC015_TREE_SITTER_GRAMMARS):
            spec = dependency_spec(package, deps)
            pattern = DEC015_VERSION_CONSTRAINTS.get(package)
            if pattern is None or not pattern.search(spec):
                offenders.append(f"{package} (spec={spec!r})")
        self.assertEqual(
            offenders,
            [],
            "DEC015-01: pacotes sem faixa de versão coerente com DEC-015 "
            f"(pin ausente/bare/major incompatível): {offenders}",
        )

    def test_bare_package_without_version_operator_fails_pattern(self) -> None:
        """Corner case: pin ``"mcp"`` sem operador não casa a regra de mcp."""
        pattern = DEC015_VERSION_CONSTRAINTS["mcp"]
        self.assertIsNone(pattern.search("mcp"))

    def test_incompatible_major_fails_pattern(self) -> None:
        """Corner case: ``apscheduler>=4`` (major incompatível) não casa a regra."""
        pattern = DEC015_VERSION_CONSTRAINTS["apscheduler"]
        self.assertIsNone(pattern.search("apscheduler>=4"))

    def test_wildcard_dependency_fails_generic_pattern(self) -> None:
        """Corner case: ``alembic*`` sem dígito não casa nem o fallback genérico."""
        pattern = DEC015_VERSION_CONSTRAINTS["alembic"]
        self.assertIsNone(pattern.search("alembic"))
        self.assertIsNone(pattern.search("alembic*"))


# ---------------------------------------------------------------------------
# DEC015-02 — GitHub API via PyGithub
# ---------------------------------------------------------------------------


class TestDEC02GitHubPyGithubBinding(unittest.TestCase):
    """DEC015-02 — GitHub via PyGithub, sem cliente HTTP caseiro."""

    def test_client_and_snapshot_modules_conform(self) -> None:
        rules = _rules_matching("GitHub API via PyGithub")
        self.assertEqual(len(rules), 2)
        for rule in rules:
            with self.subTest(clause=rule.clause):
                assert_source_conforms(rule)

    def test_public_port_has_no_manual_pagination_params(self) -> None:
        from github_rag.sources.github.client import GitHubApiClient

        for name in ("iter_org_repos", "list_org_repos"):
            method = getattr(GitHubApiClient, name)
            params = set(inspect.signature(method).parameters)
            self.assertNotIn("page", params, msg=name)
            self.assertNotIn("per_page", params, msg=name)


# ---------------------------------------------------------------------------
# DEC015-03/04/06 — referências não-duplicantes
# ---------------------------------------------------------------------------


class TestDEC03GitPythonReference(unittest.TestCase):
    """DEC015-03 — Git local via GitPython / DT-001 (referência)."""

    def test_local_discovery_git_sdk_suite_is_importable(self) -> None:
        assert_module_importable(
            "tests.bdd.test_local_discovery_git_sdk",
            clause="Git local via GitPython / DT-001 (DEC015-03)",
        )


class TestDEC04PathspecReference(unittest.TestCase):
    """DEC015-04 — ``.gitignore`` via pathspec (referência)."""

    def test_file_eligibility_suite_is_importable(self) -> None:
        assert_module_importable(
            "tests.bdd.test_file_eligibility",
            clause=".gitignore via pathspec (DEC015-04)",
        )


class TestDEC06QdrantOpenAiReference(unittest.TestCase):
    """DEC015-06 — Qdrant + embeddings OpenAI-compatible (referência)."""

    def test_qdrant_vector_store_suite_is_importable(self) -> None:
        assert_module_importable(
            "tests.bdd.test_qdrant_vector_store",
            clause="Qdrant + embeddings OpenAI-compatible (DEC015-06)",
        )


# ---------------------------------------------------------------------------
# DEC015-05 — Tree-sitter oficial (referência + grammar↔registry)
# ---------------------------------------------------------------------------


class TestDEC05TreeSitterGrammarWiring(unittest.TestCase):
    """DEC015-05 — Tree-sitter oficial: referência + nenhum pin órfão."""

    def test_treesitter_chunker_suite_is_importable(self) -> None:
        assert_module_importable(
            "tests.bdd.test_treesitter_chunker",
            clause="Tree-sitter oficial + OfficialGrammarRegistry (DEC015-05)",
        )

    def test_all_pinned_grammars_resolve_via_registry(self) -> None:
        from github_rag.index.chunk.grammar_registry import OfficialGrammarRegistry
        from github_rag.index.chunk.types import SourceLanguage

        grammar_to_language: dict[str, tuple[SourceLanguage, str]] = {
            "tree-sitter-python": (SourceLanguage.PYTHON, ".py"),
            "tree-sitter-java": (SourceLanguage.JAVA, ".java"),
            "tree-sitter-javascript": (SourceLanguage.JAVASCRIPT, ".js"),
            "tree-sitter-typescript": (SourceLanguage.TYPESCRIPT, ".ts"),
            "tree-sitter-markdown": (SourceLanguage.MARKDOWN, ".md"),
            "tree-sitter-yaml": (SourceLanguage.YAML, ".yaml"),
            "tree-sitter-json": (SourceLanguage.JSON, ".json"),
            "tree-sitter-xml": (SourceLanguage.XML, ".xml"),
            "tree-sitter-toml": (SourceLanguage.TOML, ".toml"),
        }
        registry = OfficialGrammarRegistry()
        orphans: list[str] = []
        for grammar in DEC015_TREE_SITTER_GRAMMARS:
            mapping = grammar_to_language.get(grammar)
            if mapping is None:
                orphans.append(f"{grammar} (sem SourceLanguage/extensão mapeada)")
                continue
            language, extension = mapping
            try:
                resolved = registry.resolve(language, path_extension=extension)
            except Exception as exc:  # noqa: BLE001
                orphans.append(f"{grammar} ({type(exc).__name__})")
                continue
            if resolved is None:
                orphans.append(f"{grammar} (resolve() retornou None)")
        self.assertEqual(
            orphans, [], f"grammars pinadas sem wiring no registry: {orphans}"
        )


# ---------------------------------------------------------------------------
# DEC015-07 — Cron via APScheduler
# ---------------------------------------------------------------------------


class TestDEC07ApSchedulerBinding(unittest.TestCase):
    """DEC015-07 — cron via APScheduler, sem parser manual."""

    def test_scheduler_and_cron_expr_conform(self) -> None:
        rules = _rules_matching("DEC015-07")
        self.assertEqual(len(rules), 2)
        for rule in rules:
            with self.subTest(clause=rule.clause):
                assert_source_conforms(rule)


# ---------------------------------------------------------------------------
# DEC015-08 — MCP via SDK oficial `mcp`
# ---------------------------------------------------------------------------


class TestDEC08McpSdkBinding(unittest.TestCase):
    """DEC015-08 — servidor MCP via SDK oficial ``mcp``."""

    def test_mcp_package_imports_official_sdk_only(self) -> None:
        from tests.unit.mcp.helpers import FORBIDDEN_IMPORTS, MCP_PKG, collect_imports

        imports = collect_imports(MCP_PKG)
        self.assertIn("mcp", imports)
        banned = imports & FORBIDDEN_IMPORTS
        self.assertEqual(banned, set(), f"imports banidos no pacote mcp: {banned}")

    def test_server_uses_fastmcp_binding(self) -> None:
        from github_rag.mcp import server

        source = inspect.getsource(server)
        self.assertRegex(
            source, r"from\s+mcp\.server\.fastmcp\s+import\s+FastMCP"
        )

    def test_pyproject_pins_mcp_sdk_range(self) -> None:
        deps = read_pyproject_dependencies()
        spec = dependency_spec("mcp", deps)
        self.assertRegex(spec, DEC015_VERSION_CONSTRAINTS["mcp"])


# ---------------------------------------------------------------------------
# DEC015-09 — API HTTP da UI via FastAPI
# ---------------------------------------------------------------------------


class TestDEC09FastApiBinding(unittest.TestCase):
    """DEC015-09 — API HTTP da UI via FastAPI."""

    def test_domain_modules_do_not_import_fastapi(self) -> None:
        from tests.unit.ui.helpers import (
            DOMAIN_MODULES,
            FORBIDDEN_IN_DOMAIN,
            UI_PKG,
            imports_of_file,
        )

        for name in DOMAIN_MODULES:
            found = imports_of_file(UI_PKG / name) & FORBIDDEN_IN_DOMAIN
            self.assertFalse(found, msg=f"{name}: {found}")

    def test_transport_modules_import_fastapi(self) -> None:
        from tests.unit.ui.helpers import FASTAPI_MODULES, UI_PKG, imports_of_file

        for name in FASTAPI_MODULES:
            self.assertIn("fastapi", imports_of_file(UI_PKG / name), msg=name)

    def test_ui_package_has_no_homemade_http_client(self) -> None:
        from tests.unit.ui.helpers import FORBIDDEN_HOMEMADE, UI_PKG, imports_of_file

        for path in UI_PKG.glob("*.py"):
            found = imports_of_file(path) & FORBIDDEN_HOMEMADE
            self.assertFalse(found, msg=f"{path.name}: {found}")


# ---------------------------------------------------------------------------
# DEC015-10 — PostgreSQL via SQLAlchemy 2.x + Alembic + psycopg3 (BR-024)
# ---------------------------------------------------------------------------

_MODELS_PATH = SRC / "catalog" / "postgres" / "models.py"
_FACTORY_PATH = SRC / "catalog" / "postgres" / "factory.py"
_SCHEDULE_PG_PATH = SRC / "schedule" / "postgres.py"
_WIRING_PATH = SRC / "delivery" / "wiring.py"
_TEST_WIRING_PATH = REPO_ROOT / "tests" / "unit" / "delivery" / "test_wiring.py"
_TEST_PG_REPO_PATH = (
    REPO_ROOT / "tests" / "integration" / "test_postgres_catalog_repository.py"
)


class TestDEC10Br024Postgres(unittest.TestCase):
    """DEC015-10 / BR-024 — PostgreSQL via SQLAlchemy 2.x + Alembic + psycopg3."""

    def test_models_use_sqlalchemy_2x_declarative_api(self) -> None:
        source = _MODELS_PATH.read_text(encoding="utf-8")
        self.assertRegex(source, r"DeclarativeBase")
        self.assertRegex(source, r"\bMapped\[")
        self.assertRegex(source, r"mapped_column")
        self.assertNotRegex(source, r"declarative_base\s*\(")

    def test_run_alembic_upgrade_delegates_to_alembic_command(self) -> None:
        source = _WIRING_PATH.read_text(encoding="utf-8")
        self.assertRegex(source, r"from\s+alembic\s+import\s+command")
        self.assertRegex(source, r"command\.upgrade\(")
        self.assertNotRegex(source, r"CREATE\s+TABLE|ALTER\s+TABLE")

    def test_factory_and_schedule_postgres_use_sqlalchemy_not_psycopg2(self) -> None:
        for path in (_FACTORY_PATH, _SCHEDULE_PG_PATH):
            source = path.read_text(encoding="utf-8")
            self.assertRegex(source, r"from\s+sqlalchemy", msg=str(path))
            self.assertNotRegex(source, r"psycopg2", msg=str(path))

    def test_production_fixtures_use_psycopg3_driver_never_psycopg2(self) -> None:
        # test_wiring.py: fixtures escritas à mão — driver deve ser psycopg3
        # direto, sem `+psycopg2://` em nenhuma forma.
        wiring_source = (
            _TEST_WIRING_PATH.read_text(encoding="utf-8")
            if _TEST_WIRING_PATH.is_file()
            else ""
        )
        self.assertNotIn("+psycopg2://", wiring_source, msg=str(_TEST_WIRING_PATH))
        self.assertIn(
            "postgresql+psycopg://", wiring_source, msg=str(_TEST_WIRING_PATH)
        )

        # test_postgres_catalog_repository.py: testcontainers devolve a URL
        # com `+psycopg2://` por padrão — o fixture deve normalizar
        # explicitamente para psycopg3 antes de repassar ao adaptador; não
        # pode repassar a URL bruta com driver psycopg2 ao repositório.
        if _TEST_PG_REPO_PATH.is_file():
            integration_source = _TEST_PG_REPO_PATH.read_text(encoding="utf-8")
            self.assertRegex(
                integration_source,
                r"\.replace\(\s*[\"']postgresql\+psycopg2://[\"']\s*,\s*"
                r"[\"']postgresql\+psycopg://[\"']\s*\)",
                msg=str(_TEST_PG_REPO_PATH),
            )

    def test_pyproject_pins_sqlalchemy2_and_psycopg(self) -> None:
        deps = read_pyproject_dependencies()
        names = {dependency_name(d) for d in deps}
        self.assertIn("sqlalchemy", names)
        self.assertIn("psycopg", names)
        sqlalchemy_spec = dependency_spec("sqlalchemy", deps)
        self.assertRegex(sqlalchemy_spec, DEC015_VERSION_CONSTRAINTS["sqlalchemy"])


# ---------------------------------------------------------------------------
# DEC015-11 — Zoekt: adaptador fino real (DEC-016)
# ---------------------------------------------------------------------------


class TestDEC11Dec016ZoektRealAdapter(unittest.TestCase):
    """DEC015-11 — Zoekt via CLI/HTTP oficiais no adaptador real (não só Fake)."""

    def test_http_cli_and_index_modules_conform(self) -> None:
        rules = _rules_matching("DEC015-11")
        self.assertEqual(len(rules), 3)
        for rule in rules:
            with self.subTest(clause=rule.clause):
                assert_source_conforms(rule)

    def test_fake_protocol_reference_still_importable(self) -> None:
        assert_module_importable(
            "tests.bdd.test_zoekt_adapter",
            clause="Zoekt via adaptador fino — Fake/Protocol complementar (DEC015-11)",
        )


# ---------------------------------------------------------------------------
# DEC015-12 — DT-001: eliminação do parsing ad-hoc de `.git`
# ---------------------------------------------------------------------------

_GIT_FS_RULE = next(rule for rule in DEC015_INTEGRATION_RULES if "DEC015-12" in rule.clause)


class TestDEC12Dt001Elimination(unittest.TestCase):
    """DEC015-12 — ``git_fs.py`` via GitPython, sem parsing ad-hoc (DT-001)."""

    def test_git_fs_conforms(self) -> None:
        assert_source_conforms(_GIT_FS_RULE)

    def test_behavioral_reference_still_importable(self) -> None:
        assert_module_importable(
            "tests.bdd.test_local_discovery_git_sdk",
            clause="DT-001 eliminado — regressão comportamental T20 (DEC015-12)",
        )


# ---------------------------------------------------------------------------
# DEC015-13 — Cobertura de texto integral de BDD-024 (agregador)
# ---------------------------------------------------------------------------


class TestBDD024FullTextCoverage(unittest.TestCase):
    """Agregador de rastreabilidade — DEC015-13.

    Responsabilidade
        Garantir que todo módulo citado em ``BDD024_CLAUSE_MODULE_MAP``
        continua importável; falhar nomeando cláusula + módulo se não.

    Motivo da separação
        É a única classe que conhece o mapa completo; as demais classes
        (DEC015-01..12) não precisam saber da existência umas das outras.
    """

    def test_every_clause_has_importable_evidence(self) -> None:
        for clause, modules in BDD024_CLAUSE_MODULE_MAP.items():
            for dotted in modules:
                assert_module_importable(dotted, clause=clause)

    def test_map_covers_all_bdd024_clauses(self) -> None:
        expected_clauses = {
            "sdk_oficial_por_integracao",
            "br024_sqlalchemy_alembic_psycopg3",
            "dec016_zoekt_adaptador_fino",
            "sem_reinvencao_cliente_cli_protocolo",
            "dt001_eliminado",
        }
        self.assertEqual(set(BDD024_CLAUSE_MODULE_MAP.keys()), expected_clauses)

    def test_unknown_module_in_map_fails_named(self) -> None:
        """Corner case: módulo removido/renomeado falha nomeando a cláusula."""
        with self.assertRaises(AssertionError) as ctx:
            assert_module_importable(
                "tests.bdd.test_modulo_removido_por_engano",
                clause="dt001_eliminado",
            )
        self.assertIn("dt001_eliminado", str(ctx.exception))


# ---------------------------------------------------------------------------
# Contrato dos helpers internos (unit-test-plan §5 — UT-DEC-H01..H08)
# ---------------------------------------------------------------------------


class TestSourceConformityRuleHelperContract(unittest.TestCase):
    """UT-DEC-H01..H05 — contrato de ``assert_source_conforms``."""

    def test_passes_when_required_present_and_forbidden_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mod.py"
            path.write_text("from git import Repo\n", encoding="utf-8")
            rule = SourceConformityRule(
                clause="fixture happy path",
                module_path=path,
                required_patterns=(re.compile(r"from\s+git\s+import\s+Repo"),),
            )
            source = assert_source_conforms(rule)
            self.assertIn("Repo", source)

    def test_missing_required_pattern_raises_named_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mod.py"
            path.write_text("x = 1\n", encoding="utf-8")
            rule = SourceConformityRule(
                clause="fixture missing required",
                module_path=path,
                required_patterns=(re.compile(r"from\s+git\s+import\s+Repo"),),
            )
            with self.assertRaises(AssertionError) as ctx:
                assert_source_conforms(rule)
            self.assertIn("fixture missing required", str(ctx.exception))

    def test_forbidden_pattern_present_raises_named_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mod.py"
            path.write_text("packed-refs\n", encoding="utf-8")
            rule = SourceConformityRule(
                clause="fixture forbidden hit",
                module_path=path,
                required_patterns=(),
                forbidden_patterns=(re.compile(r"packed-refs"),),
            )
            with self.assertRaises(AssertionError) as ctx:
                assert_source_conforms(rule)
            self.assertIn("fixture forbidden hit", str(ctx.exception))

    def test_missing_module_path_raises(self) -> None:
        rule = SourceConformityRule(
            clause="fixture missing file",
            module_path=Path("/no/such/module-t27-fixture.py"),
            required_patterns=(),
        )
        with self.assertRaises(AssertionError):
            assert_source_conforms(rule)

    def test_forbidden_defaults_to_empty_tuple(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mod.py"
            path.write_text("anything goes here\n", encoding="utf-8")
            rule = SourceConformityRule(
                clause="fixture default forbidden",
                module_path=path,
                required_patterns=(),
            )
            assert_source_conforms(rule)  # não levanta


class TestAssertModuleImportableContract(unittest.TestCase):
    """UT-DEC-H06..H08 — contrato de ``assert_module_importable``."""

    def test_valid_dotted_path_returns_module(self) -> None:
        module = assert_module_importable("json", clause="fixture stdlib")
        self.assertTrue(hasattr(module, "loads"))

    def test_blank_dotted_path_raises_named_error(self) -> None:
        with self.assertRaises(AssertionError) as ctx:
            assert_module_importable("   ", clause="fixture blank")
        self.assertIn("fixture blank", str(ctx.exception))

    def test_missing_module_raises_named_error_chained(self) -> None:
        with self.assertRaises(AssertionError) as ctx:
            assert_module_importable(
                "tests.bdd.test_dec015_conformity_does_not_exist",
                clause="fixture missing module",
            )
        self.assertIn("fixture missing module", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, ImportError)


if __name__ == "__main__":
    unittest.main()
