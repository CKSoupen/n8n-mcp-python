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


async def test_list_projects(mock_api):
    from n8n_mcp.tools.projects import list_projects

    mock_api.get("/projects").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "p1", "name": "Eng"}]})
    )
    result = await list_projects()
    assert result["data"][0]["name"] == "Eng"


async def test_create_project(mock_api):
    from n8n_mcp.tools.projects import create_project

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"id": "p1", **sent})

    mock_api.post("/projects").mock(side_effect=capture)
    await create_project("Engineering")
    assert sent == {"name": "Engineering"}


async def test_update_project_requires_field():
    from n8n_mcp.tools.projects import update_project

    with pytest.raises(ValueError, match="at least one of"):
        await update_project("p1")


async def test_delete_project(mock_api):
    from n8n_mcp.tools.projects import delete_project

    mock_api.delete("/projects/p1").mock(
        return_value=httpx.Response(200, json={"id": "p1"})
    )
    result = await delete_project("p1")
    assert result["deleted"] is True


async def test_add_users_to_project(mock_api):
    from n8n_mcp.tools.projects import add_users_to_project

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={})

    mock_api.put("/projects/p1/users").mock(side_effect=capture)
    await add_users_to_project(
        "p1", [{"userId": "u1", "role": "project:editor"}]
    )
    assert sent == {"relations": [{"userId": "u1", "role": "project:editor"}]}


async def test_add_users_rejects_bad_role():
    from n8n_mcp.tools.projects import add_users_to_project

    with pytest.raises(ValueError, match="role must be one of"):
        await add_users_to_project(
            "p1", [{"userId": "u1", "role": "project:overlord"}]
        )


async def test_remove_user_from_project(mock_api):
    from n8n_mcp.tools.projects import remove_user_from_project

    mock_api.delete("/projects/p1/users/u1").mock(
        return_value=httpx.Response(204)
    )
    result = await remove_user_from_project("p1", "u1")
    assert result == {"removed": True, "projectId": "p1", "userId": "u1"}
