"""Agent endpoint. Calls check_question() then run_agent(), both from src/.

The guardrail logic lives in src/guardrails.py. This router only translates its
result into HTTP: rejection into 422, and a flagged-but-allowed question into the
`flagged` field on the response.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.agent import run_agent
from src.guardrails import GuardrailRejection, check_question

from ..errors import error_detail
from ..ratelimit import ask_limiter
from ..schemas import AskRequest, AskResponse

router = APIRouter(tags=["agent"])
log = logging.getLogger("airspace.guardrails")


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(ask_limiter)])
def ask(payload: AskRequest):
    """Answers a free-form question using the tool-calling agent."""
    try:
        checked = check_question(payload.question)
    except GuardrailRejection as rejection:
        raise HTTPException(
            status_code=422,
            detail=error_detail(rejection.reason, rejection.message),
        )

    if checked["suspicious"]:
        log.warning("possible injection attempt: flags=%s", checked["flags"])

    answer = run_agent(checked["question"], region=payload.region)

    if not answer or not answer.strip():
        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "no_answer",
                "The agent could not produce an answer. Try rephrasing.",
            ),
        )

    return {
        "question": checked["original"],
        "answer": answer,
        "flagged": checked["suspicious"],
    }
