from typing import List, Optional, Literal
from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message]
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 1024


class ChatResponse(BaseModel):
    id: Optional[str]
    model: str
    reply: str
    usage: Optional[dict] = None
