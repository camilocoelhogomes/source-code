"""Entrypoint ``python -m github_rag.e2e``."""

from __future__ import annotations

from github_rag.e2e.suite import run_mvp_e2e


def main() -> None:
    """Entrypoint ``python -m github_rag.e2e`` → ``SystemExit(run_mvp_e2e())``."""
    raise SystemExit(run_mvp_e2e())


if __name__ == "__main__":
    main()
