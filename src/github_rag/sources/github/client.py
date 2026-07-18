"""Porta GitHub — listagem de repos por org via PyGithub (T05).

Responsabilidade deste módulo
    Declarar ``GitHubApiClient`` e ``PyGithubApiClient`` com iteração
    paginada de repositórios de organização.

Motivo da separação
    Isola I/O de rede da orquestração e do filtro wildcard; permite mocks nos
    testes (DEC-014). A iteração usa PyGithub para paginação e tipagem da API.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Protocol, runtime_checkable

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
    """Porta: listar repositórios de uma organização GitHub.

    Responsabilidade
        Retornar todos os repos acessíveis pelo token para a org informada.

    Motivo da separação
        ``GitHubRepoDiscovery`` depende desta abstração, não de PyGithub.
    """

    def iter_org_repos(self, org: str, *, token: str) -> Iterator[GitHubRepoRaw]:
        """Itera repos da org; implementação deve paginar até esgotar."""
        ...

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        """Lista repos da org materializando a iteração completa."""
        ...


class PyGithubApiClient:
    """Implementação via PyGithub (iteração paginada nativa).

    Responsabilidade
        Expor ``iter_org_repos`` / ``list_org_repos`` sobre
        ``Organization.get_repos``, sem vazar o token em erros.

    Motivo da separação
        Implementação concreta injetável; produção usa PyGithub em vez de
        urllib manual.
    """

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
        """Itera todos os repos da org via PyGithub (paginação automática)."""
        if not org.strip():
            raise GitHubDiscoveryError("organização GitHub inválida")

        try:
            github = self._github_factory(token)
            organization = github.get_organization(org)
            for repo in organization.get_repos(type=self._repo_type):
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
                f"limite de taxa da API GitHub excedido ao listar org {org!r}"
            ) from exc
        except GithubException as exc:
            raise _github_exception_to_discovery(exc, org=org) from exc
        except RequestException as exc:
            raise GitHubDiscoveryError(
                f"falha de rede ao listar repositórios da org {org!r}"
            ) from exc

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        """Lista todos os repos da org materializando ``iter_org_repos``."""
        return tuple(self.iter_org_repos(org, token=token))


# Alias de compatibilidade com artefatos T05 anteriores à revisão PyGithub.
HttpGitHubApiClient = PyGithubApiClient


def _github_exception_to_discovery(
    exc: GithubException,
    *,
    org: str,
) -> GitHubDiscoveryError:
    """Traduz GithubException em GitHubDiscoveryError sem expor token."""
    status = exc.status

    if status in (401, 403):
        return GitHubDiscoveryError(
            f"acesso negado ou token inválido ao listar org {org!r} (HTTP {status})"
        )

    return GitHubDiscoveryError(
        f"erro HTTP {status} ao listar repositórios da org {org!r}"
    )
