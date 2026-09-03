# tech-spec-plan

## Purpose
Convert a Business Requirements Document (BRD) or Business Use Case into a
complete, build-ready Technical Specification. This skill is loaded automatically
when the /tech-spec-plan command is run. It defines exactly how Claude should
read a BRD, profile source data, design the medallion architecture, and produce
a tech spec document that the build commands can execute against.

## When to Load This Skill
- When running /tech-spec-plan
- When asked to convert a BRD or business requirements into a tech spec
- When asked to design a dbt pipeline from a business problem description
- When a tech spec needs to be created before a build can begin

## Pre-Flight Before Starting
Before writing a single line of the tech spec:
1. Read the BRD or business requirements document completely
2. List every metric, data source, and business rule mentioned
3. Use dbt_show via MCP to profile each source table
4. Confirm actual column names match what the BRD assumes
5. Flag any discrepancies BEFORE designing the models

If source data is not accessible, STOP and report the blocker.
Do not design models based on assumed column names.

## Step 1 — Parse the BRD

Read the input document and extract:

### Metrics
For each metric identified:
- What is the exact business definition?
- What is the calculation logic?
- What level of granularity is it measured at?
- Who owns this metric?

### Data Sources
For each source table:
- Database and schema (exact Snowflake path)
- Table name
- Expected grain (what is one row?)
- Refresh frequency

### Business Rules
List every explicit and implied rule:
- What records are included vs excluded?
- How are nulls handled?
- How are duplicates handled?
- What are the accepted values for categorical fields?
- How are edge cases resolved?

### Grain Definitions
For each output model:
- What does one row represent?
- What is the natural key?
- Is this a snapshot or a current-state view?

## Step 2 — Profile Source Data

For each source table, use dbt_show to run:

### Row Count and Shape
`sql
SELECT COUNT(*) as row_count FROM source_table
`

### Column Inventory
`sql
SELECT * FROM source_table LIMIT 5
`

### Null Analysis (for key columns)
`sql
SELECT
    COUNT(*) as total_rows
    , COUNT(key_column) as non_null_count
    , COUNT(*) - COUNT(key_column) as null_count
FROM source_table
`

### Categorical Domain (for status/type columns)
`sql
SELECT column_name, COUNT(*) as row_count
FROM source_table
GROUP BY 1
ORDER BY 2 DESC
`

### Date Range (for date columns)
`sql
SELECT MIN(date_col) as earliest, MAX(date_col) as latest
FROM source_table
`

Document ALL findings. Discrepancies between BRD assumptions and actual
data must be resolved before the tech spec is written.

## Step 3 — Design Bronze Layer

For each source table produce:

### Model Definition
- Model name: bronze_[source_table_name]
- Source: source('source_name', 'table_name')
- Materialization: view
- Grain: [describe what one row is]
- Purpose: Parse and rename raw [source] data. No business logic.

### Column Mapping Table
| Target Column | Source Column | Type | Notes |
|--------------|--------------|------|-------|
| [snake_case]  | [RAW_NAME]   | [type] | [any casting needed] |

### Bronze Rules (enforce for every bronze model)
- Rename all columns to snake_case
- Remove source system prefixes (e.g. O_ from Oracle, C_ from Salesforce)
- Cast data types explicitly — never leave ambiguous types
- Do NOT filter any rows
- Do NOT apply any business logic
- Do NOT join to any other table
- Materialize as view

### Tests
- Primary key: unique + not_null
- Status/category columns: accepted_values (use profiled values)
- Foreign keys: not_null

## Step 4 — Design Intermediate Models (if needed)

Intermediate models solve cross-cutting concerns before silver joins:

### When to Create an Intermediate Model
- Standardizing raw categorical values across multiple silver models
  (e.g. role name standardization, status code mapping)
- Deduplicating source data before joining
- Flattening nested or repeated data structures

### Intermediate Model Pattern
`sql
WITH source AS (
    SELECT * FROM {{ ref('bronze_model') }}
)

, mapped AS (
    SELECT
        raw_column
        , CASE
            WHEN raw_column IN ('val1', 'val2') THEN 'Standard Value A'
            WHEN raw_column IN ('val3', 'val4') THEN 'Standard Value B'
            ELSE 'Unknown'
          END AS standardized_column
    FROM source
)

SELECT * FROM mapped
`

## Step 5 — Design Silver Layer

For each silver model produce:

### Model Definition
- Model name: silver_[entity_name]
- Depends on: [list of ref() models]
- Materialization: table
- Grain: [what one row represents]
- Purpose: [business description]

### Join Logic
List every join:
- Left table: [model]
- Right table: [model]
- Join key: [column]
- Join type: LEFT JOIN (default) or INNER JOIN (when data must exist)
- Cardinality: one-to-one or one-to-many

### Filters Applied
List every WHERE clause and the business rule it implements.

### Derived Columns
For every calculated column:
| Column | Type | Logic | Business Rule |
|--------|------|-------|---------------|
| [name] | [type] | [SQL expression] | [why] |

### Silver Rules (enforce for every silver model)
- Reference ONLY bronze or intermediate models via ref()
- Never use source() in silver
- Apply ALL business rules from the BRD here
- Filter invalid or irrelevant records here
- Standardize all categorical values here
- Materialize as table

### Tests
- Primary key: unique + not_null
- All business-critical columns: not_null
- Categorical columns: accepted_values (post-standardization values only)
- Foreign key relationships: relationships test where applicable

## Step 6 — Design Gold Layer

For each gold model produce:

### Model Definition
- Model name: gold_[use_case_name]
- Depends on: [list of ref() models — silver only, never bronze]
- Materialization: table
- Grain: [what one row represents]
- Purpose: [business description — what decision does this inform?]

### Aggregations
For every metric column:
| Column | Type | Logic | Metric Definition |
|--------|------|-------|-------------------|
| [name] | [type] | SUM/COUNT/AVG([col]) | [from BRD] |

### Gold Rules (enforce for every gold model)
- Reference ONLY silver models via ref()
- Never reference bronze directly from gold
- Every column must have a business-meaningful name
- No technical column names (no _id suffixes on final output where possible)
- Every metric must match its BRD definition exactly
- Materialize as table

### Tests
- Grain column: unique + not_null
- All metric columns: not_null
- Metrics that cannot be negative: dbt_utils.expression_is_true (>= 0)

## Step 7 — Write the Tech Spec Document

Save the completed tech spec to:
.claude/project_docs/[client-folder]/04-specs/[use-case]-tech-spec.md

### Required Sections (in this order)
1. Business Context (2-3 sentences from the BRD)
2. Source Data (database, schema, tables with descriptions)
3. Architecture Overview (text diagram: source -> bronze -> silver -> gold)
4. Bronze Models (one section per model with column mapping table)
5. Intermediate Models (if applicable)
6. Silver Models (one section per model with join logic and derived columns)
7. Gold Models (one section per model with aggregation definitions)
8. Tests Summary (table of all tests across all models)
9. Definition of Done (checklist)

### Definition of Done Template
Always include this at the end of every tech spec:
- [ ] All bronze models build without errors
- [ ] All silver models build without errors
- [ ] All gold models build without errors
- [ ] All tests pass (zero failures)
- [ ] All columns documented in schema.yml with descriptions
- [ ] No hardcoded database or schema references
- [ ] All SQL keywords uppercase
- [ ] All field names lowercase_with_underscores
- [ ] PR created with full summary and checklist complete

## Step 8 — Validate Before Handing Off

Before declaring the tech spec complete, check:

### Completeness Checklist
- [ ] Every metric in the BRD has a corresponding gold model column
- [ ] Every source table in the BRD has a bronze model
- [ ] Every join has a documented cardinality
- [ ] Every business rule has a corresponding transformation
- [ ] Every model has at least a unique + not_null test on its primary key
- [ ] The grain is defined for every model
- [ ] No assumed column names — all verified against actual source data
- [ ] Edge cases from the BRD are handled explicitly in silver

### Red Flags — Stop and Clarify Before Proceeding
- Source table does not exist or is empty
- Column name in BRD does not match actual source column
- Grain is ambiguous (stakeholder disagreement on what one row means)
- Business rule produces unexpected results against sample data
- Many-to-many join discovered that was assumed to be one-to-many
- Null rate > 50% on a column required by a metric

## Output Quality Standards
The tech spec must be detailed enough that:
1. An engineer who has never seen the BRD could build the pipeline from the spec alone
2. Claude Code can execute /build-bronze-models with zero ambiguity
3. Every column in every model is fully defined before any SQL is written
4. Dylan would approve it without requesting additional detail
