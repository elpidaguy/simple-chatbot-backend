from fastapi import APIRouter, Depends
import httpx
from config import cfg
from auth import get_current_user
from exceptions import ExternalAPIError

router = APIRouter(prefix="/api")


@router.get("/models")
async def list_models(user=Depends(get_current_user)):
    """Return the list of models available to the configured Gemini API key."""
    api_key = cfg.gemini_api_key
    if not api_key:
        raise ExternalAPIError("Missing GEMINI_API_KEY", status_code=500)

    url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models") or []
            # normalize to simple list of model names
            names = []
            for m in models:
                if isinstance(m, dict):
                    names.append(m.get("name"))
                else:
                    # fallback, stringify
                    names.append(str(m))
            return {"models": names}
    except httpx.HTTPStatusError as e:
        try:
            body = await e.response.aread()
            text = body.decode("utf-8", errors="replace")
        except Exception:
            text = str(e)
        raise ExternalAPIError(f"Failed to list models: {text}", status_code=(e.response.status_code if e.response is not None else None))
    except Exception as e:
        raise ExternalAPIError(f"Failed to list models: {e}")
