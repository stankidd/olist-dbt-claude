# Olist Semantic Layer

A local MCP server that answers metric questions against the DuckDB gold
marts using only the governed definitions in
[`models/olist/gold/semantic_models.yml`](../models/olist/gold/semantic_models.yml)
and [`metrics.yml`](../models/olist/gold/metrics.yml). It never runs
model-authored SQL: an LLM picks a metric, optional dimensions, and optional
filters, and `query_builder.py` turns that into SQL built exclusively from
the YAML catalog. Any unknown metric or dimension is rejected, not guessed.

See [`../.claude/project_docs/client-olist/04-specs/documents/olist-semantic-layer-spec.md`](../.claude/project_docs/client-olist/04-specs/documents/olist-semantic-layer-spec.md)
for the full technical spec.

## How it works

```
semantic_loader.py  -- parses the two YAML files into an in-memory catalog
                        (semantic models, entities, dimensions, measures, metrics)
query_builder.py    -- turns (metric, group_by, filters, time_grain) into a
                        parameterized DuckDB SQL string, validated against
                        that catalog
server.py           -- the MCP server; exposes list_metrics, get_dimensions,
                        query_metric, and ask as MCP tools
```

No metric math lives in Python. Every aggregation expression, join, and
filterable dimension comes from the dbt YAML; the Python files only read it.

### Governed metrics

The 11 business-facing metrics defined in the spec:

| Metric | Type |
|---|---|
| total_gmv | simple |
| order_count | simple |
| avg_order_value | ratio |
| avg_items_per_order | ratio |
| on_time_delivery_rate | ratio |
| customer_count | simple |
| repeat_customer_rate | ratio |
| avg_customer_ltv | ratio |
| avg_review_score | simple |
| seller_count | simple |
| avg_seller_review | simple |

`metrics.yml` also defines four small helper metrics (`total_items`,
`on_time_orders`, `repeat_customer_count`, `total_customer_spend`) tagged
`config.meta.component: true`. MetricFlow's `ratio` type resolves its
numerator/denominator by metric name, not raw measure name, so each measure
used only inside a ratio needs a thin `simple` metric wrapping it. These are
valid dbt metrics (required for `dbt parse` to succeed) but
`semantic_loader.py` excludes them from `list_metrics()` -- they are not
part of the governed 11 and the server never exposes them.

### Cross-mart dimensions

A metric's valid dimensions include its own mart's dimensions, plus -- one
hop out -- the dimensions of any mart reachable through a `foreign` entity
on its semantic model (e.g. `sem_orders` can filter/group by
`sem_sellers.seller_tier` via the `seller_id` entity). This is what makes
"order count where seller_tier = Gold" work without a cross-model metric
having to be declared explicitly. Call `get_dimensions(metric)` to see the
exact list for a given metric.

## Running it

Requires [uv](https://docs.astral.sh/uv/). The server's dependencies
(`mcp`, `duckdb`, `pyyaml`) are declared inline in `server.py` (PEP 723), so
`uv run` installs them automatically -- no project-level venv needed.

```bash
uv run semantic_layer/server.py
```

Or, with dependencies installed some other way:

```bash
python semantic_layer/server.py
```

It opens `data/olist.duckdb` **read-only**, using the same relative path
`profiles.yml` uses (resolved relative to the repo root, not the process's
working directory). Set `DUCKDB_PATH` to point it elsewhere, exactly as you
would for `dbt build`.

The marts (`mart_orders`, `mart_customers`, `mart_sellers`, `mart_reviews`)
and the `metricflow_time_spine` model must already be built
(`dbt build`) before the server can query them.

## Connecting a client

Add this to `.mcp.json`:

```json
{
  "mcpServers": {
    "olist-semantic-layer": {
      "command": "uv",
      "args": ["run", "semantic_layer/server.py"],
      "cwd": "C:/Users/Stan/Documents/VScode/olist-dbt-claude"
    }
  }
}
```

## Example questions -> governed queries

| Natural-language question | Governed query |
|---|---|
| "What's our total GMV?" | `query_metric("total_gmv")` |
| "What's the average order value?" | `query_metric("avg_order_value")` |
| "Break down GMV by customer state" | `query_metric("total_gmv", group_by=["customer_state"])` |
| "How many orders came from Gold-tier sellers?" | `query_metric("order_count", filters=[{"dimension": "seller_tier", "op": "=", "value": "Gold"}])` |
| "What share of customers are repeat buyers?" | `query_metric("repeat_customer_rate")` |
| "On-time delivery rate by month" | `query_metric("on_time_delivery_rate", group_by=["order_date"], time_grain="month")` |

`ask(question)` wraps this mapping step itself: it scores governed metric
names/labels against the question's words, picks the best match, pulls any
dimension names mentioned in the question into `group_by`, and calls
`query_metric()`. It is a thin planner, not a text-to-SQL engine -- it still
only ever executes a governed `query_metric()` call, so a question it can't
confidently map raises an error naming `list_metrics()` rather than guessing.

## Guardrails

1. **No arbitrary SQL from the model.** The LLM supplies a metric name,
   dimension names, and filter values; `query_builder.py` is the only thing
   that assembles SQL, and only from catalog-validated pieces.
2. **Catalog-validated.** Every metric and dimension in a request is checked
   against `semantic_loader.py`'s catalog. An unknown name raises
   `SemanticLayerError` naming what's actually valid -- never a guess.
3. **Read-only connection.** `duckdb.connect(..., read_only=True)`. The
   server cannot write to the warehouse.
4. **One definition.** The metric math lives only in `semantic_models.yml`
   and `metrics.yml`; dbt and this server read the same files, so they
   cannot drift apart.

## Definition of Done

- [x] `dbt parse` succeeds with `semantic_models.yml` and `metrics.yml`
- [x] `semantic_loader` loads all 11 governed metrics and their dimensions
- [x] `query_builder` produces correct SQL for a simple metric (`total_gmv`),
      a ratio metric (`avg_order_value`), a grouped query (`total_gmv` by
      `customer_state`), and a filtered query (`order_count` where
      `seller_tier = 'Gold'`)
- [x] `query_metric('total_gmv')` reconciles exactly against
      `SELECT SUM(total_gmv) FROM mart_orders`
- [x] `query_metric('repeat_customer_rate')` matches a hand-written check
- [x] An unknown metric, dimension, or filter operator is rejected, not guessed
- [x] The server starts and responds to `list_metrics` over real MCP stdio
      (verified with the `mcp` Python SDK's stdio client, not just a direct
      function call)
