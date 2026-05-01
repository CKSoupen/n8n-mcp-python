from typing import Any

from mcp.types import ToolAnnotations

from ..server import get_client, mcp
from .workflows import _dry_run


@mcp.tool()
async def list_tags(limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    """List tags defined on the n8n instance.

    Args:
        limit: 1-250, default 100.
        cursor: Opaque cursor from a previous response's nextCursor.
    """
    params: dict[str, Any] = {"limit": max(1, min(limit, 250))}
    if cursor:
        params["cursor"] = cursor
    raw = await get_client().request("GET", "/tags", params=params)
    items = raw.get("data", [])
    return {"data": items, "nextCursor": raw.get("nextCursor"), "count": len(items)}


@mcp.tool()
async def get_tag(tag_id: str) -> dict[str, Any]:
    """Get a single tag by id.

    Args:
        tag_id: The tag id.
    """
    return await get_client().request("GET", f"/tags/{tag_id}")


@mcp.tool()
async def create_tag(name: str, dry_run: bool = False) -> dict[str, Any]:
    """Create a new tag.

    Args:
        name: Tag name (must be unique on the instance).
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = {"name": name}
    if dry_run:
        return _dry_run("POST", "/tags", body)
    return await get_client().request("POST", "/tags", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
async def update_tag(tag_id: str, name: str, dry_run: bool = False) -> dict[str, Any]:
    """Rename an existing tag.

    Args:
        tag_id: The tag id.
        name: New tag name.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = {"name": name}
    if dry_run:
        return _dry_run("PUT", f"/tags/{tag_id}", body)
    return await get_client().request("PUT", f"/tags/{tag_id}", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
async def delete_tag(tag_id: str, dry_run: bool = False) -> dict[str, Any]:
    """Delete a tag. Removes it from any workflows it was applied to.

    Args:
        tag_id: The tag id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/tags/{tag_id}")
    deleted = await get_client().request("DELETE", f"/tags/{tag_id}")
    return {"deleted": True, "tag": deleted}


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
async def set_workflow_tags(
    workflow_id: str,
    tag_ids: list[str],
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Replace the set of tags applied to a workflow.

    This is a full replacement — any existing tags not in tag_ids are removed.
    Pass an empty list to clear all tags.

    Args:
        workflow_id: The workflow id.
        tag_ids: List of tag ids to apply.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = [{"id": tid} for tid in tag_ids]
    if dry_run:
        return _dry_run("PUT", f"/workflows/{workflow_id}/tags", body)
    return await get_client().request("PUT", f"/workflows/{workflow_id}/tags", json=body)
