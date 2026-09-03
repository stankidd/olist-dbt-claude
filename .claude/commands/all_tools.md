---
description: List all available MCP tools and slash commands in this session
allowed-tools: Bash(*)
---

# /all-tools

List every tool and slash command currently available in this Claude Code session.

## Steps

1. List all MCP servers and their exposed tools:
   - Run: `claude mcp list`
   - For each server, show the tools it exposes

2. List all custom slash commands from .claude/commands/

3. List all skills from .claude/skills/

4. Show built-in Claude Code commands

## Output Format

Print a structured summary:

```
=== MCP TOOLS ===
[server-name]
  - tool_name: description

=== CUSTOM COMMANDS ===
/command-name: description

=== SKILLS ===
/skill-name: description

=== BUILT-IN COMMANDS ===
/clear, /compact, /model, /review, /status, /usage ...
```

This command is useful at the start of a new session to confirm
all expected tools are connected before beginning a build task.
