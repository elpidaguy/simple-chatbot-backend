from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import cfg
from api.chat import router as chat_router
from api.models import router as models_router
from exceptions import external_api_exception_handler, auth_exception_handler, ExternalAPIError, AuthError
from logging_config import configure_logging


configure_logging()

app = FastAPI(title="Simple Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(models_router)


app.add_exception_handler(ExternalAPIError, external_api_exception_handler)
app.add_exception_handler(AuthError, auth_exception_handler)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
