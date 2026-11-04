import json
from typing import Any

import httpx
import pytest

from app.core.errors import LLMNotConfiguredError
from app.core.metrics import REGISTRY
from app.llm.client import Completion, GroqClient, TextDelta

pytestmark = pytest.mark.anyio

USAGE = {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}


def chunk(delta: dict[str, Any], **extra: Any) -> str:
    body = {
        "id": "c1",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "m",
        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        **extra,
    }
    return f"data: {json.dumps(body)}\n\n"


def client_for(handler: Any) -> GroqClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GroqClient("key", "m", timeout=5, http_client=http)


async def test_complete_parses_text_and_tool_calls() -> None:
    seen: dict[str, Any] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "get_metar", "arguments": '{"icao_code": "SBGR"}'},
                }
            ],
        }
        return httpx.Response(
            200,
            json={
                "id": "c1",
                "object": "chat.completion",
                "created": 0,
                "model": "m",
                "choices": [{"index": 0, "message": message, "finish_reason": "tool_calls"}],
                "usage": USAGE,
            },
        )

    tools = [{"type": "function", "function": {"name": "get_metar", "parameters": {}}}]
    before = REGISTRY.get_sample_value("llm_tokens_total", {"feature": "t", "kind": "prompt"}) or 0
    result = await client_for(handle).complete(
        [{"role": "user", "content": "hi"}], tools=tools, label="t"
    )

    assert result.content == ""
    assert result.tool_calls[0].name == "get_metar"
    assert result.tool_calls[0].arguments == '{"icao_code": "SBGR"}'
    assert seen["tool_choice"] == "auto"
    after = REGISTRY.get_sample_value("llm_tokens_total", {"feature": "t", "kind": "prompt"})
    assert after == before + 12


async def test_json_mode_requests_a_json_object() -> None:
    seen: dict[str, Any] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        message = {"role": "assistant", "content": "{}"}
        return httpx.Response(
            200,
            json={
                "id": "c1",
                "object": "chat.completion",
                "created": 0,
                "model": "m",
                "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
            },
        )

    await client_for(handle).complete([{"role": "user", "content": "JSON"}], json_mode=True)
    assert seen["response_format"] == {"type": "json_object"}
    assert "tools" not in seen


async def test_stream_yields_text_and_assembles_split_tool_calls() -> None:
    body = "".join(
        [
            chunk({"role": "assistant", "content": "Checking"}),
            chunk({"content": " now."}),
            chunk(
                {
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "count_aircraft", "arguments": '{"reg'},
                        }
                    ]
                }
            ),
            chunk({"tool_calls": [{"index": 0, "function": {"arguments": 'ion": "europe"}'}}]}),
            chunk({}, x_groq={"usage": USAGE}),
            "data: [DONE]\n\n",
        ]
    )

    def handle(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["stream"] is True
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    events = [e async for e in client_for(handle).stream([{"role": "user", "content": "hi"}])]

    deltas = [e.text for e in events if isinstance(e, TextDelta)]
    final = events[-1]
    assert deltas == ["Checking", " now."]
    assert isinstance(final, Completion)
    assert final.content == "Checking now."
    assert final.tool_calls[0].id == "call_1"
    assert final.tool_calls[0].name == "count_aircraft"
    assert json.loads(final.tool_calls[0].arguments) == {"region": "europe"}


async def test_missing_api_key_raises_not_configured() -> None:
    client = GroqClient(None, "m", timeout=5)
    assert client.configured is False
    with pytest.raises(LLMNotConfiguredError):
        await client.complete([{"role": "user", "content": "hi"}])
