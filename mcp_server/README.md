# MedMate MCP Server

A Model Context Protocol (MCP) server that exposes medication interaction checking and drug information lookup.

## Tools

- **check_interactions(drugs: list[str])**: Check for drug-drug interactions among a list of medications
- **lookup_drug_info(drug_name: str)**: Look up information about a specific drug

## Running

```bash
python mcp_server/server.py
```

## Integration with ADK

The server is integrated with the MedMate ADK agent via `MCPToolset`:

```python
from google.adk import MCPToolset, StdioServerParameters

mcp_tools = MCPToolset(
    StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
    )
)
```

The agent will automatically discover and use the MCP tools.
