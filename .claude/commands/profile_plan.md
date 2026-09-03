---
description: Create a full data profiling plan for all sources in a tech spec
allowed-tools: Read(*), mcp__dbt__dbt_show, Bash(dbt*)
---

# /profile-plan

Read a tech spec and create a comprehensive data profiling plan covering
all source tables and key columns before building begins.

## Usage
/profile-plan $ARGUMENTS

Where $ARGUMENTS is the path to the tech spec file.

## Steps

1. **Read the tech spec**
   - Open $ARGUMENTS
   - Extract all source tables listed in the Bronze Models section
   - Extract all key columns that have business logic applied in silver/gold

2. **Create profiling to-do list**
   For each source table, plan to profile:
   - Row count
   - All key columns (PKs, FKs, categorical fields, dates)
   - Any columns with business rules in the tech spec

3. **Execute profiles** (table by table)
   Using dbt show via MCP:
   - Run /profile-table for each source table
   - Run /profile-column for each key column
   - Run /profile-domain for each categorical column

4. **Compile findings**
   After all profiles complete, write a summary to plans/data-profile.md:
   - Source table inventory
   - Data quality issues found
   - Columns needing standardization
   - Recommended test configurations
   - Any spec assumptions that need revision

5. **Flag blockers**
   If any source table is missing, empty, or has critical data quality issues --
   stop and report before building begins.
