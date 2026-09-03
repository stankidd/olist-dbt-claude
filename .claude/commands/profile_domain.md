---
description: Profile all distinct values in a categorical column to define accepted_values tests
allowed-tools: mcp__dbt__dbt_show, Bash(dbt*)
---

# /profile-domain

Profile all distinct values of a categorical column to determine the correct
accepted_values test configuration for schema.yml.

## Usage
/profile-domain $ARGUMENTS

Where $ARGUMENTS is: table_name.column_name
Example: /profile-domain bronze_deal_resources.role_raw

## Steps

1. **Query all distinct values**
   Using dbt show:
   ```sql
   SELECT DISTINCT column_name, COUNT(*) as row_count
   FROM table_name
   GROUP BY 1
   ORDER BY 2 DESC
   ```

2. **Analyze**
   - How many distinct values are there?
   - Are there variations of the same value? (e.g. "AE", "Analytics Engineer", "Analytics Eng")
   - Are there nulls?
   - Are there suspicious values? ("test", "unknown", "n/a", "other")

3. **Suggest standardization** (if needed)
   If values are messy, propose a mapping table for int_role_mapping style intermediate models

4. **Generate test config**
   Output the ready-to-paste accepted_values test for schema.yml:
   ```yaml
   - name: column_name
     tests:
       - accepted_values:
           values: ['value1', 'value2', 'value3']
   ```

5. **Suggest mapping** (if standardization is needed)
   Output a ready-to-use CASE statement for the silver model.
