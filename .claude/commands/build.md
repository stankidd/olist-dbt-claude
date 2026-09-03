---
description: Run dbt build on a specific model or selector
allowed-tools: Bash(dbt build*), mcp__dbt__dbt_build
---

# /build

Run dbt build on a specified model, tag, or selector.

## Usage
/build $ARGUMENTS

Examples:
- /build bronze_deals
- /build tag:bronze
- /build tag:silver --exclude int_role_mapping
- /build +gold_hiring_gap  (build model and all upstream dependencies)

## Steps

1. Run: `dbt build --select $ARGUMENTS`

2. Parse the output:
   - Show which models ran
   - Show which tests passed or failed
   - Highlight any errors with the exact message

3. If tests fail:
   - Identify which test failed and on which model
   - Use dbt show to query the affected data
   - Suggest a fix but do NOT auto-apply without confirmation

4. Report final status: PASS or FAIL with summary counts.
