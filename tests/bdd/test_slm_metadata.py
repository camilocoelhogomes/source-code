"""
BDD executável — T12-slm-metadata.

Valida MD-01..MD-10 (BDD-007 metadados, BDD-010 payload, BDD-024, BR-009/010,
default Qwen Coder 3B, fake per-chunk + falha no meio da lista) conforme bdd.md 0.1.0.

Execução:
    python -m pytest tests/bdd/test_slm_metadata.py -q
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import unittest

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
from tests.unit.index.metadata.helpers import (
    FakeChatCompletions,
    json_metadata_content,
    make_chunk,
    make_chunks,
)


class TestMD01NChunksToNMetadata(unittest.TestCase):
    """MD-01 / BDD-007 — N chunks → N metadados via porta."""

    def test_n_invocations_produce_n_metadata(self) -> None:
        chunks = make_chunks(3)
        snapshots = [dataclasses.asdict(c) for c in chunks]
        gen: MetadataGenerator = FakeMetadataGenerator()
        metas = [gen.generate(c) for c in chunks]

        self.assertEqual(len(metas), 3)
        self.assertEqual(
            [m.chunk_id for m in metas],
            [c.chunk_id for c in chunks],
        )
        self.assertEqual([dataclasses.asdict(c) for c in chunks], snapshots)


class TestMD02FakePerChunk(unittest.TestCase):
    """MD-02 — aceite fake generator per-chunk."""

    def test_per_chunk_association(self) -> None:
        a = make_chunk(chunk_id="a", kind="class", text="class A: pass\n")
        b = make_chunk(chunk_id="b", kind="function", text="def b(): pass\n")
        gen = FakeMetadataGenerator()
        ma, mb = gen.generate(a), gen.generate(b)
        self.assertEqual(ma.chunk_id, "a")
        self.assertEqual(mb.chunk_id, "b")
        self.assertNotEqual(ma.summary, mb.summary)


class TestMD03FailMidList(unittest.TestCase):
    """MD-03 — falha tipada no meio da lista."""

    def test_typed_failure_aborts_caller_loop(self) -> None:
        chunks = make_chunks(3)
        fail_id = chunks[1].chunk_id
        gen = FakeMetadataGenerator(fail_chunk_ids={fail_id})

        collected: list[ChunkMetadata] = []
        with self.assertRaises(MetadataGenerationError) as ctx:
            for chunk in chunks:
                collected.append(gen.generate(chunk))

        self.assertEqual(len(collected), 1)
        self.assertEqual(collected[0].chunk_id, chunks[0].chunk_id)
        self.assertEqual(ctx.exception.chunk_id, fail_id)
        self.assertIsInstance(ctx.exception, MetadataModelError)


class TestMD04SerializablePayload(unittest.TestCase):
    """MD-04 / BDD-010 — metadados serializáveis para payload."""

    def test_to_payload_json_safe(self) -> None:
        meta = ChunkMetadata(
            chunk_id="p-1",
            summary="resumo",
            symbols=("Sym",),
            keywords=("kw",),
            intent="papel",
            extra=(("score", 1), ("ok", True)),
        )
        payload = meta.to_payload()
        self.assertIsInstance(payload["symbols"], list)
        self.assertIsInstance(payload["keywords"], list)
        self.assertIsInstance(payload["extra"], dict)
        self.assertEqual(payload["chunk_id"], "p-1")
        self.assertEqual(payload["summary"], "resumo")
        self.assertEqual(payload["intent"], "papel")
        json.dumps(payload)


class TestMD05OpenaiSdk(unittest.TestCase):
    """MD-05 / BDD-024 — SDK openai, não HTTP caseiro."""

    def test_adapter_uses_openai_sdk_surface(self) -> None:
        mod = importlib.import_module("github_rag.index.metadata.openai_slm")
        source = inspect.getsource(mod)
        self.assertIn("openai", source.lower())
        self.assertNotIn("import httpx", source)
        self.assertNotIn("import requests", source)

        client = FakeChatCompletions(content=json_metadata_content())
        gen = OpenAICompatibleMetadataGenerator(
            client=client,
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        meta = gen.generate(make_chunk(chunk_id="sdk-1"))
        self.assertEqual(meta.chunk_id, "sdk-1")
        self.assertTrue(meta.summary.strip())
        self.assertEqual(len(client.calls), 1)


class TestMD06DefaultQwenCoder3b(unittest.TestCase):
    """MD-06 — default Qwen Coder 3B."""

    def test_default_model_id(self) -> None:
        settings = SlmClientSettings(base_url="http://127.0.0.1:11434/v1")
        self.assertEqual(settings.model, "qwen2.5-coder:3b")

        client = FakeChatCompletions(content=json_metadata_content())
        gen = OpenAICompatibleMetadataGenerator(
            client=client,
            settings=settings,
        )
        gen.generate(make_chunk())
        self.assertEqual(client.calls[0]["model"], "qwen2.5-coder:3b")


class TestMD07ProviderSwap(unittest.TestCase):
    """MD-07 / BR-009 — troca de provedor sem alterar orquestrador."""

    def test_caller_loop_identical_for_fake_and_adapter(self) -> None:
        chunks = make_chunks(2)

        def run(gen: MetadataGenerator) -> list[str]:
            return [gen.generate(c).chunk_id for c in chunks]

        fake = FakeMetadataGenerator()
        adapter = OpenAICompatibleMetadataGenerator(
            client=FakeChatCompletions(
                contents_by_call=[
                    json_metadata_content(summary="s0"),
                    json_metadata_content(summary="s1"),
                ]
            ),
            settings=SlmClientSettings(base_url="http://127.0.0.1:11434/v1"),
        )
        self.assertIsInstance(fake, MetadataGenerator)
        self.assertIsInstance(adapter, MetadataGenerator)
        self.assertEqual(run(fake), [c.chunk_id for c in chunks])
        self.assertEqual(run(adapter), [c.chunk_id for c in chunks])

        overridden = SlmClientSettings(
            base_url="http://127.0.0.1:11434/v1",
            model="other:1b",
        )
        port_params = set(inspect.signature(MetadataGenerator.generate).parameters)
        self.assertIn("chunk", port_params)
        self.assertNotIn("chunks", port_params)
        self.assertEqual(overridden.model, "other:1b")


class TestMD08NoInventChunksNoMcp(unittest.TestCase):
    """MD-08 / BR-010 — sem inventar chunks / sem MCP."""

    def test_chunk_id_preserved_and_no_mcp_surface(self) -> None:
        chunk = make_chunk(chunk_id="original-id")
        meta = FakeMetadataGenerator().generate(chunk)
        self.assertEqual(meta.chunk_id, "original-id")

        for cls in (FakeMetadataGenerator, OpenAICompatibleMetadataGenerator):
            params = set(inspect.signature(cls.generate).parameters)
            self.assertEqual(params, {"self", "chunk"})
            self.assertFalse(hasattr(cls, "call_tool"))
            self.assertFalse(hasattr(cls, "list_tools"))
            self.assertFalse(hasattr(cls, "mcp_response"))


class TestMD09TypedErrorsNoSilentFallback(unittest.TestCase):
    """MD-09 — erros tipados sem fallback silencioso."""

    def test_model_and_parse_errors(self) -> None:
        secret = "sk-super-secret-bdd-key"
        settings = SlmClientSettings(
            base_url="http://127.0.0.1:11434/v1",
            api_key=secret,
        )

        failing = OpenAICompatibleMetadataGenerator(
            client=FakeChatCompletions(raise_exc=TimeoutError("timeout")),
            settings=settings,
        )
        with self.assertRaises(MetadataModelError) as ctx:
            failing.generate(make_chunk(chunk_id="t-out"))
        self.assertNotIn(secret, str(ctx.exception))

        bad_json = OpenAICompatibleMetadataGenerator(
            client=FakeChatCompletions(content="não é json"),
            settings=settings,
        )
        with self.assertRaises(MetadataResponseParseError):
            bad_json.generate(make_chunk(chunk_id="parse"))

        empty_summary = OpenAICompatibleMetadataGenerator(
            client=FakeChatCompletions(content=json_metadata_content(summary="")),
            settings=settings,
        )
        with self.assertRaises(MetadataResponseParseError):
            empty_summary.generate(make_chunk(chunk_id="sum"))


class TestMD10ConfigError(unittest.TestCase):
    """MD-10 — config inválida → MetadataConfigError."""

    def test_invalid_settings_raise_config_error(self) -> None:
        client = FakeChatCompletions(content=json_metadata_content())
        with self.assertRaises(MetadataConfigError):
            OpenAICompatibleMetadataGenerator(
                client=client,
                settings=SlmClientSettings(base_url=""),
            )
        with self.assertRaises(MetadataConfigError):
            OpenAICompatibleMetadataGenerator(
                client=client,
                settings=SlmClientSettings(
                    base_url="http://127.0.0.1:11434/v1",
                    timeout_seconds=-1,
                ),
            )


if __name__ == "__main__":
    unittest.main()
