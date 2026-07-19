"""Unit — McpToolError / map_query_error (T17 / UT-E*)."""

from __future__ import annotations

import unittest

from github_rag.mcp.errors import McpToolError, map_query_error
from github_rag.query.errors import (
    QueryCommitUnavailableError,
    QueryEmbeddingError,
    QueryError,
    QueryExactIndexError,
    QueryRepositoryNotFoundError,
    QuerySnapshotError,
    QueryValidationError,
    QueryVectorError,
)

from .helpers import SECRET_TOKEN


class TestMcpToolError(unittest.TestCase):
    """UT-E01."""

    def test_ut_e01_stores_message_and_kind(self) -> None:
        err = McpToolError("repo missing", kind="repository_not_found")
        self.assertEqual(err.message, "repo missing")
        self.assertEqual(err.kind, "repository_not_found")
        self.assertIn("repo missing", str(err))


class TestMapQueryError(unittest.TestCase):
    """UT-E02..E04."""

    def test_ut_e02_kind_table(self) -> None:
        cases: list[tuple[QueryError, str]] = [
            (QueryValidationError("bad"), "validation"),
            (QueryRepositoryNotFoundError("gone"), "repository_not_found"),
            (QueryCommitUnavailableError("no commit"), "commit_unavailable"),
            (QueryExactIndexError("zoekt"), "exact_index"),
            (QueryVectorError("qdrant"), "vector"),
            (QueryEmbeddingError("embed"), "embedding"),
            (QuerySnapshotError("snap"), "snapshot"),
        ]
        for exc, kind in cases:
            mapped = map_query_error(exc)
            self.assertIsInstance(mapped, McpToolError)
            self.assertEqual(mapped.kind, kind, msg=type(exc).__name__)

    def test_ut_e03_no_token_echo(self) -> None:
        poisoned = QueryRepositoryNotFoundError(
            f"missing repo token={SECRET_TOKEN}"
        )
        mapped = map_query_error(poisoned)
        self.assertNotIn(SECRET_TOKEN, mapped.message)
        self.assertNotIn(SECRET_TOKEN, str(mapped))
        self.assertNotIn(SECRET_TOKEN, repr(mapped))

    def test_ut_e04_generic_query_error_kind(self) -> None:
        mapped = map_query_error(QueryError("other"))
        self.assertIsInstance(mapped, McpToolError)
        self.assertEqual(mapped.kind, "query")
        self.assertNotIn(SECRET_TOKEN, mapped.message)


if __name__ == "__main__":
    unittest.main()
