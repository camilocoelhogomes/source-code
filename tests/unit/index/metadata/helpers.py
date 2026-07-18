"""Helpers e fixtures compartilhados — testes T12-slm-metadata."""

from __future__ import annotations

import json
from typing import Any

from github_rag.index.chunk.types import SemanticChunk, SourceLanguage


def make_chunk(
    *,
    chunk_id: str = "chunk-a",
    path: str = "src/app.py",
    language: SourceLanguage = SourceLanguage.PYTHON,
    kind: str = "function",
    text: str = "def hello():\n    return 1\n",
    start_byte: int = 0,
    end_byte: int | None = None,
) -> SemanticChunk:
    """Constrói um SemanticChunk mínimo válido para testes T12."""
    if end_byte is None:
        end_byte = start_byte + max(len(text.encode("utf-8")), 1)
    return SemanticChunk(
        chunk_id=chunk_id,
        path=path,
        language=language,
        kind=kind,
        text=text,
        start_byte=start_byte,
        end_byte=end_byte,
        start_point=(0, 0),
        end_point=(1, 0),
    )


def make_chunks(n: int, *, prefix: str = "c") -> tuple[SemanticChunk, ...]:
    """N chunks distintos com chunk_ids `{prefix}-{i}`."""
    return tuple(
        make_chunk(
            chunk_id=f"{prefix}-{i}",
            text=f"def f{i}():\n    return {i}\n",
            start_byte=i * 100,
            end_byte=i * 100 + 20,
        )
        for i in range(n)
    )


class FakeChatCompletions:
    """Client OpenAI mínimo: só `chat.completions.create`."""

    def __init__(
        self,
        *,
        content: str | None = None,
        raise_exc: BaseException | None = None,
        contents_by_call: list[str] | None = None,
        empty_choices: bool = False,
        malformed_response: bool = False,
    ) -> None:
        self._content = content
        self._raise_exc = raise_exc
        self._contents_by_call = list(contents_by_call or [])
        self._empty_choices = empty_choices
        self._malformed_response = malformed_response
        self.calls: list[dict[str, Any]] = []
        self.chat = self
        self.completions = self

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self._raise_exc is not None:
            raise self._raise_exc
        if self._malformed_response:
            return type("Resp", (), {})()  # sem atributo choices
        if self._empty_choices:
            return type("Resp", (), {"choices": []})()
        if self._contents_by_call:
            content = self._contents_by_call.pop(0)
        else:
            content = self._content
        message = type("Msg", (), {"content": content})()
        choice = type("Choice", (), {"message": message})()
        return type("Resp", (), {"choices": [choice]})()


def json_metadata_content(
    *,
    summary: str = "resumo do chunk",
    symbols: list[str] | None = None,
    keywords: list[str] | None = None,
    intent: str | None = "explica helper",
    extra: dict[str, Any] | None = None,
) -> str:
    """Serializa JSON de resposta SLM válida para o adaptador."""
    payload: dict[str, Any] = {
        "summary": summary,
        "symbols": symbols if symbols is not None else ["hello"],
        "keywords": keywords if keywords is not None else ["helper"],
    }
    if intent is not None:
        payload["intent"] = intent
    if extra:
        payload.update(extra)
    return json.dumps(payload)
