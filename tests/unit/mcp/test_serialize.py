"""Unit — serialize DetailFields / omit-null / evidências (T17 / UT-S*)."""

from __future__ import annotations

import base64
import unittest

from github_rag.catalog.models import RepoOrigin, RepoState
from github_rag.mcp.serialize import (
    details_from_includes,
    file_to_dict,
    hit_to_dict,
    omit_nulls,
    repo_entry_to_dict,
    tree_to_dict,
)
from github_rag.query.types import DetailFields, FileContent, QueryHit, TreeListing

from .helpers import COMMIT, REPO, SECRET_TOKEN, make_catalog_entry


class TestDetailsFromIncludes(unittest.TestCase):
    """UT-S01..S03."""

    def test_ut_s01_defaults_all_false(self) -> None:
        self.assertEqual(details_from_includes(), DetailFields())

    def test_ut_s02_all_true(self) -> None:
        details = details_from_includes(
            include_repository=True,
            include_path=True,
            include_commit=True,
            include_snippet=True,
        )
        self.assertEqual(
            details,
            DetailFields(
                repository=True, path=True, commit=True, snippet=True
            ),
        )

    def test_ut_s03_partial_path_only(self) -> None:
        details = details_from_includes(include_path=True)
        self.assertEqual(
            details,
            DetailFields(repository=False, path=True, commit=False, snippet=False),
        )


class TestOmitNulls(unittest.TestCase):
    """UT-S04..S06."""

    def test_ut_s04_removes_top_level_none(self) -> None:
        out = omit_nulls({"kind": "exact", "score": None, "path": "a.py"})
        self.assertEqual(out, {"kind": "exact", "path": "a.py"})
        self.assertNotIn("score", out)

    def test_ut_s05_recursive_nested(self) -> None:
        out = omit_nulls(
            {"hits": [{"kind": "exact", "repository": None, "path": "x.py"}]}
        )
        self.assertEqual(out, {"hits": [{"kind": "exact", "path": "x.py"}]})

    def test_ut_s05b_list_preserves_non_dict_items(self) -> None:
        out = omit_nulls({"paths": ["a.py", "b.py"], "n": None})
        self.assertEqual(out, {"paths": ["a.py", "b.py"]})

    def test_ut_s06_preserves_falsy_non_none(self) -> None:
        out = omit_nulls({"score": 0.0, "ok": False, "empty": "", "n": None})
        self.assertEqual(out, {"score": 0.0, "ok": False, "empty": ""})


class TestHitToDict(unittest.TestCase):
    """UT-S07..S11."""

    def test_ut_s07_exact_without_details(self) -> None:
        hit = QueryHit(kind="exact", score=None, line_number=3)
        d = hit_to_dict(hit)
        self.assertEqual(d["kind"], "exact")
        for key in ("repository", "path", "commit", "snippet", "score"):
            self.assertNotIn(key, d)
        self.assertEqual(d.get("line_number"), 3)

    def test_ut_s08_semantic_keeps_score(self) -> None:
        hit = QueryHit(kind="semantic", score=0.91)
        d = hit_to_dict(hit)
        self.assertEqual(d["kind"], "semantic")
        self.assertEqual(d["score"], 0.91)
        for key in ("repository", "path", "commit", "snippet"):
            self.assertNotIn(key, d)

    def test_ut_s09_optional_fields_when_present(self) -> None:
        hit = QueryHit(
            kind="exact",
            score=None,
            repository=REPO,
            path="src/auth.py",
            commit=COMMIT,
            snippet="code",
            line_number=1,
        )
        d = hit_to_dict(hit)
        self.assertEqual(d["repository"], REPO)
        self.assertEqual(d["path"], "src/auth.py")
        self.assertEqual(d["commit"], COMMIT)
        self.assertEqual(d["snippet"], "code")

    def test_ut_s10_never_emits_chunk_metadata_summary(self) -> None:
        hit = QueryHit(
            kind="semantic",
            score=0.5,
            chunk_metadata_summary="slm-flavored",
        )
        d = hit_to_dict(hit)
        self.assertNotIn("chunk_metadata_summary", d)

    def test_ut_s11_line_number_omitted_when_none(self) -> None:
        hit = QueryHit(kind="semantic", score=0.1, line_number=None)
        d = hit_to_dict(hit)
        self.assertNotIn("line_number", d)


class TestFileToDict(unittest.TestCase):
    """UT-S12..S14."""

    def test_ut_s12_utf8_text(self) -> None:
        d = file_to_dict(FileContent(content=b"hello\n"))
        self.assertEqual(d["content"], "hello\n")
        self.assertEqual(d["content_encoding"], "utf-8")
        self.assertNotIn("content_base64", d)

    def test_ut_s13_invalid_utf8_base64(self) -> None:
        raw = b"\xff\xfe"
        d = file_to_dict(FileContent(content=raw))
        self.assertEqual(d["content_encoding"], "base64")
        self.assertNotIn("content", d)
        self.assertEqual(d["content_base64"], base64.b64encode(raw).decode("ascii"))

    def test_ut_s14_omits_none_metadata(self) -> None:
        d = file_to_dict(
            FileContent(
                content=b"x",
                repository=None,
                path=None,
                commit=None,
            )
        )
        for key in ("repository", "path", "commit"):
            self.assertNotIn(key, d)


class TestTreeAndRepo(unittest.TestCase):
    """UT-S15..S17."""

    def test_ut_s15_tree_paths_omit_nulls(self) -> None:
        d = tree_to_dict(
            TreeListing(paths=("a.py", "b.py"), repository=None, commit=COMMIT)
        )
        self.assertEqual(list(d["paths"]), ["a.py", "b.py"])
        self.assertNotIn("repository", d)
        self.assertEqual(d["commit"], COMMIT)

    def test_ut_s16_repo_entry_required_fields_and_null_commits(self) -> None:
        entry = make_catalog_entry(
            state=RepoState.NOT_INDEXED,
            last_processed_commit=None,
            current_main_commit=None,
        )
        d = repo_entry_to_dict(entry)
        for key in (
            "repo_key",
            "repository_id",
            "origin",
            "connection_name",
            "state",
            "last_processed_commit",
            "current_main_commit",
        ):
            self.assertIn(key, d)
        self.assertEqual(d["repo_key"], REPO)
        self.assertEqual(d["repository_id"], 42)
        self.assertEqual(d["origin"], RepoOrigin.GITHUB.value)
        self.assertEqual(d["state"], RepoState.NOT_INDEXED.value)
        self.assertIsNone(d["last_processed_commit"])
        self.assertIsNone(d["current_main_commit"])

    def test_ut_s17_repo_entry_no_local_path_or_token(self) -> None:
        entry = make_catalog_entry(
            origin=RepoOrigin.LOCAL,
            local_path="/secret/mount/repo",
            last_processed_commit=None,
            current_main_commit=None,
        )
        d = repo_entry_to_dict(entry)
        self.assertNotIn("local_path", d)
        self.assertNotIn("token", d)
        blob = str(d)
        self.assertNotIn(SECRET_TOKEN, blob)
        self.assertNotIn("/secret/mount/repo", blob)


if __name__ == "__main__":
    unittest.main()
