# Prior-art research

Survey of existing n8n MCP servers and how `n8n-mcp-py` differentiates. Conducted 2026-05-01.

## Existing implementations

| Project | Lang | Focus | Notes |
|---|---|---|---|
| [`czlonkowski/n8n-mcp`](https://github.com/czlonkowski/n8n-mcp) | TypeScript | **Building** workflows from natural language | ~187★. 541-node knowledge base, 2,646 example configs, 87% docs coverage. Best-in-class for "AI, build me an n8n workflow that does X". Heavyweight. |
| [`czlonkowski/n8n-manager-for-ai-agents`](https://github.com/czlonkowski/n8n-manager-for-ai-agents) | TypeScript | Managing existing workflows | Sister project to the above, narrower scope. |
| [`leonardsellem/n8n-mcp-server`](https://github.com/leonardsellem/n8n-mcp-server) | TypeScript | API wrapper | Closest to what we want, but TS. |
| [`jasondsmith72/N8N-api-MCP`](https://github.com/jasondsmith72/N8N-api-MCP) | TypeScript | API wrapper + endpoint search | Interesting pattern: ships a local API spec DB so the LLM can discover endpoints. |
| [`ahmadsoliman/mcp-n8n-server`](https://github.com/ahmadsoliman/mcp-n8n-server) | TypeScript | API wrapper | Basic — list workflows, list webhooks. |
| [`makafeli/n8n-workflow-builder`](https://github.com/makafeli/n8n-workflow-builder) | TypeScript | API wrapper | 15 tools, workflow + execution management. |
| [`spences10/mcp-n8n-builder`](https://github.com/spences10/mcp-n8n-builder) | TypeScript | API wrapper + node listing | |
| n8n's official MCP server | n/a | Built into n8n | Gated by per-workflow `availableInMCP` flag, [broken in v2.8.x](https://github.com/n8n-io/n8n/issues/25987). Read + execute only. |

## What we observed

- **No prominent Python implementation.** Every serious option is TypeScript. Python is a clean wedge — many automation/data engineers prefer Python tooling, and Python is easier to extend with custom helpers (pandas-shaped execution analysis, etc.).
- **Most TS wrappers are thin.** They mirror REST endpoints 1:1 with little error mapping or pagination handling. We can do better.
- **The official n8n MCP is broken in self-hosted v2.8.x.** Direct motivation for this project — debugging that bug is what triggered the build.
- **`czlonkowski/n8n-mcp` is the best player for *building* workflows.** We don't compete there. Users who want "AI, design me a Slack→Notion workflow" should still use that. We focus on *managing* the workflows once they exist.

## Differentiation

1. **Python.** Clean niche; easy for Python-shop users to fork and extend.
2. **Full public-API coverage** including enterprise endpoints (gated with friendly errors).
3. **Cloudflare-friendly defaults** — browser-like User-Agent, configurable. n8n self-hosted instances commonly sit behind Cloudflare with default WAF rules that block bare-Python clients (we hit error 1010 during debugging).
4. **Documents the `availableInMCP` story** so users hitting the same bug land on this repo and have a clear answer.
5. **Modern packaging** — pyproject, single entry point, optional PyPI publish.

## What we deliberately don't try to do

- Bundle a node knowledge base. That's `czlonkowski`'s game and they do it well — 541 nodes, 87% docs coverage. We'd be reinventing it badly.
- Build workflows from natural language prompts. Same reason.
- Provide a web UI. n8n's own UI is excellent.

## Sources

- https://github.com/czlonkowski/n8n-mcp
- https://github.com/leonardsellem/n8n-mcp-server
- https://github.com/jasondsmith72/N8N-api-MCP
- https://github.com/ahmadsoliman/mcp-n8n-server
- https://github.com/makafeli/n8n-workflow-builder
- https://github.com/spences10/mcp-n8n-builder
- https://github.com/n8n-io/n8n/issues/25987
- https://community.n8n.io/t/mcp-toggle-available-in-mcp-does-not-save-workflow-never-appears-in-mcp-list-v2-8-3/269457
