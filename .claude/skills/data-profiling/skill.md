# data-profiling

## Purpose
Profile source data tables before building any dbt models. Data profiling
grounds the tech spec in reality — confirming actual column names, data
types, null rates, cardinality, and data quality issues before any SQL
is written. A model built on assumed data is a model that will fail.

## When to Load This Skill
- When running /data-profile or /profile-plan
- When running /profile-table, /profile-column, or /profile-domain
- During /tech-spec-plan before designing any models
- When the engineer asks to understand a source table
- When a build fails due to unexpected data and investigation is needed

## Profiling Philosophy
Never assume. Always query. The BRD describes what the business thinks
the data looks like. Profiling reveals what the data actually looks like.
These two things are frequently different. Every discrepancy found during
profiling is a bug caught before it became a production incident.

## Profile Level 1 - Table Profile

Run this profile for every source table before designing bronze models.

### Step 1 - Basic Shape
Use dbt_show to get row count and a sample of the data:

SELECT COUNT(*) as total_rows FROM source_table

SELECT * FROM source_table LIMIT 10

Document:
- Total row count
- Number of columns
- Column names exactly as they appear (case sensitive)
- Sample data to understand content

### Step 2 - Grain Validation
Identify the candidate primary key and confirm uniqueness:

SELECT
    candidate_key_column
    , COUNT(*) as occurrences
FROM source_table
GROUP BY candidate_key_column
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20

If duplicates exist:
- Document the duplicate rate (how many rows are duplicated?)
- Determine if duplicates are expected (slowly changing dimension?)
- Document the deduplication strategy in the tech spec
- If unexpected: FLAG as data quality issue

### Step 3 - Null Analysis
For every column that will be used in a join, filter, or metric:

SELECT
    COUNT(*) as total_rows
    , COUNT(column_name) as non_null_count
    , COUNT(*) - COUNT(column_name) as null_count
    , ROUND(100.0 * (COUNT(*) - COUNT(column_name)) / COUNT(*), 2) as null_pct
FROM source_table

Interpret results:
- null_pct = 0%: column is fully populated (ideal for join keys)
- null_pct 1-10%: acceptable for most columns, note in spec
- null_pct 10-50%: WARNING - document null handling strategy in spec
- null_pct > 50%: BLOCKER if column is required for a metric or join

### Step 4 - Date Range Analysis
For every date or timestamp column:

SELECT
    MIN(date_column) as earliest_date
    , MAX(date_column) as latest_date
    , DATEDIFF('day', MIN(date_column), MAX(date_column)) as date_range_days
    , COUNT(DISTINCT date_column) as distinct_dates
    , SUM(CASE WHEN date_column > CURRENT_DATE THEN 1 ELSE 0 END) as future_dates
    , SUM(CASE WHEN date_column < '2000-01-01' THEN 1 ELSE 0 END) as very_old_dates
FROM source_table

Document:
- Does the date range cover the expected historical period?
- Are there unexpected future dates?
- Are there suspicious dates (year 1900, year 9999)?
- Is the date column a date or a timestamp?

### Step 5 - Numeric Column Analysis
For every numeric column used in a metric calculation:

SELECT
    MIN(numeric_column) as min_value
    , MAX(numeric_column) as max_value
    , AVG(numeric_column) as avg_value
    , MEDIAN(numeric_column) as median_value
    , STDDEV(numeric_column) as std_dev
    , SUM(CASE WHEN numeric_column < 0 THEN 1 ELSE 0 END) as negative_count
    , SUM(CASE WHEN numeric_column = 0 THEN 1 ELSE 0 END) as zero_count
    , SUM(CASE WHEN numeric_column IS NULL THEN 1 ELSE 0 END) as null_count
FROM source_table

Interpret:
- Are negative values expected or a data quality issue?
- Is the average reasonable given the business context?
- Are there extreme outliers that suggest data errors?
- Are zeros meaningful or do they indicate missing data?

## Profile Level 2 - Column Profile

Run this profile for any specific column needing deeper analysis.

### Categorical Column Profile
For any column with a small number of distinct values:

SELECT
    column_name
    , COUNT(*) as row_count
    , ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct_of_total
FROM source_table
GROUP BY column_name
ORDER BY row_count DESC

Document:
- All distinct values (this becomes the accepted_values test list)
- Which values dominate (>90% one value may indicate bad data)
- Any values that look like test data (test, null as string, n/a, unknown)
- Any values that need standardization (AE vs Analytics Engineer)
- Any values not mentioned in the BRD

### High Cardinality Column Profile
For columns with many distinct values (IDs, names, free text):

SELECT
    COUNT(DISTINCT column_name) as distinct_count
    , COUNT(*) as total_rows
    , ROUND(100.0 * COUNT(DISTINCT column_name) / COUNT(*), 2) as cardinality_pct
FROM source_table

Interpret:
- cardinality_pct near 100%: likely a unique identifier (good for join key)
- cardinality_pct 50-99%: moderate cardinality (investigate duplicates)
- cardinality_pct < 10%: low cardinality (consider for accepted_values test)

### String Length Analysis
For varchar columns where length matters:

SELECT
    MIN(LENGTH(column_name)) as min_length
    , MAX(LENGTH(column_name)) as max_length
    , AVG(LENGTH(column_name)) as avg_length
    , SUM(CASE WHEN LENGTH(column_name) = 0 THEN 1 ELSE 0 END) as empty_strings
FROM source_table
WHERE column_name IS NOT NULL

Document empty strings separately from nulls - they may need different handling.

## Profile Level 3 - Relationship Profile

Run this profile before designing any silver model join.

### Join Quality Profile
For every join defined in the tech spec:

SELECT
    COUNT(DISTINCT left_table.join_key) as left_distinct_keys
    , COUNT(DISTINCT right_table.join_key) as right_distinct_keys
    , COUNT(DISTINCT CASE
        WHEN right_table.join_key IS NOT NULL
        THEN left_table.join_key
      END) as matched_keys
    , COUNT(DISTINCT CASE
        WHEN right_table.join_key IS NULL
        THEN left_table.join_key
      END) as unmatched_left_keys
    , ROUND(100.0 * COUNT(DISTINCT CASE
        WHEN right_table.join_key IS NOT NULL
        THEN left_table.join_key
      END) / NULLIF(COUNT(DISTINCT left_table.join_key), 0), 2) as match_rate_pct
FROM left_table
LEFT JOIN right_table
    ON left_table.join_key = right_table.join_key

Interpret:
- match_rate_pct = 100%: perfect join, use INNER JOIN safely
- match_rate_pct 90-99%: good join, use LEFT JOIN, investigate unmatched
- match_rate_pct 80-89%: WARNING - use LEFT JOIN, document unmatched handling
- match_rate_pct < 80%: BLOCKER - investigate before designing silver model

### Cardinality Profile
For every join determine the relationship type:

SELECT
    join_key
    , COUNT(*) as rows_per_key
FROM table_name
GROUP BY join_key
ORDER BY rows_per_key DESC
LIMIT 20

If max rows_per_key = 1: one-to-one relationship
If max rows_per_key > 1: one-to-many relationship
If both tables have max > 1: many-to-many (requires special handling)

Document the cardinality in the tech spec before writing any silver SQL.

### Fan-Out Risk Check
Before any join that could cause row multiplication:

SELECT COUNT(*) as pre_join_count FROM left_table

SELECT COUNT(*) as post_join_count
FROM left_table
JOIN right_table ON left_table.key = right_table.key

If post_join_count is significantly larger than pre_join_count:
- A fan-out is occurring (row multiplication)
- The join is one-to-many and the spec may not account for this
- FLAG and discuss with engineer before proceeding

## Profile Level 4 - Data Quality Profile

Run these checks to identify systemic data quality issues.

### Test Data Detection
Look for common test data patterns:

SELECT *
FROM source_table
WHERE LOWER(key_column) LIKE '%test%'
    OR LOWER(key_column) LIKE '%demo%'
    OR LOWER(key_column) LIKE '%sample%'
    OR LOWER(key_column) LIKE '%dummy%'
    OR key_column = '0'
    OR key_column = '-1'
LIMIT 20

Document any test data found and determine if it should be excluded
in the silver layer filter.

### Encoding and Special Character Check
For string columns that will be used as join keys or displayed:

SELECT *
FROM source_table
WHERE column_name LIKE '%[^a-zA-Z0-9 .,!@#$%^&*()-_=+]%'
LIMIT 20

Flag any unexpected special characters or encoding issues.

### Referential Integrity Check
For foreign key columns verify they point to valid parent records:

SELECT
    COUNT(*) as total_rows
    , SUM(CASE WHEN parent_table.key IS NULL THEN 1 ELSE 0 END) as orphaned_rows
    , ROUND(100.0 * SUM(CASE WHEN parent_table.key IS NULL THEN 1 ELSE 0 END)
        / COUNT(*), 2) as orphan_rate_pct
FROM child_table
LEFT JOIN parent_table ON child_table.foreign_key = parent_table.key

Orphaned rows (records with no parent):
- orphan_rate_pct = 0%: clean referential integrity
- orphan_rate_pct > 0%: document handling in silver (filter out or keep?)
- orphan_rate_pct > 10%: BLOCKER - investigate with client before building

## Profiling Output Format

After completing a table profile produce this structured summary:

TABLE PROFILE REPORT
=====================
Table: [database.schema.table_name]
Profiled: [date]
Total Rows: [count]
Total Columns: [count]

GRAIN ANALYSIS
---------------
Candidate Key: [column name]
Is Unique: [Yes / No]
Duplicate Count: [N rows are duplicated]
Recommendation: [use as PK / deduplicate in silver / investigate]

KEY COLUMN SUMMARY
-------------------
| Column | Type | Null% | Distinct | Notes |
|--------|------|-------|----------|-------|
| col1   | varchar | 0% | 50K | Good PK candidate |
| col2   | date | 5% | 730 | Date range 2022-2024 |
| col3   | varchar | 0% | 5 | Categorical: A,B,C,D,E |
| col4   | numeric | 2% | 10K | Range: 0 to 50,000 |

CATEGORICAL COLUMNS
--------------------
[column_name]: [list all distinct values with counts]

DATA QUALITY FLAGS
-------------------
BLOCKERS:
- [Description of blocker if any]

WARNINGS:
- [Description of warning if any]

RECOMMENDED TESTS
------------------
- [column]: unique, not_null
- [column]: accepted_values [list values]
- [column]: not_null
- [column]: dbt_utils.expression_is_true (>= 0)

SPEC DISCREPANCIES
-------------------
[List any column names in the spec that do not match actual source]
[List any data types that differ from spec assumptions]
[List any unexpected values not mentioned in BRD]

## Profiling Rules

### Always Profile Before Designing
Never design a bronze or silver model without first profiling the source.
The spec must reflect actual data, not assumed data.

### Document Everything
All profiling findings must be recorded in the tech spec or in the
05-data folder of the client project docs:
.claude/project_docs/[client]/05-data/[table-name]-profile.md

### Flag Before Building
Any discrepancy between the spec and actual data must be flagged
to the engineer before building begins. Never silently work around
a data issue by making an assumption.

### Re-Profile When Resuming
If returning to a build after more than 24 hours, re-profile the
source tables. Data changes. Profiles from yesterday may not reflect
the data today.

### Profile Sample vs Full Table
For very large tables (like TPCH_SF1000 lineitem with 6 billion rows):
- Use LIMIT or SAMPLE for exploratory profiling
- Use COUNT(*) for row count (runs fast even on large tables)
- Use TABLESAMPLE for statistics on large tables:

SELECT *
FROM large_table
TABLESAMPLE (0.1)

This gives a 0.1% sample which is statistically representative for
most profiling purposes while running in seconds instead of minutes.
