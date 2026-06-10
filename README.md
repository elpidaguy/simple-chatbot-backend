# Simple Chatbot Backend

This is a minimal FastAPI backend that proxies chat requests to OpenAI and exposes two endpoints:

- `POST /api/chat` — non-streaming chat completion
- `POST /api/chat/stream` — streaming chat completion via SSE (Server-Sent Events)

Setup (local):

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` and optionally `TEST_API_TOKEN` / `JWT_SECRET`.
2. Create a virtual environment and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run dev server:

```bash
uvicorn main:app --reload --port 8000
```

Auth: by default the `TEST_API_TOKEN` value in `.env` is accepted as a bearer token. If `JWT_SECRET` is set the server will attempt JWT verification for bearer tokens.

Streaming: use `EventSource` (SSE) in the frontend to consume `/api/chat/stream` responses.
# simple-chatbot-backend
A simple AI Chatbot APi build with Python FastAPI
