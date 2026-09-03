# DBT Entities

## Overview
Entities are the join keys of the semantic layer. They define how semantic
models relate to each other, allowing MetricFlow to construct joins automatically
without you writing explicit SQL join logic.

## Entity Types

| Type | Description | Example |
|------|-------------|---------|
| primary | Unique identifier for this model | order_id in orders |
| foreign | References a primary key in another model | customer_id in orders |
| unique | Unique but not the primary entity | email in users |
| natural | Business key (may not be DB primary key) | product_sku |

## YAML Structure
\\\yaml
semantic_models:
  - name: orders
    model: ref('gold_orders')
    entities:
      - name: order
        type: primary
        expr: order_id
      - name: customer
        type: foreign
        expr: customer_id
      - name: product
        type: foreign
        expr: product_id
\\\

## How MetricFlow Uses Entities
MetricFlow builds a semantic graph where:
- Semantic models are nodes
- Entities are edges connecting them

When you query a metric with a dimension from another model,
MetricFlow traces the entity path and constructs the join for you.

## DBT Project Example
\\\yaml
# gold_deals semantic model
entities:
  - name: deal
    type: primary
    expr: deal_id
  - name: employee
    type: foreign
    expr: account_executive_id

# gold_employees semantic model
entities:
  - name: employee
    type: primary
    expr: employee_id
\\\
This lets you query deal metrics broken down by employee dimensions automatically.
