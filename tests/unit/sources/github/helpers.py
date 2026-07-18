"""Helpers — testes T05 github discovery."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest import mock

from github_rag.config import ConfigLoader, GitHubConnection

SECRET_TOKEN_VALUE = "bdd-github-discovery-secret-token-do-not-leak"
TOKEN_ENV_NAME = "GITHUB_TOKEN"


def load_github_connection(
    *,
    connection_name: str = "github-test",
    orgs: list[str] | None = None,
    repos: list[str] | None = None,
    token_env: str = TOKEN_ENV_NAME,
    token_value: str = SECRET_TOKEN_VALUE,
    environ: Mapping[str, str] | None = None,
) -> GitHubConnection:
    """Carrega uma ``GitHubConnection`` válida via ``ConfigLoader``."""
    payload: dict[str, Any] = {
        "connections": {
            connection_name: {
                "type": "github",
                "token": {"env": token_env},
                "orgs": orgs if orgs is not None else ["my-org"],
                "repos": (
                    repos
                    if repos is not None
                    else ["my-org/microservice-*", "my-org/*-api"]
                ),
                "revisions": {"branches": ["main"]},
            }
        }
    }
    env_map = {token_env: token_value}
    if environ is not None:
        env_map.update(dict(environ))

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with mock.patch.dict("os.environ", env_map, clear=False):
            config = ConfigLoader().load(path)
    conn = config.connections[connection_name]
    assert conn.type == "github"
    return conn  # type: ignore[return-value]
