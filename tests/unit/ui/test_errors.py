"""Unit — mapeamento de erros HTTP da UI (T18)."""

from __future__ import annotations

import unittest

from github_rag.query.errors import QueryExactIndexError, QueryValidationError
from github_rag.ui.errors import http_status_for, safe_detail


class TestUiErrors(unittest.TestCase):
    def test_query_validation_is_400(self) -> None:
        self.assertEqual(http_status_for(QueryValidationError("bad")), 400)

    def test_unknown_is_500(self) -> None:
        self.assertEqual(http_status_for(RuntimeError("x")), 500)

    def test_redacts_token_prefixes(self) -> None:
        detail = safe_detail(QueryExactIndexError("leak ghp_abc github_pat_xyz"))
        self.assertNotIn("ghp_", detail)
        self.assertNotIn("github_pat_", detail)
        self.assertIn("[redacted]", detail)


if __name__ == "__main__":
    unittest.main()
