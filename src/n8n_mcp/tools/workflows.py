from typing import Any

from mcp.types import ToolAnnotations

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

# Whitelist of settings keys accepted by n8n's public API on POST/PUT.
# Internal keys like availableInMCP, binaryMode, callerPolicy, timeSavedMode are
# present on stored workflows but rejected as additional properties on write.
_ALLOWED_SETTINGS_KEYS = frozenset(
    {
        "saveExecutionProgress",
        "saveManualExecutions",
        "saveDataErrorExecution",
        "saveDataSuccessExecution",
        "executionTimeout",
        "errorWorkflow",
        "timezone",
        "executionOrder",
    }
)


def _summarize(workflow: dict[str, Any]) -> dict[str, Any]:
    return {k: workflow.get(k) for k in _SUMMARY_FIELDS if k in workflow}


def _clean_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    if not settings:
        return {}
    return {k: v for k, v in settings.items() if k in _ALLOWED_SETTINGS_KEYS}


def _dry_run(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"dry_run": True, "would_call": f"{method} {path}", "body": body}


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


@mcp.tool()
async def create_workflow(
    name: str,
    nodes: list[dict[str, Any]],
    connections: dict[str, Any],
    settings: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new workflow on the n8n instance.

    The new workflow is created INACTIVE. Activate it separately via activate_workflow
    once you've verified the configuration. Settings keys outside the public API
    whitelist are silently dropped (n8n's API rejects unknown keys with a 400).

    Args:
        name: Workflow name (must be non-empty).
        nodes: List of node definitions in n8n's standard format.
        connections: Connection map between nodes.
        settings: Optional workflow settings (executionOrder, timezone, etc.).
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": _clean_settings(settings),
    }
    if dry_run:
        return _dry_run("POST", "/workflows", body)
    return await get_client().request("POST", "/workflows", json=body)


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=True,
        idempotentHint=False,
    )
)
async def update_workflow(
    workflow_id: str,
    name: str | None = None,
    nodes: list[dict[str, Any]] | None = None,
    connections: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    replace: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update an existing workflow.

    By default, performs a partial update: fetches the current workflow, merges in
    the supplied fields, and PUTs the result. Pass replace=True to skip the fetch
    and PUT only the supplied fields (n8n requires the full body, so name+nodes+
    connections must all be present in that case).

    Settings keys outside the public API whitelist (availableInMCP, binaryMode,
    callerPolicy, timeSavedMode, etc.) are silently dropped — preserving them
    causes n8n's API to reject the PUT with a 400.

    Args:
        workflow_id: Target workflow id.
        name: New name, or None to leave unchanged.
        nodes: New node list, or None to leave unchanged.
        connections: New connection map, or None to leave unchanged.
        settings: New settings to merge (whitelisted keys only).
        replace: If True, skip the fetch+merge and PUT exactly what was supplied.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    client = get_client()
    if replace:
        merged: dict[str, Any] = {}
    else:
        current = await client.request("GET", f"/workflows/{workflow_id}")
        merged = {
            "name": current["name"],
            "nodes": current["nodes"],
            "connections": current["connections"],
            "settings": _clean_settings(current.get("settings")),
        }

    if name is not None:
        merged["name"] = name
    if nodes is not None:
        merged["nodes"] = nodes
    if connections is not None:
        merged["connections"] = connections
    if settings is not None:
        merged["settings"] = _clean_settings({**merged.get("settings", {}), **settings})

    if dry_run:
        return _dry_run("PUT", f"/workflows/{workflow_id}", merged)
    return await client.request("PUT", f"/workflows/{workflow_id}", json=merged)


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=True,
        idempotentHint=True,
    )
)
async def delete_workflow(workflow_id: str, dry_run: bool = False) -> dict[str, Any]:
    """Delete a workflow. Irreversible.

    Args:
        workflow_id: Target workflow id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/workflows/{workflow_id}")
    deleted = await get_client().request("DELETE", f"/workflows/{workflow_id}")
    return {"deleted": True, "workflow": deleted}


@mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
async def activate_workflow(workflow_id: str) -> dict[str, Any]:
    """Activate a workflow so its triggers fire.

    Requires the workflow to have at least one trigger node. Idempotent — calling
    on an already-active workflow is a no-op.

    Args:
        workflow_id: Target workflow id.
    """
    return await get_client().request("POST", f"/workflows/{workflow_id}/activate")


@mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
async def deactivate_workflow(workflow_id: str) -> dict[str, Any]:
    """Deactivate a workflow. Triggers stop firing. Idempotent.

    Args:
        workflow_id: Target workflow id.
    """
    return await get_client().request("POST", f"/workflows/{workflow_id}/deactivate")


@mcp.tool()
async def transfer_workflow(
    workflow_id: str,
    destination_project_id: str,
    share_credentials: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Transfer a workflow to a different project (Enterprise license required).

    Args:
        workflow_id: Source workflow id.
        destination_project_id: Target project id.
        share_credentials: Optional list of credential ids to share into the target project.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body: dict[str, Any] = {"destinationProjectId": destination_project_id}
    if share_credentials is not None:
        body["shareCredentials"] = share_credentials
    if dry_run:
        return _dry_run("PUT", f"/workflows/{workflow_id}/transfer", body)
    return await get_client().request("PUT", f"/workflows/{workflow_id}/transfer", json=body)
