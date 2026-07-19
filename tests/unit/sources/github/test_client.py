"""Testes unitários — PyGithubApiClient (T05)."""

from __future__ import annotations

import unittest
from unittest import mock

from github import GithubException
from github.GithubException import RateLimitExceededException
from requests.exceptions import ConnectionError as RequestsConnectionError

from github_rag.sources.github.client import PyGithubApiClient
from github_rag.sources.github.errors import GitHubDiscoveryError

SECRET = "http-client-secret-token-do-not-leak"


def _repo(*, full_name: str, name: str, private: bool = False) -> mock.Mock:
    repo = mock.Mock()
    repo.full_name = full_name
    repo.name = name
    repo.private = private
    return repo


class TestPyGithubApiClient(unittest.TestCase):
    def test_iter_and_list_single_page(self) -> None:
        org = mock.Mock()
        org.get_repos.return_value = [
            _repo(full_name="my-org/repo-a", name="repo-a", private=False)
        ]
        github = mock.Mock()
        github.get_organization.return_value = org

        client = PyGithubApiClient(github_factory=lambda token: github)
        repos = client.list_org_repos("my-org", token=SECRET)

        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0].full_name, "my-org/repo-a")
        github.get_organization.assert_called_once_with("my-org")
        org.get_repos.assert_called_once_with(type="all")

    def test_iter_org_repos_yields_lazily(self) -> None:
        org = mock.Mock()
        org.get_repos.return_value = [
            _repo(full_name="my-org/r1", name="r1"),
            _repo(full_name="my-org/r2", name="r2", private=True),
        ]
        github = mock.Mock()
        github.get_organization.return_value = org
        client = PyGithubApiClient(github_factory=lambda token: github)

        iterator = client.iter_org_repos("my-org", token=SECRET)
        first = next(iterator)
        self.assertEqual(first.full_name, "my-org/r1")
        second = next(iterator)
        self.assertEqual(second.full_name, "my-org/r2")
        self.assertTrue(second.private)
        with self.assertRaises(StopIteration):
            next(iterator)

    def test_paginated_iteration_consumes_all(self) -> None:
        org = mock.Mock()
        org.get_repos.return_value = [
            _repo(full_name="my-org/r1", name="r1"),
            _repo(full_name="my-org/r2", name="r2"),
            _repo(full_name="my-org/r3", name="r3", private=True),
        ]
        github = mock.Mock()
        github.get_organization.return_value = org
        client = PyGithubApiClient(github_factory=lambda token: github)

        repos = client.list_org_repos("my-org", token=SECRET)
        self.assertEqual(len(repos), 3)
        self.assertEqual(repos[2].full_name, "my-org/r3")

    def test_http_401_raises_without_token_in_message(self) -> None:
        github = mock.Mock()
        github.get_organization.side_effect = GithubException(
            401, {"message": "Bad credentials"}, None
        )
        client = PyGithubApiClient(github_factory=lambda token: github)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        msg = str(ctx.exception) + repr(ctx.exception)
        self.assertNotIn(SECRET, msg)
        self.assertIn("401", msg)

    def test_invalid_org_raises(self) -> None:
        client = PyGithubApiClient(github_factory=lambda token: mock.Mock())
        with self.assertRaises(GitHubDiscoveryError):
            client.list_org_repos("  ", token=SECRET)

    def test_network_error(self) -> None:
        github = mock.Mock()
        github.get_organization.side_effect = RequestsConnectionError(
            "connection refused"
        )
        client = PyGithubApiClient(github_factory=lambda token: github)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        self.assertIn("rede", str(ctx.exception).lower())
        self.assertNotIn(SECRET, str(ctx.exception))

    def test_skips_malformed_items(self) -> None:
        bad = mock.Mock()
        bad.full_name = "invalid"
        bad.name = "x"
        bad.private = False
        org = mock.Mock()
        org.get_repos.return_value = [
            _repo(full_name="my-org/ok", name="ok"),
            "not-a-repo",
            bad,
        ]
        github = mock.Mock()
        github.get_organization.return_value = org
        client = PyGithubApiClient(github_factory=lambda token: github)

        repos = client.list_org_repos("my-org", token=SECRET)
        self.assertEqual(len(repos), 1)

    def test_generic_http_error(self) -> None:
        github = mock.Mock()
        github.get_organization.side_effect = GithubException(500, "Server Error", None)
        client = PyGithubApiClient(github_factory=lambda token: github)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        self.assertIn("500", str(ctx.exception))

    def test_rate_limit_error(self) -> None:
        github = mock.Mock()
        github.get_organization.side_effect = RateLimitExceededException(
            403, {"message": "API rate limit exceeded"}, None
        )
        client = PyGithubApiClient(github_factory=lambda token: github)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        self.assertIn("limite de taxa", str(ctx.exception).lower())

    def test_factory_receives_token(self) -> None:
        seen: list[str] = []
        org = mock.Mock()
        org.get_repos.return_value = []
        github = mock.Mock()
        github.get_organization.return_value = org

        def factory(token: str):
            seen.append(token)
            return github

        client = PyGithubApiClient(github_factory=factory)
        client.list_org_repos("my-org", token=SECRET)
        self.assertEqual(seen, [SECRET])

    def test_user_fallback_when_org_returns_404(self) -> None:
        user = mock.Mock()
        user.get_repos.return_value = [
            _repo(full_name="camilocoelhogomes/source-a", name="source-a", private=False)
        ]
        github = mock.Mock()
        github.get_organization.side_effect = GithubException(
            404, {"message": "Not Found"}, None
        )
        github.get_user.return_value = user
        client = PyGithubApiClient(github_factory=lambda token: github)
        repos = client.list_org_repos("camilocoelhogomes", token=SECRET)
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0].full_name, "camilocoelhogomes/source-a")
        github.get_user.assert_called_once_with("camilocoelhogomes")

    def test_both_org_and_user_404_raises(self) -> None:
        github = mock.Mock()
        github.get_organization.side_effect = GithubException(404, {}, None)
        github.get_user.side_effect = GithubException(404, {}, None)
        client = PyGithubApiClient(github_factory=lambda token: github)
        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("missing-account", token=SECRET)
        self.assertIn("404", str(ctx.exception))
        self.assertNotIn(SECRET, str(ctx.exception))

    def test_org_403_does_not_fallback_to_user(self) -> None:
        github = mock.Mock()
        github.get_organization.side_effect = GithubException(403, {}, None)
        client = PyGithubApiClient(github_factory=lambda token: github)
        with self.assertRaises(GitHubDiscoveryError):
            client.list_org_repos("private-org", token=SECRET)
        github.get_user.assert_not_called()



if __name__ == "__main__":
    unittest.main()
