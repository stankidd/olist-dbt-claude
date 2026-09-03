# Claude Code MCP (Model Context Protocol)

## Overview
MCP connects Claude Code to external services, databases, and APIs.
It gives Claude Code "hands" to interact with systems beyond the local filesystem.

## How MCP Works
MCP servers expose tools that Claude Code can call during a session.
Each tool call goes: Claude decides ? calls tool ? gets result ? continues reasoning.

## Configuration — .mcp.json
Place .mcp.json at your project root. It is auto-loaded by Claude Code.

\\\json
{
  "mcpServers": {
    "dbt": {
      "command": "uvx",
      "args": ["dbt-mcp"],
      "env": {
        "DBT_PROJECT_DIR": ".",
        "DBT_PROFILES_DIR": "."
      }
    }
  }
}
\\\

## DBT MCP Server
The dbt MCP server exposes dbt CLI commands as tools Claude can call:

| Tool | What It Does |
|------|-------------|
| dbt_show | Query raw data to understand source tables |
| dbt_build | Compile, run, and test dbt models |
| dbt_test | Run tests only |
| dbt_run | Run models only |
| dbt_compile | Compile SQL without running |
| dbt_ls | List models matching a selector |
| list_metrics | List all semantic layer metrics |
| get_metadata | Get model metadata and lineage |

## Installing the DBT MCP Server
\\\ash
pip install dbt-mcp
# or
uvx dbt-mcp  # runs without install via uv
\\\

## Adding MCP Servers via CLI
\\\ash
# Add a project-scoped MCP server
claude mcp add --scope project dbt -- uvx dbt-mcp

# List configured servers
claude mcp list

# Remove a server
claude mcp remove dbt
\\\

## Transport Types
- stdio (default): runs as local subprocess — best for dbt, local tools
- http: connects to a remote server — best for SaaS integrations
- sse: legacy remote transport (prefer http for new setups)

## Security Note
Grant MCP servers only the access they need.
For dbt MCP, use a read-only Snowflake role for development,
and a separate write role only for production deployments.
