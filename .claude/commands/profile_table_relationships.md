---
description: Profile all foreign key relationships between tables in a tech spec
allowed-tools: mcp__dbt__dbt_show, Bash(dbt*), Read(*)
---

# /profile-table-relationships

Profile all join relationships between tables defined in a tech spec
to validate join quality before building silver models.

## Usage
/profile-table-relationships $ARGUMENTS

Where $ARGUMENTS is the path to the tech spec file.

## Steps

1. **Read the tech spec**
   - Extract all join relationships defined in the Silver and Gold sections
   - List every pair of tables that will be joined and their join keys

2. **For each join relationship**
   Run /profile-column-relationship on each pair:
   - Source table join key vs target table join key
   - Document match rate, orphans, and relationship cardinality

3. **Compile join quality report**
   Output a table:
   ```
   | Left Table | Left Key | Right Table | Right Key | Match Rate | Cardinality | Issues |
   |-----------|---------|------------|---------|-----------|-------------|--------|
   ```

4. **Flag bad joins**
   Warn if any join has:
   - Match rate < 80% (warning)
   - Match rate < 50% (critical -- stop and investigate)
   - Many:many relationship (confirm this is intentional)

5. **Recommend**
   For each flagged join, suggest:
   - Whether to LEFT JOIN or INNER JOIN
   - Whether to add a relationship test in schema.yml
   - Whether the tech spec needs revision
