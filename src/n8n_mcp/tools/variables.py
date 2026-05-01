from typing import Any

from mcp.types import ToolAnnotations

from ..server import get_client, mcp
from .workflows import _dry_run


@mcp.tool()
async def list_variables(limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    """List instance-level variables (Enterprise feature on older n8n; built-in on newer).

    Args:
        limit: 1-250, default 100.
        cursor: Opaque cursor from a previous response's nextCursor.
    """
    params: dict[str, Any] = {"limit": max(1, min(limit, 250))}
    if cursor:
        params["cursor"] = cursor
    raw = await get_client().request("GET", "/variables", params=params)
    items = raw.get("data", [])
    return {"data": items, "nextCursor": raw.get("nextCursor"), "count": len(items)}


@mcp.tool()
async def create_variable(
    key: str,
    value: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new instance variable.

    Args:
        key: Variable key (must be unique on the instance).
        value: Variable value (string).
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = {"key": key, "value": value}
    if dry_run:
        return _dry_run("POST", "/variables", body)
    return await get_client().request("POST", "/variables", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
async def update_variable(
    variable_id: str,
    key: str | None = None,
    value: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update a variable's key and/or value (PUT /variables/{id}).

    Note: not all n8n versions support PUT on variables. If your instance returns
    405 / 404, fall back to delete + create.

    Args:
        variable_id: The variable id.
        key: New key, or None to leave unchanged.
        value: New value, or None to leave unchanged.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if key is None and value is None:
        raise ValueError("At least one of key or value must be provided.")
    body: dict[str, Any] = {}
    if key is not None:
        body["key"] = key
    if value is not None:
        body["value"] = value
    if dry_run:
        return _dry_run("PUT", f"/variables/{variable_id}", body)
    return await get_client().request("PUT", f"/variables/{variable_id}", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
async def delete_variable(
    variable_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Delete a variable. Workflows referencing it will see undefined values.

    Args:
        variable_id: The variable id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/variables/{variable_id}")
    deleted = await get_client().request("DELETE", f"/variables/{variable_id}")
    return {"deleted": True, "variable": deleted}
