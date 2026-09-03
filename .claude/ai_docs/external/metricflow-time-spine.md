# MetricFlow Commands

## Overview
MetricFlow commands let you query, validate, and explore your semantic layer
from the command line. Use them to test metrics before connecting BI tools
or AI agents.

## Installation
\\\ash
pip install dbt-metricflow
# or included with dbt-cloud-cli
\\\

## Core Commands

### Query Metrics
\\\ash
# Basic metric query
dbt sl query --metrics total_revenue

# With dimension grouping
dbt sl query --metrics total_revenue --group-by deal__stage

# With time dimension
dbt sl query --metrics total_revenue --group-by metric_time__month

# Multiple metrics
dbt sl query --metrics total_revenue,deal_count --group-by deal__stage

# With filter
dbt sl query --metrics total_revenue \
  --group-by deal__stage \
  --where "deal__stage = 'Closed Won'"

# With ordering and limit
dbt sl query --metrics total_revenue \
  --group-by deal__stage \
  --order-by total_revenue \
  --limit 10
\\\

### List Available Metrics and Dimensions
\\\ash
dbt sl list metrics              # all metrics
dbt sl list dimensions           # all dimensions
dbt sl list entities             # all entities
dbt sl list saved-queries        # all saved queries
\\\

### Validate Configuration
\\\ash
dbt sl validate                  # validate semantic layer configs
\\\

## dbt Core Equivalents (mf prefix)
\\\ash
mf query --metrics total_revenue --group-by deal__stage
mf list metrics
mf validate-configs
\\\

## Output Formats
\\\ash
dbt sl query --metrics total_revenue --output csv > results.csv
dbt sl query --metrics total_revenue --output json
\\\
"@ | Set-Content "C:\Users\Stan\Documents\VScode\mammoth-dbt-ops-reporting\.claude\ai_docs\external\metricflow-commands.md"

@"
# MetricFlow Time Spine

## Overview
The time spine is a dbt model containing one row per date (or time period).
MetricFlow uses it to ensure all dates appear in time-series results,
even when no activity occurred on a given day. Required for
join_to_timespine functionality.

## Creating a Time Spine Model
\\\sql
-- models/marts/time_spine.sql
{{ config(materialized='table') }}

WITH spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2020-01-01' as date)",
        end_date="cast('2030-12-31' as date)"
    ) }}
)

SELECT
    cast(date_day AS DATE) AS date_day
FROM spine
\\\

## Registering the Time Spine
In your dbt_project.yml or model YAML:
\\\yaml
models:
  - name: time_spine
    config:
      meta:
        metricflow_time_spine_granularity: day
\\\

Or in semantic models:
\\\yaml
semantic_models:
  - name: time_spine
    model: ref('time_spine')
    defaults:
      agg_time_dimension: date_day
    dimensions:
      - name: date_day
        type: time
        type_params:
          time_granularity: day
          is_primary: true
\\\

## Why It Matters
Without time spine:
- Days with no deals show no row in results
- Charts have gaps
- Cumulative metrics are wrong

With time spine + join_to_timespine: true:
- Every day appears with a 0 value when no activity
- Charts are continuous
- Cumulative metrics are accurate
