from dataclasses import dataclass, field
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    provider: str = os.getenv("PROVIDER", "gemini")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "models/gemini-3.5-flash")
    test_api_token: str = os.getenv("TEST_API_TOKEN", "local-test-token")
    jwt_secret: Optional[str] = os.getenv("JWT_SECRET")
    allowed_origins: List[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
            if o.strip()
        ]
    )
    default_model: str = os.getenv("DEFAULT_MODEL", "models/gemini-3.5-flash")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

cfg = Config()