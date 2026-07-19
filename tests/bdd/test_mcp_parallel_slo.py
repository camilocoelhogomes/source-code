"""
BDD executável — T26-gap-mcp-parallel-slo (BDD-013 integral).

Cenários PS-01..PS-07: observabilidade do limiter, SLO puro e superfície MCP.
Robot bdd013 é documental aqui; prova de stack fica no green path T21/T22.

Execução:
    python -m pytest tests/bdd/test_mcp_parallel_slo.py -q
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.catalog.models import RepoOrigin
from github_rag.concurrency.limiter import SemaphoreWorkerLimiter
from github_rag.concurrency.parallel_slo import (
    ParallelSloResult,
    evaluate_parallel_slo,
    min_waves,
)
from github_rag.mcp import DefaultMcpEvidenceServer
from github_rag.query.fake import FakeQueryService
from github_rag.query.types import QueryHit, QueryHits

REPO = "acme/api"
COMMIT = "abc123"
SECRET_TOKEN = "ghp_should_never_appear_in_mcp_parallel_slo_7c1e"


def _hits() -> QueryHits:
    return QueryHits(
        hits=(
            QueryHit(
                kind="exact",
                score=None,
                repository=REPO,
                path="src/a.py",
                commit=COMMIT,
                snippet="def foo():\n    pass\n",
                line_number=1,
            ),
        )
    )


def _seed_catalog(catalog: InMemoryCatalogRepository) -> None:
    entry = catalog.upsert_repository(
        connection_name="gh",
        origin=RepoOrigin.GITHUB,
        repo_identifier=REPO,
        github_org="acme",
        local_path=None,
    )
    catalog.mark_queued(entry.id)
    catalog.mark_indexing(entry.id)
    catalog.mark_updated(entry.id, COMMIT)


class SpyQueryService:
    def __init__(
        self,
        *,
        exact_hits: QueryHits,
        work_seconds: float = 0.0,
    ) -> None:
        self._inner = FakeQueryService(exact_hits=exact_hits)
        self._work_seconds = work_seconds

    def search_exact(self, request: Any) -> QueryHits:
        if self._work_seconds > 0:
            time.sleep(self._work_seconds)
        return self._inner.search_exact(request)

    def search_semantic(self, request: Any) -> QueryHits:
        return self._inner.search_semantic(request)

    def read_file(self, request: Any) -> Any:
        return self._inner.read_file(request)

    def list_tree(self, request: Any) -> Any:
        return self._inner.list_tree(request)


def _build_server(
    *,
    catalog: InMemoryCatalogRepository,
    query: Any,
    capacity: int,
) -> tuple[Any, SemaphoreWorkerLimiter]:
    limiter = SemaphoreWorkerLimiter(capacity=capacity, pool="query")
    server = DefaultMcpEvidenceServer(
        catalog=catalog,
        query=query,
        query_limiter=limiter,
    )
    return server, limiter


def _parse_tool_payload(result: Any) -> Any:
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        return json.loads(result)
    if isinstance(result, list):
        texts: list[str] = []
        for block in result:
            text = getattr(block, "text", None)
            if text is None and isinstance(block, dict):
                text = block.get("text")
            if text is not None:
                texts.append(text)
        if len(texts) == 1:
            try:
                return json.loads(texts[0])
            except json.JSONDecodeError:
                return texts[0]
        return texts
    text = getattr(result, "text", None)
    if text is not None:
        return json.loads(text)
    raise AssertionError(f"payload de tool não reconhecido: {type(result)!r}")


def _invoke_tool(app: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    arguments = arguments or {}
    call = getattr(app, "call_tool", None)
    if call is None and hasattr(app, "_tool_manager"):
        call = app._tool_manager.call_tool
    if call is None:
        raise AssertionError("FastMCP sem call_tool")
    result = call(name, arguments)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    if isinstance(result, tuple) and result:
        result = result[0]
    content = getattr(result, "content", result)
    return _parse_tool_payload(content)


class TestPS01PeakNeverExceedsCapacity(unittest.TestCase):
    """PS-01."""

    def test_peak_active_bounded_and_active_zero_after(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=2, pool="query")
        release = threading.Event()

        def work() -> None:
            with limiter.acquire():
                release.wait(timeout=5.0)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(work) for _ in range(4)]
            time.sleep(0.1)
            self.assertLessEqual(limiter.peak_active, 2)
            self.assertLessEqual(limiter.active, 2)
            release.set()
            wait(futures)
            for future in futures:
                future.result()

        self.assertEqual(limiter.active, 0)
        self.assertLessEqual(limiter.peak_active, 2)
        self.assertGreaterEqual(limiter.peak_active, 1)


class TestPS02WaitingObservable(unittest.TestCase):
    """PS-02."""

    def test_excess_waits_and_waiting_counter(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        release_first = threading.Event()
        first_entered = threading.Event()
        second_entered = threading.Event()

        def first() -> None:
            with limiter.acquire():
                first_entered.set()
                release_first.wait(timeout=5.0)

        def second() -> None:
            with limiter.acquire():
                second_entered.set()

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        self.assertTrue(first_entered.wait(timeout=2.0))
        t2.start()
        time.sleep(0.05)
        self.assertFalse(second_entered.is_set())
        self.assertGreaterEqual(limiter.waiting, 1)
        release_first.set()
        t1.join(timeout=2.0)
        t2.join(timeout=2.0)
        self.assertTrue(second_entered.is_set())
        self.assertEqual(limiter.waiting, 0)


class TestPS03SloCapacityOne(unittest.TestCase):
    """PS-03."""

    def test_wall_clock_three_waves(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        work_t = 0.15

        def work() -> None:
            with limiter.acquire():
                time.sleep(work_t)

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(work) for _ in range(3)]
            wait(futures)
            for future in futures:
                future.result()
        wall = time.perf_counter() - started

        self.assertEqual(limiter.peak_active, 1)
        self.assertEqual(min_waves(3, 1), 3)
        result = evaluate_parallel_slo(
            capacity=1,
            n_calls=3,
            wall_seconds=wall,
            single_seconds=work_t,
        )
        self.assertIsInstance(result, ParallelSloResult)
        self.assertTrue(result.ok, msg=result.reason)


class TestPS04SloCapacityTwo(unittest.TestCase):
    """PS-04."""

    def test_two_waves_and_not_fully_serial(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=2, pool="query")
        work_t = 0.15

        def work() -> None:
            with limiter.acquire():
                time.sleep(work_t)

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(work) for _ in range(4)]
            wait(futures)
            for future in futures:
                future.result()
        wall = time.perf_counter() - started

        self.assertLessEqual(limiter.peak_active, 2)
        self.assertGreaterEqual(limiter.peak_active, 1)
        self.assertEqual(min_waves(4, 2), 2)
        result = evaluate_parallel_slo(
            capacity=2,
            n_calls=4,
            wall_seconds=wall,
            single_seconds=work_t,
        )
        self.assertTrue(result.ok, msg=result.reason)


class TestPS05PureEvaluatorRejectsDisguisedSmoke(unittest.TestCase):
    """PS-05."""

    def test_serial_wall_rejected(self) -> None:
        result = evaluate_parallel_slo(
            capacity=4,
            n_calls=8,
            wall_seconds=8.0,
            single_seconds=1.0,
        )
        self.assertFalse(result.ok)

    def test_unlimited_wall_rejected(self) -> None:
        result = evaluate_parallel_slo(
            capacity=4,
            n_calls=8,
            wall_seconds=1.0,
            single_seconds=1.0,
        )
        self.assertFalse(result.ok)

    def test_two_wave_wall_accepted(self) -> None:
        result = evaluate_parallel_slo(
            capacity=4,
            n_calls=8,
            wall_seconds=2.0,
            single_seconds=1.0,
        )
        self.assertTrue(result.ok, msg=result.reason)


class TestPS06McpSurfaceSlo(unittest.TestCase):
    """PS-06."""

    def test_search_code_parallel_slo_capacity_one(self) -> None:
        catalog = InMemoryCatalogRepository()
        _seed_catalog(catalog)
        work_t = 0.12
        query = SpyQueryService(exact_hits=_hits(), work_seconds=work_t)
        server, limiter = _build_server(catalog=catalog, query=query, capacity=1)
        app = server.build()

        def call() -> Any:
            return _invoke_tool(
                app, "search_code", {"pattern": "foo", "repo_key": REPO}
            )

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(call) for _ in range(3)]
            wait(futures)
            payloads = [future.result() for future in futures]
        wall = time.perf_counter() - started

        self.assertLessEqual(limiter.peak_active, 1)
        for payload in payloads:
            self.assertIn("hits", payload)
        result = evaluate_parallel_slo(
            capacity=1,
            n_calls=3,
            wall_seconds=wall,
            single_seconds=work_t,
        )
        self.assertTrue(result.ok, msg=result.reason)


class TestPS07NoTokenInParallelPath(unittest.TestCase):
    """PS-07 / BDD-014."""

    def test_parallel_list_repos_never_echoes_token(self) -> None:
        previous = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = SECRET_TOKEN
        try:
            catalog = InMemoryCatalogRepository()
            _seed_catalog(catalog)
            query = SpyQueryService(exact_hits=_hits())
            server, _limiter = _build_server(catalog=catalog, query=query, capacity=2)
            app = server.build()

            def call() -> str:
                payload = _invoke_tool(app, "list_repos")
                return json.dumps(payload, default=str)

            with ThreadPoolExecutor(max_workers=4) as pool:
                texts = list(pool.map(lambda _: call(), range(4)))

            for text in texts:
                self.assertNotIn(SECRET_TOKEN, text)
                self.assertIn("repos", text)
        finally:
            if previous is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = previous


if __name__ == "__main__":
    unittest.main()
