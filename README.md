# n8n-mcp-py

A Python MCP (Model Context Protocol) server that wraps the **n8n public REST API**, exposing n8n workflow management as tools any MCP-compatible client (Claude Code, Claude Desktop, Cursor, Windsurf) can call.

## Why this exists

n8n ships its own MCP server, but in self-hosted v2.8.x it depends on a per-workflow `availableInMCP` toggle that [silently fails to persist](https://github.com/n8n-io/n8n/issues/25987). It's also limited to read + execute on opt-in workflows — you can't create, update, or manage executions from an MCP client.

This server uses n8n's **public REST API** (no opt-in flags, no UI bug), giving full CRUD coverage on workflows, executions, credentials, tags, variables, and (where licensed) users / projects / source control.

## Status

🚧 **Alpha — under active development.** See [`docs/PLAN.md`](docs/PLAN.md) for the phased build plan.

## Install (once published)

```bash
pip install n8n-mcp-py
```

Or run the dev version:

```bash
git clone https://github.com/CKSoupen/n8n-mcp-python
cd n8n-mcp-python
pip install -e ".[dev]"
```

## Configure

Copy `.env.example` to `.env` and fill in:

```
N8N_BASE_URL=https://your-n8n.example.com
N8N_API_KEY=eyJhbGc...   # public-api JWT, from n8n Settings → API
```

## Add to Claude Code

```bash
claude mcp add n8n-py -- n8n-mcp
```

(or with a full path if you're not using a venv-installed entry point.)

## Project links

- [Plan / phases](docs/PLAN.md)
- [Research notes](docs/RESEARCH.md)

## License

MIT
