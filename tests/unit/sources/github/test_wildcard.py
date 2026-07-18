"""Testes unitários — wildcard de inclusão GitHub (T05)."""

from __future__ import annotations

import unittest

from github_rag.sources.github.wildcard import (
    matches_any_inclusion_pattern,
    matches_inclusion_pattern,
)


class TestWildcardInclusion(unittest.TestCase):
    def test_prefix_match(self) -> None:
        self.assertTrue(
            matches_inclusion_pattern("my-org/foo-bar", "my-org/foo-*")
        )

    def test_suffix_match(self) -> None:
        self.assertTrue(
            matches_inclusion_pattern("my-org/bar-api", "my-org/*-api")
        )

    def test_exact_match(self) -> None:
        self.assertTrue(
            matches_inclusion_pattern("my-org/exact-repo", "my-org/exact-repo")
        )

    def test_wildcard_all_in_org(self) -> None:
        self.assertTrue(matches_inclusion_pattern("my-org/anything", "my-org/*"))

    def test_wrong_org(self) -> None:
        self.assertFalse(
            matches_inclusion_pattern("other-org/foo-bar", "my-org/foo-*")
        )

    def test_no_match(self) -> None:
        self.assertFalse(
            matches_inclusion_pattern("my-org/other-tool", "my-org/microservice-*")
        )

    def test_malformed_pattern_without_slash(self) -> None:
        self.assertFalse(matches_inclusion_pattern("my-org/repo", "invalid"))

    def test_malformed_full_name_in_pattern(self) -> None:
        self.assertFalse(matches_inclusion_pattern("invalid", "my-org/*"))

    def test_matches_any(self) -> None:
        patterns = ("my-org/microservice-*", "my-org/*-api")
        self.assertTrue(
            matches_any_inclusion_pattern("my-org/microservice-x", patterns)
        )
        self.assertFalse(
            matches_any_inclusion_pattern("my-org/other", patterns)
        )


if __name__ == "__main__":
    unittest.main()
