import logging
from collections.abc import AsyncIterator

from app.llm.client import Completion, LLMClient, Message, TextDelta
from app.llm.tools import ToolRegistry
from app.traffic.regions import REGIONS

log = logging.getLogger(__name__)

MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are an airspace assistant.

STRICT RULES:
- Answer questions about live air traffic and weather ONLY using the tools.
- Never answer from your own knowledge about current traffic, aircraft counts
 or weather. If no tool can answer it, say you don't have that data.
- Data comes from OpenSky (partial volunteer coverage) — mention this when
 reporting aircraft counts.
- Answer in the same language the user asked in.
"""

REGION_CONTEXT = (
    "The user is looking at the map region '{region}'. When the question says "
    '"here", "this region" or names no place, use that region.'
)


class Agent:
    def __init__(self, llm: LLMClient, tools: ToolRegistry, max_iterations: int = MAX_ITERATIONS):
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations

    def initial_messages(self, question: str, region: str | None) -> list[Message]:
        system = SYSTEM_PROMPT
        if region in REGIONS:
            system += "\n" + REGION_CONTEXT.format(region=region)
        return [{"role": "system", "content": system}, {"role": "user", "content": question}]

    async def answer(self, question: str, region: str | None = None) -> str:
        messages = self.initial_messages(question, region)
        seen: dict[tuple[str, str], str] = {}
        for step in range(self.max_iterations):
            completion = await self.llm.complete(
                messages, tools=self.tools.schemas(), label="agent"
            )
            if not completion.tool_calls:
                return completion.content
            if await self._run_tools(messages, completion, seen, step):
                break
        final = await self.llm.complete(messages, label="agent")
        return final.content

    async def stream(self, question: str, region: str | None = None) -> AsyncIterator[str]:
        messages = self.initial_messages(question, region)
        seen: dict[tuple[str, str], str] = {}
        for step in range(self.max_iterations):
            completion: Completion | None = None
            async for event in self.llm.stream(messages, tools=self.tools.schemas(), label="agent"):
                if isinstance(event, TextDelta):
                    yield event.text
                else:
                    completion = event
            if completion is None or not completion.tool_calls:
                return
            if await self._run_tools(messages, completion, seen, step):
                break
        async for event in self.llm.stream(messages, label="agent"):
            if isinstance(event, TextDelta):
                yield event.text

    async def _run_tools(
        self,
        messages: list[Message],
        completion: Completion,
        seen: dict[tuple[str, str], str],
        step: int,
    ) -> bool:
        messages.append(
            {
                "role": "assistant",
                "content": completion.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.name, "arguments": call.arguments},
                    }
                    for call in completion.tool_calls
                ],
            }
        )
        repeated = False
        for call in completion.tool_calls:
            signature = (call.name, call.arguments)
            if signature in seen:
                log.info("step %d: repeated %s, using cached result", step + 1, call.name)
                result = seen[signature]
                repeated = True
            else:
                log.info("step %d: %s(%s)", step + 1, call.name, call.arguments)
                result = await self.tools.execute(call.name, call.arguments)
                seen[signature] = result
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        return repeated
