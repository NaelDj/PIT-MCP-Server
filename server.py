import json
import anyio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from typing import List  # Import List for type hinting
from pathlib import Path
from pit_reader import find_latest_pit_xml, pit_classes, pit_methods

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
        ),
        types.Tool(
            name="pit_find_latest_xml",
            description=(
                "Find the latest PIT mutations.xml under <workspace>/target/pit-reports. "
                "Supports both timestamped subfolders and direct (non-timestamped) layout."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "Absolute path to the project workspace root.",
                    }
                },
                "required": ["workspace"],
            },
        ),
        types.Tool(
            name="pit_classes",
            description=(
                "Return per-class PIT mutation scores (test strength) for a workspace. "
                "Uses the latest mutations.xml under <workspace>/target/pit-reports."
                "A null mutationScore means the class was not covered by any tests "
                "(i.e., no mutants were executed; only NO_COVERAGE mutants exist)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "Absolute path to the project workspace root.",
                    }
                },
                "required": ["workspace"],
            },
        ),
        types.Tool(
            name="pit_methods",
            description=(
                "Return per-method mutation scores (test strength) for a given class, using the latest PIT mutations.xml "
                "under <workspace>/target/pit-reports. "
                "A null mutationScore means that method had no mutants executed by tests (covered=0; only NO_COVERAGE)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "Absolute path to the project workspace root.",
                    },
                    "className": {
                        "type": "string",
                        "description": "Fully qualified class name, e.g., org.example.Calculator",
                    },
                },
                "required": ["workspace", "className"],
            },
        ),


    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict | None = None):
    arguments = arguments or {}

    if name == "ping":
        return [types.TextContent(type="text", text="succeeded")]

    if name == "pit_find_latest_xml":
        workspace_str = arguments.get("workspace")
        if not workspace_str or not isinstance(workspace_str, str):
            raise ValueError("pit_find_latest_xml requires a string 'workspace' argument")

        workspace = Path(workspace_str)
        xml_path = find_latest_pit_xml(workspace)

        # Keep output simple + auditable
        return [
            types.TextContent(
                type="text",
                text=str(xml_path),
            )
        ]
    
    if name == "pit_classes":
        workspace_str = arguments.get("workspace")
        if not workspace_str or not isinstance(workspace_str, str):
            raise ValueError("pit_classes requires a string 'workspace' argument")

        workspace = Path(workspace_str)
        rows = pit_classes(workspace)

        # Return as JSON text (simple + reproducible)
        return [
            types.TextContent(
                type="text",
                text=json.dumps(rows, indent=2),
            )
        ]
    
    if name == "pit_methods":
        workspace_str = arguments.get("workspace")
        class_name = arguments.get("className")
        include_details = arguments.get("includeDetails", True)

        if not workspace_str or not isinstance(workspace_str, str):
            raise ValueError("pit_methods requires a string 'workspace' argument")
        if not class_name or not isinstance(class_name, str):
            raise ValueError("pit_methods requires a string 'className' argument")
        if not isinstance(include_details, bool):
            raise ValueError("pit_methods 'includeDetails' must be a boolean")

        workspace = Path(workspace_str)
        rows = pit_methods(workspace, class_name=class_name, include_details=include_details)

        return [
            types.TextContent(
                type="text",
                text=json.dumps(rows, indent=2),
            )
        ]


    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main)
