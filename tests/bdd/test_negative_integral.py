"""BDD — gaps negativos integrais T25 (NEG-01..03 / BDD-008,018,022)."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from fastapi.testclient import TestClient

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import ExecutionStatus, RepoState
from github_rag.catalog.sync import CatalogSync
from github_rag.config.schema import _AppConfig, _GitConnection, _Revisions
from github_rag.delivery import DefaultContainerRuntime
from github_rag.query.fake import FakeQueryService
from github_rag.schedule.memory import InMemoryCronPreferenceStore
from github_rag.schedule.scheduler import DefaultDailyScheduler
from github_rag.sources.local.discovery import LocalRepoDiscovery
from github_rag.ui.api import DefaultManagementUiApi
from github_rag.ui.issues import InMemoryCatalogIssueStore
from tests.unit.catalog.sync_helpers import FakeGitHubDiscovery
from tests.unit.delivery.helpers import (
    SECRET_TOKEN,
    RecordingReconcile,
    RecordingSurfaces,
    RecordingSync,
)
from tests.unit.indexing.helpers import (
    RecordingVectorStore,
    make_orchestrator,
    seed_repo,
)
from tests.unit.ui.helpers import WEB_ROOT, NoopReconcile


class TestNeg01PartialFailureHistoryReindex(unittest.TestCase):
    """NEG-01 / BDD-008 — falha parcial + histórico + restart total via UI API."""

    def test_neg01_partial_failure_history_and_full_reindex(self) -> None:
        vector = RecordingVectorStore(fail_on="replace")
        orch, _, catalog, snap, exact, _ = make_orchestrator(vector=vector)
        rid = seed_repo(catalog)
        snap.tip = "C1"

        scheduler = DefaultDailyScheduler(
            preference_store=InMemoryCronPreferenceStore(),
            reconcile=NoopReconcile(),
            orchestrator=orch,
            default_cron="0 2 * * *",
        )
        client = TestClient(
            DefaultManagementUiApi(
                catalog=catalog,
                orchestrator=orch,
                scheduler=scheduler,
                query=FakeQueryService(),
                drain_on_index=True,
                web_root=WEB_ROOT,
            ).build()
        )

        resp = client.post("/api/repos/index", json={"repository_ids": [rid]})
        self.assertEqual(resp.status_code, 202)

        detail = client.get(f"/api/repos/{rid}").json()
        self.assertEqual(detail["state"], "error")
        self.assertEqual(detail["state_label"], "erro")

        executions = client.get(f"/api/repos/{rid}/executions").json()["executions"]
        self.assertGreaterEqual(len(executions), 1)
        failed = [e for e in executions if e.get("status") == "failed"]
        self.assertTrue(failed)
        self.assertTrue(failed[-1].get("error_message"))
        self.assertTrue(failed[-1].get("error_at"))
        first_error_msg = failed[-1]["error_message"]

        entry = catalog.get_repository(rid)
        self.assertEqual(entry.state, RepoState.ERROR)
        self.assertIsNone(entry.last_processed_commit)
        self.assertEqual(
            catalog.list_executions(rid)[-1].status, ExecutionStatus.FAILED
        )

        vector.fail_on = None
        resp2 = client.post("/api/repos/index", json={"repository_ids": [rid]})
        self.assertEqual(resp2.status_code, 202)
        detail2 = client.get(f"/api/repos/{rid}").json()
        self.assertEqual(detail2["state"], "up_to_date")
        self.assertIn(str(rid), exact.delete_calls)
        self.assertIn(str(rid), vector.deleted_repos)

        executions2 = client.get(f"/api/repos/{rid}/executions").json()["executions"]
        self.assertTrue(
            any(e.get("error_message") == first_error_msg for e in executions2),
            msg="histórico deve reter a falha anterior",
        )
        blob = str(detail) + str(executions) + str(detail2)
        self.assertNotIn(SECRET_TOKEN, blob)


class TestNeg02MissingVolumeIssuesApi(unittest.TestCase):
    """NEG-02 / BDD-018 — volume ausente → sem repos + issue na UI API."""

    def test_neg02_missing_volume_registers_issue_on_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing-volume"
            config = _AppConfig(
                connections={
                    "local-missing": _GitConnection(
                        url=f"file://{missing}/*",
                        revisions=_Revisions(branches=("main",)),
                    )
                }
            )
            catalog = InMemoryCatalogRepository()
            sync = CatalogSync(
                catalog=catalog,
                github_discovery=FakeGitHubDiscovery(),
                local_discovery=LocalRepoDiscovery(),
            )
            result = sync.sync(config)
            self.assertEqual(result.active, ())
            self.assertGreaterEqual(len(result.local_issues), 1)

            issue_store = InMemoryCatalogIssueStore()
            issue_store.replace(result.local_issues)

            orch, *_rest = make_orchestrator(catalog=catalog)
            scheduler = DefaultDailyScheduler(
                preference_store=InMemoryCronPreferenceStore(),
                reconcile=NoopReconcile(),
                orchestrator=orch,
                default_cron="0 2 * * *",
            )
            client = TestClient(
                DefaultManagementUiApi(
                    catalog=catalog,
                    orchestrator=orch,
                    scheduler=scheduler,
                    query=FakeQueryService(),
                    web_root=WEB_ROOT,
                    issue_store=issue_store,
                ).build()
            )
            resp = client.get("/api/catalog/issues")
            self.assertEqual(resp.status_code, 200)
            issues = resp.json()["issues"]
            self.assertTrue(issues)
            self.assertEqual(issues[0]["connection_name"], "local-missing")
            self.assertIn("inaccessible", issues[0]["message"].lower())
            repos = client.get("/api/repos").json()["repos"]
            self.assertEqual(repos, [])
            self.assertNotIn(SECRET_TOKEN, resp.text)


class TestNeg03ConfigPathFailFast(unittest.TestCase):
    """NEG-03 / BDD-022 — CONFIG_PATH inválido fail-fast sem parcial/leak."""

    def _assert_fail_fast(
        self, *, environ: dict[str, str]
    ) -> None:
        sync = RecordingSync()
        reconcile = RecordingReconcile()
        surfaces = RecordingSurfaces()
        runtime = DefaultContainerRuntime(
            environ=environ,
            sync=sync,
            reconcile=reconcile,
            bind_ui=surfaces.bind_ui,
            bind_mcp=surfaces.bind_mcp,
            skip_infra=True,
        )
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                runtime.boot()
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(sync.calls, [])
        self.assertEqual(reconcile.calls, 0)
        self.assertFalse(surfaces.ui_bound)
        self.assertFalse(surfaces.mcp_bound)
        text = buf_out.getvalue() + buf_err.getvalue()
        self.assertNotIn(SECRET_TOKEN, text)

    def test_neg03_missing_config_path_exits_without_partial_or_leak(self) -> None:
        self._assert_fail_fast(
            environ={
                "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
                "GITHUB_TOKEN": SECRET_TOKEN,
            }
        )

    def test_neg03_malformed_json_exits_without_partial_or_leak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "bad.json"
            cfg.write_text("{not-json", encoding="utf-8")
            self._assert_fail_fast(
                environ={
                    "CONFIG_PATH": str(cfg),
                    "GITHUB_TOKEN": SECRET_TOKEN,
                    "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
                }
            )


if __name__ == "__main__":
    unittest.main()
