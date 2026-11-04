import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.errors import AppError, error_response
from app.dependencies import AgentDep, limit_ask

from .guardrails import CheckedQuestion, check_question
from .schemas import AskRequest, AskResponse

log = logging.getLogger(__name__)

router = APIRouter(tags=["copilot"], dependencies=[Depends(limit_ask)])


class NoAnswerError(AppError):
    status_code = 502
    code = "no_answer"

    def __init__(self) -> None:
        super().__init__("The agent could not produce an answer. Try rephrasing.")


def checked(payload: AskRequest) -> CheckedQuestion:
    result = check_question(payload.question)
    if result.suspicious:
        log.warning("possible injection attempt: flags=%s", result.flags)
    return result


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, agent: AgentDep) -> AskResponse:
    """Answers a free-form question using the tool-calling agent."""
    question = checked(payload)
    answer = await agent.answer(question.question, region=payload.region)
    if not answer.strip():
        raise NoAnswerError()
    return AskResponse(question=question.original, answer=answer, flagged=question.suspicious)


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "/ask/stream",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
    description="Same as /ask, streamed as Server-Sent Events: `meta`, `delta`..., "
    "then `done` or `error`.",
)
async def ask_stream(payload: AskRequest, agent: AgentDep) -> StreamingResponse:
    question = checked(payload)

    async def events() -> AsyncIterator[str]:
        yield sse("meta", {"flagged": question.suspicious})
        received = False
        try:
            async for text in agent.stream(question.question, region=payload.region):
                received = received or bool(text.strip())
                yield sse("delta", {"text": text})
            if not received:
                raise NoAnswerError()
            yield sse("done", {})
        except Exception as exc:
            _, body = error_response(exc)
            yield sse("error", body)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
