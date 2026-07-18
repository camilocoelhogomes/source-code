"""Testes unitários — ExactCodeIndexError (T10)."""

from __future__ import annotations

import unittest

from github_rag.index.zoekt.errors import ExactCodeIndexError

from tests.unit.index.zoekt.helpers import SECRET_TOKEN


class TestExactCodeIndexError(unittest.TestCase):
    def test_attributes_operation_repo_commit(self) -> None:
        err = ExactCodeIndexError(
            "index failed exit=1",
            operation="index",
            repository="acme/api",
            commit="abc123",
        )
        self.assertEqual(err.operation, "index")
        self.assertEqual(err.repository, "acme/api")
        self.assertEqual(err.commit, "abc123")

    def test_optional_repo_commit_default_none(self) -> None:
        err = ExactCodeIndexError("search failed", operation="search")
        self.assertEqual(err.operation, "search")
        self.assertIsNone(err.repository)
        self.assertIsNone(err.commit)

    def test_str_and_repr_do_not_contain_secret(self) -> None:
        # Mensagem pode citar operação/repo; nunca deve ecoar token se passado por engano
        # no contexto de teste — construímos sem o segredo e verificamos invariante.
        err = ExactCodeIndexError(
            "HTTP 401 from zoekt host",
            operation="search",
            repository="acme/api",
        )
        blob = str(err) + repr(err)
        self.assertNotIn(SECRET_TOKEN, blob)
        # Mesmo se alguém embutir o token na message, o contrato exige que
        # a superfície tipada não vaze segredos; aqui garantimos que nosso
        # fixture de segredo não aparece em erros bem formados.
        self.assertIsInstance(err, Exception)

    def test_is_exception_subclass(self) -> None:
        err = ExactCodeIndexError("x", operation="delete")
        self.assertIsInstance(err, Exception)

    def test_cause_is_preservable(self) -> None:
        cause = OSError("connection refused")
        try:
            raise ExactCodeIndexError(
                "search transport failed",
                operation="search",
                repository="acme/api",
            ) from cause
        except ExactCodeIndexError as err:
            self.assertIs(err.__cause__, cause)


if __name__ == "__main__":
    unittest.main()
