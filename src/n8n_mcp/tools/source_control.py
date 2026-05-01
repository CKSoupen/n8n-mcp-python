from typing import Any

from mcp.types import ToolAnnotations

from ..server import get_client, mcp
from .workflows import _dry_run


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
async def source_control_pull(
    force: bool = False,
    variables: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Pull latest changes from the connected git remote (Enterprise license required).

    A pull updates workflows, credentials, tags, and variables on the instance to
    match the remote git repo. Marked destructive because local-only changes that
    aren't in git can be overwritten.

    Args:
        force: If True, override conflicts and overwrite local changes.
        variables: Optional map of variable key -> value to seed before pull.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body: dict[str, Any] = {"force": force}
    if variables is not None:
        body["variables"] = variables
    if dry_run:
        return _dry_run("POST", "/source-control/pull", body)
    return await get_client().request("POST", "/source-control/pull", json=body)
