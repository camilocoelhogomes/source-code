"""Fonte GitHub — descoberta de repositórios remotos (T05).

Responsabilidade
    Re-exportar a superfície pública de descoberta GitHub.

Motivo da separação
    Callers importam ``from github_rag.sources.github import ...`` sem acoplar
    ao layout interno ``client`` / ``wildcard`` / ``discovery``.
"""

from github_rag.sources.github.client import GitHubApiClient, HttpGitHubApiClient
from github_rag.sources.github.discovery import GitHubRepoDiscovery
from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import DiscoveredGitHubRepo, GitHubRepoRaw
from github_rag.sources.github.wildcard import (
    matches_any_inclusion_pattern,
    matches_inclusion_pattern,
)

__all__ = [
    "DiscoveredGitHubRepo",
    "GitHubApiClient",
    "GitHubDiscoveryError",
    "GitHubRepoDiscovery",
    "GitHubRepoRaw",
    "HttpGitHubApiClient",
    "matches_any_inclusion_pattern",
    "matches_inclusion_pattern",
]
