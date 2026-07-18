"""Fronteira de configuração de conexões (T02).

Responsabilidade
    Re-exportar a superfície pública do pacote ``github_rag.config`` para
    callers e BDD.

Motivo da separação
    Consumers importam ``from github_rag.config import ...`` sem acoplar ao
    layout interno ``schema`` / ``secrets`` / ``loader``.
"""

from github_rag.config.loader import ConfigLoadError, ConfigLoader
from github_rag.config.schema import (
    AppConfig,
    EnvSecretRef,
    GitConnection,
    GitHubConnection,
    ResolvedSecret,
    Revisions,
)
from github_rag.config.secrets import (
    EnvironSecretResolver,
    SecretResolutionError,
    SecretResolver,
)

__all__ = [
    "AppConfig",
    "ConfigLoadError",
    "ConfigLoader",
    "EnvSecretRef",
    "EnvironSecretResolver",
    "GitConnection",
    "GitHubConnection",
    "ResolvedSecret",
    "Revisions",
    "SecretResolutionError",
    "SecretResolver",
]
