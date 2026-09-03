# DBT Semantic Models

## Overview
Semantic models are YAML-defined abstractions that sit on top of dbt models.
They annotate your data with business meaning — declaring what each column
represents (entity, dimension, or measure) so MetricFlow can generate
consistent SQL automatically.

## Structure
\\\yaml
semantic_models:
  - name: deals
    description: "One row per deal in the pipeline"
    model: ref('gold_deals')
    defaults:
      agg_time_dimension: close_date

    entities:
      - name: deal
        type: primary
        expr: deal_id
      - name: client
        type: foreign
        expr: client_id

    dimensions:
      - name: stage
        type: categorical
        expr: deal_stage
      - name: close_date
        type: time
        type_params:
          time_granularity: day
      - name: segment
        type: categorical
        expr: client_segment

    measures:
      - name: deal_value
        description: "Total value of the deal"
        agg: sum
        expr: contract_value
      - name: deal_count
        agg: count
        expr: deal_id
\\\

## Three Column Types
- entities: join keys — how this model connects to others
- dimensions: ways to slice and filter (categorical, time, boolean)
- measures: numerical aggregations (sum, count, average, etc.)

## Relationship to dbt Models
One semantic model maps to exactly one dbt model (1:1 relationship).
Multiple semantic models can exist for the same dbt model if needed.
The semantic model does not change the underlying table — it annotates it.

## Recommended Placement
Define semantic models in the same YAML file as your model's schema definition:
\\\
models/gold/
    gold_deals.sql
    gold_deals.yml      ? put semantic model here alongside column docs
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\dbt-semantic-models.md"

@"
# DBT Simple Metrics

## Overview
Simple metrics are the most fundamental metric type. They reference a single
measure, optionally apply a filter, and produce a direct aggregation.
All other metric types are built on top of simple metrics.

## YAML Structure
\\\yaml
metrics:
  - name: total_pipeline_value
    description: "Total contract value of all active pipeline deals"
    type: simple
    label: Total Pipeline Value
    type_params:
      measure: pipeline_value
\\\

## With Filter
\\\yaml
metrics:
  - name: open_pipeline_value
    description: "Pipeline value for deals not yet closed"
    type: simple
    label: Open Pipeline Value
    type_params:
      measure: pipeline_value
    filter: |
      {{ Dimension('deal__stage') }} NOT IN ('Closed Won', 'Closed Lost')
\\\

## With fill_nulls_with
\\\yaml
metrics:
  - name: daily_new_deals
    type: simple
    type_params:
      measure:
        name: new_deal_count
        fill_nulls_with: 0
        join_to_timespine: true
\\\

## Common Simple Metrics for Consulting Projects
\\\yaml
metrics:
  - name: total_deals          # count of deals
  - name: pipeline_value       # sum of deal values
  - name: avg_deal_size        # average contract value
  - name: current_headcount    # count of active employees
  - name: hiring_gap           # demand minus supply
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\dbt-simple-metrics.md"

@"
# DBT Validation

## Overview
dbt provides built-in validation tools to ensure data quality, model correctness,
and semantic layer configuration accuracy before pushing to production.

## Model Tests (schema.yml)
\\\yaml
models:
  - name: gold_deals
    columns:
      - name: deal_id
        tests:
          - unique
          - not_null
      - name: stage
        tests:
          - accepted_values:
              values: ['Proposal', 'Negotiation', 'Verbal Close', 'Closed Won', 'Closed Lost']
      - name: client_id
        tests:
          - not_null
          - relationships:
              to: ref('gold_clients')
              field: client_id
\\\

## Running Tests
\\\ash
dbt test                           # run all tests
dbt test --select gold_deals       # test one model
dbt test --select tag:gold         # test all gold models
dbt build --select gold_deals      # run + test in one command
\\\

## Semantic Layer Validation
\\\ash
dbt sl validate                    # validate semantic model configs
mf validate-configs                # MetricFlow config validation
mf query --metrics total_revenue   # test a metric returns data
\\\

## Agent Self-Validation Pattern
Dylan's agents validate automatically:
1. Write model
2. Run dbt build (compiles + tests)
3. If tests fail ? query data with dbt show ? understand why ? fix ? retest
4. Only push PR when all tests pass

## Custom Generic Tests (macros/tests/)
\\\yaml
# test that numeric columns are non-negative
- name: deal_value
  tests:
    - dbt_utils.expression_is_true:
        expression: ">= 0"
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\dbt-validation.md"

@"
# Dimensions (MetricFlow)

## Overview
Dimensions are the columns you use to slice, filter, and group metrics.
They answer the "by what?" question — revenue by region, deals by stage,
headcount by role. Dimensions are defined in semantic models.

## Dimension Types

| Type | Description | Example |
|------|-------------|---------|
| categorical | Text or boolean groupings | stage, region, role |
| time | Date/timestamp columns | close_date, created_at |
| boolean | True/false filters | is_active, is_enterprise |

## YAML Structure
\\\yaml
dimensions:
  - name: deal_stage
    type: categorical
    expr: stage

  - name: close_date
    type: time
    type_params:
      time_granularity: day   # day, week, month, quarter, year

  - name: is_enterprise
    type: categorical         # boolean treated as categorical
    expr: "CASE WHEN segment = 'Enterprise' THEN TRUE ELSE FALSE END"
\\\

## Time Granularity Options
\\\yaml
type_params:
  time_granularity: day      # finest grain
  time_granularity: week
  time_granularity: month
  time_granularity: quarter
  time_granularity: year
\\\

## Querying with Dimensions
\\\ash
# CLI
dbt sl query --metrics total_revenue --group-by deal__deal_stage

# In Claude Desktop via MCP
"Show me pipeline value by role and stage for upcoming deals"
\\\

## Dimension Naming Convention
When querying, reference dimensions as: semantic_model_name__dimension_name
Example: deal__stage, employee__role, client__segment
