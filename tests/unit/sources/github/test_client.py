"""Testes unitários — HttpGitHubApiClient (T05)."""

from __future__ import annotations

import io
import json
import unittest
import urllib.error
from unittest import mock

from github_rag.sources.github.client import HttpGitHubApiClient
from github_rag.sources.github.errors import GitHubDiscoveryError

SECRET = "http-client-secret-token-do-not-leak"


def _json_response(payload: object, *, status: int = 200) -> io.BytesIO:
    return io.BytesIO(json.dumps(payload).encode("utf-8"))


class TestHttpGitHubApiClient(unittest.TestCase):
    def test_parses_single_page(self) -> None:
        payload = [
            {
                "full_name": "my-org/repo-a",
                "name": "repo-a",
                "private": False,
            }
        ]
        response = mock.Mock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        response.__enter__ = mock.Mock(return_value=response)
        response.__exit__ = mock.Mock(return_value=False)

        opener = mock.Mock()
        opener.open.return_value = response

        client = HttpGitHubApiClient(opener=opener)
        repos = client.list_org_repos("my-org", token=SECRET)

        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0].full_name, "my-org/repo-a")
        opener.open.assert_called_once()
        request = opener.open.call_args[0][0]
        self.assertIn("Bearer", request.headers["Authorization"])

    def test_paginates_multiple_pages(self) -> None:
        page1 = [
            {"full_name": "my-org/r1", "name": "r1", "private": False},
            {"full_name": "my-org/r2", "name": "r2", "private": False},
        ]
        page2 = [{"full_name": "my-org/r3", "name": "r3", "private": True}]

        responses = []
        for payload in (page1, page2, []):
            resp = mock.Mock()
            resp.read.return_value = json.dumps(payload).encode("utf-8")
            resp.__enter__ = mock.Mock(return_value=resp)
            resp.__exit__ = mock.Mock(return_value=False)
            responses.append(resp)

        opener = mock.Mock()
        opener.open.side_effect = responses

        client = HttpGitHubApiClient(opener=opener, per_page=2)
        repos = client.list_org_repos("my-org", token=SECRET)

        self.assertEqual(len(repos), 3)
        self.assertEqual(opener.open.call_count, 2)

    def test_http_401_raises_without_token_in_message(self) -> None:
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/orgs/my-org/repos",
            code=401,
            msg="Unauthorized",
            hdrs=mock.Mock(headers={}),
            fp=None,
        )

        client = HttpGitHubApiClient(opener=opener)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        msg = str(ctx.exception) + repr(ctx.exception)
        self.assertNotIn(SECRET, msg)
        self.assertIn("401", msg)

    def test_invalid_org_raises(self) -> None:
        client = HttpGitHubApiClient(opener=mock.Mock())
        with self.assertRaises(GitHubDiscoveryError):
            client.list_org_repos("  ", token=SECRET)

    def test_network_error(self) -> None:
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.URLError("connection refused")
        client = HttpGitHubApiClient(opener=opener)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        self.assertIn("rede", str(ctx.exception).lower())
        self.assertNotIn(SECRET, str(ctx.exception))

    def test_unexpected_payload_raises(self) -> None:
        response = mock.Mock()
        response.read.return_value = json.dumps({"not": "a list"}).encode("utf-8")
        response.__enter__ = mock.Mock(return_value=response)
        response.__exit__ = mock.Mock(return_value=False)
        opener = mock.Mock()
        opener.open.return_value = response

        client = HttpGitHubApiClient(opener=opener)
        with self.assertRaises(GitHubDiscoveryError):
            client.list_org_repos("my-org", token=SECRET)

    def test_skips_malformed_items(self) -> None:
        payload = [
            {"full_name": "my-org/ok", "name": "ok", "private": False},
            "not-a-dict",
            {"full_name": "invalid", "name": "x"},
        ]
        response = mock.Mock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        response.__enter__ = mock.Mock(return_value=response)
        response.__exit__ = mock.Mock(return_value=False)
        opener = mock.Mock()
        opener.open.return_value = response

        client = HttpGitHubApiClient(opener=opener)
        repos = client.list_org_repos("my-org", token=SECRET)
        self.assertEqual(len(repos), 1)

    def test_generic_http_error(self) -> None:
        headers = mock.Mock()
        headers.get.return_value = None
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/orgs/my-org/repos",
            code=500,
            msg="Server Error",
            hdrs=headers,
            fp=None,
        )
        client = HttpGitHubApiClient(opener=opener)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        self.assertIn("500", str(ctx.exception))

    def test_rate_limit_error(self) -> None:
        headers = mock.Mock()
        headers.get.return_value = "0"
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/orgs/my-org/repos",
            code=403,
            msg="Forbidden",
            hdrs=headers,
            fp=None,
        )

        client = HttpGitHubApiClient(opener=opener)

        with self.assertRaises(GitHubDiscoveryError) as ctx:
            client.list_org_repos("my-org", token=SECRET)

        self.assertIn("limite de taxa", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
