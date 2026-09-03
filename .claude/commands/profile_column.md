---
description: Profile a single column to understand its data quality and distribution
allowed-tools: mcp__dbt__dbt_show, Bash(dbt*)
---

# /profile-column

Profile a single column to understand nulls, distinct values, distribution,
and data quality before building models that depend on it.

## Usage
/profile-column $ARGUMENTS

Where $ARGUMENTS is: table_name.column_name
Example: /profile-column bronze_deals.deal_stage

## Steps

1. **Parse arguments**
   Extract table name and column name from $ARGUMENTS

2. **Basic stats**
   Using dbt show, query:
   - Total row count
   - Null count and null percentage
   - Distinct value count

3. **Distribution** (choose based on column type)

   For categorical columns:
   - Top 20 values with count and percentage
   - Flag values that may need standardization

   For numeric columns:
   - Min, max, average, median
   - Count of zeros
   - Count of negatives (if unexpected)

   For date columns:
   - Min date, max date, date range
   - Count of future dates (if suspicious)
   - Count of dates before 2000 (if suspicious)

4. **Data quality flags**
   Automatically flag:
   - Null rate > 10% (warning)
   - Null rate > 50% (critical)
   - Single value dominates > 90% (possible bad data)
   - Values that look like test data ("test", "NULL", "n/a", "0000")

5. **Report**
   Output a clean summary with recommendations for testing strategy.
