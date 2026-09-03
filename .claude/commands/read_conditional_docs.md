---
description: Conditionally load documentation files based on what the current task requires
allowed-tools: Read(*)
---

# /read-conditional-docs

Intelligently determine which documentation files are relevant to the current
task and load only those -- avoiding unnecessary context usage.

## Usage
/read-conditional-docs $ARGUMENTS

Where $ARGUMENTS describes what you are about to do.
Example: /read-conditional-docs "build silver models with semantic layer"

## Logic

Analyze $ARGUMENTS and load docs based on these rules:

| Task mentions | Load these files |
|--------------|-----------------|
| bronze, sources, raw | dbt-best-practices skill, dbt-validation.md |
| silver, intermediate, mapping | dbt-best-practices skill, dbt-join-logic.md |
| gold, metrics, aggregation | dbt-best-practices skill, dbt-metrics-overview.md |
| semantic, semantic model | dbt-semantic-models.md, dbt-entities.md, dbt-measures.md |
| simple metric | dbt-simple-metrics.md |
| ratio metric | dbt-ratio-metrics.md |
| cumulative metric | dbt-cumulative-metrics.md |
| derived metric | dbt-derived-metrics.md |
| fill nulls, timespine | dbt-fill-nulls-advanced.md, metricflow-time-spine.md |
| hooks | claude-code-hooks.md |
| mcp, tools | claude-code-mcp.md |
| sub-agent, subagent | claude-code-sub-agents.md |
| PR, pull request, git | skills/git/skill.md, skills/pr-from-spec/skill.md |
| tech spec, plan | skills/tech-spec-plan/skill.md |

## Steps

1. Parse $ARGUMENTS for topic keywords
2. Load the matching documentation files
3. Confirm what was loaded and what it enables
4. Proceed with the original task
