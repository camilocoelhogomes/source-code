"""Testes unitários — OpenAICompatibleMetadataGenerator (T12)."""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import unittest

from github_rag.index.metadata.config import SlmClientSettings
from github_rag.index.metadata.errors import (
    MetadataConfigError,
    MetadataGenerationError,
    MetadataModelError,
    MetadataResponseParseError,
)
from github_rag.index.metadata.openai_slm import OpenAICompatibleMetadataGenerator
from tests.unit.index.metadata.helpers import (
    FakeChatCompletions,
    json_metadata_content,
    make_chunk,
)


def _adapter(
    client: FakeChatCompletions,
    *,
    settings: SlmClientSettings | None = None,
    model: str | None = None,
) -> OpenAICompatibleMetadataGenerator:
    kwargs: dict = {"client": client}
    if settings is not None:
        kwargs["settings"] = settings
    if model is not None:
        kwargs["model"] = model
    return OpenAICompatibleMetadataGenerator(**kwargs)


class TestOpenAICompatibleHappyPath(unittest.TestCase):
    """UT-O01, UT-O06, UT-O08, UT-O10..UT-O12."""

    def test_ut_o01_success_with_fake_client(self) -> None:
        client = FakeChatCompletions(content=json_metadata_content())
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        chunk = make_chunk(chunk_id="ok-1")
        meta = gen.generate(chunk)
        self.assertEqual(meta.chunk_id, "ok-1")
        self.assertTrue(meta.summary.strip())
        self.assertIsInstance(meta.symbols, tuple)
        self.assertIsInstance(meta.keywords, tuple)
        self.assertEqual(len(client.calls), 1)

    def test_ut_o06_default_model_in_completion_call(self) -> None:
        client = FakeChatCompletions(content=json_metadata_content())
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        gen.generate(make_chunk())
        self.assertEqual(client.calls[0].get("model"), "qwen2.5-coder:3b")

    def test_ut_o08_preserves_chunk_id(self) -> None:
        client = FakeChatCompletions(content=json_metadata_content(summary="x"))
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        chunk = make_chunk(chunk_id="keep-me")
        self.assertEqual(gen.generate(chunk).chunk_id, "keep-me")

    def test_ut_o10_normalizes_lists_to_tuples_without_empty_strings(self) -> None:
        client = FakeChatCompletions(
            content=json_metadata_content(
                symbols=["A", "B"],
                keywords=["k1"],
            )
        )
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        meta = gen.generate(make_chunk())
        self.assertEqual(meta.symbols, ("A", "B"))
        self.assertEqual(meta.keywords, ("k1",))
        self.assertTrue(all(s for s in meta.symbols))
        self.assertTrue(all(k for k in meta.keywords))

    def test_ut_o11_does_not_mutate_semantic_chunk(self) -> None:
        client = FakeChatCompletions(content=json_metadata_content())
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        chunk = make_chunk(chunk_id="immutable")
        before = dataclasses.asdict(chunk)
        gen.generate(chunk)
        self.assertEqual(dataclasses.asdict(chunk), before)

    def test_ut_o12_omitted_intent_defaults_empty(self) -> None:
        client = FakeChatCompletions(
            content=json_metadata_content(intent=None)
        )
        # json_metadata_content omits intent key when None
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        meta = gen.generate(make_chunk())
        self.assertEqual(meta.intent, "")


class TestOpenAICompatibleFailures(unittest.TestCase):
    """UT-O02..UT-O05, UT-O07, UT-X02..UT-X05."""

    def test_ut_o02_non_json_content(self) -> None:
        client = FakeChatCompletions(content="```json\nnot really\n```")
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        with self.assertRaises(MetadataResponseParseError):
            gen.generate(make_chunk(chunk_id="bad-json"))

    def test_ut_o03_empty_summary(self) -> None:
        client = FakeChatCompletions(content=json_metadata_content(summary="   "))
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        with self.assertRaises(MetadataResponseParseError):
            gen.generate(make_chunk(chunk_id="empty-summary"))

    def test_ut_o04_sdk_failure(self) -> None:
        client = FakeChatCompletions(raise_exc=RuntimeError("connection refused"))
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        with self.assertRaises(MetadataModelError) as ctx:
            gen.generate(make_chunk(chunk_id="net"))
        self.assertIsInstance(ctx.exception, MetadataGenerationError)
        self.assertEqual(ctx.exception.chunk_id, "net")

    def test_ut_o05_empty_model_content(self) -> None:
        client = FakeChatCompletions(content="")
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        with self.assertRaises(MetadataGenerationError):
            gen.generate(make_chunk(chunk_id="empty-content"))

    def test_ut_o07_invalid_config(self) -> None:
        with self.assertRaises(MetadataConfigError):
            OpenAICompatibleMetadataGenerator(
                client=FakeChatCompletions(content=json_metadata_content()),
                settings=SlmClientSettings(base_url=""),
            )
        with self.assertRaises(MetadataConfigError):
            OpenAICompatibleMetadataGenerator(
                client=FakeChatCompletions(content=json_metadata_content()),
                settings=SlmClientSettings(
                    base_url="http://127.0.0.1:11434/v1",
                    timeout_seconds=0,
                ),
            )
        with self.assertRaises(MetadataConfigError):
            OpenAICompatibleMetadataGenerator(
                client=FakeChatCompletions(content=json_metadata_content()),
                settings=SlmClientSettings(
                    base_url="http://127.0.0.1:11434/v1",
                    model="",
                ),
            )

    def test_ut_x02_empty_symbol_string_rejected_or_filtered(self) -> None:
        client = FakeChatCompletions(
            content=json_metadata_content(symbols=["ok", ""])
        )
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        try:
            meta = gen.generate(make_chunk())
        except MetadataResponseParseError:
            return
        self.assertTrue(all(s for s in meta.symbols))
        self.assertNotIn("", meta.symbols)

    def test_ut_x03_json_array_root(self) -> None:
        client = FakeChatCompletions(content='[{"summary":"x"}]')
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        with self.assertRaises(MetadataResponseParseError):
            gen.generate(make_chunk())

    def test_ut_x04_nested_extra_rejected(self) -> None:
        client = FakeChatCompletions(
            content=json_metadata_content(extra={"nested": {"a": 1}})
        )
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        with self.assertRaises(MetadataResponseParseError):
            gen.generate(make_chunk())

    def test_ut_x05_model_override_on_constructor(self) -> None:
        client = FakeChatCompletions(content=json_metadata_content())
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
            model="custom-coder:7b",
        )
        gen.generate(make_chunk())
        self.assertEqual(client.calls[0].get("model"), "custom-coder:7b")

    def test_ut_x06_no_cross_state(self) -> None:
        client = FakeChatCompletions(
            contents_by_call=[
                json_metadata_content(summary="first"),
                json_metadata_content(summary="second"),
            ]
        )
        gen = _adapter(
            client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        a = gen.generate(make_chunk(chunk_id="a"))
        b = gen.generate(make_chunk(chunk_id="b"))
        self.assertEqual(a.chunk_id, "a")
        self.assertEqual(b.chunk_id, "b")
        self.assertEqual(a.summary, "first")
        self.assertEqual(b.summary, "second")


class TestOpenAISdkConformity(unittest.TestCase):
    """UT-O09 / BDD-024."""

    def test_ut_o09_uses_official_openai_sdk_not_http_homemade(self) -> None:
        mod = importlib.import_module("github_rag.index.metadata.openai_slm")
        source = inspect.getsource(mod)
        self.assertIn("openai", source.lower())
        # Proibido reinventar transporte HTTP ad-hoc como cliente SLM.
        self.assertNotIn("import httpx", source)
        self.assertNotIn("import requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertTrue(
            hasattr(mod, "OpenAICompatibleMetadataGenerator")
            or "OpenAI" in source
        )


if __name__ == "__main__":
    unittest.main()
