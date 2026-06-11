import json
import threading
import asyncio
from typing import AsyncGenerator, Dict, Any

from config import cfg
from exceptions import ExternalAPIError, UpstreamTimeout
from utils.retry import retry_on_transient

try:
    import google.generativeai as genai
    genai_available = True
except Exception:
    genai_available = False


@retry_on_transient()
async def generate_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate text using Google Generative AI SDK (standard generate_content API)."""
    if not genai_available:
        raise ExternalAPIError("Google Generative AI SDK not installed", status_code=500)

    api_key = cfg.gemini_api_key
    if not api_key:
        raise ExternalAPIError("Missing GEMINI_API_KEY", status_code=500)

    model_name = cfg.gemini_model or "models/gemini-3.5-flash"

    # Build a simple prompt by joining messages with role labels
    messages = payload.get("messages") or []
    prompt_parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        prompt_parts.append(f"{role.capitalize()}: {content}")
    prompt_text = "\n".join(prompt_parts)

    # Configure and generate
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Build generation config if options provided
        gen_config = {}
        if payload.get("temperature") is not None:
            gen_config["temperature"] = payload.get("temperature")
        if payload.get("max_tokens") is not None:
            gen_config["max_output_tokens"] = payload.get("max_tokens")

        resp = model.generate_content(prompt_text, generation_config=genai.types.GenerationConfig(**gen_config) if gen_config else None)
        
        # Extract text from response
        reply = resp.text or ""
        return {"id": None, "model": model_name, "choices": [{"text": reply}], "usage": None}
    except Exception as e:
        raise ExternalAPIError(f"Gemini generation failed: {e}")


async def stream_chat(payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Stream text using Google's GenerativeModel.generate_content with streaming."""
    if not genai_available:
        raise ExternalAPIError("Google Generative AI SDK not installed", status_code=500)

    api_key = cfg.gemini_api_key
    if not api_key:
        raise ExternalAPIError("Missing GEMINI_API_KEY", status_code=500)

    model_name = cfg.gemini_model or "models/gemini-3.5-flash"

    # Build prompt string
    messages = payload.get("messages") or []
    prompt_parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        prompt_parts.append(f"{role.capitalize()}: {content}")
    prompt_text = "\n".join(prompt_parts)

    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def run_stream():
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # Build generation config if options provided
            gen_config = {}
            if payload.get("temperature") is not None:
                gen_config["temperature"] = payload.get("temperature")
            if payload.get("max_tokens") is not None:
                gen_config["max_output_tokens"] = payload.get("max_tokens")

            # Stream the response
            stream = model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(**gen_config) if gen_config else None,
                stream=True
            )
            
            for chunk in stream:
                try:
                    text = chunk.text or ""
                    if text:
                        loop.call_soon_threadsafe(q.put_nowait, text)
                except Exception:
                    # ignore malformed chunks
                    continue
        except Exception as e:
            loop.call_soon_threadsafe(q.put_nowait, f"__ERROR__:{e}")
        finally:
            loop.call_soon_threadsafe(q.put_nowait, None)

    thread = threading.Thread(target=run_stream, daemon=True)
    thread.start()

    while True:
        item = await q.get()
        if item is None:
            break
        if isinstance(item, str) and item.startswith("__ERROR__:"):
            msg = item.split(":", 1)[1]
            raise ExternalAPIError(f"Gemini streaming error: {msg}")
        yield item
