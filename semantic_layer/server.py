# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mcp[cli]>=1.2.0,<2",
#     "duckdb>=1.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""Olist semantic layer MCP server.

Answers natural-language metric questions against the DuckDB gold marts using
ONLY the governed definitions in models/olist/gold/semantic_models.yml and
metrics.yml. It never runs model-authored SQL -- the LLM picks a metric and
dimensions, and query_builder.py turns that into SQL built exclusively from
the YAML catalog. Every metric and dimension name is validated against the
catalog before any SQL is built; an unknown name is rejected, not guessed.

Run it directly (`python semantic_layer/server.py`) or via `uv run
semantic_layer/server.py` -- see README.md for the .mcp.json snippet to
connect a client over stdio.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import duckdb
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))

from query_builder import QueryBuilder  # noqa: E402
from semantic_loader import SemanticLayerError, load_catalog  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = "data/olist.duckdb"

mcp = FastMCP("olist-semantic-layer")

_catalog = load_catalog()
_connection: duckdb.DuckDBPyConnection | None = None
_schema_cache: dict[str, str] = {}


def _resolve_db_path() -> Path:
    raw_path = os.environ.get("DUCKDB_PATH", DEFAULT_DB_PATH)
    path = Path(raw_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _get_connection() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is None:
        db_path = _resolve_db_path()
        _connection = duckdb.connect(database=str(db_path), read_only=True)
    return _connection


def _schema_lookup(mart: str) -> str:
    if mart in _schema_cache:
        return _schema_cache[mart]
    con = _get_connection()
    row = con.execute(
        "SELECT table_schema FROM information_schema.tables WHERE table_name = ? LIMIT 1",
        [mart],
    ).fetchone()
    if row is None:
        raise SemanticLayerError(f"Model '{mart}' was not found in the DuckDB catalog. Run `dbt build` first.")
    qualified = f"{row[0]}.{mart}"
    _schema_cache[mart] = qualified
    return qualified


_builder = QueryBuilder(_catalog, _schema_lookup)


def _metric_catalog_entry(name: str) -> dict[str, Any]:
    metric = _catalog.metrics[name]
    dims = sorted(_catalog.valid_dimensions(name))
    return {
        "name": metric.name,
        "label": metric.label,
        "description": metric.description,
        "type": metric.type,
        "dimensions": dims,
    }


@mcp.tool()
def list_metrics() -> list[dict[str, Any]]:
    """List every governed metric: name, label, description, type, and the
    dimensions it can be grouped or filtered by."""
    return [_metric_catalog_entry(name) for name in sorted(_catalog.governed_metrics())]


@mcp.tool()
def get_dimensions(metric: str) -> list[dict[str, Any]]:
    """List the valid group-by / filter dimensions for one metric."""
    _catalog.require_metric(metric)
    valid_dims = _catalog.valid_dimensions(metric)
    return [
        {"name": dim.name, "type": dim.type, "time_granularity": dim.time_granularity}
        for dim, _owner in sorted(valid_dims.values(), key=lambda pair: pair[0].name)
    ]


@mcp.tool()
def query_metric(
    metric: str,
    group_by: list[str] | None = None,
    filters: list[dict[str, Any]] | None = None,
    time_grain: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Run the governed SQL for one metric and return rows.

    filters: list of {"dimension": str, "op": one of = != > < >= <= IN, "value": ...}
    time_grain: one of day, week, month, quarter, year -- only applies to the
    metric's time dimension when it's included in group_by or filters.
    """
    built = _builder.build(metric, group_by=group_by, filters=filters, time_grain=time_grain, limit=limit)
    con = _get_connection()
    rows = con.execute(built.sql, built.params).fetchall()
    return {
        "sql": built.sql,
        "columns": built.columns,
        "rows": [dict(zip(built.columns, row)) for row in rows],
    }


@mcp.tool()
def ask(question: str) -> dict[str, Any]:
    """Convenience entry point: maps a natural-language question to one
    query_metric() call using the governed catalog from list_metrics(), then
    runs it. This is a thin planner, not an arbitrary-SQL path -- it still
    only ever executes a governed query_metric() call."""
    question_lower = question.lower()

    best_metric: str | None = None
    best_score = 0
    for name, metric in _catalog.governed_metrics().items():
        haystack = f"{metric.name} {metric.label}".lower().replace("_", " ")
        score = sum(1 for token in haystack.split() if token and token in question_lower)
        if score > best_score:
            best_score = score
            best_metric = name

    if best_metric is None:
        raise SemanticLayerError(
            "Could not map this question to a governed metric. Call list_metrics() "
            "to see what's available."
        )

    valid_dims = _catalog.valid_dimensions(best_metric)
    group_by = [dim_name for dim_name in valid_dims if dim_name.replace("_", " ") in question_lower]

    result = query_metric(best_metric, group_by=group_by or None)
    result["mapped_metric"] = best_metric
    result["mapped_group_by"] = group_by
    return result


if __name__ == "__main__":
    mcp.run()
