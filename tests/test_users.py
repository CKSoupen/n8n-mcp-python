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


async def test_list_users(mock_api):
    from n8n_mcp.tools.users import list_users

    captured = {}

    def capture(request):
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"data": [{"id": "u1", "email": "a@b.com"}]})

    mock_api.get("/users").mock(side_effect=capture)
    result = await list_users()
    assert captured["params"]["includeRole"] == "true"
    assert result["count"] == 1


async def test_get_user(mock_api):
    from n8n_mcp.tools.users import get_user

    mock_api.get("/users/a@b.com").mock(
        return_value=httpx.Response(200, json={"id": "u1", "email": "a@b.com"})
    )
    result = await get_user("a@b.com")
    assert result["email"] == "a@b.com"


async def test_create_users(mock_api):
    from n8n_mcp.tools.users import create_users

    sent = []

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json=[{"id": "u1"}])

    mock_api.post("/users").mock(side_effect=capture)
    await create_users(
        [{"email": "new@x.com", "role": "global:member"}]
    )
    assert sent == [{"email": "new@x.com", "role": "global:member"}]


async def test_create_users_rejects_invalid_role():
    from n8n_mcp.tools.users import create_users

    with pytest.raises(ValueError, match="role must be one of"):
        await create_users([{"email": "a@b.com", "role": "supreme-leader"}])


async def test_change_user_role(mock_api):
    from n8n_mcp.tools.users import change_user_role

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"id": "u1"})

    mock_api.patch("/users/u1/role").mock(side_effect=capture)
    await change_user_role("u1", "global:admin")
    assert sent == {"newRoleName": "global:admin"}


async def test_delete_user_dry_run(mock_api):
    from n8n_mcp.tools.users import delete_user

    route = mock_api.delete("/users/u1")
    result = await delete_user("u1", dry_run=True)
    assert result["dry_run"] is True
    assert not route.called
