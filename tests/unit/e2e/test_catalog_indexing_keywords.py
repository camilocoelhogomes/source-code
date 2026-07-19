"""Unit — CatalogIndexingKeywords helpers (T24 / UT-T24-*).

Importa de ``e2e/robot/libraries/CatalogIndexingKeywords.py`` via sys.path
(interfaces I-T24-003). RED até o Developer implementar o módulo.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tests.unit.e2e.helpers import REPO_ROOT

_LIBS = REPO_ROOT / "e2e" / "robot" / "libraries"
if str(_LIBS) not in sys.path:
    sys.path.insert(0, str(_LIBS))


def _import_cik():
    import CatalogIndexingKeywords as cik  # noqa: PLC0415

    return cik


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Contratos canônicos interfaces.md §4 (I-T24-009) — unitários não dependem
# de o módulo exportar os nomes; o conteúdo da árvore/mapa deve materializá-los.
_CANONICAL_MARKERS = {
    "MARKER_INCLUDE_JAVA": "T24_INCLUDE_JAVA_A1B2",
    "MARKER_INCLUDE_PY": "T24_INCLUDE_PY_C3D4",
    "MARKER_INCLUDE_MD": "T24_INCLUDE_MD_E5F6",
    "MARKER_EXCLUDE_CSV": "T24_EXCLUDE_CSV_G7H8",
    "MARKER_EXCLUDE_GITIGNORE": "T24_EXCLUDE_GITIGNORE_I9J0",
    "MARKER_MAIN_ONLY": "MAIN_ONLY_MARKER",
    "MARKER_OTHER_BRANCH": "OTHER_BRANCH_MARKER",
    "MARKER_UNCOMMITTED": "UNCOMMITTED_MARKER",
}


def _git_init_main(repo: Path) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "e2e",
        "GIT_AUTHOR_EMAIL": "e2e@example.com",
        "GIT_COMMITTER_NAME": "e2e",
        "GIT_COMMITTER_EMAIL": "e2e@example.com",
    }
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    for cmd in (
        ["git", "init", "-b", "main"],
        ["git", "add", "README.md"],
        ["git", "commit", "-m", "init"],
    ):
        completed = subprocess.run(
            cmd,
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def _git_rev_parse(repo: Path, ref: str = "HEAD") -> str:
    completed = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _list_repos_payload(
    *,
    repository_id: str = "42",
    repo_key: str = "sample-local",
    last_processed: str | None = "a" * 40,
    current_main: str | None = "b" * 40,
) -> str:
    return json.dumps(
        {
            "repos": [
                {
                    "repository_id": repository_id,
                    "repo_key": repo_key,
                    "origin": "local",
                    "state": "up_to_date",
                    "last_processed_commit": last_processed,
                    "current_main_commit": current_main,
                },
                {
                    "repository_id": "99",
                    "repo_key": "other-repo",
                    "origin": "github",
                    "state": "not_indexed",
                    "last_processed_commit": "",
                    "current_main_commit": "",
                },
            ]
        }
    )


class TestCronExpressionFiringSoonUtc(unittest.TestCase):
    """UT-T24-C01..C06."""

    def test_c01_injected_now_five_fields_absolute_minute(self) -> None:
        cik = _import_cik()
        now = datetime(2026, 7, 19, 12, 34, 10, tzinfo=timezone.utc)
        expr = cik.cron_expression_firing_soon_utc(now)
        parts = expr.split()
        self.assertEqual(len(parts), 5, expr)
        minute = int(parts[0])
        hour = int(parts[1])
        self.assertIn(minute, (34, 35))
        self.assertEqual(hour, 12)
        self.assertEqual(int(parts[2]), 19)
        self.assertEqual(int(parts[3]), 7)

    def test_c02_minute_59_wraps_hour(self) -> None:
        cik = _import_cik()
        now = datetime(2026, 7, 19, 14, 59, 40, tzinfo=timezone.utc)
        expr = cik.cron_expression_firing_soon_utc(now)
        parts = expr.split()
        self.assertEqual(len(parts), 5, expr)
        minute = int(parts[0])
        hour = int(parts[1])
        # current minute 59 or next → 0 @ 15
        self.assertTrue(
            (minute == 59 and hour == 14) or (minute == 0 and hour == 15),
            expr,
        )

    def test_c03_utc_2359_wraps_day(self) -> None:
        cik = _import_cik()
        now = datetime(2026, 7, 19, 23, 59, 50, tzinfo=timezone.utc)
        expr = cik.cron_expression_firing_soon_utc(now)
        parts = expr.split()
        self.assertEqual(len(parts), 5, expr)
        minute = int(parts[0])
        hour = int(parts[1])
        day = int(parts[2])
        month = int(parts[3])
        if minute == 0 and hour == 0:
            self.assertEqual(day, 20)
            self.assertEqual(month, 7)
        else:
            self.assertEqual(minute, 59)
            self.assertEqual(hour, 23)
            self.assertEqual(day, 19)

    def test_c04_format_five_numeric_fields(self) -> None:
        cik = _import_cik()
        now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        expr = cik.cron_expression_firing_soon_utc(now)
        parts = expr.split()
        self.assertEqual(len(parts), 5, expr)
        for token in parts:
            self.assertTrue(
                token.isdigit() or token == "*",
                f"token inválido {token!r} em {expr!r}",
            )
        # preferência interfaces: minuto absoluto
        self.assertTrue(parts[0].isdigit(), expr)

    def test_c05_none_uses_utc_not_naive_local(self) -> None:
        cik = _import_cik()
        fixed = datetime(2026, 3, 15, 8, 7, 0, tzinfo=timezone.utc)

        class _FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                assert tz is timezone.utc, f"esperado timezone.utc, got {tz!r}"
                return fixed

        with mock.patch("CatalogIndexingKeywords.datetime", _FixedDateTime):
            expr = cik.cron_expression_firing_soon_utc(None)
        parts = expr.split()
        self.assertEqual(len(parts), 5, expr)
        minute = int(parts[0])
        self.assertIn(minute, (7, 8))
        self.assertEqual(int(parts[1]), 8)

    def test_c06_minute_zero_boundary(self) -> None:
        cik = _import_cik()
        now = datetime(2026, 7, 19, 10, 0, 1, tzinfo=timezone.utc)
        expr = cik.cron_expression_firing_soon_utc(now)
        parts = expr.split()
        minute = int(parts[0])
        self.assertGreaterEqual(minute, 0)
        self.assertLessEqual(minute, 59)
        self.assertIn(minute, (0, 1))


class TestParseMcpListReposCommits(unittest.TestCase):
    """UT-T24-P01..P08."""

    def test_p01_happy_by_repository_id(self) -> None:
        cik = _import_cik()
        raw = _list_repos_payload(
            last_processed="1" * 40,
            current_main="2" * 40,
        )
        result = cik.parse_mcp_list_repos_commits(raw, repo_id="42")
        self.assertEqual(result["last_processed_commit"], "1" * 40)
        self.assertEqual(result["current_main_commit"], "2" * 40)

    def test_p02_happy_by_repo_identifier(self) -> None:
        cik = _import_cik()
        raw = _list_repos_payload()
        result = cik.parse_mcp_list_repos_commits(
            raw, repo_identifier="sample-local"
        )
        self.assertIn("last_processed_commit", result)
        self.assertIn("current_main_commit", result)
        self.assertEqual(len(result["last_processed_commit"]), 40)

    def test_p03_repo_absent_raises(self) -> None:
        cik = _import_cik()
        raw = _list_repos_payload()
        with self.assertRaises((AssertionError, ValueError, KeyError)):
            cik.parse_mcp_list_repos_commits(raw, repo_id="missing")

    def test_p04_invalid_json_raises(self) -> None:
        cik = _import_cik()
        with self.assertRaises((json.JSONDecodeError, AssertionError, ValueError)):
            cik.parse_mcp_list_repos_commits(
                "not-json{{{", repo_id="42"
            )

    def test_p05_null_commit_fields(self) -> None:
        cik = _import_cik()
        raw = _list_repos_payload(last_processed=None, current_main=None)
        result = cik.parse_mcp_list_repos_commits(raw, repo_id="42")
        self.assertIsInstance(result["last_processed_commit"], str)
        self.assertIsInstance(result["current_main_commit"], str)

    def test_p06_nested_content_envelope(self) -> None:
        cik = _import_cik()
        inner = {
            "repos": [
                {
                    "repository_id": "7",
                    "repo_key": "nested",
                    "last_processed_commit": "c" * 40,
                    "current_main_commit": "d" * 40,
                }
            ]
        }
        # mcp_call_tool may dump structured or content-list wrappers
        wrapped = json.dumps([inner])
        result = cik.parse_mcp_list_repos_commits(
            wrapped, repo_identifier="nested"
        )
        self.assertEqual(result["last_processed_commit"], "c" * 40)
        self.assertEqual(result["current_main_commit"], "d" * 40)

    def test_p07_empty_repos_list(self) -> None:
        cik = _import_cik()
        with self.assertRaises((AssertionError, ValueError, KeyError)):
            cik.parse_mcp_list_repos_commits(
                json.dumps({"repos": []}), repo_id="1"
            )

    def test_p08_missing_selectors(self) -> None:
        cik = _import_cik()
        with self.assertRaises((AssertionError, ValueError, TypeError)):
            cik.parse_mcp_list_repos_commits(_list_repos_payload())


class TestHostCommitOnMain(unittest.TestCase):
    """UT-T24-H01..H04."""

    def test_h01_returns_sha_and_moves_tip(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            before = _git_rev_parse(repo)
            sha = cik.host_commit_on_main(repo)
            self.assertRegex(sha, _SHA_RE)
            after = _git_rev_parse(repo)
            self.assertEqual(sha, after)
            self.assertNotEqual(before, after)

    def test_h02_second_commit_distinct_sha(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            sha_a = cik.host_commit_on_main(
                repo, content="A", message="bump-a"
            )
            sha_b = cik.host_commit_on_main(
                repo, content="B", message="bump-b"
            )
            self.assertNotEqual(sha_a, sha_b)
            self.assertRegex(sha_b, _SHA_RE)

    def test_h03_no_git_raises(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp) / "not-a-repo"
            bare.mkdir()
            with self.assertRaises(Exception) as ctx:
                cik.host_commit_on_main(bare)
            msg = str(ctx.exception).lower()
            self.assertNotIn("ghp_", msg)

    def test_h04_custom_relative_path_created(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            cik.host_commit_on_main(
                repo,
                relative_path="t24_custom.txt",
                content="unique-payload",
                message="t24 custom",
            )
            self.assertTrue((repo / "t24_custom.txt").is_file())
            self.assertIn(
                "unique-payload",
                (repo / "t24_custom.txt").read_text(encoding="utf-8"),
            )


class TestPrepareEligibilityTree(unittest.TestCase):
    """UT-T24-E01..E04."""

    def test_e01_materializes_include_exclude_paths(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            markers = cik.prepare_eligibility_tree(repo)
            self.assertIsInstance(markers, dict)
            self.assertTrue(markers, "mapa de markers não pode ser vazio")
            self.assertTrue(
                (repo / "src" / "Hello.java").is_file()
                or (repo / "src" / "app.py").is_file()
            )
            self.assertTrue((repo / "docs" / "notes.md").is_file())
            self.assertTrue((repo / "data" / "report.csv").is_file())
            self.assertTrue((repo / "img" / "photo.png").is_file())
            self.assertGreater((repo / "img" / "photo.png").stat().st_size, 0)
            self.assertTrue((repo / ".gitignore").is_file())
            self.assertTrue(
                (repo / "ignored_dir" / "secret_marker.txt").is_file()
            )
            java = repo / "src" / "Hello.java"
            py = repo / "src" / "app.py"
            include_code = ""
            if java.is_file():
                include_code = java.read_text(encoding="utf-8")
            if py.is_file():
                include_code += py.read_text(encoding="utf-8")
            md = (repo / "docs" / "notes.md").read_text(encoding="utf-8")
            csv = (repo / "data" / "report.csv").read_text(encoding="utf-8")
            ignored = (repo / "ignored_dir" / "secret_marker.txt").read_text(
                encoding="utf-8"
            )
            self.assertIn(_CANONICAL_MARKERS["MARKER_INCLUDE_MD"], md)
            self.assertIn(_CANONICAL_MARKERS["MARKER_EXCLUDE_CSV"], csv)
            self.assertIn(
                _CANONICAL_MARKERS["MARKER_EXCLUDE_GITIGNORE"], ignored
            )
            self.assertTrue(
                _CANONICAL_MARKERS["MARKER_INCLUDE_JAVA"] in include_code
                or _CANONICAL_MARKERS["MARKER_INCLUDE_PY"] in include_code,
                "include Java/Python sem token canônico",
            )
            returned = set(str(v) for v in markers.values()) | set(
                str(k) for k in markers.keys()
            )
            for key in (
                "MARKER_INCLUDE_MD",
                "MARKER_EXCLUDE_CSV",
                "MARKER_EXCLUDE_GITIGNORE",
            ):
                token = _CANONICAL_MARKERS[key]
                self.assertTrue(
                    token in returned
                    or any(token in str(v) for v in markers.values()),
                    f"{key}={token} ausente em {markers}",
                )

    def test_e02_idempotent_second_call(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            m1 = cik.prepare_eligibility_tree(repo)
            tip1 = _git_rev_parse(repo)
            m2 = cik.prepare_eligibility_tree(repo)
            tip2 = _git_rev_parse(repo)
            self.assertEqual(m1, m2)
            # may or may not create extra commit if already correct
            self.assertTrue((repo / "docs" / "notes.md").is_file())
            self.assertTrue(tip1 and tip2)

    def test_e03_gitignore_lists_ignored_dir(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            cik.prepare_eligibility_tree(repo)
            gi = (repo / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("ignored_dir", gi)

    def test_e04_no_git_raises(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp) / "bare"
            bare.mkdir()
            with self.assertRaises(Exception):
                cik.prepare_eligibility_tree(bare)


class TestPrepareMainOnlyBranches(unittest.TestCase):
    """UT-T24-M01..M04."""

    def test_m01_head_main_other_exists_uncommitted(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            markers = cik.prepare_main_only_branches(repo)
            self.assertIsInstance(markers, dict)
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(branch.stdout.strip(), "main")
            branches = subprocess.run(
                ["git", "branch", "--list", "other"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertIn("other", branches.stdout)
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertTrue(status.stdout.strip(), "esperado uncommitted no WT")
            # uncommitted must not be staged-only commit
            self.assertFalse(
                status.stdout.strip().startswith("A "),
                status.stdout,
            )

    def test_m02_markers_main_other_uncommitted(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            cik.prepare_main_only_branches(repo)
            main_marker = _CANONICAL_MARKERS["MARKER_MAIN_ONLY"]
            other_marker = _CANONICAL_MARKERS["MARKER_OTHER_BRANCH"]
            uncommitted_marker = _CANONICAL_MARKERS["MARKER_UNCOMMITTED"]
            main_blob = subprocess.run(
                ["git", "grep", "-n", main_marker, "main"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(main_blob.returncode, 0, main_blob.stderr)
            other_blob = subprocess.run(
                ["git", "grep", "-n", other_marker, "other"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(other_blob.returncode, 0, other_blob.stderr)
            # other marker must NOT be on main tip tree
            main_other = subprocess.run(
                ["git", "grep", "-n", other_marker, "main"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(main_other.returncode, 0)
            wt = "\n".join(
                p.read_text(encoding="utf-8", errors="replace")
                for p in repo.rglob("*")
                if p.is_file() and ".git" not in p.parts
            )
            self.assertIn(uncommitted_marker, wt)

    def test_m03_idempotent_rerun(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample-local"
            repo.mkdir()
            _git_init_main(repo)
            cik.prepare_main_only_branches(repo)
            cik.prepare_main_only_branches(repo)
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(branch.stdout.strip(), "main")
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertTrue(status.stdout.strip())

    def test_m04_no_git_raises(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp) / "bare"
            bare.mkdir()
            with self.assertRaises(Exception):
                cik.prepare_main_only_branches(bare)


class TestResolveSampleLocalDir(unittest.TestCase):
    """UT-T24-R01..R02."""

    def test_r01_with_repos_root(self) -> None:
        cik = _import_cik()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved = cik.resolve_sample_local_dir(root)
            self.assertEqual(resolved, (root / "sample-local").resolve())

    def test_r02_default_under_e2e_fixtures(self) -> None:
        cik = _import_cik()
        resolved = cik.resolve_sample_local_dir(None)
        self.assertEqual(resolved.name, "sample-local")
        self.assertTrue(
            "fixtures" in resolved.parts or "repos" in resolved.parts
            or resolved.is_absolute()
        )


if __name__ == "__main__":
    unittest.main()
