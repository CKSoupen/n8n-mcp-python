from typing import Any

from mcp.types import ToolAnnotations

from ..server import get_client, mcp
from .workflows import _dry_run


@mcp.tool()
async def get_credential_schema(credential_type: str) -> dict[str, Any]:
    """Get the JSON schema describing the fields a given credential type expects.

    Use this to discover what to put in the `data` argument of create_credential.
    The credential_type is the n8n internal type name, e.g. "githubApi",
    "slackOAuth2Api", "openAiApi". Note that n8n's API does NOT expose
    credential VALUES — there is no list_credentials or get_credential by design,
    and the data you create is opaque after submission.

    Args:
        credential_type: The credential type id (camelCase, e.g. "githubApi").
    """
    return await get_client().request("GET", f"/credentials/schema/{credential_type}")


@mcp.tool()
async def create_credential(
    name: str,
    credential_type: str,
    data: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new credential.

    The data dict must match the schema for credential_type — fetch it first via
    get_credential_schema. Once created, n8n will not return the values back via
    any API call (security feature).

    Args:
        name: Credential display name.
        credential_type: The credential type id (camelCase, e.g. "githubApi").
        data: Credential payload matching the type's schema.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = {"name": name, "type": credential_type, "data": data}
    if dry_run:
        # Don't echo the actual secret values back in dry-run output.
        body_preview = {**body, "data": {k: "***" for k in data}}
        return _dry_run("POST", "/credentials", body_preview)
    return await get_client().request("POST", "/credentials", json=body)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
async def delete_credential(
    credential_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Delete a credential. Workflows referencing it will fail until re-credentialed.

    Args:
        credential_id: The credential id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    if dry_run:
        return _dry_run("DELETE", f"/credentials/{credential_id}")
    deleted = await get_client().request("DELETE", f"/credentials/{credential_id}")
    return {"deleted": True, "credential": deleted}


@mcp.tool()
async def transfer_credential(
    credential_id: str,
    destination_project_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Transfer a credential to a different project (Enterprise license required).

    Args:
        credential_id: Source credential id.
        destination_project_id: Target project id.
        dry_run: If True, return the request that would be sent without calling the API.
    """
    body = {"destinationProjectId": destination_project_id}
    if dry_run:
        return _dry_run("PUT", f"/credentials/{credential_id}/transfer", body)
    return await get_client().request(
        "PUT", f"/credentials/{credential_id}/transfer", json=body
    )
