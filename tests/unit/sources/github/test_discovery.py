"""Testes unitários — GitHubRepoDiscovery (T05)."""

from __future__ import annotations

import unittest

from github_rag.sources.github.discovery import GitHubRepoDiscovery
from github_rag.sources.github.errors import GitHubDiscoveryError
from github_rag.sources.github.models import GitHubRepoRaw
from tests.unit.sources.github.helpers import (
    SECRET_TOKEN_VALUE,
    load_github_connection,
)


class FakeGitHubClient:
    def __init__(self, repos_by_org: dict[str, list[GitHubRepoRaw]]) -> None:
        self._repos_by_org = repos_by_org
        self.calls: list[tuple[str, str]] = []

    def iter_org_repos(self, org: str, *, token: str):
        self.calls.append((org, token))
        yield from self._repos_by_org.get(org, [])

    def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
        return tuple(self.iter_org_repos(org, token=token))


class TestGitHubRepoDiscovery(unittest.TestCase):
    def _sample_repos(self) -> list[GitHubRepoRaw]:
        return [
            GitHubRepoRaw("my-org/microservice-auth", "microservice-auth", True),
            GitHubRepoRaw("my-org/user-api", "user-api", False),
            GitHubRepoRaw("my-org/other-tool", "other-tool", False),
            GitHubRepoRaw("my-org/secret-internal", "secret-internal", True),
        ]

    def test_filters_by_inclusion_wildcards(self) -> None:
        client = FakeGitHubClient({"my-org": self._sample_repos()})
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection()

        result = discovery.discover("conn", connection)
        names = {item.full_name for item in result}

        self.assertEqual(names, {"my-org/microservice-auth", "my-org/user-api"})

    def test_empty_repos_patterns_returns_empty(self) -> None:
        client = FakeGitHubClient({"my-org": self._sample_repos()})
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection(repos=[])

        self.assertEqual(discovery.discover("conn", connection), ())

    def test_sorted_by_full_name(self) -> None:
        repos = [
            GitHubRepoRaw("my-org/z-last", "z-last", False),
            GitHubRepoRaw("my-org/a-first", "a-first", False),
        ]
        client = FakeGitHubClient({"my-org": repos})
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection(repos=["my-org/*"])

        result = discovery.discover("conn", connection)
        self.assertEqual(
            [item.full_name for item in result],
            ["my-org/a-first", "my-org/z-last"],
        )

    def test_deduplicates_same_full_name_across_orgs(self) -> None:
        repo = GitHubRepoRaw("my-org/dup", "dup", False)
        client = FakeGitHubClient({"my-org": [repo], "my-org": [repo]})
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection(repos=["my-org/dup"])

        result = discovery.discover("conn", connection)
        self.assertEqual(len(result), 1)

    def test_token_not_in_discovered_repr(self) -> None:
        client = FakeGitHubClient(
            {"my-org": [GitHubRepoRaw("my-org/a-first", "a-first", False)]}
        )
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection(repos=["my-org/*"])

        result = discovery.discover("conn", connection)
        blob = repr(result) + "".join(repr(item) for item in result)
        self.assertNotIn(SECRET_TOKEN_VALUE, blob)

    def test_multi_org_union(self) -> None:
        client = FakeGitHubClient(
            {
                "org-a": [GitHubRepoRaw("org-a/service-api", "service-api", False)],
                "org-b": [GitHubRepoRaw("org-b/tool-api", "tool-api", True)],
            }
        )
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection(
            orgs=["org-a", "org-b"],
            repos=["org-a/*-api", "org-b/*-api"],
        )

        result = discovery.discover("multi", connection)
        self.assertEqual(
            {item.full_name for item in result},
            {"org-a/service-api", "org-b/tool-api"},
        )

    def test_auth_error_does_not_leak_token(self) -> None:
        class FailingClient:
            def list_org_repos(self, org: str, *, token: str) -> tuple[GitHubRepoRaw, ...]:
                raise GitHubDiscoveryError(
                    f"acesso negado ao listar org {org!r} (HTTP 401)"
                )

        discovery = GitHubRepoDiscovery(client=FailingClient())
        connection = load_github_connection(repos=["my-org/*"])

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            discovery.discover("conn", connection)

        msg = str(ctx.exception) + repr(ctx.exception)
        self.assertNotIn(SECRET_TOKEN_VALUE, msg)

    def test_includes_public_and_private(self) -> None:
        client = FakeGitHubClient(
            {
                "my-org": [
                    GitHubRepoRaw("my-org/pub", "pub", False),
                    GitHubRepoRaw("my-org/priv", "priv", True),
                ]
            }
        )
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection(repos=["my-org/*"])

        result = discovery.discover("conn", connection)
        flags = {item.full_name: item.private for item in result}
        self.assertEqual(flags, {"my-org/pub": False, "my-org/priv": True})

    def test_user_login_discovery_via_fake_client(self) -> None:
        client = FakeGitHubClient(
            {"camilocoelhogomes": [GitHubRepoRaw("camilocoelhogomes/source-x", "source-x", False)]}
        )
        discovery = GitHubRepoDiscovery(client=client)
        connection = load_github_connection(
            orgs=["camilocoelhogomes"], repos=["camilocoelhogomes/source-*"]
        )
        result = discovery.discover("conn", connection)
        self.assertEqual([item.full_name for item in result], ["camilocoelhogomes/source-x"])



if __name__ == "__main__":
    unittest.main()
