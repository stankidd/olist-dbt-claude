# DBT Cumulative Metrics

## Overview
Cumulative metrics aggregate a measure over a specified window of time.
Used for running totals, trailing averages, and period-over-period analysis.

## YAML Structure
\\\yaml
metrics:
  - name: trailing_revenue_28d
    description: "Revenue over trailing 28 days"
    type: cumulative
    label: 28-Day Trailing Revenue
    type_params:
      measure:
        name: revenue
        fill_nulls_with: 0
        join_to_timespine: true
      window: 28 days
\\\

## Without Window (All-Time Cumulative)
\\\yaml
metrics:
  - name: total_revenue_all_time
    type: cumulative
    type_params:
      measure:
        name: revenue
\\\

## Key Parameters
- window: rolling time window (omit for all-time cumulative)
- fill_nulls_with: value to use when no data exists for a period
- join_to_timespine: ensures every date appears even with no activity

## Common Use Cases
- Trailing 7/28/90 day metrics
- Month-to-date and year-to-date totals
- Running headcount or pipeline totals
