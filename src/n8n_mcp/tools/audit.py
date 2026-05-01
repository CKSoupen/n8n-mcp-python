from typing import Any

from ..server import get_client, mcp
from .workflows import _dry_run

_VALID_CATEGORIES = {
    "credentials",
    "database",
    "nodes",
    "filesystem",
    "instance",
}


@mcp.tool()
async def generate_audit(
    categories: list[str] | None = None,
    days_abandoned_workflow: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate a security audit report covering the n8n instance.

    Categories: credentials, database, nodes, filesystem, instance. If categories
    is None, n8n returns a report for all categories.

    Args:
        categories: Subset of audit categories to include.
        days_abandoned_workflow: How many inactive days before a workflow is flagged
            as abandoned. Default behavior is n8n's built-in heuristic.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    options: dict[str, Any] = {}
    if categories is not None:
        invalid = [c for c in categories if c not in _VALID_CATEGORIES]
        if invalid:
            raise ValueError(
                f"invalid categories {invalid}, must be from {sorted(_VALID_CATEGORIES)}"
            )
        options["categories"] = categories
    if days_abandoned_workflow is not None:
        options["daysAbandonedWorkflow"] = days_abandoned_workflow

    body = {"additionalOptions": options} if options else {}
    if dry_run:
        return _dry_run("POST", "/audit", body)
    return await get_client().request("POST", "/audit", json=body)
