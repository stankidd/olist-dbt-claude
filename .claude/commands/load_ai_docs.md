---
description: Load relevant AI documentation files into context for a specific task
allowed-tools: Read(*)
---

# /load-ai-docs

Load the relevant documentation from .claude/ai_docs/external/ into context
before starting a build or research task.

## Usage
/load-ai-docs $ARGUMENTS

Where $ARGUMENTS specifies what to load:
- "claude" â€” load all Claude Code docs
- "dbt" â€” load all dbt semantic layer docs
- "semantic" â€” load semantic model and metrics docs
- "all" â€” load everything
- (specific topic) â€” e.g. "hooks", "mcp", "metrics"

## Steps

1. **Determine what to load** based on the argument provided:

   If "claude" or "all":
   - Read ai_docs/external/claude-code-common-workflows.md
   - Read ai_docs/external/claude-code-hooks.md
   - Read ai_docs/external/claude-code-mcp.md
   - Read ai_docs/external/claude-code-slash-commands.md
   - Read ai_docs/external/claude-code-sub-agents.md
   - Read ai_docs/external/claude-code-settings.md
   - Read ai_docs/external/claude-models-overview.md

   If "dbt" or "semantic" or "all":
   - Read ai_docs/external/dbt-semantic-models.md
   - Read ai_docs/external/dbt-metrics-overview.md
   - Read ai_docs/external/dbt-entities.md
   - Read ai_docs/external/dbt-measures.md
   - Read ai_docs/external/dbt-dimensions.md

   If specific topic (e.g. "hooks"):
   - Search for the matching file and read it

2. **Confirm** what was loaded:
   Print: "Loaded: [list of files read]"
   Print: "Ready for: [what these docs enable]"
