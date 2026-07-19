"""Probes negativos integrais para Robot green path (T25).

Responsabilidade deste módulo
    Indução controlada de BDD-008 (falha parcial + histórico + reindex) e
    BDD-022 (CONFIG_PATH inválido fail-fast sem leak) via exit code,
    invocável por ``python e2e/probes/negative_probes.py <bdd008|bdd022>``.

Motivo da separação
    Robot precisa de evidência integral sem fault-inject no compose vivo
    (D-T25-002/003); probes ficam fora de ``github_rag.e2e`` para não
    violar UT-X04 (sem imports de domínio no pacote launcher).
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
from collections.abc import Sequence
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# Repo root on path so probes can reuse test doubles when invoked via Robot Process.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "src"
for _p in (str(_REPO_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def run_bdd008_partial_failure_probe() -> int:
    """Indução controlada BDD-008 via UI TestClient + orquestrador.

    Responsabilidade
        Reproduzir falha parcial → histórico → reindex total; exit 0 se
        todos os asserts passarem, senão 1. Sem imprimir secrets.

    Motivo da separação
        Separar prova Robot da indução in-process (I-T25-007).
    """
    try:
        from fastapi.testclient import TestClient

        from github_rag.query.fake import FakeQueryService
        from github_rag.schedule.memory import InMemoryCronPreferenceStore
        from github_rag.schedule.scheduler import DefaultDailyScheduler
        from github_rag.ui.api import DefaultManagementUiApi
        from tests.unit.indexing.helpers import (
            RecordingVectorStore,
            make_orchestrator,
            seed_repo,
        )
        from tests.unit.ui.helpers import WEB_ROOT, NoopReconcile
    except Exception as exc:  # noqa: BLE001
        print(f"bdd008_probe_setup_failed error_type={type(exc).__name__}", file=sys.stderr)
        return 1

    try:
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
        assert client.post(
            "/api/repos/index", json={"repository_ids": [rid]}
        ).status_code == 202
        detail = client.get(f"/api/repos/{rid}").json()
        assert detail["state"] == "error"
        assert detail["state_label"] == "erro"
        executions = client.get(f"/api/repos/{rid}/executions").json()["executions"]
        failed = [e for e in executions if e.get("status") == "failed"]
        assert failed and failed[-1].get("error_message") and failed[-1].get("error_at")
        first_msg = failed[-1]["error_message"]
        vector.fail_on = None
        assert client.post(
            "/api/repos/index", json={"repository_ids": [rid]}
        ).status_code == 202
        detail2 = client.get(f"/api/repos/{rid}").json()
        assert detail2["state"] == "up_to_date"
        assert str(rid) in exact.delete_calls
        assert str(rid) in vector.deleted_repos
        executions2 = client.get(f"/api/repos/{rid}/executions").json()["executions"]
        assert any(e.get("error_message") == first_msg for e in executions2)
    except Exception as exc:  # noqa: BLE001
        print(f"bdd008_probe_failed error_type={type(exc).__name__}", file=sys.stderr)
        return 1
    print("bdd008_probe_ok")
    return 0


def run_bdd022_config_path_probe() -> int:
    """Boot com CONFIG_PATH inválido; exit 0 se fail-fast sem parcial/leak.

    Responsabilidade
        Exercitar ``DefaultContainerRuntime.boot`` com path inválido e token
        no env; validar SystemExit(1), sync/reconcile/bind=0 e ausência do
        valor do token na saída capturada.

    Motivo da separação
        Separar prova Robot de CONFIG_PATH (BDD-022) dos casos de payload
        de index (D-T25-003).
    """
    try:
        from github_rag.delivery import DefaultContainerRuntime
        from tests.unit.delivery.helpers import (
            SECRET_TOKEN,
            RecordingReconcile,
            RecordingSurfaces,
            RecordingSync,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"bdd022_probe_setup_failed error_type={type(exc).__name__}", file=sys.stderr)
        return 1

    token = os.environ.get("GITHUB_TOKEN") or SECRET_TOKEN
    sync = RecordingSync()
    reconcile = RecordingReconcile()
    surfaces = RecordingSurfaces()
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "missing-config.json"
        # path does not exist
        runtime = DefaultContainerRuntime(
            environ={
                "CONFIG_PATH": str(bad),
                "GITHUB_TOKEN": token,
                "DATABASE_URL": "postgresql+psycopg://u:p@postgres:5432/x",
            },
            sync=sync,
            reconcile=reconcile,
            bind_ui=surfaces.bind_ui,
            bind_mcp=surfaces.bind_mcp,
            skip_infra=True,
        )
        buf_out, buf_err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                runtime.boot()
        except SystemExit as exc:
            if exc.code != 1:
                print(
                    f"bdd022_probe_failed error_type=SystemExit code={exc.code}",
                    file=sys.stderr,
                )
                return 1
        else:
            print("bdd022_probe_failed error_type=ExpectedSystemExit", file=sys.stderr)
            return 1

        if sync.calls or reconcile.calls or surfaces.ui_bound or surfaces.mcp_bound:
            print("bdd022_probe_failed error_type=PartialApplication", file=sys.stderr)
            return 1
        text = buf_out.getvalue() + buf_err.getvalue()
        if token and token in text:
            print("bdd022_probe_failed error_type=SecretLeak", file=sys.stderr)
            return 1
    print("bdd022_probe_ok")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI ``python e2e/probes/negative_probes.py <bdd008|bdd022>``."""
    args = list(sys.argv if argv is None else argv)
    # When invoked as script, argv[0] is the path; command is argv[1].
    # When called as main(["prog", "bdd008"]), same shape.
    if len(args) < 2:
        print(
            "usage: python e2e/probes/negative_probes.py <bdd008|bdd022>",
            file=sys.stderr,
        )
        return 2
    cmd = args[1]
    if cmd == "bdd008":
        return run_bdd008_partial_failure_probe()
    if cmd == "bdd022":
        return run_bdd022_config_path_probe()
    print(f"unknown_probe error_type=UnknownCommand cmd={cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
