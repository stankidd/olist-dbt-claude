# Claude Code Common Workflows

## Overview
Common patterns and workflows used in Claude Code agentic development.

## Resume Previous Session
Claude Code picks up where it left off by reading CLAUDE.md and recent context.
Start a new session with a clear task description referencing prior work.

## Parallel Workstreams
Run multiple Claude Code instances simultaneously in separate terminal windows,
each working on different parts of the codebase to avoid conflicts.

## Git Workflow
Claude Code follows standard git branching:
- Branch naming: initials/feature-name (e.g. dc/forecasting-model)
- Commits are atomic and descriptive
- PRs are created with full context summaries

## Iterative Build Pattern
The recommended pattern for large builds:
1. Start a fresh Claude Code session for each layer (bronze, silver, gold)
2. Use /clear between layers to avoid context pollution
3. Pass the tech spec each time as the source of truth

## Headless / Automated Mode
Run Claude Code non-interactively via the Agent SDK:
  claude -p "your prompt here" --output-format json

## Checkpoint Pattern
For long-running tasks, Claude Code creates todo lists and checks off
items as it goes. This allows partial recovery if a session is interrupted.

## Context Window Management
- Start a new Claude Code instance for each major task
- Use subagents to isolate exploratory work
- Keep CLAUDE.md concise — it loads on every session

## Working with Large Codebases
Use /compact to summarize prior context before continuing long sessions.
Use subagents to explore unfamiliar areas without polluting main context.
