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


async def test_list_variables(mock_api):
    from n8n_mcp.tools.variables import list_variables

    mock_api.get("/variables").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "v1", "key": "API_HOST", "value": "x"}], "nextCursor": None}
        )
    )

    result = await list_variables()
    assert result["count"] == 1
    assert result["data"][0]["key"] == "API_HOST"


async def test_create_variable(mock_api):
    from n8n_mcp.tools.variables import create_variable

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"id": "v1", **sent})

    mock_api.post("/variables").mock(side_effect=capture)

    await create_variable("API_HOST", "https://api.example.com")
    assert sent == {"key": "API_HOST", "value": "https://api.example.com"}


async def test_update_variable_partial(mock_api):
    from n8n_mcp.tools.variables import update_variable

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"id": "v1", **sent})

    mock_api.put("/variables/v1").mock(side_effect=capture)

    await update_variable("v1", value="https://new.example.com")
    assert sent == {"value": "https://new.example.com"}


async def test_update_variable_requires_field():
    from n8n_mcp.tools.variables import update_variable

    with pytest.raises(ValueError, match="At least one of"):
        await update_variable("v1")


async def test_delete_variable_dry_run(mock_api):
    from n8n_mcp.tools.variables import delete_variable

    route = mock_api.delete("/variables/v1")
    result = await delete_variable("v1", dry_run=True)
    assert result["dry_run"] is True
    assert not route.called
