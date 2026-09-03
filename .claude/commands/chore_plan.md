---
description: Plan and execute routine maintenance tasks on the dbt project
allowed-tools: Read(*), Bash(dbt*), Bash(git*), mcp__dbt__dbt_build, mcp__dbt__dbt_ls
---

# /chore-plan

Identify and plan routine maintenance tasks for the dbt project.
Use this command to keep the codebase clean and up to date.

## Usage
/chore-plan $ARGUMENTS

Where $ARGUMENTS optionally specifies a focus area:
- "docs" â€” find undocumented models
- "tests" â€” find models missing tests
- "deps" â€” check for outdated packages
- "style" â€” run SQLFluff linting
- (empty) â€” run all checks

## Steps

1. **Documentation audit**
   - Run: dbt ls --select *
   - Find models with missing or placeholder descriptions in schema.yml
   - List them with file paths

2. **Test coverage audit**
   - Find models with no tests defined in schema.yml
   - Prioritize gold and silver models
   - List gaps

3. **Package freshness**
   - Read packages.yml
   - Check dbt Hub for newer versions of each package
   - Flag any outdated dependencies

4. **SQL style check**
   - Run: sqlfluff lint models/ --dialect snowflake
   - Summarize violations by rule

5. **Produce chore list**
   Output a prioritized markdown checklist of all findings.
   Ask which items to tackle before making any changes.
