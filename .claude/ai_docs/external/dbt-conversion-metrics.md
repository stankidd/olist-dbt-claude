# Claude Code Sub-Agents

## Overview
Sub-agents are isolated Claude Code instances that run in separate context windows.
They do focused work and return only their conclusions to the main agent.
This prevents context bloat and keeps the main session clean.

## Why Sub-Agents Matter
Every file read, tool call, and response consumes tokens from the context window.
On large projects, the main agent's context fills up and quality degrades.
Sub-agents isolate expensive exploration from the main conversation.

## How Sub-Agents Work
\\\
Main Agent
    ¦
    +-- "Explore the source schema" --? Sub-Agent A (clean context)
    ¦                                       Reads 50 tables
    ¦                                       Returns: summary of relevant tables
    ¦
    +-- "Profile the deals table" ---? Sub-Agent B (clean context)
    ¦                                       Runs 10 queries
    ¦                                       Returns: schema + sample data
    ¦
    +-- Uses summaries to build models (main context stays clean)
\\\

## Defining Sub-Agents
Sub-agent files live in .claude/agents/ with YAML frontmatter:

\\\markdown
---
name: schema-explorer
description: Explores and profiles source schemas
tools: [Read, mcp__dbt__dbt_show]
model: claude-haiku-4  # cheap model for exploration
---

# Schema Explorer

Explore the source schema provided.
Return a structured summary of:
- Table names and row counts
- Key columns and data types
- Any data quality observations
\\\

## Invoking Sub-Agents
From a skill or command file:
\\\markdown
Use the schema-explorer subagent to explore raw.\
before building any models.
\\\

## Model Routing Strategy
- Exploration / profiling ? claude-haiku (fast, cheap)
- Building / writing code ? claude-sonnet (balanced)
- Architecture / complex reasoning ? claude-opus (quality)

## DBT Agentic Pattern with Sub-Agents
\\\
Orchestrator (Sonnet)
    ¦
    +-- schema-explorer subagent (Haiku) ? understands raw data
    +-- spec-validator subagent (Haiku) ? confirms tech spec is complete
    ¦
    +-- Builds bronze/silver/gold models with full context
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\claude-code-sub-agents.md"

@"
# Claude Models Overview

## Available Models (2025-2026)

| Model | Best For | Context | Speed |
|-------|---------|---------|-------|
| claude-opus-4 | Complex reasoning, architecture decisions | 200K | Slower |
| claude-sonnet-4 | General development, balanced quality/speed | 200K | Fast |
| claude-haiku-4 | Exploration, profiling, cheap subagent tasks | 200K | Fastest |

## Model String Reference
\\\
claude-opus-4-20250514
claude-sonnet-4-20250514
claude-haiku-4-5-20251001
\\\

## Choosing the Right Model

**Use Opus when:**
- Designing overall data architecture
- Debugging complex multi-model dependency issues
- Writing intricate business logic in gold models
- Reviewing and critiquing tech specs

**Use Sonnet when:**
- Building bronze, silver, gold models (daily work)
- Writing tests and documentation
- Creating PRs and summarizing changes
- Most agentic build tasks (Dylan's choice)

**Use Haiku when:**
- Exploring source schemas
- Profiling data
- Running sub-agents for simple tasks
- Answering quick questions about the codebase

## Setting Model in Claude Code
\\\ash
# Per session
/model claude-opus-4-20250514

# In settings.json (project default)
{ "model": "claude-sonnet-4-20250514" }

# Per sub-agent (in agent frontmatter)
model: claude-haiku-4-5-20251001
\\\

## Extended Thinking
Available on Opus. Enables deeper reasoning for architectural decisions.
\\\ash
claude --thinking  # enable extended thinking mode
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\claude-models-overview.md"

# ---------------------------------------------
# DBT SEMANTIC LAYER DOCUMENTATION FILES
# ---------------------------------------------

@"
# DBT Conversion Metrics

## Overview
Conversion metrics measure how often a base event leads to a conversion event
within a defined time window. Used for funnel analysis and attribution.

## YAML Structure
\\\yaml
metrics:
  - name: visit_to_purchase_rate
    description: "Percentage of visits that result in a purchase within 7 days"
    type: conversion
    label: Visit to Purchase Rate
    type_params:
      fills_nulls_with: 0
      conversion_type_params:
        base_measure: visits
        conversion_measure: purchases
        entity: user
        window: 7 days
        calculate_per_base_measures: false
\\\

## Key Parameters
- base_measure: the starting event (e.g. visits, trials, leads)
- conversion_measure: the target event (e.g. purchases, subscriptions)
- entity: the join key connecting the two events (e.g. user_id)
- window: time window within which conversion must occur
- fills_nulls_with: replace nulls with this value (usually 0)

## DBT Agentic Use Case
Conversion metrics are useful for measuring:
- Deal stage progression rates
- Proposal to close conversion
- Trial to paid conversion for SaaS clients
