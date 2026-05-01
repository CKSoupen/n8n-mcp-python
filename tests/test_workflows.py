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


async def test_create_workflow_strips_unknown_settings(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import create_workflow

    posted = {}

    def capture(request):
        nonlocal posted
        import json as _json

        posted = _json.loads(request.content)
        return httpx.Response(200, json={"id": "new-id", **posted})

    mock_api.post("/workflows").mock(side_effect=capture)

    result = await create_workflow(
        name="Test",
        nodes=[],
        connections={},
        settings={
            "executionOrder": "v1",
            "availableInMCP": True,  # rejected by n8n public API
            "binaryMode": "filesystem",  # rejected by n8n public API
        },
    )
    assert result["id"] == "new-id"
    assert posted["settings"] == {"executionOrder": "v1"}


async def test_create_workflow_dry_run_does_not_call_api(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import create_workflow

    route = mock_api.post("/workflows").mock(return_value=httpx.Response(200, json={}))
    result = await create_workflow(name="X", nodes=[], connections={}, dry_run=True)
    assert result["dry_run"] is True
    assert result["would_call"] == "POST /workflows"
    assert not route.called


async def test_update_workflow_partial_merges(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import update_workflow

    mock_api.get("/workflows/abc").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "abc",
                "name": "Old",
                "nodes": [{"name": "n1"}],
                "connections": {"x": "y"},
                "settings": {
                    "executionOrder": "v1",
                    "availableInMCP": False,  # must be stripped on PUT
                },
            },
        )
    )

    sent = {}

    def capture(request):
        nonlocal sent
        import json as _json

        sent = _json.loads(request.content)
        return httpx.Response(200, json={"id": "abc", **sent})

    mock_api.put("/workflows/abc").mock(side_effect=capture)

    await update_workflow("abc", name="New")
    assert sent["name"] == "New"
    assert sent["nodes"] == [{"name": "n1"}]
    assert sent["connections"] == {"x": "y"}
    assert sent["settings"] == {"executionOrder": "v1"}
    assert "availableInMCP" not in sent["settings"]


async def test_update_workflow_replace_skips_fetch(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import update_workflow

    fetch_route = mock_api.get("/workflows/abc")
    put_route = mock_api.put("/workflows/abc").mock(
        return_value=httpx.Response(200, json={"id": "abc"})
    )

    await update_workflow(
        "abc", name="X", nodes=[], connections={}, replace=True
    )
    assert not fetch_route.called
    assert put_route.called


async def test_delete_workflow(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import delete_workflow

    mock_api.delete("/workflows/abc").mock(
        return_value=httpx.Response(200, json={"id": "abc", "name": "gone"})
    )

    result = await delete_workflow("abc")
    assert result["deleted"] is True
    assert result["workflow"]["id"] == "abc"


async def test_delete_workflow_dry_run(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import delete_workflow

    route = mock_api.delete("/workflows/abc")
    result = await delete_workflow("abc", dry_run=True)
    assert result["dry_run"] is True
    assert not route.called


async def test_activate_deactivate(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import activate_workflow, deactivate_workflow

    mock_api.post("/workflows/abc/activate").mock(
        return_value=httpx.Response(200, json={"id": "abc", "active": True})
    )
    mock_api.post("/workflows/abc/deactivate").mock(
        return_value=httpx.Response(200, json={"id": "abc", "active": False})
    )

    a = await activate_workflow("abc")
    d = await deactivate_workflow("abc")
    assert a["active"] is True
    assert d["active"] is False


async def test_transfer_workflow(client, mock_api):
    from n8n_mcp import server as srv

    srv._client = client
    from n8n_mcp.tools.workflows import transfer_workflow

    sent = {}

    def capture(request):
        nonlocal sent
        import json as _json

        sent = _json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    mock_api.put("/workflows/abc/transfer").mock(side_effect=capture)

    await transfer_workflow("abc", "proj-1", share_credentials=["c1", "c2"])
    assert sent == {"destinationProjectId": "proj-1", "shareCredentials": ["c1", "c2"]}
