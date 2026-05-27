# MCP Server for PIT

Minimal MCP server for exposing PIT mutation testing results to LLM agents, such as Cline.

This server was used in the thesis to let an LLM agent query PIT mutation testing results without pasting the full PIT report into the prompt. Instead, the agent can ask for scoped information, such as the latest PIT report, mutation results per class, mutation results per method, and surviving mutants for a specific method.

## Purpose

PIT reports can be large, especially for projects with many classes and mutants. This MCP server provides a small interface around PIT's `mutations.xml` file so that an LLM agent can inspect mutation testing results on demand.

The server reads the latest `mutations.xml` file from:

```text
target/pit-reports/
```

It supports both PIT report layouts:

- `target/pit-reports/mutations.xml`
- `target/pit-reports/<timestamp>/mutations.xml`

## Repository Structure

- `server.py`: defines the MCP server and exposes the available tools.
- `pit_reader.py`: contains the PIT XML parsing logic.
- `README.md`: contains setup and usage instructions.

## Available MCP Tools

The server exposes the following tools:

### `ping`

Connectivity test.

Returns:

```text
succeeded
```

### `pit_find_latest_xml`

Finds the latest PIT `mutations.xml` file under `target/pit-reports`.

Input:

```json
{
  "workspace": "C:/path/to/project"
}
```

### `pit_classes`

Returns mutation results grouped per class for the latest PIT report.

Input:

```json
{
  "workspace": "C:/path/to/project"
}
```

The result includes the class name, mutation score, killed mutants, surviving mutants, and mutants with no coverage.

### `pit_methods`

Returns mutation results grouped per method for a specific class.

Input:

```json
{
  "workspace": "C:/path/to/project",
  "className": "org.example.Calculator"
}
```

The result includes method names, method descriptors, mutation scores, killed mutants, surviving mutants, and mutants with no coverage.

### `pit_survivors_for_method`

Returns surviving mutants for a specific method in a specific class.

Input:

```json
{
  "workspace": "C:/path/to/project",
  "className": "org.example.Calculator",
  "method": "add",
  "methodDesc": "(II)I"
}
```

The `methodDesc` field is optional, but recommended when a method is overloaded.

## Setup

1. Clone this repository:

```bash
git clone https://github.com/NaelDj/PIT-MCPServer.git
cd PIT-MCPServer
```

2. Create and activate a Python virtual environment.

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the required Python packages:

```bash
pip install mcp anyio
```

## Cline Configuration

In Cline, add the following under:

```text
MCP Servers > Configure > Configure MCP Servers
```

Example configuration for Windows:

```json
{
  "mcpServers": {
    "PIT-MCPServer": {
      "command": "C:/Users/[directory]/PIT-MCPServer/.venv/Scripts/python.exe",
      "args": ["C:/Users/[directory]/PIT-MCPServer/server.py"]
    }
  }
}
```

Example configuration for Linux/macOS:

```json
{
  "mcpServers": {
    "PIT-MCPServer": {
      "command": "/home/[user]/PIT-MCPServer/.venv/bin/python",
      "args": ["/home/[user]/PIT-MCPServer/server.py"]
    }
  }
}
```

After adding the configuration, turn on the server in Cline.

## Usage

Before using the MCP tools, run PIT on the target project so that a `mutations.xml` file exists under:

```text
target/pit-reports/
```

The MCP tools expect the `workspace` argument to point to the root of the project being analysed. This is the folder that contains the project `pom.xml` and the `target/pit-reports` directory.

For example:

```json
{
  "workspace": "C:/Users/[user]/mlr-jfreechart"
}
```

## Notes

- The server does not run PIT itself. It only reads the latest PIT XML report.
- The project being analysed should already contain a generated PIT report.
- Mutation scores are calculated from the PIT XML data.
- A `null` mutation score means that no mutants were covered by the tests for that class or method.
