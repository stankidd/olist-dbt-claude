# DBT Saved Queries

## Overview
Saved queries bundle metrics, dimensions, and filters that are logically related
into reusable, named query configurations. They appear as nodes in the dbt DAG
and can be exported to tables via dbt's job scheduler.

## YAML Structure
\\\yaml
saved_queries:
  - name: hiring_gap_report
    description: "Daily hiring gap analysis for executive review"
    query_params:
      metrics:
        - total_pipeline_demand
        - current_headcount
        - hiring_gap
      group_by:
        - Dimension('role__role_name')
        - TimeDimension('metric_time', 'day')
      where:
        - "{{ Dimension('role__role_name') }} IS NOT NULL"
    exports:
      - name: hiring_gap_report
        config:
          export_as: table
          schema: gold_exports
\\\

## Key Parameters
- metrics: list of metric names to include
- group_by: dimensions to slice by (use Dimension() and TimeDimension() syntax)
- where: filter conditions
- exports: optional — write results to a table on a schedule

## Exports
Exports take saved queries further by scheduling them to write to your warehouse:
\\\yaml
exports:
  - name: my_export
    config:
      export_as: table       # or view
      schema: reporting      # target schema
      alias: daily_report    # optional table name override
\\\

## When to Use Saved Queries
- Pre-built reports for executives that need scheduling
- Frequently queried metric combinations
- Dashboard backing tables
- AI agent query starting points (Claude can reference these by name via MCP)
