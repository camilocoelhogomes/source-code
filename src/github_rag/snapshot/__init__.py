"""Snapshots da branch main — tip, árvore, read e diff (T08)."""

from github_rag.snapshot.clone import GitClonePort, ShallowGitClonePort
from github_rag.snapshot.diff import FileDiff, FileDiffSet
from github_rag.snapshot.errors import (
    CommitNotFoundError,
    CorruptRepositoryError,
    FileNotFoundInCommitError,
    GitHubSnapshotNetworkError,
    MainBranchMissingError,
    SnapshotError,
)
from github_rag.snapshot.models import (
    FileChangeKind,
    FirstIndexSignal,
    GitHubSnapshotSource,
    LocalSnapshotSource,
    MainSnapshot,
    SnapshotSource,
)
from github_rag.snapshot.provider import (
    DefaultMainSnapshotProvider,
    MainSnapshotProvider,
)

__all__ = [
    "CommitNotFoundError",
    "CorruptRepositoryError",
    "DefaultMainSnapshotProvider",
    "FileChangeKind",
    "FileDiff",
    "FileDiffSet",
    "FileNotFoundInCommitError",
    "FirstIndexSignal",
    "GitClonePort",
    "GitHubSnapshotNetworkError",
    "GitHubSnapshotSource",
    "LocalSnapshotSource",
    "MainBranchMissingError",
    "MainSnapshot",
    "MainSnapshotProvider",
    "ShallowGitClonePort",
    "SnapshotError",
    "SnapshotSource",
]
