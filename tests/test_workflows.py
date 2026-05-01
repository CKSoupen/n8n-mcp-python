import httpx
import pytest
import respx

from n8n_mcp.client import N8nApiError, N8nClient
from n8n_mcp.config import Config


@pytest.fixture
def client():
    cfg = Config(base_url="https://n8n.test", api_key="tok")
    return N8nClient(cfg)


@pytest.fixture
def mock_api():
    with respx.mock(base_url="https://n8n.test/api/v1", assert_all_called=False) as r:
        yield r


async def test_list_workflows_summarizes_by_default(monkeypatch, client, mock_api):
    monkeypatch.setenv("N8N_BASE_URL", "https://n8n.test")
    monkeypatch.setenv("N8N_API_KEY", "tok")
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import list_workflows

    mock_api.get("/workflows").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "abc",
                        "name": "W1",
                        "active": True,
                        "isArchived": False,
                        "createdAt": "2026-01-01T00:00:00Z",
                        "updatedAt": "2026-01-02T00:00:00Z",
                        "tags": [],
                        "triggerCount": 1,
                        "nodes": [{"name": "huge", "parameters": {"x": "y" * 10000}}],
                        "connections": {},
                    }
                ],
                "nextCursor": None,
            },
        )
    )

    result = await list_workflows(limit=10)
    assert result["count"] == 1
    assert result["data"][0]["id"] == "abc"
    assert "nodes" not in result["data"][0]


async def test_list_workflows_include_nodes_returns_full(monkeypatch, client, mock_api):
    monkeypatch.setenv("N8N_BASE_URL", "https://n8n.test")
    monkeypatch.setenv("N8N_API_KEY", "tok")
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import list_workflows

    mock_api.get("/workflows").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "abc", "nodes": [{"name": "n1"}]}], "nextCursor": None},
        )
    )

    result = await list_workflows(include_nodes=True)
    assert result["data"][0]["nodes"] == [{"name": "n1"}]


async def test_get_workflow(monkeypatch, client, mock_api):
    monkeypatch.setenv("N8N_BASE_URL", "https://n8n.test")
    monkeypatch.setenv("N8N_API_KEY", "tok")
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import get_workflow

    mock_api.get("/workflows/abc").mock(
        return_value=httpx.Response(200, json={"id": "abc", "name": "W1"})
    )

    result = await get_workflow("abc")
    assert result == {"id": "abc", "name": "W1"}


async def test_get_workflow_tags(monkeypatch, client, mock_api):
    monkeypatch.setenv("N8N_BASE_URL", "https://n8n.test")
    monkeypatch.setenv("N8N_API_KEY", "tok")
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import get_workflow_tags

    mock_api.get("/workflows/abc/tags").mock(
        return_value=httpx.Response(200, json=[{"id": "t1", "name": "billing"}])
    )

    result = await get_workflow_tags("abc")
    assert result == [{"id": "t1", "name": "billing"}]


async def test_api_error_propagates(monkeypatch, client, mock_api):
    monkeypatch.setenv("N8N_BASE_URL", "https://n8n.test")
    monkeypatch.setenv("N8N_API_KEY", "tok")
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import get_workflow

    mock_api.get("/workflows/missing").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )

    with pytest.raises(N8nApiError) as exc:
        await get_workflow("missing")
    assert exc.value.status == 404
