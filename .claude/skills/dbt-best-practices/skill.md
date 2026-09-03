# dbt Best Practices

## Purpose
Core coding standards for all dbt models in this project.
Load this skill before building any bronze, silver, or gold models.

## SQL Style Rules
- ALL SQL keywords UPPERCASE (SELECT, FROM, WHERE, JOIN, GROUP BY, etc.)
- All field names lowercase_with_underscores
- Always alias tables with short meaningful names (o for orders, l for lineitem)
- CTEs preferred over subqueries — always use CTEs
- One column per line in SELECT statements
- Commas at the start of each line, not the end
- Always include a blank line between CTEs

## CTE Structure (always follow this pattern)
\\\sql
WITH source AS (
    SELECT * FROM {{ source('tpch', 'orders') }}
)

, renamed AS (
    SELECT
        o_orderkey AS order_id
        , o_custkey AS customer_id
        , o_orderstatus AS order_status
        , o_totalprice AS order_total_price
        , o_orderdate AS order_date
    FROM source
)

SELECT * FROM renamed
\\\

## Bronze Layer Rules
- Source data only — no business logic whatsoever
- Rename columns to snake_case removing source system prefixes
- Cast data types explicitly (dates, timestamps, numerics)
- Materialize as views (no storage cost, always fresh)
- Name pattern: bronze_[source_table] (e.g. bronze_orders)
- One bronze model per source table
- No joins in bronze models
- No filtering in bronze models (keep all rows)

## Silver Layer Rules
- Reference bronze models using ref() only — never source()
- Apply business logic, cleaning, and conforming here
- Join related bronze models here
- Filter out invalid or irrelevant records here
- Materialize as tables
- Name pattern: silver_[entity] (e.g. silver_orders)
- Document all business rules in comments

## Gold Layer Rules
- Reference silver models using ref() only
- Final business-facing aggregations and metrics
- No raw column names — only business-meaningful names
- Materialize as tables
- Name pattern: gold_[use_case] (e.g. gold_order_summary)
- These are what dashboards and AI agents query

## Model File Structure
Every model must have a corresponding entry in schema.yml:
\\\yaml
models:
  - name: bronze_orders
    description: "Raw orders data from TPCH source, renamed columns only"
    columns:
      - name: order_id
        description: "Unique order identifier"
        tests:
          - unique
          - not_null
\\\

## Required Tests
- Primary key columns: unique + not_null on every model
- Foreign key columns: not_null
- Status/category columns: accepted_values
- All gold model columns: not_null

## Materialization Settings
Already configured in dbt_project.yml:
- bronze: view
- silver: table
- gold: table

## Source Definitions
Always define sources in models/sources/sources.yml before referencing them:
\\\yaml
sources:
  - name: tpch
    database: SNOWFLAKE_SAMPLE_DATA
    schema: TPCH_SF1000
    tables:
      - name: orders
      - name: lineitem
      - name: customer
      - name: supplier
      - name: nation
      - name: region
      - name: part
      - name: partsupp
\\\

## Naming Conventions
| Layer  | Prefix   | Example              |
|--------|----------|----------------------|
| Source | source() | source('tpch','orders') |
| Bronze | bronze_  | ref('bronze_orders') |
| Silver | silver_  | ref('silver_orders') |
| Gold   | gold_    | ref('gold_orders')   |

## Before Submitting Any Work
- [ ] All models build without errors (dbt_build passes)
- [ ] All tests pass (zero failures)
- [ ] All columns documented in schema.yml
- [ ] No hardcoded database or schema references
- [ ] All SQL keywords uppercase
- [ ] All field names lowercase_with_underscores
