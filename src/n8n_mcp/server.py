from mcp.server.fastmcp import FastMCP

from .client import N8nClient
from .config import Config

mcp = FastMCP("n8n-mcp-py")
_client: N8nClient | None = None


def get_client() -> N8nClient:
    global _client
    if _client is None:
        _client = N8nClient(Config.from_env())
    return _client


def main() -> None:
    from . import tools  # noqa: F401  (registers tools as a side effect)

    mcp.run()


if __name__ == "__main__":
    main()
