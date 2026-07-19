"""Entrypoint ``python -m github_rag.e2e``."""

from __future__ import annotations

from github_rag.e2e.env_loader import load_dotenv_file
from github_rag.e2e.suite import run_mvp_e2e


def main() -> None:
    """Entrypoint ``python -m github_rag.e2e`` → ``SystemExit(run_mvp_e2e())``."""
    load_dotenv_file(".env")
    raise SystemExit(run_mvp_e2e())


if __name__ == "__main__":
    main()
