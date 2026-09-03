---
description: Diagnose a failing dbt model or test and create a fix plan
allowed-tools: Read(*), Bash(dbt*), mcp__dbt__dbt_build, mcp__dbt__dbt_show, mcp__dbt__dbt_test
---

# /bug-plan

Diagnose a failing dbt model or test and produce a structured fix plan.

## Usage
/bug-plan $ARGUMENTS

Where $ARGUMENTS is the model name or error description.

## Steps

1. **Read the error**
   - If a model name is given, run: `dbt build --select $ARGUMENTS`
   - Capture the full error output

2. **Inspect the model**
   - Read the SQL file for the failing model
   - Read its schema.yml for test definitions
   - Identify the failing test or compilation error

3. **Query the data**
   - Use dbt show to inspect the underlying source data
   - Check for nulls, unexpected values, or schema mismatches

4. **Root cause analysis**
   Identify which of these caused the failure:
   - Column does not exist in source
   - Data type mismatch
   - Test accepted_values does not match actual data
   - Upstream model not built yet
   - Business logic error in SQL
   - Jinja/macro syntax error

5. **Produce fix plan**
   Output a numbered list of exact changes needed:
   - File to edit
   - Line to change
   - What to change it to
   - Why

6. **Ask for approval before making changes**
   Present the plan and wait for confirmation before editing any files.
