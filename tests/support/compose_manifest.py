"""Parse/assert de manifesto compose — só testes (I-T22-007).

Não é API de produção. Usado por unitários T22 (e opcionalmente BDD)
para extrair o bloco ``zoekt`` e validar M-T22-001 sem ``compose up``.
"""

from __future__ import annotations

import re
from typing import Sequence

# Argv mínimo do filho do tini (D-T22-001 / M-T22-001).
ZOEKT_COMMAND_TOKENS: tuple[str, ...] = (
    "zoekt-webserver",
    "-index",
    "/data/index",
    "-rpc",
)

_SERVICE_BLOCK_RE = re.compile(
    r"^  (?P<name>[A-Za-z0-9_-]+):\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:|\Z)",
    re.M | re.S,
)

_COMMAND_JSON_RE = re.compile(
    r"^\s*command\s*:\s*\[(?P<body>.*?)\]\s*$",
    re.M | re.S,
)

_COMMAND_MULTILINE_RE = re.compile(
    r"^\s*command\s*:\s*\n(?P<body>(?:^[ \t]+-[ \t]+.+\n?)+)",
    re.M,
)

_COMMAND_SCALAR_RE = re.compile(
    r"^\s*command\s*:\s*(?P<body>.+)$",
    re.M,
)


def service_block(compose_text: str, service: str) -> str:
    """Extrai o bloco YAML textual de um serviço sob ``services:``.

    Responsabilidade
        Isolar a fatia do manifesto correspondente a ``service`` para
        asserts de regressão sem subir stack e sem ``compose config``.

    Motivo da separação
        Parser de texto de teste ≠ launcher T21 ≠ domínio Zoekt (T10).
    """
    if not compose_text or not compose_text.strip():
        raise AssertionError("compose vazio: impossível extrair serviço")
    for match in _SERVICE_BLOCK_RE.finditer(compose_text):
        if match.group("name") == service:
            return match.group(0)
    raise AssertionError(f"serviço compose ausente: {service}")


def zoekt_command_blob(compose_text: str) -> str:
    """Retorna o texto do ``command`` do serviço ``zoekt``.

    Responsabilidade
        Localizar ``command`` (JSON inline preferido; multilinha YAML
        suportada) e expor o blob para checagem dos tokens M-T22-001.
        Ausência de ``command`` falha com mensagem acionável (F-T04-002).

    Motivo da separação
        Extração do argv ≠ asserção de paridade entre composes ≠ docs.
    """
    block = service_block(compose_text, "zoekt")
    list_match = _COMMAND_JSON_RE.search(block)
    if list_match is not None:
        return list_match.group(0)
    multi_match = _COMMAND_MULTILINE_RE.search(block)
    if multi_match is not None:
        return multi_match.group(0)
    scalar_match = _COMMAND_SCALAR_RE.search(block)
    if scalar_match is not None:
        return scalar_match.group(0)
    raise AssertionError(
        "serviço zoekt sem `command` — ENTRYPOINT tini sem filho "
        "(F-T04-002: tini help → exit 1)"
    )


def parse_command_argv(command_blob: str) -> list[str]:
    """Normaliza o blob ``command`` em lista de tokens argv.

    Responsabilidade
        Suportar forma JSON inline e lista YAML multilinha para asserts
        de ordem lógica (M-T22-001) e extremos (command só tini, etc.).

    Motivo da separação
        Parsing de argv ≠ validação de tokens canônicos.
    """
    json_match = _COMMAND_JSON_RE.search(command_blob)
    if json_match is not None:
        inner = json_match.group("body")
        parts = re.findall(r'"([^"]+)"|\'([^\']+)\'|([^,\s\[\]]+)', inner)
        tokens = [a or b or c for a, b, c in parts if (a or b or c)]
        if not tokens:
            raise AssertionError("command zoekt vazio (lista JSON sem tokens)")
        return tokens

    multi_match = _COMMAND_MULTILINE_RE.search(command_blob)
    if multi_match is not None:
        items = re.findall(r"^[ \t]+-[ \t]+(.+)$", multi_match.group("body"), re.M)
        tokens = [item.strip().strip("\"'") for item in items if item.strip()]
        if not tokens:
            raise AssertionError("command zoekt vazio (lista multilinha sem itens)")
        return tokens

    scalar_match = _COMMAND_SCALAR_RE.search(command_blob)
    if scalar_match is not None:
        body = scalar_match.group("body").strip()
        if not body or body in ("[]", "~", "null", '""', "''"):
            raise AssertionError("command zoekt vazio (scalar/lista vazia)")
        return body.split()

    raise AssertionError("não foi possível parsear command zoekt")


def assert_zoekt_webserver_command(
    compose_text: str,
    *,
    compose_name: str,
    require_logical_order: bool = True,
) -> str:
    """Valida M-T22-001/003 no texto de um compose.

    Responsabilidade
        Gate reutilizável: tokens do webserver + ``/data/index`` no bloco
        ``zoekt``; opcionalmente ordem lógica dos tokens.

    Motivo da separação
        EZ-02 (por arquivo) e EZ-03 (paridade) compartilham a mesma regra;
        unitários de extremo reusam o mesmo gate com YAML sintético.
    """
    command_blob = zoekt_command_blob(compose_text)
    argv = parse_command_argv(command_blob)
    for token in ZOEKT_COMMAND_TOKENS:
        if token not in argv:
            raise AssertionError(
                f"{compose_name}: command zoekt deve conter {token!r} "
                f"(argv={argv!r})"
            )
    if require_logical_order:
        positions = [argv.index(t) for t in ZOEKT_COMMAND_TOKENS]
        if positions != sorted(positions):
            raise AssertionError(
                f"{compose_name}: command zoekt fora da ordem lógica "
                f"{ZOEKT_COMMAND_TOKENS!r} (argv={argv!r})"
            )
    block = service_block(compose_text, "zoekt")
    if "/data/index" not in block:
        raise AssertionError(
            f"{compose_name}: serviço zoekt deve montar/usar /data/index"
        )
    return command_blob


def assert_compose_provider_prereq_docs(text: str, *, doc_name: str) -> None:
    """Pré-req F-T04-001 / M-T22-010..012: binário + PATH + instalação."""
    if not text or not text.strip():
        raise AssertionError(f"{doc_name}: documento vazio")
    if not re.search(r"\bpodman-compose\b", text, re.I):
        raise AssertionError(
            f"{doc_name}: deve citar o binário `podman-compose` como pré-req "
            "(não apenas `podman compose` / nome de arquivo compose)"
        )
    if not re.search(
        r"command\s+-v\s+podman-compose"
        r"|podman\s+compose\s+version"
        r"|provider.*\bPATH\b|\bPATH\b.*(?:compose|provider)",
        text,
        re.I,
    ):
        raise AssertionError(
            f"{doc_name}: deve documentar verificação do provider no PATH"
        )
    if not re.search(
        r"brew\s+install\s+podman-compose"
        r"|install(?:ar)?\s+podman-compose",
        text,
        re.I,
    ):
        raise AssertionError(
            f"{doc_name}: deve orientar instalação tipica do provider "
            "(ex.: brew install podman-compose)"
        )


def assert_no_embedded_secrets(text: str, *, artifact_name: str) -> None:
    """Negativos M-T22-006/014 — sem PAT real / assignment de token."""
    if re.search(r"ghp_[A-Za-z0-9_]{20,}", text):
        raise AssertionError(f"{artifact_name}: não deve embutir PAT real")
    if re.search(
        r"(GITHUB_TOKEN|E2E_GITHUB_TOKEN)\s*=\s*"
        r"(?!ghp_\.\.\.)(?!\.\.\.)(?!\$\{)(?!\S*:-)\S{8,}",
        text,
    ):
        raise AssertionError(f"{artifact_name}: não deve embutir valor de token")


def canonical_argv_present(argv: Sequence[str]) -> bool:
    """True se argv contém todos os tokens M-T22-001."""
    return all(token in argv for token in ZOEKT_COMMAND_TOKENS)
