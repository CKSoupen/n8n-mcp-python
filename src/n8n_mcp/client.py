from typing import Any

import httpx

from .config import Config


class N8nApiError(RuntimeError):
    def __init__(self, status: int, message: str, payload: Any | None = None):
        super().__init__(f"n8n API {status}: {message}")
        self.status = status
        self.payload = payload


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
