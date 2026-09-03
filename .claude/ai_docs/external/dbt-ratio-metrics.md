# DBT Ratio Metrics

## Overview
Ratio metrics divide one measure by another to create rates, percentages,
and efficiency calculations. They are one of the four core metric types
in the dbt Semantic Layer.

## YAML Structure
\\\yaml
metrics:
  - name: deal_close_rate
    description: "Percentage of created deals that close successfully"
    type: ratio
    label: Deal Close Rate
    type_params:
      numerator: deals_closed
      denominator: deals_created
\\\

## With Filters
\\\yaml
metrics:
  - name: enterprise_close_rate
    type: ratio
    type_params:
      numerator:
        name: deals_closed
        filter: "{{ Dimension('deal__segment') }} = 'Enterprise'"
      denominator:
        name: deals_created
        filter: "{{ Dimension('deal__segment') }} = 'Enterprise'"
\\\

## Handling Nulls in Ratio Metrics
Use fill_nulls_with and join_to_timespine on both measures:
\\\yaml
type_params:
  numerator:
    name: deals_closed
    fill_nulls_with: 0
    join_to_timespine: true
  denominator:
    name: deals_created
    fill_nulls_with: 1
    join_to_timespine: true
\\\

## Common Use Cases
- Close rate (closed / created)
- Utilization rate (billed hours / available hours)
- Hiring fill rate (filled roles / open roles)
- Win rate (won deals / total deals)
