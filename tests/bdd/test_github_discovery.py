"""
BDD executável — T05-github-discovery.

Valida BDD-001, BDD-019 e BDD-014 (camada discovery) conforme design 0.1.0.

Execução:
    python -m pytest tests/bdd/test_github_discovery.py -q
"""

from __future__ import annotations

import unittest

from github_rag.sources.github.discovery import GitHubRepoDiscovery
from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import GitHubRepoRaw
from tests.unit.sources.github.helpers import (
    SECRET_TOKEN_VALUE,
    load_github_connection,
)


class FakeClient:
    def __init__(self, repos_by_org: dict[str, list[GitHubRepoRaw]]) -> None:
        self._repos_by_org = repos_by_org

    def iter_org_repos(self, org: str, *, token: str):
        yield from self._repos_by_org.get(org, [])

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        return tuple(self.iter_org_repos(org, token=token))


class TestGH01DiscoverByWildcards(unittest.TestCase):
    """GH-01 / BDD-001 — somente repos que casam wildcards."""

    def test_inclusion_filter(self) -> None:
        repos = [
            GitHubRepoRaw("my-org/microservice-auth", "microservice-auth", True),
            GitHubRepoRaw("my-org/user-api", "user-api", False),
            GitHubRepoRaw("my-org/other-tool", "other-tool", False),
            GitHubRepoRaw("my-org/secret-internal", "secret-internal", True),
        ]
        discovery = GitHubRepoDiscovery(client=FakeClient({"my-org": repos}))
        connection = load_github_connection()

        result = discovery.discover("github-microservices", connection)
        names = {item.full_name for item in result}

        self.assertEqual(names, {"my-org/microservice-auth", "my-org/user-api"})


class TestGH02TokenFromEnvNotInResult(unittest.TestCase):
    """GH-02 / BDD-019 — token via env; não serializado."""

    def test_no_token_in_result(self) -> None:
        repos = [GitHubRepoRaw("my-org/microservice-auth", "microservice-auth", False)]
        discovery = GitHubRepoDiscovery(client=FakeClient({"my-org": repos}))
        connection = load_github_connection()

        result = discovery.discover("conn", connection)
        serialized = repr(result) + "".join(str(item) + repr(item) for item in result)
        self.assertNotIn(SECRET_TOKEN_VALUE, serialized)


class TestGH03ProtectTokenInErrors(unittest.TestCase):
    """GH-03 / BDD-014 — token ausente de erros desta camada."""

    def test_auth_failure_no_leak(self) -> None:
        class AuthFailClient:
            def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
                raise GitHubDiscoveryError(
                    f"acesso negado ou token inválido ao listar org {org!r} (HTTP 401)"
                )

        discovery = GitHubRepoDiscovery(client=AuthFailClient())
        connection = load_github_connection(repos=["my-org/*"])

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            discovery.discover("conn", connection)

        blob = str(ctx.exception) + repr(ctx.exception)
        self.assertNotIn(SECRET_TOKEN_VALUE, blob)


class TestGH04EmptyReposPatterns(unittest.TestCase):
    """GH-04 — repos vazio ⇒ nenhum descoberto."""

    def test_empty_patterns(self) -> None:
        repos = [GitHubRepoRaw("my-org/any", "any", False)]
        discovery = GitHubRepoDiscovery(client=FakeClient({"my-org": repos}))
        connection = load_github_connection(repos=[])

        self.assertEqual(discovery.discover("conn", connection), ())


class TestGH05PublicAndPrivate(unittest.TestCase):
    """GH-05 / REQ-011 — públicos e privados acessíveis."""

    def test_both_visibility(self) -> None:
        repos = [
            GitHubRepoRaw("my-org/public-repo", "public-repo", False),
            GitHubRepoRaw("my-org/private-repo", "private-repo", True),
        ]
        discovery = GitHubRepoDiscovery(client=FakeClient({"my-org": repos}))
        connection = load_github_connection(repos=["my-org/*"])

        result = discovery.discover("conn", connection)
        self.assertEqual(len(result), 2)
        vis = {item.full_name: item.private for item in result}
        self.assertFalse(vis["my-org/public-repo"])
        self.assertTrue(vis["my-org/private-repo"])


class TestGH06Pagination(unittest.TestCase):
    """GH-06 — paginação agrega páginas (via client fake multi-call simulado)."""

    def test_multi_page_via_discovery_multi_org(self) -> None:
        page_a = [GitHubRepoRaw("my-org/r1", "r1", False)]
        page_b = [GitHubRepoRaw("my-org/r2", "r2", False)]

        class PaginatedClient:
            def __init__(self) -> None:
                self._calls = 0

            def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
                self._calls += 1
                if self._calls == 1:
                    return tuple(page_a)
                return tuple(page_b)

        discovery = GitHubRepoDiscovery(client=PaginatedClient())
        connection = load_github_connection(repos=["my-org/*"], orgs=["my-org", "my-org"])

        result = discovery.discover("conn", connection)
        self.assertEqual({item.full_name for item in result}, {"my-org/r1", "my-org/r2"})


class TestGH07AuthFailure(unittest.TestCase):
    """GH-07 — falha de autenticação."""

    def test_raises_discovery_error(self) -> None:
        class FailClient:
            def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
                raise GitHubDiscoveryError("acesso negado (HTTP 401)")

        discovery = GitHubRepoDiscovery(client=FailClient())
        connection = load_github_connection(repos=["my-org/*"])

        with self.assertRaises(GitHubDiscoveryError):
            discovery.discover("conn", connection)


if __name__ == "__main__":
    unittest.main()
