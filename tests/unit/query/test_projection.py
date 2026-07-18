"""Unit — projeção DetailFields (T16 / UT-P*)."""

from __future__ import annotations

import unittest

from github_rag.index.chunk.types import SemanticChunk, SourceLanguage
from github_rag.index.vector.types import ChunkMetadata, SemanticHit
from github_rag.index.zoekt.models import ExactMatch
from github_rag.query.projection import project_exact, project_semantic
from github_rag.query.types import DetailFields


def _exact() -> ExactMatch:
    return ExactMatch(
        repository="acme/api",
        path="src/a.py",
        commit="abc",
        snippet="line with hit",
        line_number=3,
    )


def _semantic() -> SemanticHit:
    return SemanticHit(
        score=0.77,
        repo_id="acme/api",
        commit_sha="abc",
        chunk=SemanticChunk(
            chunk_id="c1",
            path="src/a.py",
            language=SourceLanguage.PYTHON,
            kind="function",
            text="chunk text",
            start_byte=0,
            end_byte=10,
            start_point=(0, 0),
            end_point=(0, 10),
        ),
        metadata=ChunkMetadata(summary="s", keywords=("k",)),
    )


class TestProjection(unittest.TestCase):
    def test_exact_all_false(self) -> None:
        hit = project_exact(_exact(), DetailFields())
        self.assertEqual(hit.kind, "exact")
        self.assertIsNone(hit.score)
        self.assertIsNone(hit.repository)
        self.assertIsNone(hit.path)
        self.assertIsNone(hit.commit)
        self.assertIsNone(hit.snippet)

    def test_exact_all_true(self) -> None:
        hit = project_exact(
            _exact(),
            DetailFields(
                repository=True, path=True, commit=True, snippet=True
            ),
        )
        self.assertEqual(hit.repository, "acme/api")
        self.assertEqual(hit.path, "src/a.py")
        self.assertEqual(hit.commit, "abc")
        self.assertEqual(hit.snippet, "line with hit")

    def test_semantic_all_false(self) -> None:
        hit = project_semantic(_semantic(), DetailFields())
        self.assertEqual(hit.kind, "semantic")
        self.assertEqual(hit.score, 0.77)
        self.assertIsNone(hit.repository)
        self.assertIsNone(hit.path)
        self.assertIsNone(hit.commit)
        self.assertIsNone(hit.snippet)

    def test_semantic_all_true(self) -> None:
        hit = project_semantic(
            _semantic(),
            DetailFields(
                repository=True, path=True, commit=True, snippet=True
            ),
        )
        self.assertEqual(hit.repository, "acme/api")
        self.assertEqual(hit.path, "src/a.py")
        self.assertEqual(hit.commit, "abc")
        self.assertEqual(hit.snippet, "chunk text")

    def test_partial_flags_matrix(self) -> None:
        m = _exact()
        self.assertEqual(
            project_exact(m, DetailFields(repository=True)).repository,
            "acme/api",
        )
        self.assertIsNone(project_exact(m, DetailFields(repository=True)).path)
        self.assertEqual(
            project_exact(m, DetailFields(path=True)).path, "src/a.py"
        )
        self.assertEqual(
            project_exact(m, DetailFields(commit=True)).commit, "abc"
        )
        self.assertEqual(
            project_exact(m, DetailFields(snippet=True)).snippet,
            "line with hit",
        )


if __name__ == "__main__":
    unittest.main()
