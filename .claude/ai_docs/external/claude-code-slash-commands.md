# Claude Agent SDK — Python

## Overview
The Claude Agent SDK (claude-agent-sdk) is Anthropic's official Python package
for building autonomous AI agents programmatically. It wraps the Claude Code CLI
binary, giving Python code access to the same agentic engine used in the terminal.

## Two Different Packages — Know the Difference

| Package | Purpose | Use When |
|---------|---------|----------|
| anthropic | REST API client | You manage the tool loop yourself |
| claude-agent-sdk | Agentic engine | Claude manages tools autonomously |

## Installation
\\\ash
pip install claude-agent-sdk
\\\

## Basic Usage
\\\python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(
        prompt="Read dbt_project.yml and summarize the model structure",
        options={"cwd": "/path/to/your/dbt/project"}
    ):
        print(message)

asyncio.run(main())
\\\

## Running Headless Builds
\\\python
async for message in query(
    prompt="Build all bronze models from this tech spec: tech-spec.md",
    options={
        "cwd": "/path/to/project",
        "allowedTools": ["Read", "Edit", "Bash", "mcp__dbt__dbt_build"]
    }
):
    print(message)
\\\

## Key Options
- cwd: working directory for the agent
- allowedTools: restrict which tools Claude can use
- maxTurns: limit the number of agentic turns
- model: specify which Claude model to use

## When to Use SDK vs CLI
- CLI: daily interactive development
- SDK: automated pipelines, CI/CD, scheduled builds, multi-agent orchestration

## Headless Mode via CLI
\\\ash
claude -p "Build bronze models from tech-spec.md" --output-format json
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\claude-code-sdk-python.md"

@"
# Claude Code Settings

## Configuration Hierarchy
Settings are applied in this order (later overrides earlier):

1. ~/.claude/settings.json          (global, all projects)
2. .claude/settings.json            (project, shared via git)
3. .claude/settings.local.json      (project, local only, gitignored)
4. ~/.claude/settings.local.json    (global local overrides)

## Key Settings — .claude/settings.json

\\\json
{
  "model": "claude-sonnet-4-20250514",
  "defaultMode": "auto",
  "permissions": {
    "allow": [
      "Bash(dbt build*)",
      "Bash(dbt show*)",
      "Bash(dbt test*)",
      "Bash(git commit*)",
      "Bash(git push*)"
    ],
    "deny": [
      "Bash(rm -rf*)",
      "Edit(.env*)"
    ]
  },
  "hooks": {
    "PostToolUse": []
  }
}
\\\

## Permission Modes
- default: Claude asks before sensitive operations
- auto: Claude uses AI judgment on what is safe (Shift+Tab to cycle)
- bypassPermissions: skips all prompts (use only in trusted automated environments)

## Model Selection
- claude-opus-4: complex architectural reasoning, highest quality
- claude-sonnet-4: general development work, best speed/quality balance
- claude-haiku-4: fast exploration, cheap subagent tasks

## Environment Variables
\\\ash
ANTHROPIC_API_KEY=your-key          # required
CLAUDE_CODE_DEFAULT_MODEL=claude-sonnet-4-20250514
CLAUDE_CODE_MAX_TOKENS=8192
\\\

## DBT Project Recommended Settings
\\\json
{
  "model": "claude-sonnet-4-20250514",
  "defaultMode": "auto",
  "permissions": {
    "allow": [
      "Bash(dbt*)",
      "Bash(git branch*)",
      "Bash(git checkout*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git push*)"
    ],
    "deny": [
      "Edit(.env*)",
      "Bash(rm -rf*)",
      "Bash(drop table*)"
    ]
  }
}
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\claude-code-settings.md"

@"
# Claude Code Slash Commands

## Overview
Slash commands are shortcuts that trigger predefined workflows in Claude Code.
Type / in the Claude Code terminal to see all available commands.

## Built-in Commands

| Command | What It Does |
|---------|-------------|
| /help | Show all available commands |
| /clear | Clear conversation context (start fresh) |
| /compact | Summarize context to save tokens |
| /model | Switch model for current session |
| /review | Review current branch changes |
| /init | Initialize CLAUDE.md for the project |
| /login | Authenticate with Anthropic |
| /logout | Sign out |
| /status | Show current session status |
| /usage | Show token usage and costs |
| /config | Open configuration settings |
| /bug | Report a Claude Code bug |

## Custom Commands (Project Level)
Stored in .claude/commands/ as markdown files.
File name becomes the command name.

Example: .claude/commands/build-bronze-models.md
Invoked as: /build-bronze-models tech-spec.md

## Custom Skills (Recommended over commands)
Stored in .claude/skills/skill-name/SKILL.md
More powerful than commands — support frontmatter, auto-invocation, subagents.

## Passing Arguments
Use \ in your command/skill file to accept input:

\\\markdown
# /build-bronze-models

Load skills/dbt-best-practices.
Build all bronze models from \.
Use dbt show to inspect raw data first.
Run dbt build to validate.
\\\

Called as: /build-bronze-models path/to/tech-spec.md

## Mammoth Growth Commands
| Command | Purpose |
|---------|---------|
| /build-bronze-models | Build bronze layer from tech spec |
| /build-silver-models | Build silver layer from tech spec |
| /build-gold-models | Build gold layer from tech spec |
| /pr-from-spec | Push PR with full context summary |
| /data-profile | Profile source data before building |
| /validate-spec | Validate tech spec completeness |
