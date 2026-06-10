from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import AsyncGenerator
import json

from schemas import ChatRequest, ChatResponse, Message
from openai_client import generate_chat, stream_chat
from auth import get_current_user
from utils.sse import sse_message
from exceptions import ExternalAPIError, UpstreamTimeout

router = APIRouter(prefix="/api")


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, user=Depends(get_current_user)):
    payload = {
        "model": req.model or "gpt-4o-mini",
        "messages": [m.dict() for m in req.messages],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
    }
    try:
        resp = await generate_chat(payload)
        # attempt to normalize response
        choices = resp.get("choices") or []
        reply = ""
        if choices:
            # for chat completions, content may be under message.content
            first = choices[0]
            message = first.get("message") or {}
            reply = message.get("content") or first.get("text") or ""

        return ChatResponse(id=resp.get("id"), model=resp.get("model", ""), reply=reply, usage=resp.get("usage"))
    except UpstreamTimeout:
        return JSONResponse(status_code=504, content={"detail": "Upstream timeout"})
    except ExternalAPIError as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.message})


async def _sse_generator(payload) -> AsyncGenerator[str, None]:
    # stream_chat yields plain text pieces; wrap as SSE
    async for chunk in stream_chat(payload):
        yield sse_message(chunk)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, user=Depends(get_current_user)):
    payload = {
        "model": req.model or "gpt-4o-mini",
        "messages": [m.dict() for m in req.messages],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
    }
    try:
        generator = _sse_generator(payload)
        return StreamingResponse(generator, media_type="text/event-stream")
    except UpstreamTimeout:
        return JSONResponse(status_code=504, content={"detail": "Upstream timeout"})
    except ExternalAPIError as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.message})
