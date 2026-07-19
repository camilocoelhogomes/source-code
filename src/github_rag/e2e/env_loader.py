"""Loader seguro de .env para e2e (T29)."""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from pathlib import Path


def parse_dotenv_text(text: str) -> dict[str, str]:
    """Parse conteúdo estilo .env sem interpretação shell."""
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def load_dotenv_file(
    path: Path | str,
    *,
    override: bool = False,
    environ: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
    """Carrega .env em environ (noop se arquivo ausente)."""
    target = os.environ if environ is None else environ
    file_path = Path(path)
    if not file_path.is_file():
        return {}
    parsed = parse_dotenv_text(file_path.read_text(encoding="utf-8"))
    for key, value in parsed.items():
        if override or key not in target:
            target[key] = value
    return parsed
