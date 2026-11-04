import json
import logging
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.core.errors import AppError

from .client import ToolSchema

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args: type[BaseModel]
    handler: Callable[[Any], Awaitable[str]]

    def schema(self) -> ToolSchema:
        parameters = self.args.model_json_schema()
        parameters.pop("title", None)
        for prop in parameters.get("properties", {}).values():
            prop.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
            },
        }


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool]):
        self._tools = {t.name: t for t in tools}

    @property
    def names(self) -> list[str]:
        return list(self._tools)

    def schemas(self) -> list[ToolSchema]:
        return [t.schema() for t in self._tools.values()]

    async def execute(self, name: str, raw_arguments: str) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'. Available tools: {', '.join(self._tools)}."
        try:
            data = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError:
            return "Error: tool arguments were not valid JSON."
        if not isinstance(data, dict):
            return "Error: tool arguments must be a JSON object."
        try:
            args = tool.args.model_validate(data)
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in error.errors()
            )
            return f"Error: invalid arguments for {name}: {details}"
        try:
            result = await tool.handler(args)
        except (httpx.HTTPError, AppError) as error:
            log.warning("tool %s failed upstream: %s", name, error)
            return (
                f"Error: the data source for {name} is unavailable right now. "
                "Tell the user this part could not be checked."
            )
        return result if result.strip() else "No data available for this request."
