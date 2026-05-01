
import httpx
import pytest
import respx

from n8n_mcp.client import N8nClient
from n8n_mcp.config import Config


@pytest.fixture
def client():
    cfg = Config(base_url="https://n8n.test", api_key="tok")
    return N8nClient(cfg)


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


async def test_list_executions_basic(mock_api):
    from n8n_mcp.tools.executions import list_executions

    mock_api.get("/executions").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "1", "status": "success"}, {"id": "2", "status": "error"}],
                "nextCursor": None,
            },
        )
    )

    result = await list_executions()
    assert result["count"] == 2
    assert result["data"][0]["id"] == "1"


async def test_list_executions_filters_to_query_string(mock_api):
    from n8n_mcp.tools.executions import list_executions

    captured = {}

    def capture(request):
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"data": []})

    mock_api.get("/executions").mock(side_effect=capture)
    await list_executions(workflow_id="abc", status="error", include_data=True, limit=50)
    assert captured["params"]["workflowId"] == "abc"
    assert captured["params"]["status"] == "error"
    assert captured["params"]["includeData"] == "true"
    assert captured["params"]["limit"] == "50"


async def test_list_executions_rejects_invalid_status():
    from n8n_mcp.tools.executions import list_executions

    with pytest.raises(ValueError, match="status must be one of"):
        await list_executions(status="bogus")


async def test_get_execution_truncates_large_data(mock_api):
    from n8n_mcp.tools.executions import get_execution

    huge = {"big": "x" * 100_000}
    mock_api.get("/executions/99").mock(
        return_value=httpx.Response(200, json={"id": "99", "data": huge})
    )

    result = await get_execution("99", truncate_kb=10)
    assert result["data"]["_truncated"] is True
    assert result["data"]["_original_size_bytes"] > 10 * 1024
    assert "big" not in result["data"]


async def test_get_execution_no_truncation_when_under_limit(mock_api):
    from n8n_mcp.tools.executions import get_execution

    small = {"items": [1, 2, 3]}
    mock_api.get("/executions/100").mock(
        return_value=httpx.Response(200, json={"id": "100", "data": small})
    )

    result = await get_execution("100", truncate_kb=50)
    assert result["data"] == small


async def test_get_execution_truncate_kb_zero_disables(mock_api):
    from n8n_mcp.tools.executions import get_execution

    huge = {"big": "x" * 100_000}
    mock_api.get("/executions/101").mock(
        return_value=httpx.Response(200, json={"id": "101", "data": huge})
    )

    result = await get_execution("101", truncate_kb=0)
    assert result["data"] == huge


async def test_delete_execution(mock_api):
    from n8n_mcp.tools.executions import delete_execution

    mock_api.delete("/executions/77").mock(
        return_value=httpx.Response(200, json={"id": "77"})
    )

    result = await delete_execution("77")
    assert result["deleted"] is True
    assert result["execution"]["id"] == "77"


async def test_delete_execution_dry_run(mock_api):
    from n8n_mcp.tools.executions import delete_execution

    route = mock_api.delete("/executions/77")
    result = await delete_execution("77", dry_run=True)
    assert result["dry_run"] is True
    assert not route.called
