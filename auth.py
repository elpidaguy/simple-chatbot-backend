from fastapi import Depends, Header
from fastapi import HTTPException
from typing import Optional
import jwt
from config import cfg


def _validate_test_token(token: str) -> bool:
    return token == cfg.test_api_token


def _verify_jwt(token: str) -> Optional[dict]:
    if not cfg.jwt_secret:
        return None
    try:
        payload = jwt.decode(token, cfg.jwt_secret, algorithms=["HS256"])
        return payload
    except Exception:
        return None


async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]
    # Accept the test token
    if _validate_test_token(token):
        return {"sub": "test-user"}

    # Otherwise try JWT verification if secret provided
    payload = _verify_jwt(token)
    if payload:
        return payload

    raise HTTPException(status_code=401, detail="Invalid or expired token")
