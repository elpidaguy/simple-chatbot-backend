from fastapi import Request
from fastapi.responses import JSONResponse


class ExternalAPIError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code


class UpstreamTimeout(Exception):
    pass


class AuthError(Exception):
    pass


async def external_api_exception_handler(request: Request, exc: ExternalAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def auth_exception_handler(request: Request, exc: AuthError):
    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
