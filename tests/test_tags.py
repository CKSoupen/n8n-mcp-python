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


async def test_list_tags(mock_api):
    from n8n_mcp.tools.tags import list_tags

    mock_api.get("/tags").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "t1", "name": "billing"}], "nextCursor": None}
        )
    )

    result = await list_tags()
    assert result["count"] == 1
    assert result["data"][0]["name"] == "billing"


async def test_create_tag(mock_api):
    from n8n_mcp.tools.tags import create_tag

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"id": "t1", **sent})

    mock_api.post("/tags").mock(side_effect=capture)

    result = await create_tag("urgent")
    assert sent == {"name": "urgent"}
    assert result["id"] == "t1"


async def test_update_tag_dry_run(mock_api):
    from n8n_mcp.tools.tags import update_tag

    route = mock_api.put("/tags/t1")
    result = await update_tag("t1", "renamed", dry_run=True)
    assert result["dry_run"] is True
    assert result["body"] == {"name": "renamed"}
    assert not route.called


async def test_delete_tag(mock_api):
    from n8n_mcp.tools.tags import delete_tag

    mock_api.delete("/tags/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "name": "gone"})
    )

    result = await delete_tag("t1")
    assert result["deleted"] is True


async def test_set_workflow_tags_replaces(mock_api):
    from n8n_mcp.tools.tags import set_workflow_tags

    sent = []

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json=[{"id": "t1"}, {"id": "t2"}])

    mock_api.put("/workflows/wf1/tags").mock(side_effect=capture)

    await set_workflow_tags("wf1", ["t1", "t2"])
    assert sent == [{"id": "t1"}, {"id": "t2"}]


async def test_set_workflow_tags_clear(mock_api):
    from n8n_mcp.tools.tags import set_workflow_tags

    sent = None

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json=[])

    mock_api.put("/workflows/wf1/tags").mock(side_effect=capture)

    await set_workflow_tags("wf1", [])
    assert sent == []
