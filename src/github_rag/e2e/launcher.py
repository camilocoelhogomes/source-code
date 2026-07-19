"""Adaptador Podman + compose dev/e2e (T21) com app no host.

Responsabilidade deste módulo
    Subir infra via compose (sem build de app), iniciar ``github_rag.delivery``
    no host e poll ``/healthz``.

Motivo da separação
    Mantém a porta estável; acelera ciclo TDD local vs rebuild de imagem.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable

from github_rag.e2e.errors import E2eStackError
from github_rag.e2e.host_env import build_host_delivery_env, default_zoekt_index_dir
from github_rag.e2e.paths import (
    COMPOSE_DEV,
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


def _load_catalog_indexing_keywords():
    """Importa helpers T24 de ``e2e/robot/libraries`` (sys.path)."""
    import sys

    libs = resolve_repo_root(Path(__file__)) / "e2e" / "robot" / "libraries"
    libs_str = str(libs.resolve())
    if libs_str not in sys.path:
        sys.path.insert(0, libs_str)
    import CatalogIndexingKeywords as cik  # noqa: PLC0415

    return cik


def ensure_local_git_fixture(repos_dir: Path) -> None:
    """Garante sample-local com git + seed e2e T24 (BDD-006 base).

    Responsabilidade
        Preparar volume HOST_REPOS/sample-local para catálogo local:
        init main (legado T21) + árvore elegibilidade idempotente.
        Se ``.git`` já existe, não faz early-return cego — aplica seed T24.

    Motivo da separação
        Superfície e2e (D-T24-010), não ETL; suite Robot assume fixture
        montada e legível pelo container (:ro).
    """
    sample = repos_dir / "sample-local"
    sample.mkdir(parents=True, exist_ok=True)
    readme = sample / "README.md"
    if not readme.is_file():
        readme.write_text(
            "# sample-local\n\nMinimal local Git fixture for T21 e2e.\n",
            encoding="utf-8",
        )
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "e2e",
        "GIT_AUTHOR_EMAIL": "e2e@example.com",
        "GIT_COMMITTER_NAME": "e2e",
        "GIT_COMMITTER_EMAIL": "e2e@example.com",
    }
    if not (sample / ".git").is_dir():
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

    # Seed T24 (BDD-006 paths + MAIN_ONLY) — sempre, idempotente (S01/S02).
    try:
        cik = _load_catalog_indexing_keywords()
        cik.prepare_eligibility_tree(sample)
    except Exception as exc:  # noqa: BLE001 — surface as E2eStackError
        raise E2eStackError.from_stderr(str(exc)) from exc


class PodmanE2eStackLauncher:
    """Adaptador Podman compose + app no host (I-T21-003/004).

    Responsabilidade
        ``podman compose -f docker-compose.dev.yml up -d`` (infra, sem build),
        iniciar ``python -m github_rag.delivery`` no host, poll ``/healthz``.

    Motivo da separação
        Porta estável; detalhe Podman/host-app substituível por doubles.
    """

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        compose_file: Path | None = None,
        health_url: str = "http://127.0.0.1:8080/healthz",
        healthy_timeout_seconds: float | None = None,
        run_command: CommandRunner | None = None,
        host_app: bool = True,
    ) -> None:
        self._repo_root = (
            repo_root.resolve()
            if repo_root is not None
            else resolve_repo_root()
        )
        self.compose_file = (
            compose_file.resolve()
            if compose_file is not None
            else COMPOSE_DEV.resolve()
        )
        self._health_url = health_url
        self._healthy_timeout = (
            COMPOSE_UP_HEALTHY_TIMEOUT_SECONDS
            if healthy_timeout_seconds is None
            else healthy_timeout_seconds
        )
        self._run_command = run_command or _default_run_command
        self._host_app = host_app
        self._app_process: subprocess.Popen[str] | None = None
        self._host_config = self._repo_root / "e2e/fixtures/config.e2e.json"
        self._host_repos = self._repo_root / "e2e/fixtures/repos"
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
        index_host = str(
            default_zoekt_index_dir(
                self._repo_root,
                e2e=self.compose_file.name == COMPOSE_E2E.name,
            )
        )
        merged.setdefault("ZOEKT_INDEX_HOST", index_host)
        return merged

    def _secrets_from(self, env: Mapping[str, str]) -> list[str]:
        secrets: list[str] = []
        for key in ("E2E_GITHUB_TOKEN", "GITHUB_TOKEN"):
            val = env.get(key, "").strip()
            if val:
                secrets.append(val)
        return secrets

    def _start_host_app(self, effective: Mapping[str, str]) -> None:
        token_extra: dict[str, str] = {}
        if effective.get("E2E_GITHUB_TOKEN", "").strip():
            token_extra["E2E_GITHUB_TOKEN"] = effective["E2E_GITHUB_TOKEN"].strip()
            token_extra["GITHUB_TOKEN"] = effective["E2E_GITHUB_TOKEN"].strip()
        elif effective.get("GITHUB_TOKEN", "").strip():
            token_extra["GITHUB_TOKEN"] = effective["GITHUB_TOKEN"].strip()

        host_env = build_host_delivery_env(
            repo_root=self._repo_root,
            config_path=Path(effective["HOST_CONFIG"]),
            repos_dir=Path(effective["HOST_REPOS"]),
            zoekt_index_dir=Path(effective["ZOEKT_INDEX_HOST"]),
            extra=token_extra,
        )
        self._app_process = subprocess.Popen(
            [sys.executable, "-m", "github_rag.delivery"],
            env=host_env,
            cwd=str(self._repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _stop_host_app(self) -> None:
        proc = self._app_process
        self._app_process = None
        if proc is None:
            return
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

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
        ]
        code, _stdout, stderr = self._run_command(cmd, effective)
        if code != 0:
            raise E2eStackError.from_stderr(
                stderr or f"podman compose up failed with exit {code}",
                secrets=self._secrets_from(effective),
            )
        if self._host_app:
            self._start_host_app(effective)

    def wait_healthy(self, *, timeout_seconds: float | None = None) -> None:
        if self._host_app and self._app_process is not None:
            exit_code = self._app_process.poll()
            if exit_code is not None:
                stderr = (self._app_process.stderr.read() or "") if self._app_process.stderr else ""
                raise E2eStackError.from_stderr(
                    f"host app exited before healthy (code={exit_code}): {stderr[:500]}"
                )

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
        if self._host_app:
            self._stop_host_app()
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
            _ = E2eStackError.from_stderr(
                stderr or "podman compose down failed",
                secrets=self._secrets_from(effective),
            )
