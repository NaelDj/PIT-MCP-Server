# mcp-pit-server

Minimal MCP server for exposing PIT mutation testing results to LLM agents (e.g. Cline).

In Cline, add the following under MCP Servers > Configure > Configure MCP Servers

```
{
  "mcpServers": {
    "PIT-MCPServer": {
      "command": "C:/Users/[directory]/PIT-MCPServer/.venv/Scripts/python.exe",
      "args": ["C:/Users/[directory]/PIT-MCPServer/server.py"]
    }
  }
}

```

and turn on the server in Cline.
