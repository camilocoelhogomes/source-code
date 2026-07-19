"""Porta GitHub — listagem de repos por org via PyGithub (T05).

Responsabilidade deste módulo
    Declarar ``GitHubApiClient`` e ``PyGithubApiClient`` com iteração
    paginada de repositórios de organização ou usuário.

Motivo da separação
    Isola I/O de rede da orquestração e do filtro wildcard; permite mocks nos
    testes (DEC-014). A iteração usa PyGithub para paginação e tipagem da API.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, Protocol, runtime_checkable

from github import Auth, Github, GithubException
from github.GithubException import RateLimitExceededException
from requests.exceptions import RequestException

from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import GitHubRepoRaw

GithubFactory = Callable[[str], Github]


def _default_github(token: str) -> Github:
    """Cria cliente PyGithub autenticado por token Bearer."""
    return Github(auth=Auth.Token(token))


@runtime_checkable
class GitHubApiClient(Protocol):
    """Porta: listar repositórios de uma conta GitHub (org ou user)."""

    def iter_org_repos(self, org: str, *, token: str) -> Iterator[GitHubRepoRaw]:
        """Itera repos da conta; implementação deve paginar até esgotar."""
        ...

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        """Lista repos da conta materializando a iteração completa."""
        ...


class PyGithubApiClient:
    """Implementação via PyGithub (iteração paginada nativa)."""

    def __init__(
        self,
        *,
        github_factory: GithubFactory | None = None,
        repo_type: str = "all",
    ) -> None:
        self._github_factory = (
            github_factory if github_factory is not None else _default_github
        )
        self._repo_type = repo_type

    def iter_org_repos(self, org: str, *, token: str) -> Iterator[GitHubRepoRaw]:
        """Itera repos de org ou user via PyGithub (paginação automática)."""
        if not org.strip():
            raise GitHubDiscoveryError("conta GitHub inválida")

        try:
            github = self._github_factory(token)
            for repo in _resolve_account_repos(
                github,
                org,
                repo_type=self._repo_type,
            ):
                full_name = getattr(repo, "full_name", None)
                name = getattr(repo, "name", None)
                private = getattr(repo, "private", False)
                if (
                    isinstance(full_name, str)
                    and isinstance(name, str)
                    and "/" in full_name
                ):
                    yield GitHubRepoRaw(
                        full_name=full_name,
                        name=name,
                        private=bool(private),
                    )
        except RateLimitExceededException as exc:
            raise GitHubDiscoveryError(
                f"limite de taxa da API GitHub excedido ao listar conta {org!r}"
            ) from exc
        except GithubException as exc:
            raise _github_exception_to_discovery(exc, account=org) from exc
        except RequestException as exc:
            raise GitHubDiscoveryError(
                f"falha de rede ao listar repositórios da conta {org!r}"
            ) from exc

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        return tuple(self.iter_org_repos(org, token=token))


HttpGitHubApiClient = PyGithubApiClient


def _resolve_account_repos(github: Github, login: str, *, repo_type: str) -> Any:
    """Resolve iterador de repos para login de org ou user (fallback em 404)."""
    try:
        organization = github.get_organization(login)
        return organization.get_repos(type=repo_type)
    except GithubException as org_exc:
        if org_exc.status != 404:
            raise
        user = github.get_user(login)
        return user.get_repos(type=repo_type)


def _github_exception_to_discovery(
    exc: GithubException,
    *,
    account: str,
) -> GitHubDiscoveryError:
    status = exc.status
    if status in (401, 403):
        return GitHubDiscoveryError(
            f"acesso negado ou token inválido ao listar conta {account!r} (HTTP {status})"
        )
    return GitHubDiscoveryError(
        f"erro HTTP {status} ao listar repositórios da conta {account!r}"
    )
