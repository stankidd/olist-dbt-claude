# Claude Code Hooks

## Overview
Hooks are shell commands that run automatically at specific points in the
Claude Code lifecycle, regardless of model behavior. Use hooks for anything
that MUST always execute — linting, formatting, security checks, logging.

## Hook Events

| Event | When It Fires |
|-------|--------------|
| PreToolUse | Before any tool call (Read, Edit, Bash, MCP, etc.) |
| PostToolUse | After any tool call completes |
| Stop | When Claude finishes a response |
| Notification | When Claude sends a user notification |
| SubagentStop | When a subagent completes |

## Hook Configuration
Hooks are defined in .claude/settings.json:

\\\json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "sqlfluff lint \"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Claude session complete' >> logs/claude-activity.log"
          }
        ]
      }
    ]
  }
}
\\\

## Hook Environment Variables
- CLAUDE_TOOL_INPUT — full JSON input to the tool
- CLAUDE_TOOL_INPUT_FILE_PATH — file path being edited (for Edit/Write tools)
- CLAUDE_TOOL_OUTPUT — output from the tool (PostToolUse only)
- CLAUDE_HOOK_EVENT — which event triggered this hook

## DBT-Specific Hook Examples

Run SQLFluff after every SQL file edit:
\\\json
{
  "matcher": "Edit",
  "hooks": [{
    "type": "command",
    "command": "echo \"\\" | jq -r '.file_path' | grep '\\.sql\$' | xargs -r sqlfluff lint"
  }]
}
\\\

Log all dbt MCP calls for audit trail:
\\\json
{
  "matcher": "mcp__dbt",
  "hooks": [{
    "type": "command",
    "command": "echo \"\05/23/2026 09:25:20: \\" >> logs/dbt-mcp-calls.log"
  }]
}
\\\

## Key Rule
Hooks guarantee execution. Prompts do not.
Use hooks for standards enforcement. Use prompts for guidance.
