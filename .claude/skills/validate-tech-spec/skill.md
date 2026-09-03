# validate-tech-spec

## Purpose
Validate that a technical specification is complete, unambiguous, and
build-ready before any dbt models are written. This skill is a quality
gate — it prevents wasted build time on incomplete or incorrect specs.
A spec that fails validation must be fixed before /build-bronze-models
is run.

## When to Load This Skill
- When running /validate-spec
- After /tech-spec-plan completes and before any build command runs
- When a tech spec is received from a client or stakeholder
- When resuming a build after a gap in work

## Validation Philosophy
A tech spec is complete when an engineer who has never seen the BRD
could build the entire pipeline from the spec alone with zero ambiguity.
Every question Claude might ask during the build must already be answered
in the spec. If it is not, the spec is incomplete.

## Section 1 - Structure Validation

Check that the tech spec contains ALL of these sections:

### Required Sections Checklist
- [ ] Business Context - describes the business problem being solved
- [ ] Source Data - lists every source table with database, schema, and description
- [ ] Architecture Overview - shows the full bronze to silver to gold flow
- [ ] Bronze Models - one section per source table
- [ ] Silver Models - one section per conformed entity
- [ ] Gold Models - one section per business output
- [ ] Tests Summary - table of all tests across all models
- [ ] Definition of Done - checklist of completion criteria

If any section is missing: STOP. Report which sections are missing.
Do not proceed with validation until all sections exist.

## Section 2 - Source Data Validation

For every source table listed in the spec:

### Existence Check
Use dbt_show to confirm the table exists and is accessible:

SELECT COUNT(*) FROM database.schema.table_name

If the table does not exist or returns an error: FLAG as BLOCKER.

### Column Name Verification
For every column mapping in the bronze models:
- Confirm the source column name exists in the actual table
- Confirm the data type matches what the spec assumes

Use dbt_show to inspect actual columns:

SELECT * FROM source_table LIMIT 1

Flag any column in the spec that does not exist in the source.
Flag any assumed data type that differs from the actual type.

### Row Count Check
Confirm the table has data:

SELECT COUNT(*) FROM source_table

If row count is zero: FLAG as BLOCKER - cannot validate against empty table.

## Section 3 - Bronze Model Validation

For each bronze model in the spec check:

### Completeness
- [ ] Model name follows pattern: bronze_[source_table]
- [ ] Source reference is defined (source name and table name)
- [ ] Materialization is set to view
- [ ] Grain is described (what is one row?)
- [ ] Column mapping table is present with ALL columns mapped
- [ ] No columns left as TBD or placeholder
- [ ] Primary key column is identified
- [ ] Data type is specified for every column

### Business Logic Check
- [ ] No WHERE clauses (bronze never filters rows)
- [ ] No JOIN statements (bronze never joins tables)
- [ ] No CASE statements for business logic (bronze renames only)
- [ ] No calculated columns (bronze maps source to target only)

Flag any bronze model that contains business logic.
Bronze = parse and rename ONLY.

### Test Coverage
- [ ] Primary key has unique test
- [ ] Primary key has not_null test
- [ ] All foreign key columns have not_null test
- [ ] Status/category columns have accepted_values test
- [ ] Accepted values are verified against actual source data (not assumed)

## Section 4 - Silver Model Validation

For each silver model in the spec check:

### Completeness
- [ ] Model name follows pattern: silver_[entity]
- [ ] All upstream dependencies listed (ref() models only)
- [ ] Materialization is set to table
- [ ] Grain is defined precisely
- [ ] Every join is documented with: left table, right table, key, type, cardinality
- [ ] Every derived column has its calculation logic defined
- [ ] Every filter has its corresponding business rule documented

### Join Quality Checks
For every join defined in the spec:
- [ ] Join cardinality is stated (1:1, 1:many, many:many)
- [ ] If many:many: confirm this is intentional and documented
- [ ] Join key exists in both tables as verified against source data
- [ ] Join type (LEFT vs INNER) matches the business intent

Use dbt_show to verify join quality by checking match rates between tables.
Flag any join with match rate below 80%.

### Business Rule Coverage
- [ ] Every business rule from the BRD has a corresponding transformation
- [ ] Every edge case mentioned in the BRD is handled explicitly
- [ ] Null handling is defined for every column that can be null
- [ ] Duplicate handling is defined if source data has duplicates

### Test Coverage
- [ ] Primary key: unique + not_null
- [ ] All metric input columns: not_null
- [ ] Categorical columns: accepted_values (post-standardization values)
- [ ] At least one relationship test where foreign keys exist

## Section 5 - Gold Model Validation

For each gold model in the spec check:

### Completeness
- [ ] Model name follows pattern: gold_[use_case]
- [ ] Depends ONLY on silver models (never bronze)
- [ ] Materialization is set to table
- [ ] Grain is defined
- [ ] Every metric column has its aggregation logic defined
- [ ] Every metric matches its definition in the BRD exactly

### Metric Accuracy Check
For each metric in the gold model:
- [ ] The metric name matches what stakeholders will look for
- [ ] The aggregation function is correct (SUM vs COUNT vs AVG)
- [ ] The column being aggregated is the right one
- [ ] Any filters on the metric match the BRD definition
- [ ] The metric cannot produce a negative value unintentionally

### Test Coverage
- [ ] Grain column(s): unique + not_null
- [ ] All metric columns: not_null
- [ ] Revenue and amount columns: expression_is_true (>= 0)

## Section 6 - Cross-Model Validation

Check consistency across the entire spec:

### Lineage Check
- [ ] Every model referenced via ref() in silver exists in the bronze section
- [ ] Every model referenced via ref() in gold exists in the silver section
- [ ] No circular dependencies
- [ ] No gold model references a bronze model directly

### Column Continuity
- [ ] Every column used in a join exists in the upstream model spec
- [ ] Every column used in a derived calculation exists in the upstream model
- [ ] No column is referenced before it is created

### Naming Consistency
- [ ] All model names follow the layer naming pattern
- [ ] All column names are lowercase_with_underscores
- [ ] No column has the same name with different meanings across models
- [ ] Primary key columns are named consistently across all models

## Section 7 - Definition of Done Validation

Confirm the spec includes a Definition of Done with ALL of these items:
- [ ] All bronze models build without errors
- [ ] All silver models build without errors
- [ ] All gold models build without errors
- [ ] All tests pass (zero failures)
- [ ] All columns documented in schema.yml
- [ ] No hardcoded database or schema references
- [ ] All SQL keywords uppercase
- [ ] All field names lowercase_with_underscores
- [ ] PR created with full summary and checklist complete

## Section 8 - Data Quality Validation

Run these checks against actual source data using dbt_show:

### Duplicate Check on Primary Keys
For each source table primary key:

SELECT key_column, COUNT(*) as cnt
FROM source_table
GROUP BY key_column
HAVING COUNT(*) > 1
LIMIT 10

If duplicates exist: FLAG as WARNING and document in spec how they are handled.

### Null Rate Check on Critical Columns
For every column used in a join or metric calculation:

SELECT
    COUNT(*) as total_rows
    , SUM(CASE WHEN column_name IS NULL THEN 1 ELSE 0 END) as null_count
    , ROUND(100.0 * SUM(CASE WHEN column_name IS NULL THEN 1 ELSE 0 END)
        / COUNT(*), 2) as null_pct
FROM source_table

Flag columns with null rate above 10% as WARNING.
Flag columns with null rate above 50% as BLOCKER.

### Categorical Value Verification
For every accepted_values test defined in the spec:

SELECT DISTINCT column_name
FROM source_table
ORDER BY 1

Compare actual distinct values against the values listed in the spec.
Flag any values in the spec that do not appear in the actual data.
Flag any values in the actual data that are not in the spec.

### Date Range Sanity Check
For every date column used in a filter or metric:

SELECT
    MIN(date_column) as earliest
    , MAX(date_column) as latest
    , COUNT(*) as total_rows
    , SUM(CASE WHEN date_column > CURRENT_DATE THEN 1 ELSE 0 END) as future_dates
FROM source_table

Flag future dates as WARNING if unexpected.
Flag date ranges that do not cover the expected historical period.

## Validation Output Format

After running all checks produce this structured report:

TECH SPEC VALIDATION REPORT
============================
Spec: [filename]
Date: [date]
Validated by: Claude Code

BLOCKERS (must fix before build can start)
-------------------------------------------
1. [Blocker description] - [which model/section it affects]
2. [Blocker description] - [which model/section it affects]
None if no blockers found.

WARNINGS (should fix before build, proceed with caution)
----------------------------------------------------------
1. [Warning description] - [which model/section it affects]
2. [Warning description] - [which model/section it affects]
None if no warnings found.

DATA QUALITY FINDINGS
----------------------
[Summary of null rates, duplicate counts, and categorical value findings]

PASSED CHECKS
--------------
[Count of checks passed] of [total checks] passed.
[List notable passes — e.g. all source tables confirmed accessible]

VERDICT
--------
APPROVED  - Spec is complete and build-ready. Proceed with /build-bronze-models.
BLOCKED   - [N] blocker(s) must be resolved before building. Do not proceed.
WARNING   - [N] warning(s) noted. Engineer should review before proceeding.

## Blockers vs Warnings Reference

### Blockers - Build CANNOT proceed until resolved
- Source table does not exist or is inaccessible
- Column name in spec does not exist in actual source table
- Grain is undefined for any model
- A required spec section is missing entirely
- Bronze model contains business logic (joins, filters, calculations)
- Gold model references a bronze model directly (skips silver)
- Any undocumented many-to-many join
- Null rate above 50% on any join key or metric input column
- Zero rows in any required source table

### Warnings - Build can proceed but engineer should review
- Join match rate below 80%
- Null rate between 10% and 50% on a key column
- Accepted values in spec do not match all actual source values
- Missing tests on non-primary-key columns
- Edge case from BRD not explicitly handled in spec
- Column description missing from a model
- Future dates found in a date column
- Duplicate primary keys found in source (must document handling)

## Final Rule
If there are ANY blockers: do not run any build commands.
Report the blockers clearly, explain exactly what needs to be fixed,
and wait for the engineer to update the spec before proceeding.
Never attempt to work around a blocker by making assumptions.
Always ask for clarification rather than guessing.
