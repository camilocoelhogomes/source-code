"""Índice Zoekt — adaptador fino HTTP/CLI oficial (T10).

Responsabilidade
    Re-exportar a superfície pública da porta ExactCodeIndex e do adaptador
    Zoekt (DEC-016).

Motivo da separação
    Callers importam ``from github_rag.index.zoekt import ...`` sem acoplar
    ao layout interno models/client/runner/index/fake.
"""

from github_rag.index.zoekt.client import HttpZoektSearchTransport, ZoektSearchTransport
from github_rag.index.zoekt.errors import ExactCodeIndexError
from github_rag.index.zoekt.fake import FakeExactCodeIndex
from github_rag.index.zoekt.index import ZoektExactCodeIndex
from github_rag.index.zoekt.models import ExactMatch, ExactSearchQuery, FileToIndex
from github_rag.index.zoekt.port import ExactCodeIndex
from github_rag.index.zoekt.runner import (
    SubprocessZoektIndexRunner,
    ZoektIndexRunResult,
    ZoektIndexRunner,
)

__all__ = [
    "ExactCodeIndex",
    "ExactCodeIndexError",
    "ExactMatch",
    "ExactSearchQuery",
    "FakeExactCodeIndex",
    "FileToIndex",
    "HttpZoektSearchTransport",
    "SubprocessZoektIndexRunner",
    "ZoektExactCodeIndex",
    "ZoektIndexRunResult",
    "ZoektIndexRunner",
    "ZoektSearchTransport",
]
