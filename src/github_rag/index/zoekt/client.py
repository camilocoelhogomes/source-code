"""Transporte HTTP oficial Zoekt POST /api/search (T10).

Responsabilidade deste módulo
    Declarar ``ZoektSearchTransport`` e ``HttpZoektSearchTransport`` (stdlib
    urllib) sobre o JSON oficial documentado.

Motivo da separação
    Isola URL, timeout e status HTTP; mockável em unit tests sem processo
    Zoekt (D-T10-002 / DEC-016).
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ZoektSearchTransport(Protocol):
    """Porta fina: POST JSON oficial em ``/api/search``.

    Responsabilidade
        Enviar o body JSON oficial e devolver o mapping da resposta.

    Motivo da separação
        Isola URL/timeout/status; a porta de domínio envelopa erros em
        ``ExactCodeIndexError`` (D-T10-002).
    """

    def post_search(self, body: Mapping[str, Any]) -> Mapping[str, Any]:
        """POST ``{base}/api/search``; devolve mapping JSON da resposta."""
        ...


class HttpZoektSearchTransport:
    """Implementação stdlib de ``ZoektSearchTransport``.

    Responsabilidade
        POST JSON via ``urllib.request`` para ``{base_url}/api/search``.

    Motivo da separação
        Adaptador fino sem SDK proprietário (DEC-016); não interpreta domínio
        além de JSON.
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def post_search(self, body: Mapping[str, Any]) -> Mapping[str, Any]:
        """POST oficial; levanta exceções stdlib para a porta envelopar."""
        url = f"{self._base_url}/api/search"
        payload = json.dumps(dict(body)).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            raw = response.read()
        parsed: Any = json.loads(raw.decode("utf-8"))
        return parsed
