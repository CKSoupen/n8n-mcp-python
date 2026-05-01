import json
from typing import Any

from mcp.types import ToolAnnotations

from ..server import get_client, mcp
from .workflows import _dry_run

_VALID_STATUSES = {"success", "error", "waiting"}


def _maybe_truncate_data(execution: dict[str, Any], max_bytes: int) -> dict[str, Any]:
    data = execution.get("data")
    if data is None:
        return execution
    serialized = json.dumps(data, default=str)
    size = len(serialized.encode())
    if size <= max_bytes:
        return execution
    return {
        **execution,
        "data": {
            "_truncated": True,
            "_original_size_bytes": size,
            "_note": (
                f"Execution data truncated: {size:,} bytes exceeds the {max_bytes:,} "
                "byte limit. Re-fetch with a larger truncate_kb to see the full data."
            ),
        },
    }


@mcp.tool()
async def list_executions(
    workflow_id: str | None = None,
    status: str | None = None,
    project_id: str | None = None,
    include_data: bool = False,
    truncate_kb: int = 50,
    limit: int = 100,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List workflow executions on the n8n instance.

    Defaults to a slim view (no per-execution data field). Pass include_data=True
    to fetch results — but heavy executions will be truncated per truncate_kb.

    Args:
        workflow_id: Restrict to executions of a specific workflow.
        status: Filter by status. One of: success, error, waiting.
        project_id: Restrict to a specific project (Enterprise).
        include_data: Include the full result data on each execution.
        truncate_kb: Per-execution data truncation threshold in KB. 0 = no limit.
        limit: 1-250, default 100.
        cursor: Opaque cursor from a previous response's nextCursor.
    """
    if status is not None and status not in _VALID_STATUSES:
        raise ValueError(
            f"status must be one of {sorted(_VALID_STATUSES)}, got {status!r}"
        )

    params: dict[str, Any] = {"limit": max(1, min(limit, 250))}
    if workflow_id:
        params["workflowId"] = workflow_id
    if status:
        params["status"] = status
    if project_id:
        params["projectId"] = project_id
    if include_data:
        params["includeData"] = "true"
    if cursor:
        params["cursor"] = cursor

    raw = await get_client().request("GET", "/executions", params=params)
    items = raw.get("data", [])
    if include_data and truncate_kb > 0:
        items = [_maybe_truncate_data(e, truncate_kb * 1024) for e in items]
    return {"data": items, "nextCursor": raw.get("nextCursor"), "count": len(items)}


@mcp.tool()
async def get_execution(
    execution_id: str,
    include_data: bool = True,
    truncate_kb: int = 50,
) -> dict[str, Any]:
    """Get a single execution by id, including its result data by default.

    Args:
        execution_id: The execution id (numeric in older n8n, string in newer).
        include_data: Include the full result data. Default True.
        truncate_kb: Data truncation threshold in KB. 0 = no truncation.
    """
    params = {"includeData": "true"} if include_data else None
    raw = await get_client().request("GET", f"/executions/{execution_id}", params=params)
    if include_data and truncate_kb > 0:
        raw = _maybe_truncate_data(raw, truncate_kb * 1024)
    return raw


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=True,
        idempotentHint=True,
    )
)
async def delete_execution(
    execution_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Delete an execution record. Irreversible.

    Args:
        execution_id: The execution id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/executions/{execution_id}")
    deleted = await get_client().request("DELETE", f"/executions/{execution_id}")
    return {"deleted": True, "execution": deleted}
