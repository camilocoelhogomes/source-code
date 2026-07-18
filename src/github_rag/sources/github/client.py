"""Porta HTTP para API GitHub — listagem de repos por org (T05).

Responsabilidade deste módulo
    Declarar ``GitHubApiClient`` e ``HttpGitHubApiClient`` com paginação
    completa de ``/orgs/{org}/repos``.

Motivo da separação
    Isola I/O de rede da orquestração e do filtro wildcard; permite mocks nos
    testes (DEC-014).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol, runtime_checkable

from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import GitHubRepoRaw

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_PER_PAGE = 100


@runtime_checkable
class GitHubApiClient(Protocol):
    """Porta: listar repositórios de uma organização GitHub.

    Responsabilidade
        Retornar todos os repos acessíveis pelo token para a org informada.

    Motivo da separação
        ``GitHubRepoDiscovery`` depende desta abstração, não de urllib/requests.
    """

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        """Lista repos da org; implementação deve paginar até esgotar."""
        ...


class HttpGitHubApiClient:
    """Implementação HTTP via stdlib (urllib).

    Responsabilidade
        Chamar REST GitHub com Bearer token e agregar páginas.

    Motivo da separação
        Implementação concreta injetável; produção usa stdlib sem nova dep.
    """

    def __init__(
        self,
        *,
        api_base: str = GITHUB_API_BASE,
        per_page: int = DEFAULT_PER_PAGE,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._per_page = per_page
        self._opener = opener if opener is not None else urllib.request.build_opener()

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        """Lista todos os repos da org com paginação."""
        if not org.strip():
            raise GitHubDiscoveryError("organização GitHub inválida")

        collected: list[GitHubRepoRaw] = []
        page = 1

        while True:
            url = (
                f"{self._api_base}/orgs/{org}/repos"
                f"?page={page}&per_page={self._per_page}&type=all"
            )
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                method="GET",
            )
            try:
                with self._opener.open(request, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                raise _http_error_to_discovery(exc, org=org) from exc
            except urllib.error.URLError as exc:
                raise GitHubDiscoveryError(
                    f"falha de rede ao listar repositórios da org {org!r}"
                ) from exc

            if not isinstance(payload, list):
                raise GitHubDiscoveryError(
                    f"resposta inesperada da API GitHub para org {org!r}"
                )

            if not payload:
                break

            for item in payload:
                if not isinstance(item, dict):
                    continue
                full_name = item.get("full_name")
                name = item.get("name")
                private = item.get("private", False)
                if (
                    isinstance(full_name, str)
                    and isinstance(name, str)
                    and "/" in full_name
                ):
                    collected.append(
                        GitHubRepoRaw(
                            full_name=full_name,
                            name=name,
                            private=bool(private),
                        )
                    )

            if len(payload) < self._per_page:
                break
            page += 1

        return tuple(collected)


def _http_error_to_discovery(
    exc: urllib.error.HTTPError,
    *,
    org: str,
) -> GitHubDiscoveryError:
    """Traduz HTTPError em GitHubDiscoveryError sem expor token."""
    status = exc.code
    remaining = exc.headers.get("X-RateLimit-Remaining") if exc.headers else None

    if status in (401, 403):
        if remaining == "0":
            return GitHubDiscoveryError(
                f"limite de taxa da API GitHub excedido ao listar org {org!r}"
            )
        return GitHubDiscoveryError(
            f"acesso negado ou token inválido ao listar org {org!r} (HTTP {status})"
        )

    return GitHubDiscoveryError(
        f"erro HTTP {status} ao listar repositórios da org {org!r}"
    )
