# DBT Derived Metrics

## Overview
Derived metrics are created by writing expressions using other metrics.
They let you combine, divide, or transform existing metrics into new ones.

## YAML Structure
\\\yaml
metrics:
  - name: profit_margin
    description: "Profit as a percentage of revenue"
    type: derived
    label: Profit Margin
    type_params:
      expr: "profit / revenue"
      metrics:
        - name: profit
        - name: revenue
\\\

## With Filters on Component Metrics
\\\yaml
metrics:
  - name: enterprise_revenue_share
    type: derived
    type_params:
      expr: "enterprise_revenue / total_revenue"
      metrics:
        - name: enterprise_revenue
          filter: "{{ Dimension('customer__segment') }} = 'Enterprise'"
        - name: total_revenue
\\\

## fill_nulls_with for Derived Metrics
\\\yaml
type_params:
  expr: "metric_a / metric_b"
  metrics:
    - name: metric_a
      fill_nulls_with: 0
      join_to_timespine: true
    - name: metric_b
      fill_nulls_with: 1  # avoid divide by zero
      join_to_timespine: true
\\\

## Common Use Cases
- Margin calculations (profit / revenue)
- Utilization rates (hours_billed / hours_available)
- Average deal size (total_revenue / deal_count)
- Hiring gap (demand - supply)
