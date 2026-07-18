"""Adaptador default ``MetadataGenerator`` via SDK oficial ``openai`` (T12).

Responsabilidade deste módulo
    Implementar ``OpenAICompatibleMetadataGenerator`` com
    ``chat.completions.create`` apontando a runtime local OpenAI-compatible.

Motivo da separação
    Concentra DEC-015/BDD-024 atrás da porta; testes injetam client fake
    sem rede. Proibido cliente HTTP caseiro (httpx/requests/urllib).
"""

from __future__ import annotations

import json
from typing import Any

import openai

from github_rag.index.chunk.types import SemanticChunk
from github_rag.index.metadata.config import SlmClientSettings
from github_rag.index.metadata.errors import (
    MetadataConfigError,
    MetadataModelError,
    MetadataResponseParseError,
)
from github_rag.index.metadata.types import ChunkMetadata

_DEFAULT_MODEL = "qwen2.5-coder:3b"
_KNOWN_KEYS = frozenset({"summary", "symbols", "keywords", "intent"})

_SYSTEM_PROMPT = (
    "You generate contextual metadata for a single source-code chunk. "
    "Respond with a single strict JSON object only (no markdown, no prose). "
    "Required keys: summary (non-empty string), symbols (array of strings), "
    "keywords (array of strings), intent (string). "
    "Optional extra keys must be JSON scalars only (string, number, boolean, null)."
)


class OpenAICompatibleMetadataGenerator:
    """``MetadataGenerator`` via SDK ``openai`` (OpenAI-compatible local).

    Responsabilidade
        Montar prompt por chunk, chamar o runtime e parsear JSON → ``ChunkMetadata``.

    Motivo da separação
        Isola transporte/SDK da porta de domínio; client injetável para testes.
    """

    def __init__(
        self,
        client: Any | None = None,
        *,
        settings: SlmClientSettings | None = None,
        model: str | None = None,
    ) -> None:
        if settings is not None:
            effective_model = model if model is not None else settings.model
            self._validate_settings(settings, effective_model=effective_model)
            self._model = effective_model.strip()
            if client is None:
                client = openai.OpenAI(
                    base_url=settings.base_url,
                    api_key=settings.api_key,
                    timeout=settings.timeout_seconds,
                )
        else:
            if client is None:
                raise MetadataConfigError(
                    "settings ou client é obrigatório para OpenAICompatibleMetadataGenerator"
                )
            self._model = (model if model is not None else _DEFAULT_MODEL).strip()
            if not self._model:
                raise MetadataConfigError("model não pode ser vazio")

        self._client = client

    @staticmethod
    def _validate_settings(
        settings: SlmClientSettings,
        *,
        effective_model: str,
    ) -> None:
        if not settings.base_url.strip():
            raise MetadataConfigError("base_url não pode ser vazio")
        if not effective_model.strip():
            raise MetadataConfigError("model não pode ser vazio")
        if settings.timeout_seconds <= 0:
            raise MetadataConfigError("timeout_seconds deve ser positivo")

    def generate(self, chunk: SemanticChunk) -> ChunkMetadata:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_prompt(chunk)},
        ]
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
        except Exception as exc:
            raise MetadataModelError(
                f"falha no runtime SLM: {type(exc).__name__}",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            ) from exc

        content = self._extract_content(response, chunk)
        return self._parse_metadata(content, chunk)

    @staticmethod
    def _build_user_prompt(chunk: SemanticChunk) -> str:
        language = (
            chunk.language.value
            if hasattr(chunk.language, "value")
            else str(chunk.language)
        )
        return (
            f"path: {chunk.path}\n"
            f"language: {language}\n"
            f"kind: {chunk.kind}\n"
            f"start_byte: {chunk.start_byte}\n"
            f"end_byte: {chunk.end_byte}\n"
            f"start_point: {chunk.start_point}\n"
            f"end_point: {chunk.end_point}\n"
            f"text:\n{chunk.text}"
        )

    @staticmethod
    def _extract_content(response: Any, chunk: SemanticChunk) -> str:
        try:
            choices = response.choices
            if not choices:
                raise MetadataModelError(
                    "resposta vazia do modelo (sem choices)",
                    chunk_id=chunk.chunk_id,
                    path=chunk.path,
                )
            content = choices[0].message.content
        except MetadataModelError:
            raise
        except Exception as exc:
            raise MetadataModelError(
                f"resposta inválida do SDK: {type(exc).__name__}",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            ) from exc

        if content is None or (isinstance(content, str) and not content.strip()):
            raise MetadataModelError(
                "resposta vazia do modelo",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            )
        return content if isinstance(content, str) else str(content)

    def _parse_metadata(self, content: str, chunk: SemanticChunk) -> ChunkMetadata:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise MetadataResponseParseError(
                "content não é JSON válido",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            ) from exc

        if not isinstance(data, dict):
            raise MetadataResponseParseError(
                "JSON raiz deve ser objeto",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            )

        summary = data.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise MetadataResponseParseError(
                "summary vazio ou inválido",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            )

        symbols = self._normalize_string_list(
            data.get("symbols", []),
            field="symbols",
            chunk=chunk,
        )
        keywords = self._normalize_string_list(
            data.get("keywords", []),
            field="keywords",
            chunk=chunk,
        )

        intent_raw = data.get("intent", "")
        if intent_raw is None:
            intent = ""
        elif isinstance(intent_raw, str):
            intent = intent_raw
        else:
            raise MetadataResponseParseError(
                "intent deve ser string",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            )

        extra = self._normalize_extra(data, chunk)
        return ChunkMetadata(
            chunk_id=chunk.chunk_id,
            summary=summary,
            symbols=symbols,
            keywords=keywords,
            intent=intent,
            extra=extra,
        )

    @staticmethod
    def _normalize_string_list(
        value: Any,
        *,
        field: str,
        chunk: SemanticChunk,
    ) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list):
            raise MetadataResponseParseError(
                f"{field} deve ser lista",
                chunk_id=chunk.chunk_id,
                path=chunk.path,
            )
        result: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise MetadataResponseParseError(
                    f"{field} deve conter apenas strings",
                    chunk_id=chunk.chunk_id,
                    path=chunk.path,
                )
            if item == "":
                continue  # filtra strings vazias (UT-X02)
            result.append(item)
        return tuple(result)

    @staticmethod
    def _normalize_extra(
        data: dict[str, Any],
        chunk: SemanticChunk,
    ) -> tuple[tuple[str, str | int | float | bool | None], ...]:
        pairs: list[tuple[str, str | int | float | bool | None]] = []
        for key, value in data.items():
            if key in _KNOWN_KEYS:
                continue
            if isinstance(value, (dict, list)):
                raise MetadataResponseParseError(
                    f"extra '{key}' não pode ser nested object/list",
                    chunk_id=chunk.chunk_id,
                    path=chunk.path,
                )
            if not isinstance(value, (str, int, float, bool, type(None))):
                raise MetadataResponseParseError(
                    f"extra '{key}' deve ser escalar JSON-safe",
                    chunk_id=chunk.chunk_id,
                    path=chunk.path,
                )
            pairs.append((key, value))
        return tuple(pairs)
