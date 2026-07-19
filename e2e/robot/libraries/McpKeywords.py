"""Robot keywords for MCP SSE evidence tools (T21 / BDD-011–014; T26 / BDD-013).

Responsabilidade
    Invocar tools MCP aprovadas via transporte SSE sem logar tokens.
    Disparar calls concorrentes e avaliar SLO de paralelismo sob limite.

Motivo da separação
    Protocolo MCP não cabe em RequestsLibrary puro; Robot só orquestra.
    Aritmética SLO fica em ``github_rag.concurrency.parallel_slo``.
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from github_rag.concurrency.parallel_slo import evaluate_parallel_slo


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


def mcp_measure_single_call_seconds(
    name: str,
    arguments_json: str = "{}",
    base_url: str = "http://127.0.0.1:8001",
    samples: int = 2,
) -> float:
    """Mediana de ``samples`` chamadas sequenciais (baseline single_seconds)."""
    if samples < 1:
        raise AssertionError(f"samples must be >= 1, got {samples}")
    durations: list[float] = []
    for _ in range(int(samples)):
        started = time.perf_counter()
        mcp_call_tool(name, arguments_json, base_url)
        durations.append(time.perf_counter() - started)
    median = float(statistics.median(durations))
    if median <= 0:
        raise AssertionError("single_seconds baseline measured as non-positive")
    return median


def mcp_parallel_call_tools(
    name: str,
    arguments_json: str,
    n_calls: int,
    base_url: str = "http://127.0.0.1:8001",
) -> dict[str, Any]:
    """Dispara ``n_calls`` sessões MCP em paralelo; retorna results/wall/n_calls."""
    n = int(n_calls)
    if n < 1:
        raise AssertionError(f"n_calls must be >= 1, got {n}")

    def _one(_: int) -> str:
        return mcp_call_tool(name, arguments_json, base_url)

    started = time.perf_counter()
    results: list[str] = []
    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(_one, i) for i in range(n)]
        for future in as_completed(futures):
            results.append(future.result())
    wall_seconds = time.perf_counter() - started
    return {
        "results": results,
        "wall_seconds": wall_seconds,
        "n_calls": n,
    }


def mcp_assert_parallel_slo(
    capacity: int,
    n_calls: int,
    wall_seconds: float,
    single_seconds: float,
) -> None:
    """Delega ``evaluate_parallel_slo``; falha com AssertionError se ok=False."""
    result = evaluate_parallel_slo(
        capacity=int(capacity),
        n_calls=int(n_calls),
        wall_seconds=float(wall_seconds),
        single_seconds=float(single_seconds),
    )
    if not result.ok:
        raise AssertionError(result.reason or "parallel SLO failed")


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
