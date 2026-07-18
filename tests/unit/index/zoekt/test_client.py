"""Testes unitários — HttpZoektSearchTransport (T10) com mock urllib."""

from __future__ import annotations

import io
import json
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError

from github_rag.index.zoekt.client import HttpZoektSearchTransport


class TestHttpZoektSearchTransport(unittest.TestCase):
    def _transport(self, **kwargs: object) -> HttpZoektSearchTransport:
        return HttpZoektSearchTransport(
            base_url=str(kwargs.pop("base_url", "http://127.0.0.1:6070")),
            timeout_seconds=float(kwargs.pop("timeout_seconds", 30.0)),
        )

    def test_posts_official_json_body_to_api_search(self) -> None:
        body = {"Q": 'content:"authenticate"', "Opts": {"NumContextLines": 2}}
        response_payload = {"Result": {"FileMatches": []}}
        raw = json.dumps(response_payload).encode("utf-8")

        with mock.patch(
            "urllib.request.urlopen",
            return_value=io.BytesIO(raw),
        ) as urlopen:
            # urlopen pode ser usado como context manager; aceitar ambos.
            cm = mock.MagicMock()
            cm.__enter__.return_value = io.BytesIO(raw)
            cm.__exit__.return_value = False
            urlopen.return_value = cm

            transport = self._transport()
            result = transport.post_search(body)

        self.assertEqual(result, response_payload)
        self.assertTrue(urlopen.called)
        req = urlopen.call_args.args[0]
        # Request oficial: URL termina em /api/search
        full_url = req.full_url if hasattr(req, "full_url") else str(req)
        self.assertTrue(
            str(full_url).rstrip("/").endswith("/api/search"),
            msg=full_url,
        )
        data = req.data if hasattr(req, "data") else urlopen.call_args.kwargs.get("data")
        if data is None and len(urlopen.call_args.args) > 1:
            data = urlopen.call_args.args[1]
        self.assertIsNotNone(data)
        parsed = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)
        self.assertEqual(parsed["Q"], body["Q"])
        self.assertEqual(parsed["Opts"]["NumContextLines"], 2)

    def test_returns_parsed_mapping(self) -> None:
        payload = {"Result": {"FileMatches": [{"FileName": "a.py"}]}}
        raw = json.dumps(payload).encode("utf-8")
        cm = mock.MagicMock()
        cm.__enter__.return_value = io.BytesIO(raw)
        cm.__exit__.return_value = False
        with mock.patch("urllib.request.urlopen", return_value=cm):
            result = self._transport().post_search({"Q": "x", "Opts": {}})
        self.assertEqual(result["Result"]["FileMatches"][0]["FileName"], "a.py")

    def test_http_500_raises_envelopable(self) -> None:
        err = HTTPError(
            "http://127.0.0.1:6070/api/search",
            500,
            "Internal Server Error",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises((HTTPError, OSError, URLError, ValueError)):
                self._transport().post_search({"Q": "x", "Opts": {}})

    def test_http_404_raises_envelopable(self) -> None:
        err = HTTPError(
            "http://127.0.0.1:6070/api/search",
            404,
            "Not Found",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises((HTTPError, OSError, URLError, ValueError)):
                self._transport().post_search({"Q": "x", "Opts": {}})

    def test_invalid_json_raises_envelopable(self) -> None:
        cm = mock.MagicMock()
        cm.__enter__.return_value = io.BytesIO(b"not-json{{{")
        cm.__exit__.return_value = False
        with mock.patch("urllib.request.urlopen", return_value=cm):
            with self.assertRaises((ValueError, json.JSONDecodeError, OSError)):
                self._transport().post_search({"Q": "x", "Opts": {}})

    def test_base_url_does_not_duplicate_api_search_path(self) -> None:
        raw = json.dumps({"Result": {}}).encode("utf-8")
        cm = mock.MagicMock()
        cm.__enter__.return_value = io.BytesIO(raw)
        cm.__exit__.return_value = False
        with mock.patch("urllib.request.urlopen", return_value=cm) as urlopen:
            self._transport(base_url="http://zoekt:6070").post_search(
                {"Q": "x", "Opts": {}}
            )
        req = urlopen.call_args.args[0]
        full_url = getattr(req, "full_url", str(req))
        self.assertEqual(str(full_url).count("/api/search"), 1)

    def test_timeout_is_forwarded(self) -> None:
        raw = json.dumps({"Result": {}}).encode("utf-8")
        cm = mock.MagicMock()
        cm.__enter__.return_value = io.BytesIO(raw)
        cm.__exit__.return_value = False
        with mock.patch("urllib.request.urlopen", return_value=cm) as urlopen:
            self._transport(timeout_seconds=1.5).post_search({"Q": "x", "Opts": {}})
        # timeout pode ir como kwarg ou posicional
        kwargs = urlopen.call_args.kwargs
        args = urlopen.call_args.args
        timeout = kwargs.get("timeout")
        if timeout is None and len(args) >= 2:
            timeout = args[1]
        self.assertEqual(timeout, 1.5)


if __name__ == "__main__":
    unittest.main()
