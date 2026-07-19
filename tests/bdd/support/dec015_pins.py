"""Pins DEC-015 no manifesto — dado compartilhado de teste (T27 / I-T27-001).

Responsabilidade deste módulo
    Único ponto público de leitura/parse de ``[project].dependencies`` do
    ``pyproject.toml`` e da lista canônica de pacotes/grammars exigidos pela
    tabela DEC-015 (``requirements.md`` §DEC-015).

Motivo da separação
    Antes duplicado implicitamente como ``_pyproject_deps``/``_dep_name``
    privados em ``tests/bdd/test_container_delivery.py``. Extrair para um
    módulo público evita duas fontes de verdade quando
    ``tests/bdd/test_dec015_conformity.py`` precisa do mesmo conjunto de
    dados (nome do pacote + faixa de versão), sem reimplementar o parser TOML.
    Não é API de produção — vive em ``tests/`` por convenção do repositório
    (``tests/unit/<pacote>/helpers.py``).
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[3]
"""Raiz do repositório, resolvida a partir deste arquivo.

Responsabilidade
    Âncora única de path para localizar ``pyproject.toml`` sem repetir
    ``Path(__file__).resolve().parents[N]`` em cada teste que precisa dos
    pins.

Motivo da separação
    Antes duplicado (implicitamente) em ``test_container_delivery.py``; um
    único ponto evita drift se a árvore de testes for reorganizada.
"""

PYPROJECT_PATH: Path = REPO_ROOT / "pyproject.toml"
"""``REPO_ROOT / "pyproject.toml"``."""

DEC015_RUNTIME_PACKAGES: tuple[str, ...] = (
    "sqlalchemy",
    "alembic",
    "psycopg",
    "apscheduler",
    "PyGithub",
    "GitPython",
    "pathspec",
    "tree-sitter",
    "qdrant-client",
    "openai",
    "mcp",
    "fastapi",
    "uvicorn",
)
"""Nomes de pacote (sem versão) exigidos por DEC-015 em ``[project].dependencies``.

Responsabilidade
    Lista única/canônica dos pacotes runtime da tabela DEC-015.

Motivo da separação
    Migrada de ``tests/bdd/test_container_delivery.py`` (I-T27-001): evita
    duas fontes de verdade da mesma tabela quando
    ``test_dec015_conformity.py`` precisa do mesmo conjunto.
"""

DEC015_TREE_SITTER_GRAMMARS: tuple[str, ...] = (
    "tree-sitter-python",
    "tree-sitter-java",
    "tree-sitter-javascript",
    "tree-sitter-typescript",
    "tree-sitter-markdown",
    "tree-sitter-yaml",
    "tree-sitter-json",
    "tree-sitter-xml",
    "tree-sitter-toml",
)
"""Nomes das 9 grammars Tree-sitter pinadas (mesmo racional acima)."""

_GENERIC_MIN_VERSION_RE = re.compile(r"[<>=~!]=?\s*\d")
_GRAMMAR_EXACT_PIN_RE = re.compile(r"==\s*\d+(?:\.\d+)*")

DEC015_VERSION_CONSTRAINTS: dict[str, re.Pattern[str]] = {
    "sqlalchemy": re.compile(r">=\s*2\b"),
    "alembic": _GENERIC_MIN_VERSION_RE,
    "psycopg": _GENERIC_MIN_VERSION_RE,
    "apscheduler": re.compile(r">=\s*3\.10.*<\s*4"),
    "PyGithub": re.compile(r">=\s*2\b"),
    "GitPython": re.compile(r">=\s*3\.1\b"),
    "pathspec": re.compile(r">=\s*0\.12\b"),
    "tree-sitter": _GRAMMAR_EXACT_PIN_RE,
    "qdrant-client": re.compile(r">=\s*1\.12\b"),
    "openai": re.compile(r">=\s*1\.40\b"),
    "mcp": re.compile(r">=\s*1\.27.*<\s*2"),
    "fastapi": re.compile(r">=\s*0\.115.*<\s*1"),
    "uvicorn": re.compile(r">=\s*0\.32\b"),
    **{grammar: _GRAMMAR_EXACT_PIN_RE for grammar in DEC015_TREE_SITTER_GRAMMARS},
}
"""Pacote → regex da faixa de versão mínima esperada pela tabela DEC-015.

Responsabilidade
    Formalizar, por pacote, o que conta como "faixa de versão coerente com o
    default DEC-015" (ex.: ``sqlalchemy`` → ``r">=\\s*2"``; ``mcp`` →
    ``r">=\\s*1\\.27.*<\\s*2"``; ``apscheduler`` → ``r">=\\s*3\\.10.*<\\s*4"``).
    Não valida SemVer completo — só que a linha declara *alguma* faixa
    mínima plausível, suficiente para pegar regressões grosseiras (pin
    removido, ``*``, ou major incompatível). Pacotes sem faixa semântica
    específica na tabela (``alembic``, ``psycopg``) usam
    ``_GENERIC_MIN_VERSION_RE`` — qualquer operador de versão presente
    satisfaz; ausência total de operador (pin bare) falha.

Motivo da separação
    Cenário novo (DEC015-01 na versão desta task); nasce aqui porque é dado,
    não comportamento — Developer/QA podem revisar/estender sem tocar em
    lógica de teste.
"""


def read_pyproject_dependencies(path: Path = PYPROJECT_PATH) -> list[str]:
    """Lê ``[project].dependencies`` de ``pyproject.toml``; levanta se ausente/vazio.

    Responsabilidade
        Único parser TOML dos testes de conformidade de manifesto.

    Motivo da separação
        Substitui ``_pyproject_deps`` privado de ``test_container_delivery.py``
        (I-T27-001) — mesma assinatura semântica, nome público.
    """
    if not path.is_file():
        raise AssertionError(f"artefato de manifesto ausente: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deps = data.get("project", {}).get("dependencies", [])
    if not isinstance(deps, list) or not deps:
        raise AssertionError("[project].dependencies ausente ou vazio")
    return [str(d) for d in deps]


def dependency_name(spec: str) -> str:
    """Extrai o nome do pacote de uma linha de dependência.

    Ex.: ``"mcp>=1.27,<2"`` → ``"mcp"``; ``"psycopg[binary]"`` → ``"psycopg"``.

    Motivo da separação
        Substitui ``_dep_name`` privado (I-T27-001); usado tanto pelo assert
        de presença (CD-05) quanto pelo assert de faixa de versão
        (DEC015-01).
    """
    return re.split(r"[<>=!~;\[]", spec, maxsplit=1)[0].strip()


def dependency_spec(name: str, deps: list[str]) -> str:
    """Retorna a linha de dependência completa para ``name``; levanta se ausente.

    Responsabilidade
        Dar à DEC015-01 acesso à *string* completa (com faixa de versão), não
        só ao nome — o que ``dependency_name``/o assert de presença de CD-05
        não precisavam expor antes.

    Motivo da separação
        Nova necessidade (checar faixa de versão) não existia em T19;
        adicionar aqui em vez de em ``test_container_delivery.py`` mantém
        CD-05 sem conhecer o conceito de "faixa de versão exigida" —
        responsabilidade de T27, não de T19.
    """
    for spec in deps:
        if dependency_name(spec) == name:
            return spec
    raise AssertionError(f"dependência {name!r} ausente em [project].dependencies")
