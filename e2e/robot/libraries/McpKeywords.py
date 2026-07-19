"""Robot keywords for MCP SSE evidence tools (T21 / BDD-011–014).

Responsabilidade
    Invocar tools MCP aprovadas via transporte SSE sem logar tokens.

Motivo da separação
    Protocolo MCP não cabe em RequestsLibrary puro; Robot só orquestra.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any


def _token_values() -> list[str]:
    values: list[str] = []
    for key in ("E2E_GITHUB_TOKEN", "GITHUB_TOKEN"):
        raw = os.environ.get(key, "").strip()
        if raw:
            values.append(raw)
    return values


def _assert_no_token(blob: str) -> None:
    for token in _token_values():
        if token and token in blob:
            raise AssertionError("MCP response leaked credential material")


def mcp_list_tools(base_url: str = "http://127.0.0.1:8001") -> list[str]:
    """Lista nomes das tools MCP (deve incluir as 5 aprovadas)."""
    names = asyncio.run(_list_tool_names(base_url.rstrip("/")))
    _assert_no_token(",".join(names))
    return names


def mcp_call_tool(
    name: str,
    arguments_json: str = "{}",
    base_url: str = "http://127.0.0.1:8001",
) -> str:
    """Chama uma tool MCP e retorna JSON string do resultado."""
    args = json.loads(arguments_json) if arguments_json else {}
    payload = asyncio.run(_call_tool(base_url.rstrip("/"), name, args))
    text = json.dumps(payload, default=str)
    _assert_no_token(text)
    return text


async def _list_tool_names(base_url: str) -> list[str]:
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    url = f"{base_url}/sse"
    async with sse_client(url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            listed = await session.list_tools()
            return [t.name for t in listed.tools]


async def _call_tool(
    base_url: str, name: str, arguments: dict[str, Any]
) -> Any:
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    url = f"{base_url}/sse"
    async with sse_client(url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            # structured / content blocks
            if getattr(result, "structuredContent", None) is not None:
                return result.structuredContent
            chunks: list[Any] = []
            for block in getattr(result, "content", ()) or ():
                text = getattr(block, "text", None)
                if text is not None:
                    try:
                        chunks.append(json.loads(text))
                    except json.JSONDecodeError:
                        chunks.append(text)
            return chunks if len(chunks) != 1 else chunks[0]
