"""Helpers — testes unitários T10 zoekt-adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SECRET_TOKEN = "ghp_unit_zoekt_secret_do_not_leak_7c4e"
REPO = "acme/api"
OTHER_REPO = "acme/other"
COMMIT = "abc123"
COMMIT_V2 = "def456"


def make_file(
    path: str,
    content: bytes,
    *,
    repository: str = REPO,
    commit: str = COMMIT,
) -> Any:
    from github_rag.index.zoekt.models import FileToIndex

    return FileToIndex(
        repository=repository,
        path=path,
        commit=commit,
        content=content,
    )


@dataclass
class RecordingSearchTransport:
    """Fake de ZoektSearchTransport: registra bodies e devolve resposta configurável."""

    response: Mapping[str, Any] = field(default_factory=dict)
    error: BaseException | None = None
    calls: list[Mapping[str, Any]] = field(default_factory=list)

    def post_search(self, body: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(dict(body))
        if self.error is not None:
            raise self.error
        return dict(self.response)


@dataclass
class RecordingIndexRunner:
    """Fake de ZoektIndexRunner: registra argv e devolve resultado configurável."""

    result: Any = None
    error: BaseException | None = None
    calls: list[tuple[str, ...]] = field(default_factory=list)
    capture_tree: list[dict[str, bytes]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.result is None:
            from github_rag.index.zoekt.runner import ZoektIndexRunResult

            self.result = ZoektIndexRunResult(returncode=0, stdout="", stderr="")

    def run(self, argv: Sequence[str]) -> Any:
        self.calls.append(tuple(argv))
        if self.error is not None:
            raise self.error
        if len(argv) >= 1:
            tree_candidate = Path(argv[-1])
            if tree_candidate.is_dir():
                snapshot: dict[str, bytes] = {}
                for p in tree_candidate.rglob("*"):
                    if p.is_file():
                        snapshot[str(p.relative_to(tree_candidate))] = p.read_bytes()
                self.capture_tree.append(snapshot)
        return self.result


def zoekt_file_matches_payload(
    *,
    repository: str = REPO,
    path: str = "src/main.py",
    lines: Sequence[tuple[int, str]] | None = None,
) -> dict[str, Any]:
    """Monta um fragmento mínimo no formato FileMatches do JSON oficial Zoekt."""
    if lines is None:
        lines = ((10, "def authenticate():"),)
    return {
        "Result": {
            "FileMatches": [
                {
                    "FileName": path,
                    "Repository": repository,
                    "Matches": [
                        {
                            "LineNumber": ln,
                            "Fragments": [{"Pre": "", "Match": text, "Post": ""}],
                        }
                        for ln, text in lines
                    ],
                }
            ]
        }
    }
