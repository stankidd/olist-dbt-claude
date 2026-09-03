---
description: Profile a complete table to understand its shape, grain, and data quality
allowed-tools: mcp__dbt__dbt_show, Bash(dbt*)
---

# /profile-table

Profile a complete dbt model or source table to understand its shape,
grain, row count, and key column quality.

## Usage
/profile-table $ARGUMENTS

Where $ARGUMENTS is the table or model name.
Example: /profile-table bronze_deals
Example: /profile-table raw.crm.deals

## Steps

1. **Basic shape**
   Using dbt show, query:
   - Row count
   - Column count
   - Column names and data types
   - Sample of 5 rows

2. **Grain validation**
   - Find the candidate primary key
   - Check if it is unique: SELECT COUNT(*) vs COUNT(DISTINCT pk_col)
   - Report duplicate rate

3. **Null analysis**
   For every column:
   - Count nulls and null percentage
   - Flag columns with > 10% nulls

4. **Date range** (for any date columns)
   - Min and max date
   - Flag suspicious dates

5. **Key categorical columns**
   For any column that looks categorical (< 50 distinct values):
   - List all distinct values with counts

6. **Report**
   Output a structured profile:
   ```
   TABLE PROFILE: table_name
   Rows: X | Columns: Y | Grain: column_name (unique: yes/no)

   NULLS:
   column_name: X% null

   CATEGORICALS:
   stage: ['Open', 'Closed', 'Pending']

   SAMPLE:
   [5 row preview]
   ```
