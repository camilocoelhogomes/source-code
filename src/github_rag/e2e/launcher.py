"""Adaptador Podman + docker-compose.e2e.yml (T21).

Responsabilidade deste módulo
    Implementar ``E2eStackLauncher`` via Podman compose e poll ``/healthz``.

Motivo da separação
    Mantém a porta estável; ``run_command`` injetável nos unit tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable

from github_rag.e2e.errors import E2eStackError
from github_rag.e2e.paths import (
    COMPOSE_E2E,
    E2E_CONFIG_FIXTURE,
    E2E_REPOS_FIXTURE,
    resolve_repo_root,
)
from github_rag.e2e.timeouts import COMPOSE_UP_HEALTHY_TIMEOUT_SECONDS

CommandRunner = Callable[
    [Sequence[str], Mapping[str, str]], tuple[int, str, str]
]


def _default_run_command(
    cmd: Sequence[str], env: Mapping[str, str]
) -> tuple[int, str, str]:
    completed = subprocess.run(
        list(cmd),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def ensure_local_git_fixture(repos_dir: Path) -> None:
    """Garante um clone/repo mínimo sob ``repos_dir/sample-local`` (BDD-016).

    Responsabilidade
        Criar ``main`` com commit inicial se ``.git`` ausente (fixture versionável
        sem nested ``.git`` no git do produto).

    Motivo da separação
        Evita commitar objetos git aninhados; runtime prepara o volume local.
    """
    sample = repos_dir / "sample-local"
    sample.mkdir(parents=True, exist_ok=True)
    readme = sample / "README.md"
    if not readme.is_file():
        readme.write_text(
            "# sample-local\n\nMinimal local Git fixture for T21 e2e.\n",
            encoding="utf-8",
        )
    if (sample / ".git").is_dir():
        return
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "e2e",
        "GIT_AUTHOR_EMAIL": "e2e@example.com",
        "GIT_COMMITTER_NAME": "e2e",
        "GIT_COMMITTER_EMAIL": "e2e@example.com",
    }
    commands = (
        ["git", "init", "-b", "main"],
        ["git", "add", "README.md"],
        ["git", "commit", "-m", "init e2e local fixture"],
    )
    for cmd in commands:
        completed = subprocess.run(
            cmd,
            cwd=sample,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise E2eStackError.from_stderr(
                completed.stderr or f"git fixture failed: {cmd}",
            )


class PodmanE2eStackLauncher:
    """Adaptador Podman + docker-compose.e2e.yml (I-T21-003/004).

    Responsabilidade
        Implementar ``E2eStackLauncher`` invocando Podman compose no compose
        canônico T19; mesclar ``HOST_CONFIG``/``HOST_REPOS``; poll ``/healthz``.

    Motivo da separação
        Porta estável; detalhe Podman substituível por doubles (D-T21-008).
    """

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        compose_file: Path | None = None,
        health_url: str = "http://127.0.0.1:8080/healthz",
        healthy_timeout_seconds: float | None = None,
        run_command: CommandRunner | None = None,
    ) -> None:
        self._repo_root = (
            repo_root.resolve()
            if repo_root is not None
            else resolve_repo_root()
        )
        self.compose_file = (
            compose_file.resolve()
            if compose_file is not None
            else (self._repo_root / COMPOSE_E2E.name)
        )
        self._health_url = health_url
        self._healthy_timeout = (
            COMPOSE_UP_HEALTHY_TIMEOUT_SECONDS
            if healthy_timeout_seconds is None
            else healthy_timeout_seconds
        )
        self._run_command = run_command or _default_run_command
        self._host_config = self._repo_root / "e2e/fixtures/config.e2e.json"
        self._host_repos = self._repo_root / "e2e/fixtures/repos"
        # Prefer package constants when they match repo_root layout
        if E2E_CONFIG_FIXTURE.exists() and self._repo_root == resolve_repo_root(
            Path(__file__)
        ):
            self._host_config = E2E_CONFIG_FIXTURE
            self._host_repos = E2E_REPOS_FIXTURE

    def _merge_env(self, env: Mapping[str, str] | None) -> dict[str, str]:
        merged = dict(os.environ)
        if env:
            merged.update({k: str(v) for k, v in env.items()})
        merged.setdefault("HOST_CONFIG", str(self._host_config.resolve()))
        merged.setdefault("HOST_REPOS", str(self._host_repos.resolve()))
        return merged

    def _secrets_from(self, env: Mapping[str, str]) -> list[str]:
        secrets: list[str] = []
        for key in ("E2E_GITHUB_TOKEN", "GITHUB_TOKEN"):
            val = env.get(key, "").strip()
            if val:
                secrets.append(val)
        return secrets

    def up(self, env: Mapping[str, str] | None = None, **_kwargs: Any) -> None:
        effective = self._merge_env(env)
        host_repos = Path(effective["HOST_REPOS"])
        ensure_local_git_fixture(host_repos)
        cmd = [
            "podman",
            "compose",
            "-f",
            str(self.compose_file),
            "up",
            "-d",
            "--build",
        ]
        code, _stdout, stderr = self._run_command(cmd, effective)
        if code != 0:
            raise E2eStackError.from_stderr(
                stderr or f"podman compose up failed with exit {code}",
                secrets=self._secrets_from(effective),
            )

    def wait_healthy(self, *, timeout_seconds: float | None = None) -> None:
        deadline = time.monotonic() + (
            self._healthy_timeout
            if timeout_seconds is None
            else timeout_seconds
        )
        last_error = "healthz not ready"
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(self._health_url, timeout=2.0) as resp:
                    body = resp.read()
                    status = getattr(resp, "status", 200)
                    if status == 200 and self._health_ok(body):
                        return
                    last_error = f"healthz status={status} body={body!r}"
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = str(exc)
            time.sleep(0.05)
        raise E2eStackError.from_stderr(
            f"healthz timeout: {last_error}",
        )

    @staticmethod
    def _health_ok(body: bytes) -> bool:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False
        return (
            payload.get("status") == "ok"
            and payload.get("ui") == "ready"
            and payload.get("mcp") == "ready"
        )

    def down(self) -> None:
        effective = self._merge_env(None)
        cmd = [
            "podman",
            "compose",
            "-f",
            str(self.compose_file),
            "down",
        ]
        try:
            code, _stdout, stderr = self._run_command(cmd, effective)
        except OSError:
            return
        if code != 0:
            # best-effort: swallow after ensuring no secret leak if raised
            _ = E2eStackError.from_stderr(
                stderr or "podman compose down failed",
                secrets=self._secrets_from(effective),
            )
