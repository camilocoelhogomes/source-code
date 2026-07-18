"""
BDD executável — T10-zoekt-adapter.

Valida BDD-009, metadados, ExactCodeIndexError, BDD-024/DEC-016,
delete_repository e corners (files vazio, pattern vazio, reindex)
conforme design 0.1.1 — via FakeExactCodeIndex (sem Zoekt real).

Execução:
    python -m pytest tests/bdd/test_zoekt_adapter.py -q
"""

from __future__ import annotations

import unittest

from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.fake import FakeExactCodeIndex
from github_rag.index.zoekt.models import ExactSearchQuery, FileToIndex
from github_rag.index.zoekt.port import ExactCodeIndex

REPO = "acme/api"
OTHER_REPO = "acme/other"
COMMIT = "abc123"
COMMIT_V2 = "def456"
SECRET_TOKEN = "ghp_should_never_appear_in_errors_9f3a2"


def _file(
    path: str,
    content: bytes,
    *,
    repository: str = REPO,
    commit: str = COMMIT,
) -> FileToIndex:
    return FileToIndex(
        repository=repository,
        path=path,
        commit=commit,
        content=content,
    )


class TestZOEKT01IndexMakesContentSearchable(unittest.TestCase):
    """ZOEKT-01 / BDD-009 — indexação torna conteúdo buscável por match exato."""

    def test_exact_match_after_index(self) -> None:
        index: ExactCodeIndex = FakeExactCodeIndex()
        files = (
            _file(
                "src/main.py",
                b"def authenticate():\n    return True\n",
            ),
        )

        index.index(REPO, COMMIT, files)
        matches = index.search(ExactSearchQuery(pattern="def authenticate"))

        self.assertGreaterEqual(len(matches), 1)
        hit = matches[0]
        self.assertEqual(hit.repository, REPO)
        self.assertEqual(hit.path, "src/main.py")
        self.assertIn("def authenticate", hit.snippet)


class TestZOEKT02MatchMetadata(unittest.TestCase):
    """ZOEKT-02 — ExactMatch expõe repository, path, commit, snippet."""

    def test_metadata_fields_present(self) -> None:
        index = FakeExactCodeIndex()
        index.index(
            REPO,
            COMMIT,
            (_file("lib/util.py", b"UNIQUE_TOKEN_XYZ = 1\n"),),
        )

        matches = index.search(ExactSearchQuery(pattern="UNIQUE_TOKEN_XYZ"))

        self.assertEqual(len(matches), 1)
        hit = matches[0]
        self.assertEqual(hit.repository, REPO)
        self.assertEqual(hit.path, "lib/util.py")
        self.assertEqual(hit.commit, COMMIT)
        self.assertTrue(hit.commit)
        self.assertTrue(hit.snippet)
        self.assertIn("UNIQUE_TOKEN_XYZ", hit.snippet)


class TestZOEKT03TypedExactCodeIndexError(unittest.TestCase):
    """ZOEKT-03 — falhas tipadas ExactCodeIndexError para T14."""

    def test_index_failure_raises_typed_error(self) -> None:
        index = FakeExactCodeIndex(fail_operations=frozenset({"index"}))

        with self.assertRaises(ExactCodeIndexError) as ctx:
            index.index(
                REPO,
                COMMIT,
                (_file("a.py", b"x = 1\n"),),
            )

        blob = str(ctx.exception) + repr(ctx.exception)
        self.assertNotIn(SECRET_TOKEN, blob)
        self.assertIsInstance(ctx.exception, ExactCodeIndexError)

    def test_search_failure_raises_typed_error(self) -> None:
        index = FakeExactCodeIndex(fail_operations=frozenset({"search"}))
        index_ok = FakeExactCodeIndex()
        index_ok.index(REPO, COMMIT, (_file("a.py", b"needle\n"),))

        # Fake configurado só para search; estado prévio irrelevante.
        with self.assertRaises(ExactCodeIndexError):
            index.search(ExactSearchQuery(pattern="needle"))


class TestZOEKT04FakePortContractNoRealZoekt(unittest.TestCase):
    """ZOEKT-04 / BDD-024 / DEC-016 — fake da porta; sem Zoekt real."""

    def test_fake_satisfies_exact_code_index_port(self) -> None:
        fake = FakeExactCodeIndex()

        for name in ("index", "search", "delete_repository"):
            self.assertTrue(callable(getattr(fake, name)), msg=name)

        # Protocol estrutural (runtime_checkable quando disponível).
        self.assertIsInstance(fake, ExactCodeIndex)

    def test_fake_module_is_in_memory_double(self) -> None:
        import github_rag.index.zoekt.fake as fake_mod

        self.assertTrue(hasattr(fake_mod, "FakeExactCodeIndex"))
        # Aceite T10: BDD não depende de processo/container Zoekt.
        self.assertNotIn("zoekt-webserver", fake_mod.__doc__ or "")


class TestZOEKT05DeleteRepository(unittest.TestCase):
    """ZOEKT-05 — delete_repository remove índice do repositório."""

    def test_delete_removes_only_target_repo(self) -> None:
        index = FakeExactCodeIndex()
        index.index(
            REPO,
            COMMIT,
            (_file("a.py", b"MARKER_API_ONLY\n"),),
        )
        index.index(
            OTHER_REPO,
            COMMIT,
            (
                _file(
                    "b.py",
                    b"MARKER_OTHER_ONLY\n",
                    repository=OTHER_REPO,
                ),
            ),
        )

        index.delete_repository(REPO)

        api_hits = index.search(
            ExactSearchQuery(pattern="MARKER_API_ONLY", repository=REPO)
        )
        other_hits = index.search(
            ExactSearchQuery(pattern="MARKER_OTHER_ONLY", repository=OTHER_REPO)
        )

        self.assertEqual(list(api_hits), [])
        self.assertGreaterEqual(len(other_hits), 1)
        self.assertEqual(other_hits[0].repository, OTHER_REPO)

    def test_delete_missing_repository_is_noop(self) -> None:
        index = FakeExactCodeIndex()
        index.delete_repository("acme/never-indexed")


class TestZOEKT06EmptyFilesNoOp(unittest.TestCase):
    """ZOEKT-06 — files vazio em index = no-op sucesso."""

    def test_empty_files_noop(self) -> None:
        index = FakeExactCodeIndex()

        index.index(REPO, COMMIT, ())

        matches = index.search(ExactSearchQuery(pattern="anything"))
        self.assertEqual(list(matches), [])


class TestZOEKT07EmptyPatternReturnsEmpty(unittest.TestCase):
    """ZOEKT-07 — pattern vazio em search = lista vazia."""

    def test_empty_pattern_empty_list(self) -> None:
        index = FakeExactCodeIndex()
        index.index(
            REPO,
            COMMIT,
            (_file("a.py", b"some content here\n"),),
        )

        matches = index.search(ExactSearchQuery(pattern=""))

        self.assertEqual(list(matches), [])


class TestZOEKT08ReindexDropsAbsentPath(unittest.TestCase):
    """ZOEKT-08 — reindex do conjunto remove path ausente (ENG-012)."""

    def test_reindex_replaces_repository_file_set(self) -> None:
        index = FakeExactCodeIndex()
        index.index(
            REPO,
            COMMIT,
            (
                _file("src/a.py", b"KEEP_ME\n"),
                _file("src/b.py", b"DROP_ME\n"),
            ),
        )

        index.index(
            REPO,
            COMMIT_V2,
            (_file("src/a.py", b"KEEP_ME\n", commit=COMMIT_V2),),
        )

        dropped = index.search(ExactSearchQuery(pattern="DROP_ME"))
        kept = index.search(ExactSearchQuery(pattern="KEEP_ME"))

        self.assertEqual(list(dropped), [])
        self.assertGreaterEqual(len(kept), 1)
        self.assertEqual(kept[0].path, "src/a.py")
        self.assertEqual(kept[0].commit, COMMIT_V2)


if __name__ == "__main__":
    unittest.main()
