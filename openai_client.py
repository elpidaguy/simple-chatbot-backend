import json
from typing import AsyncGenerator, Dict, Any
import httpx
from exceptions import ExternalAPIError, UpstreamTimeout
from config import cfg
from utils.retry import retry_on_transient

OPENAI_BASE = "https://api.openai.com/v1"


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {cfg.openai_api_key}", "Content-Type": "application/json"}


@retry_on_transient()
async def generate_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{OPENAI_BASE}/chat/completions"
    timeout = httpx.Timeout(cfg.request_timeout_seconds, read=cfg.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=_headers(), json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as e:
            raise UpstreamTimeout() from e
        except httpx.HTTPStatusError as e:
            # normalize upstream error
            raise ExternalAPIError(f"OpenAI error: {e.response.text}", status_code=e.response.status_code)


async def stream_chat(payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Call OpenAI with streaming=True and yield raw text pieces as they arrive.
    The caller is responsible for formatting SSE events.
    """
    url = f"{OPENAI_BASE}/chat/completions"
    # ensure streaming
    payload = dict(payload)
    payload["stream"] = True
    timeout = httpx.Timeout(None)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream("POST", url, headers=_headers(), json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    # OpenAI stream sends lines like: data: {json}
                    if line.startswith("data:"):
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            # Try to extract delta content if present
                            choices = obj.get("choices") or []
                            for choice in choices:
                                delta = choice.get("delta") or {}
                                content = delta.get("content")
                                if content:
                                    yield content
                        except Exception:
                            # yield raw chunk if json parse fails
                            yield data
        except httpx.TimeoutException as e:
            raise UpstreamTimeout() from e
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(f"OpenAI stream error: {e.response.text}", status_code=e.response.status_code)
