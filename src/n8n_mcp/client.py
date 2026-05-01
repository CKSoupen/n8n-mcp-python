from typing import Any

import httpx

from .config import Config


class N8nApiError(RuntimeError):
    def __init__(self, status: int, message: str, payload: Any | None = None):
        super().__init__(f"n8n API {status}: {message}")
        self.status = status
        self.message = message
        self.payload = payload

    @property
    def is_license_gated(self) -> bool:
        """True when the n8n instance refused this endpoint because of license tier.

        Matches both the public 403 "Your license does not allow for feat:..."
        message and the rarer 501 "Not implemented" used by some endpoints.
        """
        if self.status not in (403, 501):
            return False
        msg = (self.message or "").lower()
        return "license" in msg or "feat:" in msg


class N8nClient:
    def __init__(self, config: Config):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=f"{config.base_url}/api/v1",
            headers={
                "X-N8N-API-KEY": config.api_key,
                "Accept": "application/json",
                "User-Agent": config.user_agent,
            },
            timeout=config.timeout_seconds,
            verify=config.verify_ssl,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        resp = await self._client.request(method, path, params=params, json=json)
        if resp.status_code >= 400:
            try:
                payload = resp.json()
                message = payload.get("message", resp.text)
            except Exception:
                payload = None
                message = resp.text
            raise N8nApiError(resp.status_code, message, payload)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()
