"""Testes unitários — Protocol MetadataGenerator (T12)."""

from __future__ import annotations

import inspect
import unittest

from github_rag.index.metadata.fakes import FakeMetadataGenerator
from github_rag.index.metadata.openai_slm import OpenAICompatibleMetadataGenerator
from github_rag.index.metadata.ports import MetadataGenerator
from tests.unit.index.metadata.helpers import FakeChatCompletions, json_metadata_content


class TestMetadataGeneratorProtocol(unittest.TestCase):
    """UT-P01, UT-P02."""

    def test_ut_p01_runtime_checkable_implementations(self) -> None:
        fake = FakeMetadataGenerator()
        adapter = OpenAICompatibleMetadataGenerator(
            client=FakeChatCompletions(content=json_metadata_content()),
        )
        self.assertIsInstance(fake, MetadataGenerator)
        self.assertIsInstance(adapter, MetadataGenerator)

    def test_ut_p02_generate_accepts_single_chunk_only(self) -> None:
        for cls in (FakeMetadataGenerator, OpenAICompatibleMetadataGenerator):
            params = list(inspect.signature(cls.generate).parameters)
            # self + chunk
            self.assertEqual(params, ["self", "chunk"], msg=cls.__name__)
            self.assertNotIn("chunks", params)
            self.assertNotIn("content", params)
            self.assertNotIn("file", params)


if __name__ == "__main__":
    unittest.main()
