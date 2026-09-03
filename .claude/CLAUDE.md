# Mammoth Growth DBT Project

## Project Overview
Analytics engineering project using Mammoth Growth agentic dbt workflow.
Medallion architecture: Bronze -> Silver -> Gold.
Warehouse: Snowflake (MAMMOTH_WH / MAMMOTH_DB / MAMMOTH_SCHEMA)
Engineer: Stan Kidd (initials: sk)

## MCP Tools Available
The dbt MCP server is connected with 47 tools including:
- dbt_show: query raw data before building models
- dbt_build: compile, run, and test models
- dbt_test: run tests only
- dbt_ls: list models

## On Every Task
1. Load the relevant skill from .claude/skills/ before starting
2. Use dbt_show via MCP to query source data before writing any SQL
3. Follow all rules in .claude/skills/dbt-best-practices/skill.md
4. Run dbt_build via MCP to validate all models before finishing
5. Never push code that has failing tests

## Layer Rules
- Bronze: No business logic. Parse raw data only. Materialize as views.
- Silver: Clean, conform, join. Apply business rules. Materialize as tables.
- Gold: Business metrics and aggregations. Materialize as tables.

## SQL Standards
- ALL SQL keywords UPPERCASE
- all field names lowercase_with_underscores
- Always alias tables with meaningful short names
- CTEs preferred over subqueries
- Always use ref() to reference other dbt models

## Source Data

### TPCH_SF1000 — Order Analytics
Database: SNOWFLAKE_SAMPLE_DATA
Schema: TPCH_SF1000
Tables: ORDERS, LINEITEM, CUSTOMER, SUPPLIER, PART, PARTSUPP, NATION, REGION
Scale: 6 billion rows in LINEITEM (production scale)
Use case: Order analytics — revenue by segment, supplier nation, part type
Models: models/tpch_sf1000/bronze|silver|gold
Project docs: .claude/project_docs/client-tpch_sf1000/

### TPCH_SF10 — Supplier Performance
Database: SNOWFLAKE_SAMPLE_DATA
Schema: TPCH_SF10
Tables: ORDERS, LINEITEM, CUSTOMER, SUPPLIER, PART, PARTSUPP, NATION, REGION
Scale: 60 million rows in LINEITEM (fast iteration)
Use case: Supplier performance — delivery timeliness, discount rates, return rates
Models: models/tpch_sf10/bronze|silver|gold
Project docs: .claude/project_docs/client-tpch_sf10/

### pharma_sales — Sales Effectiveness
Database: MAMMOTH_DB
Schema: MAMMOTH_SCHEMA_pharma_sales_seeds (dev) / PHARMA_SALES_SEEDS (prod)
Tables: seed_territories, seed_physicians, seed_products, seed_sales_calls, seed_prescriptions
Scale: 180 rows total across 5 seed tables
Use case: Pharma sales effectiveness — rep performance, physician scorecard, product performance
Models: models/pharma_sales/bronze|silver|gold
Seeds: seeds/pharma_sales/
Project docs: .claude/project_docs/client-pharma_sales/
Note: Use ref('seed_*') not source() — seeds loaded via dbt seed command

### champion_homes — Enterprise Performance Management
Database: TBD (pending client source system access)
Schema: TBD
Tables: TBD — see BRD at .claude/project_docs/client-champion_homes/03-requirements/
Scale: TBD
Use case: Channel x plant x brand performance management across 9 business functions
Models: models/champion_homes/bronze|silver|gold (structure ready, build pending)
Project docs: .claude/project_docs/client-champion_homes/

## Schema Naming
Dev schemas use MAMMOTH_SCHEMA_ prefix (e.g. MAMMOTH_SCHEMA_tpch_sf10_bronze)
Prod schemas use clean names (e.g. TPCH_SF10_BRONZE) via generate_schema_name macro
Macro location: macros/generate_schema_name.sql

## Git Workflow
- Branch naming: sk/feature-name
- Always run dbt_build before committing
- Use /github-create-pr when work is complete
- Never commit to main directly

## On Completing Any Task
Run /github-create-pr to push a PR with full context summary.
