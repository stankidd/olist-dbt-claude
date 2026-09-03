# DBT Fill Nulls Advanced

## Overview
fill_nulls_with and join_to_timespine work together to ensure every date
in your time series has a value, even when no activity occurred that day.
Essential for accurate time-series analysis and dashboards.

## fill_nulls_with
Replaces null metric values with a specified value (usually 0).

\\\yaml
metrics:
  - name: daily_deals_closed
    type: simple
    type_params:
      measure:
        name: deals_closed
        fill_nulls_with: 0
\\\

## join_to_timespine
Ensures every date in your time range appears in results, even with no data.
Without it, dates with zero activity are simply missing from results.

\\\yaml
metrics:
  - name: daily_revenue
    type: simple
    type_params:
      measure:
        name: revenue
        fill_nulls_with: 0
        join_to_timespine: true
\\\

## For Derived and Ratio Metrics
Both component metrics need join_to_timespine to avoid nulls:

\\\yaml
metrics:
  - name: close_rate
    type: derived
    type_params:
      expr: "deals_closed / deals_created"
      metrics:
        - name: deals_closed
          fill_nulls_with: 0
          join_to_timespine: true
        - name: deals_created
          fill_nulls_with: 1  # avoid divide by zero
          join_to_timespine: true
\\\

## Timespine Table
Your dbt project needs a timespine model (a table with one row per date).
Reference it in dbt_project.yml:
\\\yaml
models:
  mammoth_dbt_ops_reporting:
    +meta:
      metricflow_time_spine_granularity: day
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\dbt-fill-nulls-advanced.md"

@"
# DBT Join Logic (MetricFlow)

## Overview
MetricFlow constructs joins automatically based on entity definitions.
You never write explicit JOIN SQL in the semantic layer — you define relationships
via entities and MetricFlow figures out the correct join path and type.

## Join Types MetricFlow Uses

| Scenario | Join Type |
|---------|----------|
| One fact model + one dimension model | LEFT OUTER JOIN |
| Two fact models (multi-hop) | FULL OUTER JOIN |
| SCD Type II dimension | Special validity window join |

## Fan-Out and Chasm Join Prevention
MetricFlow automatically avoids:
- Fan-out joins: one row joining to many rows, inflating counts
- Chasm joins: two fact tables joining through a shared dimension

## Left Join Example
\\\sql
-- MetricFlow generates this automatically when you query
-- deal metrics with employee dimensions
SELECT
    deals.deal_id,
    deals.revenue,
    employees.region
FROM gold_deals deals
LEFT OUTER JOIN gold_employees employees
    ON deals.account_executive_id = employees.employee_id
\\\

## Multi-Hop Joins
If you need dimensions from a model two hops away, MetricFlow
traces the entity graph path automatically:
deals ? employees ? regions (two hops, no manual SQL needed)

## Explicit Join Configuration (when needed)
\\\yaml
entities:
  - name: customer
    type: foreign
    expr: customer_id
    join_type: left  # override default join type
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\dbt-join-logic.md"

@"
# DBT Measures

## Overview
Measures are the numerical aggregations defined in semantic models.
They are the building blocks for metrics. A measure defines WHAT to aggregate
and HOW to aggregate it. Metrics then reference measures to create
business-facing calculations.

## Aggregation Types

| Type | Description | Example |
|------|-------------|---------|
| sum | Sum of values | total_revenue |
| count | Count of rows | number_of_orders |
| count_distinct | Unique count | unique_customers |
| average | Mean value | average_deal_size |
| max | Maximum value | largest_deal |
| min | Minimum value | earliest_close_date |

## YAML Structure
\\\yaml
semantic_models:
  - name: deals
    model: ref('gold_deals')
    measures:
      - name: total_revenue
        description: "Sum of all deal revenue"
        agg: sum
        expr: deal_value
      - name: deal_count
        description: "Count of deals"
        agg: count
        expr: deal_id
      - name: avg_deal_size
        description: "Average deal value"
        agg: average
        expr: deal_value
      - name: unique_clients
        description: "Count of distinct clients"
        agg: count_distinct
        expr: client_id
\\\

## Measures vs Metrics
- Measure: raw aggregation defined in semantic model (technical)
- Metric: business-facing calculation that references a measure (semantic)

One measure can power multiple metrics.
\\\yaml
# One measure
measures:
  - name: revenue
    agg: sum
    expr: deal_value

# Multiple metrics using it
metrics:
  - name: total_revenue          # simple metric
  - name: trailing_28d_revenue   # cumulative metric
  - name: enterprise_revenue     # filtered simple metric
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\dbt-measures.md"

@"
# DBT Metrics Overview

## Overview
Metrics are business-facing calculations built on top of semantic model measures.
They are defined once in YAML and served consistently to all downstream tools.

## Four Metric Types

| Type | Description | Example |
|------|-------------|---------|
| simple | Single measure, optionally filtered | total_revenue |
| ratio | One measure divided by another | close_rate |
| cumulative | Rolling window aggregation | trailing_28d_revenue |
| derived | Expression combining other metrics | profit_margin |
| conversion | Base event to conversion event rate | trial_to_paid |

## Simple Metric
\\\yaml
metrics:
  - name: total_pipeline_value
    description: "Total value of all open deals"
    type: simple
    label: Total Pipeline Value
    type_params:
      measure: pipeline_value
    filter: "{{ Dimension('deal__stage') }} IN ('Proposal','Negotiation')"
\\\

## Why Metrics Matter for AI Agents
When the dbt MCP server is connected, Claude can:
- list all available metrics via list_metrics tool
- Query metrics by name without knowing underlying SQL
- Combine metrics with dimensions to answer business questions
- Generate consistent answers regardless of which AI tool is used

This is how Dylan queried the hiring gap analysis in Claude Desktop —
Claude used the MCP server to find and query the gold metrics,
not by guessing table names.
