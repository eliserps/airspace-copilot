from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.traffic.regions import REGIONS, RegionId, normalise_region

MAX_HISTORY_TURNS = 8
MAX_TURN_LENGTH = 2000


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_TURN_LENGTH)


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=500,
        description="Natural-language question about traffic or weather.",
        examples=["Is the weather good for landing at Guarulhos?"],
    )
    region: RegionId | None = Field(
        default=None,
        description='Map region the user is viewing, so "how many planes here?" resolves.',
        examples=["south_america"],
    )
    history: list[ChatTurn] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_TURNS,
        description="Earlier turns of this conversation, oldest first, so follow-ups resolve.",
    )

    @field_validator("region", mode="before")
    @classmethod
    def known_region(cls, value: object) -> object:
        if isinstance(value, str):
            key = normalise_region(value)
            if key not in REGIONS:
                raise ValueError(f"region must be one of {sorted(REGIONS)}")
            return key
        return value


class AskResponse(BaseModel):
    question: str = Field(description="The question as the user typed it.")
    answer: str = Field(description="Markdown.")
    flagged: bool = Field(
        default=False,
        description="True when the input guardrails flagged a possible injection attempt.",
    )
