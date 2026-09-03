---
description: Profile the relationship between two columns to understand join quality
allowed-tools: mcp__dbt__dbt_show, Bash(dbt*)
---

# /profile-column-relationship

Analyze the relationship between two columns, typically to validate a join
or understand foreign key quality before building a silver model.

## Usage
/profile-column-relationship $ARGUMENTS

Where $ARGUMENTS is: table1.column1 table2.column2
Example: /profile-column-relationship bronze_deals.client_id bronze_clients.client_id

## Steps

1. **Parse the arguments**
   Extract: table1, column1, table2, column2

2. **Profile left side**
   Using dbt show, query:
   - Total rows in table1
   - Distinct values of column1
   - Null count in column1
   - Sample values

3. **Profile right side**
   Using dbt show, query:
   - Total rows in table2
   - Distinct values of column2
   - Null count in column2
   - Sample values

4. **Join analysis**
   - Count how many table1.column1 values exist in table2.column2 (match rate)
   - Count orphaned records (in table1 but not table2)
   - Count unmatched records (in table2 but not table1)
   - Identify if this is a 1:1, 1:many, or many:many relationship

5. **Report**
   Output:
   ```
   COLUMN RELATIONSHIP PROFILE
   Left:  table1.column1 -- X rows, Y distinct, Z nulls
   Right: table2.column2 -- X rows, Y distinct, Z nulls

   Match rate:     XX%
   Orphaned left:  X rows
   Relationship:   1:many

   RECOMMENDATION: [safe to join / investigate orphans / do not join]
   ```
