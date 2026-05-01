from typing import Any

from mcp.types import ToolAnnotations

from ..server import get_client, mcp
from .workflows import _dry_run

_VALID_ROLES = {
    "global:owner",
    "global:admin",
    "global:member",
}


@mcp.tool()
async def list_users(
    limit: int = 100,
    cursor: str | None = None,
    include_role: bool = True,
) -> dict[str, Any]:
    """List users on the n8n instance. Requires an admin/owner role.

    Args:
        limit: 1-250, default 100.
        cursor: Opaque cursor from a previous response's nextCursor.
        include_role: Include the user's global role in each entry.
    """
    params: dict[str, Any] = {"limit": max(1, min(limit, 250))}
    if cursor:
        params["cursor"] = cursor
    if include_role:
        params["includeRole"] = "true"
    raw = await get_client().request("GET", "/users", params=params)
    items = raw.get("data", [])
    return {"data": items, "nextCursor": raw.get("nextCursor"), "count": len(items)}


@mcp.tool()
async def get_user(id_or_email: str, include_role: bool = True) -> dict[str, Any]:
    """Get a user by id or email.

    Args:
        id_or_email: The user id (UUID) or email address.
        include_role: Include the user's global role.
    """
    params = {"includeRole": "true"} if include_role else None
    return await get_client().request("GET", f"/users/{id_or_email}", params=params)


@mcp.tool()
async def create_users(
    invites: list[dict[str, str]],
    dry_run: bool = False,
) -> Any:
    """Invite one or more users to the n8n instance.

    Each invite is {"email": ..., "role": ...} where role is one of
    global:admin, global:member. Owners cannot be created via this endpoint.

    Args:
        invites: List of {email, role} dicts.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    for inv in invites:
        if "email" not in inv:
            raise ValueError("each invite must include 'email'")
        role = inv.get("role")
        if role and role not in _VALID_ROLES:
            raise ValueError(
                f"role must be one of {sorted(_VALID_ROLES)}, got {role!r}"
            )
    if dry_run:
        return _dry_run("POST", "/users", invites)
    return await get_client().request("POST", "/users", json=invites)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
async def change_user_role(
    id_or_email: str,
    new_role: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Change a user's global role.

    Args:
        id_or_email: The user id or email.
        new_role: One of global:owner, global:admin, global:member.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if new_role not in _VALID_ROLES:
        raise ValueError(f"new_role must be one of {sorted(_VALID_ROLES)}")
    body = {"newRoleName": new_role}
    if dry_run:
        return _dry_run("PATCH", f"/users/{id_or_email}/role", body)
    return await get_client().request(
        "PATCH", f"/users/{id_or_email}/role", json=body
    )


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
async def delete_user(id_or_email: str, dry_run: bool = False) -> dict[str, Any]:
    """Delete a user from the instance. Their workflows transfer to the owner.

    Args:
        id_or_email: The user id or email.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/users/{id_or_email}")
    deleted = await get_client().request("DELETE", f"/users/{id_or_email}")
    return {"deleted": True, "user": deleted}
