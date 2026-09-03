---
description: Build all silver models defined in a tech spec using the dbt MCP server
allowed-tools: Read(*), Edit(*), Bash(dbt*), mcp__dbt__dbt_build, mcp__dbt__dbt_show, mcp__dbt__dbt_test
---

# /build-silver-models

Build all silver layer dbt models from a technical specification.

## Usage
/build-silver-models $ARGUMENTS

Where $ARGUMENTS is the path to the tech spec file.

## Pre-Flight
Load and follow these skills before starting:
- skills/dbt-implementation-validator
- skills/dbt-best-practices

## Important
Start a fresh Claude Code instance (or /clear) before running this command.
Do not carry bronze context into the silver build.

## Steps

1. **Read the tech spec**
   - Open $ARGUMENTS and locate the Silver Models section
   - Also read any Intermediate Models section
   - Create a to-do list in dependency order

2. **Verify bronze models exist**
   - Run: dbt ls --select tag:bronze
   - Confirm all bronze models the silver layer depends on are present

3. **Build intermediate models first** (if any)
   - Create any mapping or intermediate models (e.g. int_role_mapping)
   - These live in models/silver/ with an int_ prefix

4. **Build each silver model**
   For every silver model in the to-do list:
   - Create the .sql file in models/silver/
   - Reference bronze using ref()
   - Apply cleaning, conforming, and joining logic
   - Document all columns in schema.yml

5. **Validate**
   - Run: dbt build --select tag:silver
   - If tests fail: use dbt show to query data, fix, rerun
   - All tests must pass

6. **Summary**
   Report which models were built and any mapping decisions made.
