"""Unit — DefaultMcpEvidenceServer lifecycle (T17 / UT-B*)."""

from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

from github_rag.catalog.memory import InMemoryCatalogRepository
from github_rag.concurrency.limiter import SemaphoreWorkerLimiter
from github_rag.mcp import DEFAULT_SERVER_NAME, DefaultMcpEvidenceServer
from github_rag.mcp.ports import McpEvidenceServer
from github_rag.mcp.server import _EvidenceFastMCP
from github_rag.query.fake import FakeQueryService
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .helpers import APPROVED_TOOLS, build_server, list_tool_names, seed_catalog


class TestDefaultMcpEvidenceServer(unittest.TestCase):
    """UT-B01..B04."""

    def test_ut_b01_build_returns_fastmcp_with_five_tools(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, _, _, _ = build_server(catalog=catalog)
        app = server.build()
        self.assertIsInstance(app, FastMCP)
        self.assertEqual(list_tool_names(app), set(APPROVED_TOOLS))

    def test_ut_b02_run_callable_stdio_default(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, _, _, _ = build_server(catalog=catalog)
        self.assertTrue(callable(server.run))
        sig = inspect.signature(server.run)
        transport = sig.parameters["transport"]
        self.assertEqual(transport.default, "stdio")

    def test_ut_b03_default_server_name(self) -> None:
        self.assertEqual(DEFAULT_SERVER_NAME, "github-rag-evidence")
        catalog = InMemoryCatalogRepository()
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        server = DefaultMcpEvidenceServer(
            catalog=catalog,
            query=FakeQueryService(),
            query_limiter=limiter,
        )
        self.assertEqual(server._server_name, DEFAULT_SERVER_NAME)

    def test_ut_b04_protocol_runtime_checkable(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, _, _, _ = build_server(catalog=catalog)
        self.assertIsInstance(server, McpEvidenceServer)
        app = server.build()
        self.assertIsInstance(app, FastMCP)

    def test_ut_b05_run_delegates_to_fastmcp_stdio(self) -> None:
        catalog = InMemoryCatalogRepository()
        seed_catalog(catalog)
        server, _, _, _ = build_server(catalog=catalog)
        with patch.object(_EvidenceFastMCP, "run") as run_mock:
            server.run()
            run_mock.assert_called_once_with(transport="stdio")

    def test_ut_b06_tool_error_without_mcp_cause_is_reraised(self) -> None:
        import asyncio

        app = _EvidenceFastMCP("unit")

        async def _boom(_self: FastMCP, name: str, arguments: dict) -> None:
            err = ToolError("wrapped")
            err.__cause__ = RuntimeError("not mcp")
            raise err

        with patch.object(FastMCP, "call_tool", _boom):
            with self.assertRaises(ToolError):
                asyncio.run(app.call_tool("x", {}))


if __name__ == "__main__":
    unittest.main()
