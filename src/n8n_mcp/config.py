import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; n8n-mcp-py)"


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    timeout_seconds: float = 30.0
    user_agent: str = DEFAULT_USER_AGENT
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        base_url = os.environ.get("N8N_BASE_URL", "").rstrip("/")
        api_key = os.environ.get("N8N_API_KEY", "")
        if not base_url or not api_key:
            raise RuntimeError(
                "N8N_BASE_URL and N8N_API_KEY must be set (see .env.example)."
            )
        return cls(
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=float(os.environ.get("N8N_TIMEOUT_SECONDS", "30")),
            user_agent=os.environ.get("N8N_USER_AGENT", DEFAULT_USER_AGENT),
            verify_ssl=os.environ.get("N8N_VERIFY_SSL", "true").lower() != "false",
        )
