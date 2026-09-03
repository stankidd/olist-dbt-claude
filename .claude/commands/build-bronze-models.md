---
description: Build all bronze models defined in a tech spec using the dbt MCP server
allowed-tools: Read(*), Edit(*), Bash(dbt*), mcp__dbt__dbt_build, mcp__dbt__dbt_show, mcp__dbt__dbt_test
---

# /build-bronze-models

Build all bronze layer dbt models from a technical specification.

## Usage
/build-bronze-models $ARGUMENTS

Where $ARGUMENTS is the path to the tech spec file.

## Pre-Flight
Load and follow these skills before starting:
- skills/dbt-implementation-validator (pre-flight checklist)
- skills/dbt-best-practices (60+ coding rules)

## Steps

1. **Read the tech spec**
   - Open $ARGUMENTS and locate the Bronze Models section
   - Create a to-do list of every bronze model to build

2. **Understand the raw data**
   - For each source table, use dbt show via MCP to query 10 rows
   - Confirm column names match what the tech spec expects
   - Note any discrepancies

3. **Define sources**
   - Create or update models/sources/sources.yml
   - Add all new source tables referenced by bronze models

4. **Build each bronze model**
   For every model in the to-do list:
   - Create the .sql file in models/bronze/
   - Follow bronze rules: no business logic, parse raw only, capitalize SQL keywords
   - Add column documentation to schema.yml
   - Check off the model when complete

5. **Validate**
   - Run: dbt build --select tag:bronze (or each model name)
   - If tests fail: use dbt show to query the data, understand why, fix, rerun
   - All tests must pass before proceeding

6. **Summary**
   Report which models were built, which tests passed, and any decisions made.
