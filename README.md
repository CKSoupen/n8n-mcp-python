# n8n-mcp-py

[![CI](https://github.com/CKSoupen/n8n-mcp-python/actions/workflows/ci.yml/badge.svg)](https://github.com/CKSoupen/n8n-mcp-python/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A Python **MCP** (Model Context Protocol) server that wraps the **n8n public REST API**, exposing 40 tools any MCP-compatible client (Claude Code, Claude Desktop, Cursor, Windsurf) can call.

## Why

n8n ships its own MCP server, but in self-hosted v2.8.x it depends on a per-workflow `availableInMCP` toggle that [silently fails to persist](https://github.com/n8n-io/n8n/issues/25987). It's also limited to *read + execute* on opt-in workflows — you can't create, update, or manage executions from an MCP client.

This server uses n8n's **public REST API** (no opt-in flags, no UI bug), giving full coverage on workflows, executions, credentials, tags, variables, users, projects, source control, and audit.

## What's inside

| Category | Tools |
|---|---|
| **Workflows** | `list_workflows`, `get_workflow`, `get_workflow_tags`, `create_workflow`, `update_workflow`, `delete_workflow`, `activate_workflow`, `deactivate_workflow`, `transfer_workflow` |
| **Executions** | `list_executions`, `get_execution`, `delete_execution` (with output truncation) |
| **Tags** | `list_tags`, `get_tag`, `create_tag`, `update_tag`, `delete_tag`, `set_workflow_tags` |
| **Credentials** | `get_credential_schema`, `create_credential`, `delete_credential`, `transfer_credential` |
| **Variables** | `list_variables`, `create_variable`, `update_variable`, `delete_variable` |
| **Users** | `list_users`, `get_user`, `create_users`, `change_user_role`, `delete_user` |
| **Projects** *(Enterprise)* | `list_projects`, `create_project`, `update_project`, `delete_project`, `add_users_to_project`, `change_project_user_role`, `remove_user_from_project` |
| **Source control** *(Enterprise)* | `source_control_pull` |
| **Audit** | `generate_audit` |

All mutating tools accept `dry_run=True` to preview the request without calling the API. Destructive tools carry MCP `destructiveHint` annotations so clients can surface confirmation prompts.

## Install

```bash
pip install n8n-mcp-py
```

Or from source:

```bash
git clone https://github.com/CKSoupen/n8n-mcp-python
cd n8n-mcp-python
pip install -e ".[dev]"
```

## Configure

Set two environment variables — either in your shell, in a `.env` file (see [`.env.example`](.env.example)), or via your MCP client's config:

```
N8N_BASE_URL=https://your-n8n.example.com
N8N_API_KEY=eyJhbGc...   # public-api JWT, from n8n Settings → API
```

Optional knobs:

```
N8N_TIMEOUT_SECONDS=30
N8N_USER_AGENT=Mozilla/5.0 (compatible; n8n-mcp-py)
N8N_VERIFY_SSL=true
```

> **Cloudflare note:** the default User-Agent is browser-like because many self-hosted n8n instances sit behind Cloudflare, whose default WAF rules can block bare `python/requests` clients with a 1010 error.

## Add to your MCP client

### Claude Code

```bash
claude mcp add n8n-py -- n8n-mcp
```

Then put `N8N_BASE_URL` and `N8N_API_KEY` in `~/.claude.env` or set them in your shell profile.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "n8n-py": {
      "command": "n8n-mcp",
      "env": {
        "N8N_BASE_URL": "https://your-n8n.example.com",
        "N8N_API_KEY": "eyJhbGc..."
      }
    }
  }
}
```

### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "n8n-py": {
      "command": "n8n-mcp",
      "env": {
        "N8N_BASE_URL": "https://your-n8n.example.com",
        "N8N_API_KEY": "eyJhbGc..."
      }
    }
  }
}
```

### Windsurf

Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "n8n-py": {
      "command": "n8n-mcp",
      "env": {
        "N8N_BASE_URL": "https://your-n8n.example.com",
        "N8N_API_KEY": "eyJhbGc..."
      }
    }
  }
}
```

## Project links

- [Build plan / phases](docs/PLAN.md)
- [Prior-art research](docs/RESEARCH.md)
- [Issues](https://github.com/CKSoupen/n8n-mcp-python/issues)

## Development

```bash
# install
pip install -e ".[dev]"

# lint
ruff check src tests

# test
pytest -q

# run the server locally (stdio) — useful for ad-hoc debugging
N8N_BASE_URL=https://... N8N_API_KEY=... n8n-mcp
```

## License

MIT
