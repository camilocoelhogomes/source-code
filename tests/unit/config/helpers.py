"""Helpers compartilhados — testes unitários T02 config."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest import mock

SECRET_TOKEN_VALUE = "unit-test-super-secret-token-do-not-leak"
TOKEN_ENV_NAME = "GITHUB_TOKEN"


def write_config(payload: dict[str, Any], directory: Path) -> Path:
    path = directory / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_raw(content: str, directory: Path, name: str = "config.json") -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


def github_connection(
    *,
    orgs: list[str] | None = None,
    repos: list[str] | None = None,
    branches: list[str] | None = None,
    token: Any = None,
    token_env: str = TOKEN_ENV_NAME,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conn: dict[str, Any] = {
        "type": "github",
        "token": {"env": token_env} if token is None else token,
        "orgs": orgs if orgs is not None else ["my-org"],
        "repos": (
            repos
            if repos is not None
            else ["my-org/microservice-*", "my-org/*-api"]
        ),
        "revisions": {"branches": branches if branches is not None else ["main"]},
    }
    if extra:
        conn.update(extra)
    return conn


def git_connection(
    *,
    url: str = "file:///repos/*",
    branches: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conn: dict[str, Any] = {
        "type": "git",
        "url": url,
        "revisions": {"branches": branches if branches is not None else ["main"]},
    }
    if extra:
        conn.update(extra)
    return conn


def load_with_environ(
    path: Path | None,
    environ: Mapping[str, str] | None = None,
    *,
    loader: Any | None = None,
) -> Any:
    from github_rag.config import ConfigLoader

    target = loader if loader is not None else ConfigLoader()
    env_map = dict(environ) if environ is not None else {}
    with mock.patch.dict("os.environ", env_map, clear=False):
        if TOKEN_ENV_NAME not in env_map:
            import os

            os.environ.pop(TOKEN_ENV_NAME, None)
        return target.load(path)
