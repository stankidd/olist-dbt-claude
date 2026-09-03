---
description: Build all gold models defined in a tech spec using the dbt MCP server
allowed-tools: Read(*), Edit(*), Bash(dbt*), mcp__dbt__dbt_build, mcp__dbt__dbt_show, mcp__dbt__dbt_test
---

# /build-gold-models

Build all gold layer dbt models from a technical specification.

## Usage
/build-gold-models $ARGUMENTS

Where $ARGUMENTS is the path to the tech spec file.

## Pre-Flight
Load and follow these skills before starting:
- skills/dbt-implementation-validator
- skills/dbt-best-practices

## Important
Start a fresh Claude Code instance (or /clear) before running this command.
Do not carry bronze/silver context into the gold build.

## Steps

1. **Read the tech spec**
   - Open $ARGUMENTS and locate the Gold Models section
   - Create a to-do list of every gold model to build
   - Note dependencies on silver models

2. **Verify silver models exist**
   - Run: dbt ls --select tag:silver
   - Confirm all silver models the gold layer depends on are built

3. **Build each gold model**
   For every gold model in the to-do list:
   - Create the .sql file in models/gold/
   - Reference silver models using ref()
   - Apply business metrics and aggregations
   - Document all columns in schema.yml

4. **Validate**
   - Run: dbt build --select tag:gold
   - If tests fail: query data with dbt show, fix, rerun
   - All tests must pass

5. **Verify analysis output**
   - Use dbt show to query the final gold models
   - Confirm results match what the tech spec intended

6. **Summary**
   Report which models were built and confirm data looks correct.
