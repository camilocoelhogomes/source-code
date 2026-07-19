"""BDD T28 — user/org discovery fallback."""
from __future__ import annotations
import unittest
from unittest import mock
from github import GithubException
from github_rag.sources.github.client import PyGithubApiClient
from github_rag.sources.github.discovery import GitHubRepoDiscovery
from github_rag.sources.github.errors import GitHubDiscoveryError
from tests.unit.sources.github.helpers import SECRET_TOKEN_VALUE, load_github_connection

SECRET = "bdd-t28-secret"

def _repo(**kw):
    r = mock.Mock()
    r.full_name, r.name, r.private = kw["full_name"], kw["name"], kw.get("private", False)
    return r

class TestGHT2801(unittest.TestCase):
    def test_org_unchanged(self):
        org = mock.Mock()
        org.get_repos.return_value = [_repo(full_name="my-org/r", name="r")]
        gh = mock.Mock(get_organization=mock.Mock(return_value=org))
        repos = PyGithubApiClient(github_factory=lambda t: gh).list_org_repos("my-org", token=SECRET)
        self.assertEqual(repos[0].full_name, "my-org/r")
        gh.get_user.assert_not_called()

class TestGHT2802(unittest.TestCase):
    def test_user_fallback(self):
        user = mock.Mock(get_repos=mock.Mock(return_value=[
            _repo(full_name="camilocoelhogomes/source-api", name="source-api"),
            _repo(full_name="camilocoelhogomes/other", name="other"),
        ]))
        gh = mock.Mock()
        gh.get_organization.side_effect = GithubException(404, {}, None)
        gh.get_user.return_value = user
        d = GitHubRepoDiscovery(client=PyGithubApiClient(github_factory=lambda t: gh))
        r = d.discover("c", load_github_connection(orgs=["camilocoelhogomes"], repos=["camilocoelhogomes/source-*"]))
        self.assertEqual({x.full_name for x in r}, {"camilocoelhogomes/source-api"})
        self.assertNotIn(SECRET_TOKEN_VALUE, repr(r))

class TestGHT2803(unittest.TestCase):
    def test_missing_account(self):
        gh = mock.Mock()
        gh.get_organization.side_effect = GithubException(404, {}, None)
        gh.get_user.side_effect = GithubException(404, {}, None)
        with self.assertRaises(GitHubDiscoveryError) as ctx:
            PyGithubApiClient(github_factory=lambda t: gh).list_org_repos("ghost", token=SECRET)
        self.assertIn("404", str(ctx.exception))
        self.assertNotIn(SECRET, str(ctx.exception))
