from typing import Any

from ..server import get_client, mcp

_SUMMARY_FIELDS = (
    "id",
    "name",
    "active",
    "isArchived",
    "createdAt",
    "updatedAt",
    "tags",
    "triggerCount",
)


def _summarize(workflow: dict[str, Any]) -> dict[str, Any]:
    return {k: workflow.get(k) for k in _SUMMARY_FIELDS if k in workflow}


@mcp.tool()
async def list_workflows(
    active: bool | None = None,
    name: str | None = None,
    tags: str | None = None,
    project_id: str | None = None,
    exclude_pinned_data: bool = True,
    limit: int = 100,
    cursor: str | None = None,
    include_nodes: bool = False,
) -> dict[str, Any]:
    """List workflows on the n8n instance.

    Returns a slim summary by default (id, name, active, archived, timestamps, tags,
    triggerCount). Set include_nodes=True to get the full workflow JSON for every
    item — usually too large for a single MCP turn, prefer get_workflow per id.

    Args:
        active: Filter by active status. None returns both.
        name: Substring match on workflow name.
        tags: Comma-separated tag names to filter by.
        project_id: Restrict to a specific n8n project (Enterprise).
        exclude_pinned_data: Strip pinned execution data from results.
        limit: 1-250, default 100.
        cursor: Opaque cursor from a previous response's nextCursor.
        include_nodes: Return full node configs per workflow. Defaults to False.
    """
    params: dict[str, Any] = {"limit": max(1, min(limit, 250))}
    if active is not None:
        params["active"] = "true" if active else "false"
    if name:
        params["name"] = name
    if tags:
        params["tags"] = tags
    if project_id:
        params["projectId"] = project_id
    if exclude_pinned_data:
        params["excludePinnedData"] = "true"
    if cursor:
        params["cursor"] = cursor

    raw = await get_client().request("GET", "/workflows", params=params)
    items = raw.get("data", [])
    data = items if include_nodes else [_summarize(w) for w in items]
    return {"data": data, "nextCursor": raw.get("nextCursor"), "count": len(data)}


@mcp.tool()
async def get_workflow(
    workflow_id: str,
    exclude_pinned_data: bool = False,
) -> dict[str, Any]:
    """Get a single workflow by id, including all nodes, connections, and settings.

    Args:
        workflow_id: The workflow id (e.g. "rs80gpUmpx6skc8M").
        exclude_pinned_data: Strip pinned execution data from the response.
    """
    params = {"excludePinnedData": "true"} if exclude_pinned_data else None
    return await get_client().request("GET", f"/workflows/{workflow_id}", params=params)


@mcp.tool()
async def get_workflow_tags(workflow_id: str) -> list[dict[str, Any]]:
    """List the tags applied to a workflow.

    Args:
        workflow_id: The workflow id.
    """
    return await get_client().request("GET", f"/workflows/{workflow_id}/tags")
