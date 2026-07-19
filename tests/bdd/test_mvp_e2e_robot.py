"""
BDD executável — T21-mvp-e2e-robot (CONTRATOS com doubles).

Valida BDD-026/027/028 e política de exclusão BDD-015 via
E2eCredentialResolver / E2eStackLauncher / RobotMvpSuite.
NÃO sobe Podman nem compose real (D-T21-008).

Prova Robot em stack real: documentada em bdd.md (ROBOT-01..06);
invocada só via RobotMvpSuite.run() em gate e2e dedicado.

Cenários: E2E-01..E2E-10 — ver
    spec/features/github-etl-mcp-rag/tasks/T21-mvp-e2e-robot/bdd.md

Execução (CI padrão):
    python -m pytest tests/bdd/test_mvp_e2e_robot.py -q

TDD: ImportError de github_rag.e2e é falha esperada até a implementação.
"""

from __future__ import annotations

import unittest
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = REPO_ROOT / ".gitignore"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
COMPOSE_E2E = REPO_ROOT / "docker-compose.e2e.yml"
E2E_CONFIG_FIXTURE = REPO_ROOT / "e2e" / "fixtures" / "config.e2e.json"
E2E_REPOS_FIXTURE = REPO_ROOT / "e2e" / "fixtures" / "repos"
SECRET_TOKEN = "ghp_should_never_appear_in_e2e_9f3a2"

GREEN_PATH_SUITE_MARKERS = (
    "health",
    "catalog_indexing",
    "ui",
    "mcp",
    "negative",
)


def _import_e2e_surface() -> Any:
    """Importa superfície pública github_rag.e2e (red até T21 implementar)."""
    import github_rag.e2e as e2e_pkg  # noqa: PLC0415

    return e2e_pkg


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"artefato ausente: {path}")
    return path.read_text(encoding="utf-8")


class RecordingLauncher:
    """Double de E2eStackLauncher — registra up/down/wait_healthy sem Podman."""

    def __init__(
        self,
        *,
        up_error: BaseException | None = None,
        healthy_error: BaseException | None = None,
    ) -> None:
        self.up_calls: list[Mapping[str, str]] = []
        self.down_calls = 0
        self.healthy_calls = 0
        self._up_error = up_error
        self._healthy_error = healthy_error
        self.order: list[str] = []

    def up(self, env: Mapping[str, str] | None = None, **_kwargs: Any) -> None:
        self.order.append("up")
        self.up_calls.append(dict(env or {}))
        if self._up_error is not None:
            raise self._up_error

    def wait_healthy(self, *_a: Any, **_k: Any) -> None:
        self.order.append("wait_healthy")
        self.healthy_calls += 1
        if self._healthy_error is not None:
            raise self._healthy_error

    def down(self, *_a: Any, **_k: Any) -> None:
        self.order.append("down")
        self.down_calls += 1


class RecordingRobotRunner:
    """Double do CLI robot — registra invocações; retorna exit code configurável."""

    def __init__(self, *, exit_code: int = 0) -> None:
        self.exit_code = exit_code
        self.calls: list[dict[str, Any]] = []
        self.order_hook: list[str] | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> int:
        if self.order_hook is not None:
            self.order_hook.append("robot")
        self.calls.append({"args": args, "kwargs": dict(kwargs)})
        return self.exit_code


def _suite_run(
    *,
    environ: MutableMapping[str, str],
    launcher: RecordingLauncher,
    robot_runner: RecordingRobotRunner | None = None,
    e2e_pkg: Any | None = None,
) -> int:
    """Constrói DefaultRobotMvpSuite com doubles e executa run()."""
    e2e_pkg = e2e_pkg or _import_e2e_surface()
    DefaultRobotMvpSuite = e2e_pkg.DefaultRobotMvpSuite
    robot_runner = robot_runner or RecordingRobotRunner(exit_code=0)
    robot_runner.order_hook = launcher.order

    # Contrato esperado (design §3.3 / §3.8): injeção de launcher + runner + environ.
    try:
        suite = DefaultRobotMvpSuite(
            launcher=launcher,
            robot_runner=robot_runner,
            environ=environ,
        )
    except TypeError:
        suite = DefaultRobotMvpSuite(
            launcher=launcher,
            run_robot=robot_runner,
            environ=environ,
        )
    return int(suite.run())


# ---------------------------------------------------------------------------
# E2E-01 / E2E-02 — credenciais (CONTRATO)
# ---------------------------------------------------------------------------


class TestE2E01MissingCredential(unittest.TestCase):
    """E2E-01 — credencial ausente → falha antes de up (BDD-027)."""

    def test_missing_token_fails_before_up(self) -> None:
        e2e = _import_e2e_surface()
        launcher = RecordingLauncher()
        env: dict[str, str] = {
            "GITHUB_ACTIONS": "false",
        }
        env.pop("GITHUB_TOKEN", None)
        env.pop("E2E_GITHUB_TOKEN", None)

        CredentialError = e2e.E2eCredentialError
        err_text = ""
        failed = False
        try:
            if hasattr(e2e, "E2eCredentialResolver"):
                e2e.E2eCredentialResolver().resolve(environ=env)
                self.fail("resolver deveria falhar sem token")
            else:
                code = _suite_run(environ=env, launcher=launcher, e2e_pkg=e2e)
                self.assertNotEqual(code, 0, "suite.run deve falhar sem token")
                failed = True
        except CredentialError as exc:
            failed = True
            err_text = str(exc)

        self.assertTrue(failed)
        self.assertEqual(launcher.up_calls, [])
        self.assertNotIn(SECRET_TOKEN, err_text)


class TestE2E02CiRequiresE2eGithubToken(unittest.TestCase):
    """E2E-02 — CI exige E2E_GITHUB_TOKEN; rejeita só GITHUB_TOKEN Actions."""

    def test_ci_with_only_actions_github_token_fails(self) -> None:
        e2e = _import_e2e_surface()
        launcher = RecordingLauncher()
        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_TOKEN": SECRET_TOKEN,
        }
        CredentialError = e2e.E2eCredentialError

        failed = False
        err_text = ""
        try:
            if hasattr(e2e, "E2eCredentialResolver"):
                e2e.E2eCredentialResolver().resolve(environ=env)
                self.fail(
                    "CI com só GITHUB_TOKEN (Actions) deve falhar; "
                    "exige E2E_GITHUB_TOKEN (REQ-049 / D-T21-006)"
                )
            else:
                code = _suite_run(environ=env, launcher=launcher, e2e_pkg=e2e)
                self.assertNotEqual(code, 0)
                failed = True
        except CredentialError as exc:
            failed = True
            err_text = str(exc)

        self.assertTrue(failed, "CI sem E2E_GITHUB_TOKEN deve falhar")
        self.assertEqual(launcher.up_calls, [])
        self.assertNotIn(SECRET_TOKEN, err_text)

    def test_ci_with_e2e_github_token_resolves(self) -> None:
        e2e = _import_e2e_surface()
        env = {
            "GITHUB_ACTIONS": "true",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
            "GITHUB_TOKEN": "should_not_be_preferred_in_ci",
        }
        if hasattr(e2e, "E2eCredentialResolver"):
            resolved = e2e.E2eCredentialResolver().resolve(environ=env)
            token = getattr(resolved, "token", None) or getattr(
                resolved, "value", resolved
            )
            self.assertEqual(str(token), SECRET_TOKEN)
        else:
            launcher = RecordingLauncher()
            robot = RecordingRobotRunner(exit_code=0)
            code = _suite_run(
                environ=env, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
            )
            self.assertEqual(code, 0)
            self.assertGreaterEqual(len(launcher.up_calls), 1)


# ---------------------------------------------------------------------------
# E2E-03 / E2E-04 — falhas de stack (CONTRATO)
# ---------------------------------------------------------------------------


class TestE2E03StackFailsToStart(unittest.TestCase):
    """E2E-03 — stack que não sobe → exit ≠ 0; robot não roda; down no finally."""

    def test_up_failure_exits_nonzero_and_cleans_up(self) -> None:
        e2e = _import_e2e_surface()
        StackError = e2e.E2eStackError
        launcher = RecordingLauncher(up_error=StackError("compose failed"))
        robot = RecordingRobotRunner(exit_code=0)
        env = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
        }

        code: int | None = None
        err_text = ""
        try:
            code = _suite_run(
                environ=env, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
            )
        except Exception as exc:  # noqa: BLE001
            code = 1
            err_text = str(exc)

        self.assertNotEqual(code, 0)
        self.assertEqual(robot.calls, [])
        self.assertEqual(launcher.down_calls, 1)
        self.assertNotIn(SECRET_TOKEN, err_text)


class TestE2E04HealthTimeout(unittest.TestCase):
    """E2E-04 — health timeout → falha; robot não roda; down no finally."""

    def test_health_timeout_exits_nonzero(self) -> None:
        e2e = _import_e2e_surface()
        StackError = e2e.E2eStackError
        launcher = RecordingLauncher(
            healthy_error=StackError("healthz timeout"),
        )
        robot = RecordingRobotRunner(exit_code=0)
        env = {
            "GITHUB_ACTIONS": "false",
            "GITHUB_TOKEN": SECRET_TOKEN,
        }

        code: int | None = None
        try:
            code = _suite_run(
                environ=env, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
            )
        except StackError:
            code = 1

        self.assertNotEqual(code, 0)
        self.assertEqual(robot.calls, [])
        self.assertEqual(launcher.down_calls, 1)
        self.assertIn("up", launcher.order)
        self.assertIn("wait_healthy", launcher.order)


# ---------------------------------------------------------------------------
# E2E-05 / E2E-06 / E2E-07 — orquestração green path (CONTRATO)
# ---------------------------------------------------------------------------


class TestE2E05GreenPathOrchestration(unittest.TestCase):
    """E2E-05 — resolve → up → healthy → robot → down; HOST_* fixtures."""

    def test_happy_path_order_and_fixture_env(self) -> None:
        e2e = _import_e2e_surface()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        env = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
        }

        code = _suite_run(
            environ=env, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
        )

        self.assertEqual(code, 0)
        self.assertEqual(
            launcher.order,
            ["up", "wait_healthy", "robot", "down"],
        )
        self.assertEqual(len(launcher.up_calls), 1)
        up_env = launcher.up_calls[0]
        host_config = up_env.get("HOST_CONFIG", "")
        host_repos = up_env.get("HOST_REPOS", "")
        self.assertTrue(
            host_config.endswith("e2e/fixtures/config.e2e.json")
            or Path(host_config) == E2E_CONFIG_FIXTURE,
            f"HOST_CONFIG inesperado: {host_config!r}",
        )
        self.assertTrue(
            host_repos.endswith("e2e/fixtures/repos")
            or Path(host_repos) == E2E_REPOS_FIXTURE,
            f"HOST_REPOS inesperado: {host_repos!r}",
        )
        # Compose e2e canônico (constante do pacote ou path no launcher)
        compose_path = getattr(e2e, "COMPOSE_E2E", None) or getattr(
            e2e, "COMPOSE_E2E_PATH", None
        )
        if compose_path is not None:
            self.assertTrue(
                str(compose_path).endswith("docker-compose.e2e.yml"),
                compose_path,
            )
        else:
            self.assertTrue(COMPOSE_E2E.is_file(), "compose e2e T19 deve existir")


class TestE2E06RobotFailureBlocksMvp(unittest.TestCase):
    """E2E-06 — robot exit ≠ 0 → suite exit ≠ 0; down ainda roda."""

    def test_robot_nonzero_fails_mvp(self) -> None:
        e2e = _import_e2e_surface()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=1)
        env = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
        }

        code = _suite_run(
            environ=env, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
        )

        self.assertNotEqual(code, 0)
        self.assertEqual(len(robot.calls), 1)
        self.assertEqual(launcher.down_calls, 1)


class TestE2E07ExcludeBdd015(unittest.TestCase):
    """E2E-07 — invocação robot exclui tag bdd015; green path suites presentes."""

    def test_robot_invocation_excludes_bdd015(self) -> None:
        e2e = _import_e2e_surface()
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        env = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
        }

        code = _suite_run(
            environ=env, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(robot.calls), 1)

        call = robot.calls[0]
        blob = " ".join(str(a) for a in call["args"])
        blob += " " + " ".join(f"{k}={v}" for k, v in call["kwargs"].items())
        exclude = call["kwargs"].get("exclude") or call["kwargs"].get("excludes")
        if exclude is not None:
            exclude_s = (
                " ".join(str(x) for x in exclude)
                if not isinstance(exclude, str)
                else exclude
            )
            blob += " " + exclude_s

        blob_l = blob.lower()
        # Exclusão explícita — não aceitar mera menção a "bdd015" (falso positivo)
        self.assertRegex(
            blob_l,
            r"(--exclude(\s+|=)bdd015|exclude[=:].*bdd015|\bexcludes?\b.*\bbdd015\b)",
            msg=f"invocação robot sem --exclude bdd015: {call!r}",
        )
        self.assertNotRegex(
            blob_l,
            r"(discovery.?cursor|cursor.?discovery|bdd015\.robot)",
            msg=f"green path não deve exigir Discovery/Cursor: {call!r}",
        )
        for marker in GREEN_PATH_SUITE_MARKERS:
            self.assertIn(
                marker,
                blob_l,
                msg=f"green path deve incluir suite/marker {marker!r}: {call!r}",
            )


# ---------------------------------------------------------------------------
# E2E-08 — sem secrets no git (MANIFESTO; sem Podman)
# ---------------------------------------------------------------------------


class TestE2E08NoSecretsInGit(unittest.TestCase):
    """E2E-08 — .gitignore / .env.example / fixtures sem tokens reais (BDD-027)."""

    def test_gitignore_covers_env_and_e2e_results(self) -> None:
        text = _read(GITIGNORE)
        self.assertIn(".env", text)
        # e2e/results ou padrão equivalente documentado
        self.assertTrue(
            "e2e/results" in text
            or "*.secret" in text
            or "e2e/results/" in text,
            ".gitignore deve cobrir e2e/results/ ou *.secret (BDD-027)",
        )

    def test_env_example_has_no_real_secrets(self) -> None:
        text = _read(ENV_EXAMPLE)
        self.assertNotRegex(text, r"ghp_[A-Za-z0-9_]{20,}")
        self.assertNotRegex(
            text,
            r"(?m)^(?:export\s+)?GITHUB_TOKEN=\s*['\"]?[A-Za-z0-9_\-]{20,}",
        )
        self.assertIn("GITHUB_TOKEN", text)
        self.assertIn("E2E_GITHUB_TOKEN", text)

    def test_e2e_config_fixture_uses_env_ref_not_literal_token(self) -> None:
        if not E2E_CONFIG_FIXTURE.is_file():
            self.fail(
                "fixture e2e/fixtures/config.e2e.json ausente "
                "(esperada na implementação T21; red até criar)"
            )
        text = _read(E2E_CONFIG_FIXTURE)
        self.assertNotRegex(text, r"ghp_[A-Za-z0-9_]{20,}")
        self.assertRegex(
            text,
            r'"token"\s*:\s*\{\s*"env"\s*:\s*"GITHUB_TOKEN"\s*\}',
        )


# ---------------------------------------------------------------------------
# E2E-09 — ownership / superfície consumível (CONTRATO)
# ---------------------------------------------------------------------------


class TestE2E09PublicHandoffSurface(unittest.TestCase):
    """E2E-09 — E2eStackLauncher / RobotMvpSuite consumíveis (BDD-028)."""

    def test_public_exports_and_stable_usage(self) -> None:
        e2e = _import_e2e_surface()
        for name in (
            "E2eStackLauncher",
            "RobotMvpSuite",
            "PodmanE2eStackLauncher",
            "DefaultRobotMvpSuite",
        ):
            self.assertTrue(
                hasattr(e2e, name),
                f"github_rag.e2e deve exportar {name}",
            )

        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        env = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
        }
        code = _suite_run(
            environ=env, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
        )
        self.assertEqual(code, 0)

        # Ownership Robot: path canônico sob e2e/robot
        robot_root = getattr(e2e, "ROBOT_ROOT", None) or getattr(
            e2e, "ROBOT_SUITE_ROOT", None
        )
        if robot_root is not None:
            self.assertIn("e2e/robot", str(robot_root).replace("\\", "/"))


# ---------------------------------------------------------------------------
# E2E-10 — redaction (CONTRATO)
# ---------------------------------------------------------------------------


class TestE2E10NoSecretLeakInErrors(unittest.TestCase):
    """E2E-10 — erros não vazam token (BDD-014 smoke / BDD-027)."""

    def test_stack_error_message_redacts_token(self) -> None:
        e2e = _import_e2e_surface()
        CredentialError = e2e.E2eCredentialError
        StackError = e2e.E2eStackError

        # 1) Falha de credencial com token presente no env — mensagem sem secret
        env_cred = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_TOKEN": SECRET_TOKEN,
        }
        cred_msg = ""
        try:
            if hasattr(e2e, "E2eCredentialResolver"):
                e2e.E2eCredentialResolver().resolve(environ=env_cred)
                self.fail("CI sem E2E_GITHUB_TOKEN deve falhar")
            else:
                launcher = RecordingLauncher()
                code = _suite_run(
                    environ=env_cred, launcher=launcher, e2e_pkg=e2e
                )
                self.assertNotEqual(code, 0)
        except CredentialError as exc:
            cred_msg = str(exc)
        self.assertNotIn(SECRET_TOKEN, cred_msg)

        # 2) StackError construído a partir de stderr bruto — str redigida
        raw = f"podman failed env={SECRET_TOKEN}"
        if hasattr(StackError, "from_stderr"):
            err = StackError.from_stderr(raw)
        else:
            err = StackError(raw)
        self.assertNotIn(SECRET_TOKEN, str(err))

        # 3) Green path: robot argv/kwargs nunca carregam o token
        launcher = RecordingLauncher()
        robot = RecordingRobotRunner(exit_code=0)
        env_ok = {
            "GITHUB_ACTIONS": "false",
            "E2E_GITHUB_TOKEN": SECRET_TOKEN,
        }
        code = _suite_run(
            environ=env_ok, launcher=launcher, robot_runner=robot, e2e_pkg=e2e
        )
        self.assertEqual(code, 0)
        for call in robot.calls:
            self.assertNotIn(SECRET_TOKEN, repr(call))
            for arg in call["args"]:
                self.assertNotIn(SECRET_TOKEN, str(arg))
            for val in call["kwargs"].values():
                self.assertNotIn(SECRET_TOKEN, str(val))


if __name__ == "__main__":
    unittest.main()
