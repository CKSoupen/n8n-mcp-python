import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .client import N8nClient
from .config import Config


def build_server(client: N8nClient) -> Server:
    server: Server = Server("n8n-mcp-py")
    # Tools registered in subsequent phases (1-5).
    return server


async def _run() -> None:
    config = Config.from_env()
    client = N8nClient(config)
    server = build_server(client)
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        await client.aclose()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
