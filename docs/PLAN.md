# n8n-mcp-py — Build Plan

## Goal

A Python MCP server wrapping the **n8n public REST API**, packaged as a pip-installable GitHub project. End users add it to Claude Code / Desktop / Cursor with one command and get full programmatic control of their n8n instance.

## Why not use the existing options?

See [`RESEARCH.md`](RESEARCH.md). Short version: the dominant existing MCP (`czlonkowski/n8n-mcp`) is TypeScript and optimized for *building* workflows from a 541-node knowledge base. n8n's own MCP server is gated by a [broken `availableInMCP` toggle](https://github.com/n8n-io/n8n/issues/25987) in v2.8.x. There is no prominent Python implementation. We fill that niche.

## Stack

- `mcp` — official Python MCP SDK, stdio transport
- `httpx` — async HTTP client, browser-UA default to dodge Cloudflare WAFs
- `pydantic` v2 — tool I/O schemas
- `python-dotenv` — env loading
- `pytest` + `respx` — HTTP-mocked tests
- `ruff` — lint + format
- `hatchling` — build backend, single entry point `n8n-mcp`

## Phases

### Phase 0 — Scaffold (✅ done)

Repo layout, `pyproject.toml`, MCP server skeleton, `N8nClient` shell, env config, this plan, research notes.

### Phase 1 — Read-only workflows (~45 min)

Tools:
- `list_workflows(active?, tags?, limit?, cursor?)`
- `get_workflow(id)`
- `get_workflow_tags(id)`

End of phase = parity with the broken built-in MCP, but actually returns workflows. **Demoable.**

### Phase 2 — Workflow mutations (~45 min)

Tools:
- `create_workflow(name, nodes, connections, settings?)`
- `update_workflow(id, ...)`
- `delete_workflow(id)`
- `activate_workflow(id)` / `deactivate_workflow(id)`
- `transfer_workflow(id, destination_project_id)` *(enterprise)*

Mark mutating tools with MCP `destructiveHint: true` annotation. Add a `dry_run` parameter to mutations.

### Phase 3 — Executions (~45 min)

Tools:
- `list_executions(workflow_id?, status?, limit?, cursor?)`
- `get_execution(id, include_data?)`
- `delete_execution(id)`

Add output-size truncation (default 50 KB) so a single huge execution doesn't blow client context.

### Phase 4 — Tags, Credentials, Variables (~45 min)

Standard CRUD per resource. Note: n8n's API never returns credential **values** (security) — only schema/metadata. Document this clearly in the tool description.

### Phase 5 — Enterprise endpoints (~30 min)

Wrap Users, Projects, Source Control (`pull`), Audit (`generate-audit`). Detect license-gated 403/501 responses and surface a friendly "this endpoint requires an n8n Enterprise license" message.

### Phase 6 — Packaging & GitHub (~45 min)

- README install snippets for Claude Code / Claude Desktop / Cursor / Windsurf
- GitHub Actions: ruff + pytest on push
- `pyproject` entry point: `n8n-mcp = "n8n_mcp.server:main"`
- MIT license (already added)
- Optional: PyPI publish workflow

**Total estimate: ~4.5 hours.**

## Cross-cutting concerns

- **Auth**: env-driven (`N8N_BASE_URL`, `N8N_API_KEY`), never accept secrets via tool args.
- **Cloudflare**: default User-Agent is browser-like (`Mozilla/5.0 ...`) since n8n self-hosted often sits behind Cloudflare with a default WAF rule that blocks bare `python/requests` UAs (we hit this in our debugging session — got a 403/error 1010).
- **Pagination**: every list tool exposes `limit` and `cursor`; default `limit=100`, max 250.
- **Error mapping**: n8n's `{message, code}` errors → MCP tool errors with the original payload preserved.
- **No credential leakage**: credential values are never logged or returned.
- **Versioning**: pin `n8n` API contract assumptions to public API v1; document the n8n versions tested against.

## Out of scope (for now)

- Building n8n nodes or workflows from natural language (that's `czlonkowski/n8n-mcp`'s niche).
- A bundled n8n node knowledge base — we trust the user to know their nodes, or to query `czlonkowski/n8n-mcp` separately.
- WebSocket/SSE live tail of executions.
- A web UI.
