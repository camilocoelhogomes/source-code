"""Metadados contextuais SLM por chunk (T12)."""

from github_rag.index.metadata.config import SlmClientSettings
from github_rag.index.metadata.errors import (
    MetadataConfigError,
    MetadataGenerationError,
    MetadataModelError,
    MetadataResponseParseError,
)
from github_rag.index.metadata.fakes import FakeMetadataGenerator
from github_rag.index.metadata.openai_slm import OpenAICompatibleMetadataGenerator
from github_rag.index.metadata.ports import MetadataGenerator
from github_rag.index.metadata.types import ChunkMetadata

__all__ = [
    "ChunkMetadata",
    "FakeMetadataGenerator",
    "MetadataConfigError",
    "MetadataGenerationError",
    "MetadataGenerator",
    "MetadataModelError",
    "MetadataResponseParseError",
    "OpenAICompatibleMetadataGenerator",
    "SlmClientSettings",
]
