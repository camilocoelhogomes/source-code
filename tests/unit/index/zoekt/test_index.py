"""Testes unitários — ZoektExactCodeIndex (T10) com transports fake."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.index import ZoektExactCodeIndex
from github_rag.index.zoekt.models import ExactSearchQuery
from github_rag.index.zoekt.runner import ZoektIndexRunResult

from tests.unit.index.zoekt.helpers import (
    COMMIT,
    REPO,
    SECRET_TOKEN,
    RecordingIndexRunner,
    RecordingSearchTransport,
    make_file,
    zoekt_file_matches_payload,
)


class TestZoektExactCodeIndexIndex(unittest.TestCase):
    def _build(
        self,
        *,
        search: RecordingSearchTransport | None = None,
        indexer: RecordingIndexRunner | None = None,
        index_dir: str | Path | None = None,
    ) -> tuple[ZoektExactCodeIndex, RecordingSearchTransport, RecordingIndexRunner, Path]:
        tmp = Path(tempfile.mkdtemp())
        search = search or RecordingSearchTransport()
        indexer = indexer or RecordingIndexRunner()
        dest = Path(index_dir) if index_dir is not None else tmp / "index"
        dest.mkdir(parents=True, exist_ok=True)
        adapter = ZoektExactCodeIndex(
            search=search,
            indexer=indexer,
            index_dir=dest,
            index_bin="zoekt-index",
        )
        return adapter, search, indexer, dest

    def test_index_materializes_tree_and_calls_runner(self) -> None:
        adapter, _, indexer, index_dir = self._build()
        adapter.index(
            REPO,
            COMMIT,
            (make_file("src/main.py", b"def authenticate():\n"),),
        )

        self.assertEqual(len(indexer.calls), 1)
        argv = list(indexer.calls[0])
        self.assertEqual(argv[0], "zoekt-index")
        self.assertIn("-index", argv)
        idx_flag = argv.index("-index")
        self.assertEqual(Path(argv[idx_flag + 1]), index_dir)
        self.assertTrue(indexer.capture_tree)
        self.assertIn("src/main.py", indexer.capture_tree[0])
        self.assertEqual(
            indexer.capture_tree[0]["src/main.py"],
            b"def authenticate():\n",
        )

    def test_index_writes_file_content_into_tree(self) -> None:
        adapter, _, indexer, _ = self._build()
        content = b"UNIQUE_BYTES_\xff\xfe"
        adapter.index(REPO, COMMIT, (make_file("lib/x.py", content),))
        self.assertEqual(indexer.capture_tree[0]["lib/x.py"], content)

    def test_runner_nonzero_exit_raises_typed_index_error(self) -> None:
        indexer = RecordingIndexRunner(
            result=ZoektIndexRunResult(
                returncode=1,
                stdout="",
                stderr="index failed",
            )
        )
        adapter, _, _, _ = self._build(indexer=indexer)
        with self.assertRaises(ExactCodeIndexError) as ctx:
            adapter.index(REPO, COMMIT, (make_file("a.py", b"x\n"),))
        self.assertEqual(ctx.exception.operation, "index")
        self.assertEqual(ctx.exception.repository, REPO)
        self.assertEqual(ctx.exception.commit, COMMIT)
        blob = str(ctx.exception) + repr(ctx.exception)
        self.assertNotIn(SECRET_TOKEN, blob)

    def test_empty_files_is_noop_runner_not_called(self) -> None:
        adapter, _, indexer, _ = self._build()
        adapter.index(REPO, COMMIT, ())
        self.assertEqual(indexer.calls, [])

    def test_file_to_index_mismatch_raises_without_calling_runner(self) -> None:
        adapter, _, indexer, _ = self._build()
        with self.assertRaises(ExactCodeIndexError) as ctx:
            adapter.index(
                REPO,
                COMMIT,
                (make_file("a.py", b"x\n", commit="other-sha"),),
            )
        self.assertEqual(ctx.exception.operation, "index")
        self.assertEqual(indexer.calls, [])


class TestZoektExactCodeIndexSearch(unittest.TestCase):
    def _adapter_with_indexed_commit(
        self,
        *,
        response: dict | None = None,
        search_error: BaseException | None = None,
    ) -> tuple[ZoektExactCodeIndex, RecordingSearchTransport, RecordingIndexRunner]:
        search = RecordingSearchTransport(
            response=response or zoekt_file_matches_payload(),
            error=search_error,
        )
        indexer = RecordingIndexRunner()
        dest = Path(tempfile.mkdtemp()) / "index"
        dest.mkdir(parents=True)
        adapter = ZoektExactCodeIndex(
            search=search,
            indexer=indexer,
            index_dir=dest,
        )
        adapter.index(
            REPO,
            COMMIT,
            (make_file("src/main.py", b"def authenticate():\n"),),
        )
        return adapter, search, indexer

    def test_search_maps_file_matches_to_exact_match(self) -> None:
        adapter, search, _ = self._adapter_with_indexed_commit(
            response=zoekt_file_matches_payload(
                path="src/main.py",
                lines=((12, "def authenticate():"),),
            )
        )
        matches = adapter.search(ExactSearchQuery(pattern="def authenticate"))
        self.assertGreaterEqual(len(matches), 1)
        hit = matches[0]
        self.assertEqual(hit.repository, REPO)
        self.assertEqual(hit.path, "src/main.py")
        self.assertIn("authenticate", hit.snippet)
        self.assertTrue(search.calls)

    def test_empty_pattern_returns_empty_without_transport(self) -> None:
        adapter, search, _ = self._adapter_with_indexed_commit()
        matches = adapter.search(ExactSearchQuery(pattern=""))
        self.assertEqual(list(matches), [])
        self.assertEqual(search.calls, [])

    def test_literal_escape_quotes_metacharacters(self) -> None:
        adapter, search, _ = self._adapter_with_indexed_commit(
            response={"Result": {"FileMatches": []}}
        )
        adapter.search(ExactSearchQuery(pattern="foo.bar*baz:qux"))
        self.assertEqual(len(search.calls), 1)
        q = search.calls[0]["Q"]
        self.assertIsInstance(q, str)
        # Escape literal oficial: preferência content:"…" — metacaracteres não
        # devem aparecer como regex cru sem quoting.
        self.assertTrue(
            'content:"' in q or "content:'" in q or q.startswith('"') or "\\." in q,
            msg=f"Q não parece literal escapado: {q!r}",
        )
        # Padrão completo deve estar presente de alguma forma escapada/quoted
        self.assertTrue(
            "foo.bar" in q or "foo\\.bar" in q,
            msg=q,
        )

    def test_filters_repo_and_file_in_query_string(self) -> None:
        adapter, search, _ = self._adapter_with_indexed_commit(
            response={"Result": {"FileMatches": []}}
        )
        adapter.search(
            ExactSearchQuery(
                pattern="needle",
                repository=REPO,
                path_prefix="src/",
            )
        )
        q = search.calls[0]["Q"]
        self.assertIn("repo:", q)
        self.assertIn(REPO, q)
        self.assertTrue("file:" in q or "src/" in q)

    def test_opts_num_context_lines(self) -> None:
        adapter, search, _ = self._adapter_with_indexed_commit(
            response={"Result": {"FileMatches": []}}
        )
        adapter.search(ExactSearchQuery(pattern="x", context_lines=5))
        opts = search.calls[0]["Opts"]
        self.assertEqual(opts["NumContextLines"], 5)

    def test_search_results_sorted_deterministically(self) -> None:
        payload = {
            "Result": {
                "FileMatches": [
                    {
                        "FileName": "z.py",
                        "Repository": REPO,
                        "Matches": [
                            {
                                "LineNumber": 2,
                                "Fragments": [
                                    {"Pre": "", "Match": "needle", "Post": ""}
                                ],
                            }
                        ],
                    },
                    {
                        "FileName": "a.py",
                        "Repository": REPO,
                        "Matches": [
                            {
                                "LineNumber": 1,
                                "Fragments": [
                                    {"Pre": "", "Match": "needle", "Post": ""}
                                ],
                            }
                        ],
                    },
                ]
            }
        }
        adapter, _, _ = self._adapter_with_indexed_commit(response=payload)
        hits = list(adapter.search(ExactSearchQuery(pattern="needle")))
        self.assertGreaterEqual(len(hits), 2)
        keys = [(h.repository, h.path, h.line_number or 0, h.snippet) for h in hits]
        self.assertEqual(keys, sorted(keys))

    def test_transport_failure_wrapped_as_search_error(self) -> None:
        adapter, _, _ = self._adapter_with_indexed_commit(
            search_error=OSError("connection refused")
        )
        with self.assertRaises(ExactCodeIndexError) as ctx:
            adapter.search(ExactSearchQuery(pattern="authenticate"))
        self.assertEqual(ctx.exception.operation, "search")
        self.assertNotIn(SECRET_TOKEN, str(ctx.exception) + repr(ctx.exception))

    def test_commit_filled_from_internal_map_never_empty(self) -> None:
        # Resposta sem SHA — adaptador preenche via mapa repository→last_commit
        payload = zoekt_file_matches_payload(path="src/main.py")
        adapter, _, _ = self._adapter_with_indexed_commit(response=payload)
        hits = adapter.search(ExactSearchQuery(pattern="authenticate"))
        self.assertTrue(hits)
        self.assertEqual(hits[0].commit, COMMIT)
        self.assertTrue(hits[0].commit)


class TestZoektExactCodeIndexDelete(unittest.TestCase):
    def test_delete_repository_is_idempotent_noop_when_absent(self) -> None:
        index_dir = Path(tempfile.mkdtemp()) / "index"
        index_dir.mkdir(parents=True)
        adapter = ZoektExactCodeIndex(
            search=RecordingSearchTransport(),
            indexer=RecordingIndexRunner(),
            index_dir=index_dir,
        )
        adapter.delete_repository("acme/never-indexed")
        adapter.delete_repository("acme/never-indexed")

    def test_delete_repository_after_index_clears_repo_association(self) -> None:
        index_dir = Path(tempfile.mkdtemp()) / "index"
        index_dir.mkdir(parents=True)
        search = RecordingSearchTransport(
            response=zoekt_file_matches_payload(path="a.py", lines=((1, "MARKER"),))
        )
        indexer = RecordingIndexRunner()
        adapter = ZoektExactCodeIndex(
            search=search,
            indexer=indexer,
            index_dir=index_dir,
        )
        adapter.index(REPO, COMMIT, (make_file("a.py", b"MARKER\n"),))
        self.assertTrue(indexer.calls)
        # Planta artefato associado ao nome do repo (I-T10-012: associação por nome,
        # sem parse de shard). Sem isso o assert de leftovers seria vácuo com runner fake.
        repo_slug = REPO.replace("/", "_")
        sentinel = index_dir / f"{repo_slug}_v16.00000.zoekt"
        sentinel.write_bytes(b"fake-shard")
        self.assertTrue(sentinel.exists())
        adapter.delete_repository(REPO)
        self.assertFalse(sentinel.exists())
        leftovers = [
            p
            for p in index_dir.iterdir()
            if repo_slug in p.name or "acme_api" in p.name
        ]
        self.assertEqual(leftovers, [])
        # 2ª chamada permanece no-op sucesso
        adapter.delete_repository(REPO)

    def test_delete_io_failure_raises_typed_error(self) -> None:
        # index_dir como arquivo (não diretório) força falha de I/O na limpeza
        bad = Path(tempfile.mkdtemp()) / "not-a-dir"
        bad.write_text("x", encoding="utf-8")
        adapter = ZoektExactCodeIndex(
            search=RecordingSearchTransport(),
            indexer=RecordingIndexRunner(),
            index_dir=bad,
        )
        with self.assertRaises(ExactCodeIndexError) as ctx:
            adapter.delete_repository(REPO)
        self.assertEqual(ctx.exception.operation, "delete")


class TestZoektExactCodeIndexFromEnviron(unittest.TestCase):
    def test_from_environ_reads_zoekt_envs(self) -> None:
        index_dir = Path(tempfile.mkdtemp()) / "index"
        index_dir.mkdir(parents=True)
        env = {
            "ZOEKT_URL": "http://zoekt-host:6070",
            "ZOEKT_INDEX_DIR": str(index_dir),
            "ZOEKT_INDEX_BIN": "custom-zoekt-index",
            "ZOEKT_GIT_INDEX_BIN": "custom-zoekt-git-index",
        }
        search = RecordingSearchTransport(response={"Result": {"FileMatches": []}})
        indexer = RecordingIndexRunner()
        adapter = ZoektExactCodeIndex.from_environ(
            env,
            search=search,
            indexer=indexer,
        )
        self.assertIsInstance(adapter, ZoektExactCodeIndex)
        adapter.index(REPO, COMMIT, (make_file("a.py", b"x\n"),))
        self.assertTrue(indexer.calls)
        argv = list(indexer.calls[0])
        self.assertEqual(argv[0], "custom-zoekt-index")
        self.assertIn("-index", argv)
        self.assertEqual(Path(argv[argv.index("-index") + 1]), index_dir)

    def test_from_environ_defaults_index_bin_and_url(self) -> None:
        """Sem overrides: index_bin default + HttpZoektSearchTransport usa ZOEKT_URL default."""
        import io
        import json
        from unittest import mock

        index_dir = Path(tempfile.mkdtemp()) / "index"
        index_dir.mkdir(parents=True)
        indexer = RecordingIndexRunner()
        adapter = ZoektExactCodeIndex.from_environ(
            {"ZOEKT_INDEX_DIR": str(index_dir)},
            indexer=indexer,
        )
        adapter.index(REPO, COMMIT, (make_file("a.py", b"x\n"),))
        self.assertEqual(indexer.calls[0][0], "zoekt-index")

        raw = json.dumps({"Result": {"FileMatches": []}}).encode("utf-8")
        cm = mock.MagicMock()
        cm.__enter__.return_value = io.BytesIO(raw)
        cm.__exit__.return_value = False
        with mock.patch("urllib.request.urlopen", return_value=cm) as urlopen:
            adapter.search(ExactSearchQuery(pattern="x"))
        req = urlopen.call_args.args[0]
        full_url = getattr(req, "full_url", str(req))
        self.assertIn("127.0.0.1:6070", str(full_url))
        self.assertTrue(str(full_url).rstrip("/").endswith("/api/search"))


if __name__ == "__main__":
    unittest.main()
