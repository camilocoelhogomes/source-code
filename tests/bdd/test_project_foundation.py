"""
BDD executável — T01-project-foundation.

Valida critérios de aceite da fundação (design 0.2.0) via comportamento
observável em artefatos e bootstrap. Sem implementação de produção nesta etapa:
os cenários devem falhar enquanto a fundação estiver ausente.

Não antecipa contratos de API de settings (gate interfaces / D-T01-008).

Execução (stdlib, sem depender de pyproject ainda):
    python3 -m unittest discover -s tests/bdd -p "test_*.py" -v

Após fundação com pytest:
    python -m pytest tests/bdd -q
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_PLACEHOLDERS = (
    "config",
    "sources/github",
    "sources/local",
    "catalog",
    "snapshot",
    "eligibility",
    "index/zoekt",
    "index/chunk",
    "index/metadata",
    "index/vector",
    "indexing",
    "schedule",
    "query",
    "mcp",
    "ui",
    "delivery",
)

DOMAIN_FORBIDDEN_PATTERNS = (
    re.compile(r"json\.loads", re.I),
    re.compile(r"sourcebot", re.I),
    re.compile(r"psycopg|sqlalchemy|asyncpg|create_engine", re.I),
    re.compile(r"SecretResolver|GITHUB_TOKEN|resolve_secret", re.I),
    re.compile(r"connect\s*\(", re.I),
)

BOOTSTRAP_ENV_NAMES = ("INDEX_WORKERS", "QUERY_WORKERS", "CONFIG_PATH")


def _readme() -> Path:
    return REPO_ROOT / "README.md"


def _read_readme() -> str:
    path = _readme()
    if not path.is_file():
        raise AssertionError(
            "README.md ausente — fundação de documentação não criada (FND-01..04, FND-10)"
        )
    return path.read_text(encoding="utf-8")


def _pyproject() -> Path:
    return REPO_ROOT / "pyproject.toml"


def _read_pyproject() -> str:
    path = _pyproject()
    if not path.is_file():
        raise AssertionError(
            "pyproject.toml ausente — manifesto da fundação não criado (FND-05, FND-07)"
        )
    return path.read_text(encoding="utf-8")


def _settings_path() -> Path:
    return REPO_ROOT / "src" / "github_rag" / "settings.py"


class TestFND01VenvWindowsPowerShell(unittest.TestCase):
    """FND-01 — README documenta fluxo completo de venv no Windows PowerShell."""

    def test_readme_documents_powershell_venv_flow(self) -> None:
        text = _read_readme()
        self.assertIn("py -3.12 -m venv .venv", text)
        self.assertIn(r".venv\Scripts\Activate.ps1", text)
        self.assertIn('python -m pip install -e ".[dev]"', text)
        self.assertIn("python -m pytest", text)
        self.assertRegex(
            text,
            re.compile(r"powershell|PowerShell", re.I),
            "README deve nomear PowerShell como shell Windows de primeira classe",
        )
        # S-02 (leve): mitigações Windows first-class do design §2.3 / §2.10
        self.assertRegex(
            text,
            re.compile(r"ExecutionPolicy|RemoteSigned", re.I),
            "README deve documentar ExecutionPolicy / RemoteSigned para Activate.ps1",
        )
        self.assertIn(r".venv\Scripts\python.exe", text)


class TestFND02VenvWindowsCmd(unittest.TestCase):
    """FND-02 — README documenta fluxo completo de venv no Windows cmd."""

    def test_readme_documents_cmd_venv_flow(self) -> None:
        text = _read_readme()
        self.assertIn("py -3.12 -m venv .venv", text)
        self.assertIn(r".venv\Scripts\activate.bat", text)
        self.assertIn('python -m pip install -e ".[dev]"', text)
        self.assertIn("python -m pytest", text)
        self.assertRegex(
            text,
            re.compile(r"\bcmd\b", re.I),
            "README deve nomear cmd como shell Windows de primeira classe",
        )


class TestFND03VenvUnix(unittest.TestCase):
    """FND-03 — README documenta fluxo completo de venv no macOS/Linux."""

    def test_readme_documents_unix_venv_flow(self) -> None:
        text = _read_readme()
        self.assertIn("python3.12 -m venv .venv", text)
        self.assertIn("source .venv/bin/activate", text)
        self.assertIn('python -m pip install -e ".[dev]"', text)
        self.assertIn("python -m pytest", text)
        # S-02 (leve): invoke sem activate no Unix
        self.assertIn(".venv/bin/python", text)


class TestFND04DockerT19NoHostVenv(unittest.TestCase):
    """FND-04 — Docker/T19 entrega padronizada; não usa/monta .venv do host."""

    def test_readme_distinguishes_local_venv_from_docker_delivery(self) -> None:
        text = _read_readme()

        self.assertRegex(
            text,
            re.compile(
                r"(não|nao).{0,120}(monta|usa).{0,80}(\.venv|venv).{0,80}(host|hospedeiro)"
                r"|(não|nao).{0,80}(\.venv|venv).{0,80}(host|hospedeiro)"
                r"|does not (use|mount).{0,60}(\.venv|venv).{0,40}host",
                re.I | re.S,
            ),
            "README deve declarar que a imagem/container não monta nem usa .venv do host",
        )
        self.assertRegex(
            text,
            re.compile(
                r"(venv|\.venv).{0,100}(desenvolvimento local|dev local)"
                r"|(desenvolvimento local|dev local).{0,100}(venv|\.venv)",
                re.I | re.S,
            ),
            "README deve associar venv a desenvolvimento local",
        )
        self.assertRegex(
            text,
            re.compile(
                r"(docker|t19|container).{0,120}(entrega padronizada|entrega)"
                r"|(entrega padronizada|entrega).{0,120}(docker|t19|container)",
                re.I | re.S,
            ),
            "README deve associar Docker/T19 a entrega (padronizada)",
        )


class TestFND05Python312(unittest.TestCase):
    """FND-05 — Projeto declara runtime Python 3.12+."""

    def test_requires_python_at_least_3_12(self) -> None:
        text = _read_pyproject()
        match = re.search(
            r"requires-python\s*=\s*[\"']([^\"']+)[\"']",
            text,
            re.I,
        )
        self.assertIsNotNone(match, "requires-python ausente em pyproject.toml")
        constraint = match.group(1)
        self.assertRegex(
            constraint,
            re.compile(r">=\s*3\.12"),
            f"requires-python deve exigir >=3.12; obtido: {constraint!r}",
        )


class TestFND06ModuleLayout(unittest.TestCase):
    """FND-06 — Layout src espelha fronteiras do plano §1.3."""

    def test_package_placeholders_and_settings_exist(self) -> None:
        root = REPO_ROOT / "src" / "github_rag"
        self.assertTrue(
            root.is_dir(),
            "src/github_rag ausente — layout da fundação não criado",
        )
        missing_dirs = [
            rel for rel in PACKAGE_PLACEHOLDERS if not (root / rel).is_dir()
        ]
        self.assertEqual(
            missing_dirs,
            [],
            f"Pacotes placeholder ausentes: {missing_dirs}",
        )
        self.assertTrue(
            _settings_path().is_file(),
            "src/github_rag/settings.py ausente",
        )
        # S-01: cada fronteira (e a raiz) deve ser pacote importável
        missing_inits = []
        if not (root / "__init__.py").is_file():
            missing_inits.append("github_rag/__init__.py")
        for rel in PACKAGE_PLACEHOLDERS:
            if not (root / rel / "__init__.py").is_file():
                missing_inits.append(f"github_rag/{rel}/__init__.py")
        self.assertEqual(
            missing_inits,
            [],
            f"__init__.py ausentes nos placeholders: {missing_inits}",
        )


class TestFND07PytestCoverageFailUnder(unittest.TestCase):
    """FND-07 — pytest + coverage com fail_under 95%."""

    def test_pytest_and_coverage_fail_under_95_configured(self) -> None:
        text = _read_pyproject()
        lowered = text.lower()
        self.assertTrue(
            "pytest" in lowered,
            "pytest deve estar declarado na configuração do projeto",
        )
        self.assertTrue(
            "cov" in lowered or "coverage" in lowered,
            "coverage/pytest-cov deve estar configurado",
        )
        self.assertRegex(
            text,
            re.compile(
                r"fail[_-]under\s*=\s*95|--cov-fail-under\s*=\s*95",
                re.I,
            ),
            "fail_under/cov-fail-under deve ser 95",
        )


class TestFND08SettingsBootstrapOnly(unittest.TestCase):
    """FND-08 — Settings skeleton bootstrap; sem domínio; sem API prescrita."""

    def test_settings_skeleton_has_no_domain_logic(self) -> None:
        settings_file = _settings_path()
        self.assertTrue(
            settings_file.is_file(),
            "settings.py ausente — skeleton bootstrap não criado",
        )
        source = settings_file.read_text(encoding="utf-8")
        for pattern in DOMAIN_FORBIDDEN_PATTERNS:
            self.assertIsNone(
                pattern.search(source),
                f"settings.py contém lógica de domínio proibida: {pattern.pattern}",
            )
        for env_name in BOOTSTRAP_ENV_NAMES:
            self.assertIn(
                env_name,
                source,
                f"settings.py deve declarar/documentar o nome de env bootstrap {env_name}",
            )
        # Defaults conceituais do design (§2.5) como literais no módulo —
        # sem exigir load_settings/Settings/AppSettings (gate interfaces).
        self.assertRegex(
            source,
            re.compile(r"\b2\b"),
            "settings.py deve refletir default conceitual INDEX_WORKERS=2 (literal no módulo)",
        )
        self.assertRegex(
            source,
            re.compile(r"\b4\b"),
            "settings.py deve refletir default conceitual QUERY_WORKERS=4 (literal no módulo)",
        )
        self.assertRegex(
            source,
            re.compile(r"None|null|ausente|unset", re.I),
            "settings.py deve indicar CONFIG_PATH ausente/nulo no bootstrap (sem API prescrita)",
        )


class TestFND09CrossPlatformPathsAndEol(unittest.TestCase):
    """FND-09 — pathlib no settings e .gitattributes para EOL."""

    def test_gitattributes_and_pathlib_in_settings(self) -> None:
        gitattributes = REPO_ROOT / ".gitattributes"
        self.assertTrue(
            gitattributes.is_file(),
            ".gitattributes ausente — normalização EOL não configurada",
        )
        ga_text = gitattributes.read_text(encoding="utf-8")
        self.assertRegex(
            ga_text,
            re.compile(r"text\s*=\s*auto|eol\s*=\s*lf", re.I),
            ".gitattributes deve normalizar EOL (text=auto e/ou eol=lf)",
        )

        settings_file = _settings_path()
        self.assertTrue(settings_file.is_file(), "settings.py ausente")
        source = settings_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        uses_pathlib = "pathlib" in source or any(
            isinstance(node, ast.ImportFrom) and node.module == "pathlib"
            for node in ast.walk(tree)
        ) or any(
            isinstance(node, ast.Import)
            and any(alias.name == "pathlib" for alias in node.names)
            for node in ast.walk(tree)
        )
        self.assertTrue(
            uses_pathlib,
            "settings.py deve tratar paths via pathlib",
        )
        self.assertNotRegex(
            source,
            re.compile(r"[\"'][^\"']*\\\\[^\"']*[\"']"),
            "settings.py não deve hardcodar separadores Windows em literais de path",
        )


class TestFND10VenvGitignoreAndInstallDocs(unittest.TestCase):
    """FND-10 — .venv gitignored; install no venv, não no Python do sistema."""

    def test_venv_gitignored_and_install_inside_venv_not_system(self) -> None:
        gitignore = REPO_ROOT / ".gitignore"
        self.assertTrue(gitignore.is_file(), ".gitignore ausente")
        gi_text = gitignore.read_text(encoding="utf-8")
        self.assertRegex(
            gi_text,
            re.compile(r"^\s*\.venv/?\s*$", re.M),
            ".venv/ deve estar em .gitignore",
        )

        readme = _read_readme()
        self.assertIn(".venv", readme)
        self.assertIn('python -m pip install -e ".[dev]"', readme)
        # Fluxo no interpretador do venv: após activate e/ou caminho completo
        self.assertTrue(
            re.search(r"activate", readme, re.I)
            or r".venv\Scripts\python.exe" in readme
            or ".venv/bin/python" in readme,
            "README deve situar o install no venv (activate e/ou caminho completo do python do .venv)",
        )
        self.assertRegex(
            readme,
            re.compile(
                r"(não|nao).{0,80}(python do sistema|interpretador do sistema|sistema como fluxo)"
                r"|(não|nao).{0,40}instalar.{0,60}(sistema)"
                r"|not .{0,40}system python",
                re.I | re.S,
            ),
            "README deve deixar explícito que o fluxo padrão não é instalar no Python do sistema",
        )


if __name__ == "__main__":
    unittest.main()
