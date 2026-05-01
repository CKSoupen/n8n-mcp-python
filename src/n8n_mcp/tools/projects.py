from typing import Any

from mcp.types import ToolAnnotations

from ..server import get_client, mcp
from .workflows import _dry_run

_VALID_PROJECT_ROLES = {
    "project:admin",
    "project:editor",
    "project:viewer",
    "project:personalOwner",
}


@mcp.tool()
async def list_projects(
    limit: int = 100, cursor: str | None = None
) -> dict[str, Any]:
    """List projects (Enterprise license required).

    Args:
        limit: 1-250, default 100.
        cursor: Opaque cursor from a previous response's nextCursor.
    """
    params: dict[str, Any] = {"limit": max(1, min(limit, 250))}
    if cursor:
        params["cursor"] = cursor
    raw = await get_client().request("GET", "/projects", params=params)
    items = raw.get("data", [])
    return {"data": items, "nextCursor": raw.get("nextCursor"), "count": len(items)}


@mcp.tool()
async def create_project(name: str, dry_run: bool = False) -> dict[str, Any]:
    """Create a new project (Enterprise license required).

    Args:
        name: Project display name.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = {"name": name}
    if dry_run:
        return _dry_run("POST", "/projects", body)
    return await get_client().request("POST", "/projects", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
async def update_project(
    project_id: str,
    name: str | None = None,
    icon: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update a project's name and/or icon (Enterprise license required).

    Args:
        project_id: The project id.
        name: New name, or None to leave unchanged.
        icon: New icon spec, or None to leave unchanged.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if name is None and icon is None:
        raise ValueError("at least one of name or icon must be provided")
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if icon is not None:
        body["icon"] = icon
    if dry_run:
        return _dry_run("PUT", f"/projects/{project_id}", body)
    return await get_client().request("PUT", f"/projects/{project_id}", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
async def delete_project(project_id: str, dry_run: bool = False) -> dict[str, Any]:
    """Delete a project (Enterprise license required). Workflows in it are also deleted.

    Args:
        project_id: The project id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/projects/{project_id}")
    deleted = await get_client().request("DELETE", f"/projects/{project_id}")
    return {"deleted": True, "project": deleted}


@mcp.tool()
async def add_users_to_project(
    project_id: str,
    relations: list[dict[str, str]],
    dry_run: bool = False,
) -> Any:
    """Add users to a project with roles (Enterprise license required).

    Each relation is {"userId": ..., "role": "project:admin|editor|viewer"}.

    Args:
        project_id: The project id.
        relations: List of {userId, role} dicts.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    for rel in relations:
        if "userId" not in rel or "role" not in rel:
            raise ValueError("each relation must include userId and role")
        if rel["role"] not in _VALID_PROJECT_ROLES:
            raise ValueError(
                f"role must be one of {sorted(_VALID_PROJECT_ROLES)}, got {rel['role']!r}"
            )
    body = {"relations": relations}
    if dry_run:
        return _dry_run("PUT", f"/projects/{project_id}/users", body)
    return await get_client().request("PUT", f"/projects/{project_id}/users", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
async def change_project_user_role(
    project_id: str,
    user_id: str,
    new_role: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Change a user's role within a project (Enterprise license required).

    Args:
        project_id: The project id.
        user_id: The user id.
        new_role: One of project:admin, project:editor, project:viewer.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if new_role not in _VALID_PROJECT_ROLES:
        raise ValueError(f"new_role must be one of {sorted(_VALID_PROJECT_ROLES)}")
    body = {"role": new_role}
    if dry_run:
        return _dry_run("PATCH", f"/projects/{project_id}/users/{user_id}", body)
    return await get_client().request(
        "PATCH", f"/projects/{project_id}/users/{user_id}", json=body
    )


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
async def remove_user_from_project(
    project_id: str,
    user_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Remove a user from a project (Enterprise license required).

    Args:
        project_id: The project id.
        user_id: The user id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/projects/{project_id}/users/{user_id}")
    await get_client().request(
        "DELETE", f"/projects/{project_id}/users/{user_id}"
    )
    return {"removed": True, "projectId": project_id, "userId": user_id}
