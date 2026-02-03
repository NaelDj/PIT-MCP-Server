import anyio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

app = Server("mcp-ping-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="ping",
            description="Connectivity test. Returns 'succeeded'.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict | None = None):
    if name != "ping":
        raise ValueError(f"Unknown tool: {name}")

    return [types.TextContent(type="text", text="succeeded")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main)
