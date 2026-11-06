# Olist Semantic Layer — Technical Specification

**Project:** olist-dbt-claude
**Builds on:** the existing 20-model medallion pipeline (4 gold marts)
**Author:** Stan Kidd — Cloud Analytics Consulting
**Status:** Ready to Build
**Approach:** MetricFlow-style semantic definitions in dbt YAML, served to LLMs
through a local MCP server that queries the DuckDB marts.

---

## Goal

Add a governed semantic layer on top of the gold marts so a business user — or
an AI agent — can ask questions of trusted metrics in plain English, without
writing SQL and without an engineer in the loop. Metrics, dimensions, and joins
are defined once; every consumer inherits the same governed definitions.

Two deliverables:
1. **Semantic definitions** in dbt (semantic_models + metrics YAML) — the
   portable, standard artifact. Valid dbt, portable to the dbt Semantic Layer
   on Snowflake/BigQuery.
2. **A local MCP server** (Python) that reads those definitions and answers
   natural-language metric questions against the DuckDB marts — so the whole
   thing runs on a clone with no cloud account, preserving the repo's
   "clone and reproduce every number" promise.

---

## Design Principles

- **Define once.** Each metric and dimension is declared a single time in YAML.
  The MCP server reads the same definitions; it never redefines a metric in code.
- **Governed.** The server can only answer using declared metrics and
  dimensions. It will not run arbitrary SQL from the LLM — it builds SQL from
  the governed definitions. This is the guardrail that makes the answers
  trustworthy.
- **Portable.** Semantic YAML follows MetricFlow conventions so the same
  definitions move to a Cloud warehouse unchanged. SQL generated for DuckDB
  uses portable expressions.
- **Reproducible.** Runs locally against data/olist.duckdb. No credentials.

---

## Part 1 — Semantic Definitions (dbt YAML)

Create `models/olist/gold/semantic_models.yml` declaring semantic models over
the existing marts, then `models/olist/gold/metrics.yml` declaring metrics.

### Semantic models (entities, dimensions, measures)

**sem_orders** (over `mart_orders`)
- entity: order_id (primary)
- dimensions:
  - order_date (time, day grain) — from order_purchase_timestamp
  - customer_state (categorical)
  - seller_state (categorical)
  - is_on_time (categorical/boolean)
- measures:
  - total_gmv (sum of total_gmv)
  - order_count (count of order_id)
  - total_items (sum of total_items)

**sem_customers** (over `mart_customers`)
- entity: customer_unique_id (primary)
- dimensions:
  - customer_state (categorical)
  - is_repeat_customer (categorical/boolean)
  - first_order_date (time, day grain)
- measures:
  - customer_count (count of customer_unique_id)
  - repeat_customer_count (sum where is_repeat_customer)
  - total_customer_spend (sum of total_spend)

**sem_sellers** (over `mart_sellers`)
- entity: seller_id (primary)
- dimensions:
  - seller_state (categorical)
  - seller_tier (categorical: Gold/Silver/Bronze)
- measures:
  - seller_count (count of seller_id)
  - seller_gmv (sum of total_gmv)
  - avg_seller_review (avg of avg_review_score)

**sem_reviews** (over `mart_reviews`)
- entity: review_id (primary)
- dimensions:
  - sentiment_bucket (categorical: Positive/Neutral/Negative)
  - product_category (categorical)
  - is_late_delivery (categorical/boolean)
- measures:
  - review_count (count of review_id)
  - avg_review_score (avg of review_score)

### Metrics (the governed, business-facing definitions)

| Metric | Type | Definition | Primary semantic model |
|--------|------|-----------|------------------------|
| total_gmv | simple | sum(total_gmv) | sem_orders |
| order_count | simple | count(order_id) | sem_orders |
| avg_order_value | ratio | total_gmv / order_count | sem_orders |
| avg_items_per_order | ratio | total_items / order_count | sem_orders |
| on_time_delivery_rate | ratio | on_time_orders / order_count | sem_orders |
| customer_count | simple | count(customer_unique_id) | sem_customers |
| repeat_customer_rate | ratio | repeat_customer_count / customer_count | sem_customers |
| avg_customer_ltv | ratio | total_customer_spend / customer_count | sem_customers |
| avg_review_score | simple | avg(review_score) | sem_reviews |
| seller_count | simple | count(seller_id) | sem_sellers |
| avg_seller_review | simple | avg(avg_review_score) | sem_sellers |

Each metric carries a one-line `description` and a `label` for display. These
descriptions are what the MCP server surfaces to the LLM so it can pick the
right metric.

---

## Part 2 — The MCP Server

Create `semantic_layer/` at the repo root:

```
semantic_layer/
  server.py            # the MCP server
  semantic_loader.py   # parses the YAML into an in-memory metric catalog
  query_builder.py     # turns (metric, group_by, filter) into DuckDB SQL
  README.md            # how to run and connect it
```

### semantic_loader.py
- Parses `models/olist/gold/semantic_models.yml` and `metrics.yml`.
- Builds a catalog: for each metric, its type, the measure expression, the
  source mart table, the valid dimensions it can be grouped/filtered by, and
  the description.
- This is the single source of truth the server queries — no metric logic is
  written in Python, only read from the YAML.

### query_builder.py
- Input: a metric name, an optional list of group-by dimensions, an optional
  list of filters (dimension op value), an optional time grain.
- Output: a parameterized DuckDB SQL string built **only** from governed
  definitions. Rejects any metric or dimension not in the catalog.
- Ratio metrics expand to numerator/denominator over the same grain.
- Validates every dimension against the metric's allowed dimension list before
  building SQL — the guardrail against hallucinated columns.

### server.py — MCP tools exposed
- `list_metrics()` → returns each metric's name, label, description, and the
  dimensions it can be sliced by.
- `get_dimensions(metric)` → valid group-by / filter dimensions for a metric.
- `query_metric(metric, group_by=[], filters=[], time_grain=None, limit=100)`
  → runs the governed SQL against DuckDB, returns rows.
- `ask(question)` → convenience entry point: the LLM maps a natural-language
  question to one `query_metric` call using the catalog from `list_metrics`.
  The server still only executes governed `query_metric` calls — `ask` is a
  thin planner, not an arbitrary-SQL path.

### Connection to DuckDB
- Opens `data/olist.duckdb` **read-only** using the same relative path as
  profiles.yml. No writes. No absolute paths.

### Transport
- Standard MCP stdio server (runs via `python semantic_layer/server.py` or
  `uv run`), so Claude Code / Claude Desktop / any MCP client can connect by
  pointing an `.mcp.json` entry at it.

---

## Guardrails (what makes the answers trustworthy)

1. **No arbitrary SQL from the model.** The LLM chooses a metric and
   dimensions; the server builds the SQL. The model never hands raw SQL to the
   database.
2. **Catalog-validated.** Every metric and every dimension in a request is
   checked against the YAML catalog. Unknown name → rejected with a clear error,
   not a guess.
3. **Read-only connection.** The server cannot modify the warehouse.
4. **One definition.** The metric math lives only in the YAML; the server reads
   it. dbt and the MCP server cannot drift because they share the source.

---

## Tests / Definition of Done

- [ ] `dbt parse` succeeds with the new semantic_models.yml and metrics.yml
      (definitions are valid dbt)
- [ ] `semantic_loader` loads all 11 metrics and their dimensions without error
- [ ] `query_builder` produces correct SQL for: a simple metric (total_gmv),
      a ratio metric (avg_order_value), a grouped query (total_gmv by
      customer_state), and a filtered query (order_count where
      seller_tier = 'Gold')
- [ ] Reconciliation: `query_metric('total_gmv')` equals
      `SELECT SUM(total_gmv) FROM mart_orders` run directly — the semantic layer
      returns the same number as the mart
- [ ] `query_metric('repeat_customer_rate')` matches a hand-written check
- [ ] An unknown metric or dimension is rejected, not guessed
- [ ] Server starts and responds to `list_metrics` over MCP stdio
- [ ] README documents: run the loader, start the server, example questions,
      and the .mcp.json snippet to connect a client

---

## README Additions

Add a "Semantic Layer" section to the repo README documenting, honestly:
- Metrics defined once in MetricFlow-style dbt YAML (portable to the dbt
  Semantic Layer on Snowflake/BigQuery)
- Served locally through a custom MCP server so anyone can query governed
  metrics on DuckDB with no cloud account
- The guardrail: the server answers only from governed definitions and never
  runs model-authored SQL
- Example natural-language questions and the governed metric query each maps to

---

## Out of Scope (keep it tight)

- No hosted/Cloud dbt Semantic Layer wiring (noted as the portability target,
  not built)
- No write-back, no caching layer, no auth (local single-user)
- No new marts or model changes — the semantic layer sits on what exists
