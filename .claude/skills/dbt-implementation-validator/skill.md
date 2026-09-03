# dbt-implementation-validator

## Purpose
Run a pre-flight checklist immediately before any build command executes.
This skill confirms that the environment, context, and spec are all ready
before Claude writes a single line of SQL. It prevents the most common
causes of failed or incomplete agentic builds.

## When to Load This Skill
- Automatically loaded by /build-bronze-models before starting
- Automatically loaded by /build-silver-models before starting
- Automatically loaded by /build-gold-models before starting
- Automatically loaded by /build-full-spec before starting
- Any time a build is resumed after a gap in work

## Pre-Flight Philosophy
A build that starts with missing context, incomplete specs, or broken
environment configuration will fail midway and leave the codebase in a
partially built state. Five minutes of pre-flight saves hours of cleanup.
Never skip this checklist regardless of time pressure.

## Check 1 - Environment Validation

Confirm the dbt environment is configured and connected:

### dbt Connection
Run dbt debug to confirm Snowflake connection is working:
- Profile name matches dbt_project.yml
- Target is set correctly (dev not prod)
- Snowflake credentials are valid
- Warehouse, database, and schema are accessible

If dbt debug fails: STOP. Do not proceed until connection is restored.

### MCP Server
Confirm dbt MCP server is connected and tools are available:
- dbt_show tool is accessible
- dbt_build tool is accessible
- dbt_test tool is accessible
- dbt_ls tool is accessible

If MCP tools are unavailable: STOP. The agentic build requires MCP.
Instruct the engineer to check .mcp.json and restart Claude Code.

### Working Directory
Confirm Claude Code is running from the correct project root:
- dbt_project.yml exists in current directory
- models/ folder exists
- .claude/ folder exists
- sources.yml exists in the correct models subfolder

## Check 2 - Tech Spec Validation

Confirm the tech spec is present and complete:

### Spec Exists
- [ ] Tech spec file exists at the path provided
- [ ] Tech spec is not empty
- [ ] Tech spec contains all required sections

### Spec Matches Current Layer
If building bronze:
- [ ] Bronze Models section exists and is not empty
- [ ] At least one bronze model is fully defined
- [ ] All source tables in the spec are accessible via dbt_show

If building silver:
- [ ] Silver Models section exists and is not empty
- [ ] All bronze models referenced in silver exist in models/bronze/
- [ ] All bronze models have been successfully built (run dbt_ls to confirm)

If building gold:
- [ ] Gold Models section exists and is not empty
- [ ] All silver models referenced in gold exist in models/silver/
- [ ] All silver models have been successfully built (run dbt_ls to confirm)

### Spec Quality Check
Perform a rapid scan of the spec for common problems:
- [ ] No column names listed as TBD or placeholder
- [ ] No model grain listed as unclear or to be confirmed
- [ ] No business rules listed as check with client
- [ ] All source table names match the sources.yml definitions

If any of the above are found: FLAG and ask engineer to resolve before building.

## Check 3 - Sources Configuration

Confirm sources.yml is correctly configured:

### File Exists
- [ ] sources.yml exists in the correct bronze folder for this project
- [ ] sources.yml has the correct project subfolder path
  Example: models/tpch_sf10/bronze/tpch_sf10_sources.yml

### Source Definition Matches Spec
For each source table in the tech spec:
- [ ] Source name in sources.yml matches the name used in spec
- [ ] Database in sources.yml matches actual Snowflake database
- [ ] Schema in sources.yml matches actual Snowflake schema
- [ ] Table name in sources.yml matches actual Snowflake table name

### Source Accessibility
Use dbt_show to confirm each source table returns data:

SELECT COUNT(*) FROM {{ source('source_name', 'table_name') }}

If any source table returns zero rows or an error: FLAG as BLOCKER.

## Check 4 - Existing Models Audit

Before building check what already exists:

### Run dbt ls
Use dbt_ls to list all currently built models:
- Identify which models already exist
- Identify which models are new and need to be built
- Confirm no naming conflicts with existing models

### Check for Stale Models
If resuming a partial build:
- [ ] Identify which models were built in the previous session
- [ ] Confirm previously built models still compile correctly
- [ ] Run dbt_build on previously built models to confirm they still pass tests
- [ ] Do not assume previously built models are still valid

### Check for Naming Conflicts
- [ ] No new model has the same name as an existing model in a different layer
- [ ] No new model name conflicts with a dbt package model name
- [ ] All new model names follow the layer naming convention

## Check 5 - Coding Standards Confirmation

Confirm dbt-best-practices skill is loaded and standards are clear:

### Layer Rules Confirmed
Bronze layer rules:
- [ ] Will materialize as view
- [ ] Will use source() references only
- [ ] Will not contain any business logic
- [ ] Will rename columns to snake_case
- [ ] Will not filter any rows

Silver layer rules:
- [ ] Will materialize as table
- [ ] Will use ref() references to bronze only
- [ ] Will apply all business rules from spec
- [ ] Will join models as defined in spec
- [ ] Will filter records as defined in spec

Gold layer rules:
- [ ] Will materialize as table
- [ ] Will use ref() references to silver only
- [ ] Will produce business-facing metric names
- [ ] Will aggregate as defined in spec

### SQL Standards Confirmed
- [ ] All SQL keywords will be UPPERCASE
- [ ] All field names will be lowercase_with_underscores
- [ ] All CTEs will be used instead of subqueries
- [ ] All tables will be aliased with meaningful short names
- [ ] Commas will be at the start of each new column line

## Check 6 - Git Status

Confirm the working state of the repository:

### Branch Check
- [ ] Currently on a feature branch (not main)
- [ ] Branch name follows convention: initials/use-case-name
- [ ] Branch has been pushed to GitHub remote

If on main: create a feature branch before writing any files.

Run:
git branch --show-current

If result is main or master: STOP and create a feature branch first.

### Clean Working Tree (for resuming builds)
If resuming a build after a previous session:
- [ ] Check git status for any uncommitted changes
- [ ] Commit or stash any unintended changes before continuing
- [ ] Confirm the working tree is in the expected state

## Check 7 - Context Completeness

Confirm Claude has all the context needed to build:

### Skills Loaded
- [ ] dbt-best-practices skill is loaded
- [ ] dbt-implementation-validator skill is loaded (this skill)
- [ ] build-from-spec skill is loaded

### Spec in Context
- [ ] Tech spec has been fully read (not just skimmed)
- [ ] All bronze model definitions are in active context
- [ ] All silver model definitions are in active context (for silver builds)
- [ ] All gold model definitions are in active context (for gold builds)

### Source Data Profiled
- [ ] At least one dbt_show query has been run on each source table
- [ ] Actual column names have been confirmed against the spec
- [ ] Any discrepancies between spec and actual data have been noted

## Pre-Flight Output Format

After completing all checks produce this summary:

PRE-FLIGHT CHECKLIST RESULTS
==============================
Layer: [Bronze / Silver / Gold]
Project: [project name from dbt_project.yml]
Spec: [tech spec filename]
Branch: [current git branch]

BLOCKERS (build cannot start)
--------------------------------
[List blockers or "None"]

WARNINGS (noted, proceeding with caution)
-------------------------------------------
[List warnings or "None"]

ENVIRONMENT
------------
dbt connection:    [PASS / FAIL]
MCP server:        [PASS / FAIL]
Sources file:      [PASS / FAIL]
Source tables:     [PASS / FAIL] ([N] of [N] accessible)
Git branch:        [PASS / FAIL] ([branch name])

SPEC READINESS
---------------
Spec found:        [PASS / FAIL]
Required section:  [PASS / FAIL]
Upstream models:   [PASS / FAIL] (for silver and gold only)
Column names:      [PASS / FAIL]

VERDICT
--------
GO     - All checks passed. Starting [layer] build now.
NO-GO  - [N] blocker(s) found. Resolve before building.

## Blocker Definitions

### Immediate Blockers - Build cannot start under any circumstances
- dbt connection is broken
- MCP server tools are unavailable
- Tech spec file does not exist
- Required spec section for this layer is missing
- Source table does not exist or is empty
- Upstream models for silver or gold layer are not built yet
- Currently on main branch with no feature branch created

### Warnings - Document and proceed carefully
- Minor column name discrepancy that has an obvious mapping
- A warning-level null rate on a non-critical column
- A model that already exists and will be overwritten
- Context window is getting large (consider using /compact)

## Post-Build Validation

After every build command completes run these final checks:

### Test Results
- [ ] All dbt tests passed (zero failures)
- [ ] Row counts in new models are reasonable (not zero, not unexpectedly large)
- [ ] Sample data from new models looks correct via dbt_show

### Spot Check Queries
Run dbt_show on each newly built model to verify the output looks right:

SELECT * FROM {{ ref('new_model_name') }} LIMIT 10

Confirm:
- Column names match the tech spec
- Data types are correct
- No unexpected nulls in critical columns
- Row count is in the expected range

### Documentation Check
- [ ] schema.yml entry exists for every new model
- [ ] Every column in schema.yml has a description
- [ ] All tests are defined in schema.yml

If any post-build check fails: do not proceed to the next layer.
Fix the issue first, rerun dbt_build, confirm tests pass, then continue.
