import logging
import time
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
from groq import AsyncGroq

from app.core.errors import LLMNotConfiguredError
from app.core.metrics import LLM_CALLS, LLM_LATENCY, LLM_TOKENS

log = logging.getLogger(__name__)

Message = dict[str, Any]
ToolSchema = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True, slots=True)
class Completion:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


StreamEvent = TextDelta | Completion


class LLMClient(Protocol):
    @property
    def configured(self) -> bool: ...

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolSchema] | None = None,
        json_mode: bool = False,
        label: str = "llm",
    ) -> Completion: ...

    def stream(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolSchema] | None = None,
        label: str = "llm",
    ) -> AsyncIterator[StreamEvent]: ...


class GroqClient:
    def __init__(
        self,
        api_key: str | None,
        model: str,
        timeout: float,
        temperature: float = 0.2,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.model = model
        self.temperature = temperature
        self._client = (
            AsyncGroq(api_key=api_key, timeout=timeout, max_retries=2, http_client=http_client)
            if api_key
            else None
        )

    @property
    def configured(self) -> bool:
        return self._client is not None

    def _require(self) -> AsyncGroq:
        if self._client is None:
            raise LLMNotConfiguredError("The AI model is not configured on this server.")
        return self._client

    def _request(
        self, messages: Sequence[Message], tools: Sequence[ToolSchema] | None, json_mode: bool
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": list(messages),
            "temperature": self.temperature,
        }
        if tools:
            kwargs["tools"] = list(tools)
            kwargs["tool_choice"] = "auto"
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolSchema] | None = None,
        json_mode: bool = False,
        label: str = "llm",
    ) -> Completion:
        client = self._require()
        LLM_CALLS.labels(label).inc()
        with LLM_LATENCY.labels(label).time():
            response = await client.chat.completions.create(
                **self._request(messages, tools, json_mode)
            )
        _log_usage(label, response.usage)
        message = response.choices[0].message
        calls = [
            ToolCall(c.id, c.function.name, c.function.arguments) for c in message.tool_calls or []
        ]
        return Completion(message.content or "", calls)

    async def stream(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolSchema] | None = None,
        label: str = "llm",
    ) -> AsyncIterator[StreamEvent]:
        client = self._require()
        LLM_CALLS.labels(label).inc()
        started = time.perf_counter()
        chunks = await client.chat.completions.create(
            **self._request(messages, tools, json_mode=False), stream=True
        )
        text: list[str] = []
        partial: dict[int, dict[str, str]] = {}
        async for chunk in chunks:
            usage = getattr(getattr(chunk, "x_groq", None), "usage", None)
            if usage is not None:
                _log_usage(label, usage)
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                text.append(delta.content)
                yield TextDelta(delta.content)
            for call in delta.tool_calls or []:
                slot = partial.setdefault(call.index, {"id": "", "name": "", "arguments": ""})
                if call.id:
                    slot["id"] = call.id
                if call.function and call.function.name:
                    slot["name"] += call.function.name
                if call.function and call.function.arguments:
                    slot["arguments"] += call.function.arguments
        LLM_LATENCY.labels(label).observe(time.perf_counter() - started)
        yield Completion(
            "".join(text),
            [ToolCall(s["id"], s["name"], s["arguments"]) for _, s in sorted(partial.items())],
        )


def _log_usage(label: str, usage: Any) -> None:
    if usage is None:
        return
    LLM_TOKENS.labels(label, "prompt").inc(usage.prompt_tokens or 0)
    LLM_TOKENS.labels(label, "completion").inc(usage.completion_tokens or 0)
    log.info(
        "tokens %s: prompt=%s completion=%s total=%s",
        label,
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
    )
