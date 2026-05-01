import json

import httpx
import pytest
import respx

from n8n_mcp.client import N8nClient
from n8n_mcp.config import Config


@pytest.fixture
def client():
    return N8nClient(Config(base_url="https://n8n.test", api_key="tok"))


@pytest.fixture
def mock_api():
    with respx.mock(base_url="https://n8n.test/api/v1", assert_all_called=False) as r:
        yield r


@pytest.fixture(autouse=True)
def use_test_client(client):
    from n8n_mcp import server as srv

    srv._client = client
    yield
    srv._client = None


async def test_get_credential_schema(mock_api):
    from n8n_mcp.tools.credentials import get_credential_schema

    mock_api.get("/credentials/schema/githubApi").mock(
        return_value=httpx.Response(
            200,
            json={"properties": {"accessToken": {"type": "string"}}},
        )
    )

    result = await get_credential_schema("githubApi")
    assert "properties" in result


async def test_create_credential(mock_api):
    from n8n_mcp.tools.credentials import create_credential

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"id": "c1"})

    mock_api.post("/credentials").mock(side_effect=capture)

    await create_credential("My GH", "githubApi", {"accessToken": "secret"})
    assert sent == {"name": "My GH", "type": "githubApi", "data": {"accessToken": "secret"}}


async def test_create_credential_dry_run_redacts_secrets(mock_api):
    from n8n_mcp.tools.credentials import create_credential

    route = mock_api.post("/credentials")
    result = await create_credential(
        "My GH", "githubApi", {"accessToken": "secret-value"}, dry_run=True
    )
    assert result["dry_run"] is True
    assert result["body"]["data"] == {"accessToken": "***"}
    assert not route.called


async def test_delete_credential(mock_api):
    from n8n_mcp.tools.credentials import delete_credential

    mock_api.delete("/credentials/c1").mock(
        return_value=httpx.Response(200, json={"id": "c1"})
    )

    result = await delete_credential("c1")
    assert result["deleted"] is True


async def test_transfer_credential(mock_api):
    from n8n_mcp.tools.credentials import transfer_credential

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    mock_api.put("/credentials/c1/transfer").mock(side_effect=capture)

    await transfer_credential("c1", "proj-1")
    assert sent == {"destinationProjectId": "proj-1"}
