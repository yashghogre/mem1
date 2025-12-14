from typing import Optional, Literal, List
from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMChoices(BaseModel):
    index: int
    message: Message
    logprobs: Optional[float]
    finish_reason: str


class LLMUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[LLMChoices]
    usage: LLMUsage
