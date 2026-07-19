"""Robot keywords helpers — catalog indexing integral (T24).

Responsabilidade
    Cron UTC, parse MCP list_repos commits, mutação Git no host e
    prepare idempotente da árvore BDD-006/017.

Motivo da separação
    Operações frágeis em Robot puro (R-T24-01); testável com pytest;
    não é domínio ETL (I-T24-003).
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SAMPLE_LOCAL_REL = "sample-local"

MARKER_INCLUDE_JAVA = "T24_INCLUDE_JAVA_A1B2"
MARKER_INCLUDE_PY = "T24_INCLUDE_PY_C3D4"
MARKER_INCLUDE_MD = "T24_INCLUDE_MD_E5F6"
MARKER_EXCLUDE_CSV = "T24_EXCLUDE_CSV_G7H8"
MARKER_EXCLUDE_GITIGNORE = "T24_EXCLUDE_GITIGNORE_I9J0"
MARKER_MAIN_ONLY = "MAIN_ONLY_MARKER"
MARKER_OTHER_BRANCH = "OTHER_BRANCH_MARKER"
MARKER_UNCOMMITTED = "UNCOMMITTED_MARKER"
OTHER_BRANCH_NAME = "other"

SCHEDULER_TICK_TIMEOUT_SECONDS = 120
SCHEDULER_TICK_POLL_SECONDS = 5

# Minimal valid 1x1 PNG (IHDR+IDAT+IEND).
_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c63f80f00000101000518d84e0000000049454e44ae426082"
)

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "e2e",
    "GIT_AUTHOR_EMAIL": "e2e@example.com",
    "GIT_COMMITTER_NAME": "e2e",
    "GIT_COMMITTER_EMAIL": "e2e@example.com",
}


def _git_env() -> dict[str, str]:
    return {**os.environ, **_GIT_ENV}


def _run_git(fixture_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=fixture_dir,
        env=_git_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def _require_git(fixture_dir: Path) -> None:
    if not (fixture_dir / ".git").is_dir():
        raise RuntimeError(f"not a git repository: {fixture_dir}")


def _rev_parse(fixture_dir: Path, ref: str = "HEAD") -> str:
    completed = _run_git(fixture_dir, "rev-parse", ref)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or f"git rev-parse {ref} failed")
    return completed.stdout.strip()


def _commit_if_staged(fixture_dir: Path, message: str) -> None:
    status = _run_git(fixture_dir, "status", "--porcelain")
    if status.returncode != 0:
        raise RuntimeError(status.stderr or "git status failed")
    if not status.stdout.strip():
        return
    completed = _run_git(fixture_dir, "commit", "-m", message)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or f"git commit failed: {message}")


def cron_expression_firing_soon_utc(now: datetime | None = None) -> str:
    """Calcula expressão cron de 5 campos que dispara na janela do teste (UTC).

    Responsabilidade
        Produzir cron reproduzível (minuto corrente ou próximo minuto UTC)
        para PUT /api/scheduler/cron sem esperar 24h.

    Motivo da separação
        Relógio/fuso em Robot puro é flaky (R-T24-01); Python fixa UTC.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    # Próximo minuto absoluto — evita miss se o minuto corrente já passou.
    target = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    return (
        f"{target.minute} {target.hour} {target.day} {target.month} *"
    )


def _unwrap_list_repos_payload(data: Any) -> dict[str, Any]:
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "repos" in item:
                return item
            if isinstance(item, str):
                try:
                    parsed = json.loads(item)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict) and "repos" in parsed:
                    return parsed
        raise AssertionError("MCP list_repos: envelope list sem 'repos'")
    if isinstance(data, dict):
        if "repos" in data:
            return data
        # structured wrappers comuns
        for key in ("result", "structuredContent", "data"):
            inner = data.get(key)
            if isinstance(inner, dict) and "repos" in inner:
                return inner
            if isinstance(inner, list):
                return _unwrap_list_repos_payload(inner)
        raise AssertionError("MCP list_repos: shape inválido sem 'repos'")
    raise AssertionError(f"MCP list_repos: tipo inesperado {type(data).__name__}")


def parse_mcp_list_repos_commits(
    list_repos_json: str,
    *,
    repo_id: str | None = None,
    repo_identifier: str | None = None,
) -> dict[str, str]:
    """Extrai last_processed_commit e current_main_commit de um repo.

    Responsabilidade
        Normalizar o JSON retornado por mcp_call_tool('list_repos') e
        localizar o repo alvo.

    Motivo da separação
        Formato MCP (structured/content) não deve ser parseado ad hoc
        em cada caso Robot; um parser único evita asserts fracos.
    """
    if not repo_id and not repo_identifier:
        raise ValueError("repo_id or repo_identifier is required")

    data = json.loads(list_repos_json)
    payload = _unwrap_list_repos_payload(data)
    repos = payload.get("repos")
    if not isinstance(repos, list) or not repos:
        raise AssertionError("MCP list_repos: repos ausente ou vazio")

    found: dict[str, Any] | None = None
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        rid = str(repo.get("repository_id", ""))
        key = str(
            repo.get("repo_key")
            or repo.get("repo_identifier")
            or repo.get("full_name")
            or ""
        )
        if repo_id is not None and rid == str(repo_id):
            found = repo
            break
        if repo_identifier is not None and key == str(repo_identifier):
            found = repo
            break

    if found is None:
        raise AssertionError(
            f"MCP list_repos: repo não encontrado "
            f"(repo_id={repo_id!r}, repo_identifier={repo_identifier!r})"
        )

    def _as_str(value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    return {
        "last_processed_commit": _as_str(found.get("last_processed_commit")),
        "current_main_commit": _as_str(found.get("current_main_commit")),
        "repository_id": _as_str(found.get("repository_id")),
        "repo_key": _as_str(
            found.get("repo_key") or found.get("repo_identifier") or ""
        ),
    }


def host_commit_on_main(
    fixture_dir: str | Path,
    *,
    relative_path: str = "t24_bump.txt",
    content: str | None = None,
    message: str | None = None,
) -> str:
    """Cria commit na main do fixture no host; retorna SHA tip.

    Responsabilidade
        Mutar tip da main para deixar o catálogo desatualizado (003/005).

    Motivo da separação
        Git no host (D-T24-009); subprocess + author env ficam fora do .robot.
    """
    root = Path(fixture_dir)
    _require_git(root)

    checkout = _run_git(root, "checkout", "main")
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stderr or "git checkout main failed")

    token = uuid.uuid4().hex[:12]
    payload = content if content is not None else f"t24-bump-{token}\n"
    commit_msg = message if message is not None else f"t24 bump {token}"

    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")

    add = _run_git(root, "add", relative_path)
    if add.returncode != 0:
        raise RuntimeError(add.stderr or f"git add {relative_path} failed")

    commit = _run_git(root, "commit", "-m", commit_msg)
    if commit.returncode != 0:
        raise RuntimeError(commit.stderr or "git commit failed")

    return _rev_parse(root, "HEAD")


def _eligibility_markers() -> dict[str, str]:
    return {
        "MARKER_INCLUDE_JAVA": MARKER_INCLUDE_JAVA,
        "MARKER_INCLUDE_PY": MARKER_INCLUDE_PY,
        "MARKER_INCLUDE_MD": MARKER_INCLUDE_MD,
        "MARKER_EXCLUDE_CSV": MARKER_EXCLUDE_CSV,
        "MARKER_EXCLUDE_GITIGNORE": MARKER_EXCLUDE_GITIGNORE,
    }


def _write_eligibility_files(fixture_dir: Path) -> bool:
    """Escreve árvore BDD-006. Retorna True se algum arquivo mudou."""
    specs: list[tuple[Path, str | bytes, bool]] = [
        (
            fixture_dir / "src" / "Hello.java",
            (
                f"// {MARKER_INCLUDE_JAVA}\n"
                "public class Hello {\n"
                "  public static void main(String[] args) {}\n"
                "}\n"
            ),
            False,
        ),
        (
            fixture_dir / "src" / "app.py",
            f"# {MARKER_INCLUDE_PY}\ndef greet():\n    return 'ok'\n",
            False,
        ),
        (
            fixture_dir / "docs" / "notes.md",
            f"# Notes\n\n{MARKER_INCLUDE_MD}\n",
            False,
        ),
        (
            fixture_dir / "data" / "report.csv",
            f"col1,col2\n{MARKER_EXCLUDE_CSV},1\n",
            False,
        ),
        (fixture_dir / "img" / "photo.png", _MINIMAL_PNG, True),
        (fixture_dir / ".gitignore", "ignored_dir/\n", False),
        (
            fixture_dir / "ignored_dir" / "secret_marker.txt",
            f"{MARKER_EXCLUDE_GITIGNORE}\n",
            False,
        ),
        (
            fixture_dir / "main_only.txt",
            f"{MARKER_MAIN_ONLY}\n",
            False,
        ),
    ]
    changed = False
    for path, content, is_binary in specs:
        path.parent.mkdir(parents=True, exist_ok=True)
        if is_binary:
            assert isinstance(content, bytes)
            if path.is_file() and path.read_bytes() == content:
                continue
            path.write_bytes(content)
            changed = True
        else:
            assert isinstance(content, str)
            if path.is_file() and path.read_text(encoding="utf-8") == content:
                continue
            path.write_text(content, encoding="utf-8")
            changed = True
    return changed


def prepare_eligibility_tree(fixture_dir: str | Path) -> dict[str, str]:
    """Garante árvore include/exclude commitada na main (idempotente).

    Responsabilidade
        Materializar paths/markers BDD-006 no fixture host.

    Motivo da separação
        Seed de arquivos + .gitignore + commit inicial/atualização
        é I/O; Robot só valida busca/files[].
    """
    root = Path(fixture_dir)
    _require_git(root)

    checkout = _run_git(root, "checkout", "main")
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stderr or "git checkout main failed")

    changed = _write_eligibility_files(root)
    if changed:
        # force-add ignored_dir (está no .gitignore) para existir no tip main
        add = _run_git(
            root,
            "add",
            "-A",
            "src",
            "docs",
            "data",
            "img",
            ".gitignore",
            "main_only.txt",
        )
        if add.returncode != 0:
            raise RuntimeError(add.stderr or "git add eligibility failed")
        force = _run_git(root, "add", "-f", "ignored_dir/secret_marker.txt")
        if force.returncode != 0:
            raise RuntimeError(force.stderr or "git add -f ignored_dir failed")
        _commit_if_staged(root, "t24 seed eligibility tree")

    return _eligibility_markers()


def prepare_main_only_branches(fixture_dir: str | Path) -> dict[str, str]:
    """Garante markers main / other branch / uncommitted (idempotente).

    Responsabilidade
        Estado git para BDD-017: tip main com MAIN_ONLY; branch other
        com OTHER; working tree com UNCOMMITTED não staged.

    Motivo da separação
        Checkout/branch/uncommitted é frágil em Robot; helper único
        documenta a ordem segura (voltar para main ao final).
    """
    root = Path(fixture_dir)
    _require_git(root)

    checkout = _run_git(root, "checkout", "main")
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stderr or "git checkout main failed")

    main_file = root / "main_only.txt"
    desired_main = f"{MARKER_MAIN_ONLY}\n"
    if not main_file.is_file() or main_file.read_text(encoding="utf-8") != desired_main:
        main_file.write_text(desired_main, encoding="utf-8")
        add = _run_git(root, "add", "main_only.txt")
        if add.returncode != 0:
            raise RuntimeError(add.stderr or "git add main_only.txt failed")
        _commit_if_staged(root, "t24 seed MAIN_ONLY_MARKER")

    # Garantir que OTHER não está na tip main
    other_on_main = root / "other_branch_only.txt"
    if other_on_main.is_file():
        other_on_main.unlink()
        _run_git(root, "add", "-u", "other_branch_only.txt")
        _commit_if_staged(root, "t24 remove other marker from main")

    branches = _run_git(root, "branch", "--list", OTHER_BRANCH_NAME)
    if OTHER_BRANCH_NAME not in (branches.stdout or ""):
        created = _run_git(root, "branch", OTHER_BRANCH_NAME)
        if created.returncode != 0:
            raise RuntimeError(created.stderr or "git branch other failed")

    switch = _run_git(root, "checkout", OTHER_BRANCH_NAME)
    if switch.returncode != 0:
        raise RuntimeError(switch.stderr or "git checkout other failed")

    other_file = root / "other_branch_only.txt"
    desired_other = f"{MARKER_OTHER_BRANCH}\n"
    if (
        not other_file.is_file()
        or other_file.read_text(encoding="utf-8") != desired_other
    ):
        other_file.write_text(desired_other, encoding="utf-8")
        add = _run_git(root, "add", "other_branch_only.txt")
        if add.returncode != 0:
            raise RuntimeError(add.stderr or "git add other_branch_only failed")
        _commit_if_staged(root, "t24 seed OTHER_BRANCH_MARKER")

    back = _run_git(root, "checkout", "main")
    if back.returncode != 0:
        raise RuntimeError(back.stderr or "git checkout main failed")

    # Uncommitted no WT (não staged)
    uncommitted = root / "uncommitted_marker.txt"
    uncommitted.write_text(f"{MARKER_UNCOMMITTED}\n", encoding="utf-8")
    # garantir que não está no index
    _run_git(root, "reset", "HEAD", "--", "uncommitted_marker.txt")

    return {
        "MARKER_MAIN_ONLY": MARKER_MAIN_ONLY,
        "MARKER_OTHER_BRANCH": MARKER_OTHER_BRANCH,
        "MARKER_UNCOMMITTED": MARKER_UNCOMMITTED,
    }


def resolve_sample_local_dir(repos_root: str | Path | None = None) -> Path:
    """Resolve e2e/fixtures/repos/sample-local (HOST_REPOS ou default repo).

    Responsabilidade
        Um único resolvedor de path para keywords e unitários.

    Motivo da separação
        Evita hardcode divergente entre launcher e Robot library.
    """
    if repos_root is not None:
        return (Path(repos_root) / SAMPLE_LOCAL_REL).resolve()

    host = os.environ.get("HOST_REPOS", "").strip()
    if host:
        return (Path(host) / SAMPLE_LOCAL_REL).resolve()

    # Default: e2e/fixtures/repos/sample-local relativo a este arquivo
    here = Path(__file__).resolve()
    # .../e2e/robot/libraries/CatalogIndexingKeywords.py → repo root
    repo_root = here.parents[3]
    return (repo_root / "e2e" / "fixtures" / "repos" / SAMPLE_LOCAL_REL).resolve()
