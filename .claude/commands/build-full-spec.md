---
description: Build all layers (bronze, silver, gold) from a tech spec in one agentic run
allowed-tools: Read(*), Edit(*), Bash(dbt*), Bash(git*), mcp__dbt__dbt_build, mcp__dbt__dbt_show, mcp__dbt__dbt_test
---

# /build-full-spec

Build the complete data pipeline (bronze -> silver -> gold) from a tech spec
in a single end-to-end agentic run.

## Usage
/build-full-spec $ARGUMENTS

Where $ARGUMENTS is the path to the tech spec file.

## Warning
This command runs the full build autonomously. Use it only when:
- The tech spec is complete and validated (/validate-spec first)
- You have reviewed the data profile (/data-profile first)
- You are comfortable with a 20-40 minute unattended run

For more control, run /build-bronze-models, /build-silver-models,
and /build-gold-models separately with review between each layer.

## Steps

1. **Load skills**
   - skills/dbt-implementation-validator
   - skills/dbt-best-practices

2. **Read and plan**
   - Read $ARGUMENTS completely
   - Create a full to-do list across all three layers

3. **Build bronze** (same as /build-bronze-models)
   - Define sources
   - Build all bronze models
   - Validate with dbt build

4. **Build silver** (fresh context approach)
   - Build all silver models referencing bronze
   - Validate with dbt build

5. **Build gold**
   - Build all gold models referencing silver
   - Validate with dbt build

6. **Push PR**
   - Run /pr-from-spec to create the PR automatically

7. **Final summary**
   Report all models built, all tests passed, and PR link.
