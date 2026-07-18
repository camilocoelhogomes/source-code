"""Testes unitários — FakeExactCodeIndex (T10)."""

from __future__ import annotations

import unittest

from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.fake import FakeExactCodeIndex
from github_rag.index.zoekt.models import ExactSearchQuery
from github_rag.index.zoekt.port import ExactCodeIndex

from tests.unit.index.zoekt.helpers import (
    COMMIT,
    COMMIT_V2,
    OTHER_REPO,
    REPO,
    SECRET_TOKEN,
    make_file,
)


class TestFakeExactCodeIndex(unittest.TestCase):
    def test_index_then_search_exact_substring(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(
            REPO,
            COMMIT,
            (make_file("src/main.py", b"def authenticate():\n    return True\n"),),
        )
        matches = fake.search(ExactSearchQuery(pattern="def authenticate"))
        self.assertGreaterEqual(len(matches), 1)
        hit = matches[0]
        self.assertEqual(hit.repository, REPO)
        self.assertEqual(hit.path, "src/main.py")
        self.assertEqual(hit.commit, COMMIT)
        self.assertIn("def authenticate", hit.snippet)

    def test_fail_operations_index_raises_without_secret(self) -> None:
        fake = FakeExactCodeIndex(fail_operations=frozenset({"index"}))
        with self.assertRaises(ExactCodeIndexError) as ctx:
            fake.index(REPO, COMMIT, (make_file("a.py", b"x\n"),))
        blob = str(ctx.exception) + repr(ctx.exception)
        self.assertNotIn(SECRET_TOKEN, blob)
        self.assertEqual(ctx.exception.operation, "index")

    def test_fail_operations_search_raises(self) -> None:
        fake = FakeExactCodeIndex(fail_operations=frozenset({"search"}))
        with self.assertRaises(ExactCodeIndexError) as ctx:
            fake.search(ExactSearchQuery(pattern="needle"))
        self.assertEqual(ctx.exception.operation, "search")

    def test_fail_operations_delete_raises(self) -> None:
        fake = FakeExactCodeIndex(fail_operations=frozenset({"delete"}))
        with self.assertRaises(ExactCodeIndexError) as ctx:
            fake.delete_repository(REPO)
        self.assertEqual(ctx.exception.operation, "delete")

    def test_delete_repository_removes_only_target(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(REPO, COMMIT, (make_file("a.py", b"MARKER_API\n"),))
        fake.index(
            OTHER_REPO,
            COMMIT,
            (make_file("b.py", b"MARKER_OTHER\n", repository=OTHER_REPO),),
        )
        fake.delete_repository(REPO)
        self.assertEqual(
            list(fake.search(ExactSearchQuery(pattern="MARKER_API", repository=REPO))),
            [],
        )
        other = fake.search(
            ExactSearchQuery(pattern="MARKER_OTHER", repository=OTHER_REPO)
        )
        self.assertGreaterEqual(len(other), 1)
        self.assertEqual(other[0].repository, OTHER_REPO)

    def test_delete_missing_is_noop(self) -> None:
        fake = FakeExactCodeIndex()
        fake.delete_repository("acme/never-indexed")

    def test_empty_files_is_noop(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(REPO, COMMIT, ())
        self.assertEqual(list(fake.search(ExactSearchQuery(pattern="anything"))), [])

    def test_empty_pattern_returns_empty(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(REPO, COMMIT, (make_file("a.py", b"content\n"),))
        self.assertEqual(list(fake.search(ExactSearchQuery(pattern=""))), [])

    def test_reindex_replaces_file_set(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(
            REPO,
            COMMIT,
            (
                make_file("src/a.py", b"KEEP_ME\n"),
                make_file("src/b.py", b"DROP_ME\n"),
            ),
        )
        fake.index(
            REPO,
            COMMIT_V2,
            (make_file("src/a.py", b"KEEP_ME\n", commit=COMMIT_V2),),
        )
        self.assertEqual(list(fake.search(ExactSearchQuery(pattern="DROP_ME"))), [])
        kept = fake.search(ExactSearchQuery(pattern="KEEP_ME"))
        self.assertGreaterEqual(len(kept), 1)
        self.assertEqual(kept[0].path, "src/a.py")
        self.assertEqual(kept[0].commit, COMMIT_V2)

    def test_search_filter_repository(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(REPO, COMMIT, (make_file("a.py", b"SHARED\n"),))
        fake.index(
            OTHER_REPO,
            COMMIT,
            (make_file("a.py", b"SHARED\n", repository=OTHER_REPO),),
        )
        hits = fake.search(ExactSearchQuery(pattern="SHARED", repository=REPO))
        self.assertTrue(hits)
        self.assertTrue(all(h.repository == REPO for h in hits))

    def test_search_filter_path_prefix(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(
            REPO,
            COMMIT,
            (
                make_file("src/a.py", b"TOKEN\n"),
                make_file("docs/a.md", b"TOKEN\n"),
            ),
        )
        hits = fake.search(ExactSearchQuery(pattern="TOKEN", path_prefix="src/"))
        self.assertTrue(hits)
        self.assertTrue(all(h.path.startswith("src/") for h in hits))

    def test_file_to_index_mismatch_raises(self) -> None:
        fake = FakeExactCodeIndex()
        with self.assertRaises(ExactCodeIndexError) as ctx:
            fake.index(
                REPO,
                COMMIT,
                (make_file("a.py", b"x\n", repository="other/repo"),),
            )
        self.assertEqual(ctx.exception.operation, "index")

    def test_file_to_index_commit_mismatch_raises(self) -> None:
        fake = FakeExactCodeIndex()
        with self.assertRaises(ExactCodeIndexError) as ctx:
            fake.index(
                REPO,
                COMMIT,
                (make_file("a.py", b"x\n", commit="other-sha"),),
            )
        self.assertEqual(ctx.exception.operation, "index")

    def test_satisfies_exact_code_index_protocol(self) -> None:
        fake = FakeExactCodeIndex()
        self.assertIsInstance(fake, ExactCodeIndex)

    def test_search_results_are_deterministically_ordered(self) -> None:
        fake = FakeExactCodeIndex()
        fake.index(
            REPO,
            COMMIT,
            (
                make_file("z.py", b"needle in z\n"),
                make_file("a.py", b"needle in a\n"),
            ),
        )
        hits = list(fake.search(ExactSearchQuery(pattern="needle")))
        self.assertGreaterEqual(len(hits), 2)
        keys = [(h.repository, h.path, h.line_number or 0, h.snippet) for h in hits]
        self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main()
