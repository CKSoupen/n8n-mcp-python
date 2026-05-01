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


async def test_source_control_pull(mock_api):
    from n8n_mcp.tools.source_control import source_control_pull

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"variables": {}, "credentials": []})

    mock_api.post("/source-control/pull").mock(side_effect=capture)
    await source_control_pull(force=True, variables={"k": "v"})
    assert sent == {"force": True, "variables": {"k": "v"}}


async def test_generate_audit_default(mock_api):
    from n8n_mcp.tools.audit import generate_audit

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={"Database Settings": {}})

    mock_api.post("/audit").mock(side_effect=capture)
    await generate_audit()
    assert sent == {}


async def test_generate_audit_with_categories(mock_api):
    from n8n_mcp.tools.audit import generate_audit

    sent = {}

    def capture(request):
        nonlocal sent
        sent = json.loads(request.content)
        return httpx.Response(200, json={})

    mock_api.post("/audit").mock(side_effect=capture)
    await generate_audit(categories=["credentials", "nodes"], days_abandoned_workflow=30)
    assert sent == {
        "additionalOptions": {
            "categories": ["credentials", "nodes"],
            "daysAbandonedWorkflow": 30,
        }
    }


async def test_generate_audit_rejects_invalid_category():
    from n8n_mcp.tools.audit import generate_audit

    with pytest.raises(ValueError, match="invalid categories"):
        await generate_audit(categories=["credentials", "made-up"])
