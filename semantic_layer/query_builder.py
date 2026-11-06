"""Turns (metric, group_by, filters, time_grain) into governed DuckDB SQL.

No metric math lives here -- every aggregation expression comes from the
SemanticCatalog, which reads it from semantic_models.yml/metrics.yml. This
module's only job is to assemble that governed SQL and reject anything
(metric, dimension, operator, grain) that isn't in the catalog.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from semantic_loader import Dimension, SemanticCatalog, SemanticLayerError, SemanticModel

_ALLOWED_OPS = {"=", "!=", ">", "<", ">=", "<=", "IN"}
_ALLOWED_GRAINS = {"day", "week", "month", "quarter", "year"}
_SIMPLE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _qualify(expr: str, alias: str) -> str:
    """Prefixes a bare column name with its table alias. A measure/dimension
    `expr` can also be a full SQL expression (e.g. a CASE statement) built
    from columns that already resolve unambiguously against the base table
    -- those are left as-is rather than mangled by a blind string prefix."""
    if _SIMPLE_IDENT_RE.match(expr):
        return f"{alias}.{expr}"
    return expr

_AGG_SQL = {
    "sum": "SUM",
    "count": "COUNT",
    "average": "AVG",
    "avg": "AVG",
    "max": "MAX",
    "min": "MIN",
}


@dataclass
class Filter:
    dimension: str
    op: str
    value: Any


@dataclass
class BuiltQuery:
    sql: str
    params: list[Any]
    columns: list[str]


def _aggregate_sql(agg: str, expr: str) -> str:
    if agg == "count_distinct":
        return f"COUNT(DISTINCT {expr})"
    func = _AGG_SQL.get(agg)
    if func is None:
        raise SemanticLayerError(f"Unsupported aggregation type '{agg}'")
    return f"{func}({expr})"


class QueryBuilder:
    """Builds SQL for one metric request against a single DuckDB connection.

    `schema_lookup` resolves a dbt model name (e.g. "mart_orders") to its
    fully-qualified `schema.table` in the DuckDB file, so the generated SQL
    never hardcodes a dev schema name.
    """

    def __init__(self, catalog: SemanticCatalog, schema_lookup: Callable[[str], str]):
        self.catalog = catalog
        self.schema_lookup = schema_lookup

    def build(
        self,
        metric_name: str,
        group_by: list[str] | None = None,
        filters: list[dict] | None = None,
        time_grain: str | None = None,
        limit: int = 100,
    ) -> BuiltQuery:
        group_by = group_by or []
        filters = [Filter(**f) for f in (filters or [])]

        metric = self.catalog.require_metric(metric_name)
        sm = self.catalog.semantic_models[metric.semantic_model]
        valid_dims = self.catalog.valid_dimensions(metric_name)

        if time_grain is not None and time_grain not in _ALLOWED_GRAINS:
            raise SemanticLayerError(
                f"Unsupported time_grain '{time_grain}'. Valid grains: {sorted(_ALLOWED_GRAINS)}"
            )

        base_table = self.schema_lookup(sm.mart)
        join_clauses: list[str] = []
        joined_aliases: dict[str, str] = {}

        def resolve_dimension(dim_name: str) -> str:
            if dim_name not in valid_dims:
                raise SemanticLayerError(
                    f"Unknown dimension '{dim_name}' for metric '{metric_name}'. "
                    f"Valid dimensions: {sorted(valid_dims)}"
                )
            dim, owner_model = valid_dims[dim_name]

            if owner_model is None:
                column_expr = _qualify(dim.expr, "base")
            else:
                alias = joined_aliases.get(owner_model.name)
                if alias is None:
                    alias = f"j_{owner_model.name}"
                    joined_aliases[owner_model.name] = alias
                    join_table = self.schema_lookup(owner_model.mart)
                    fk_expr = None
                    for entity in sm.entities.values():
                        if entity.type == "foreign" and entity.name == owner_model.primary_entity:
                            fk_expr = entity.expr
                            break
                    if fk_expr is None:
                        raise SemanticLayerError(
                            f"No foreign entity on '{sm.name}' links to '{owner_model.name}'"
                        )
                    pk_expr = owner_model.entities[owner_model.primary_entity].expr
                    join_clauses.append(
                        f"LEFT JOIN {join_table} AS {alias} "
                        f"ON {_qualify(fk_expr, 'base')} = {_qualify(pk_expr, alias)}"
                    )
                column_expr = _qualify(dim.expr, alias)

            if dim.type == "time" and time_grain:
                column_expr = f"DATE_TRUNC('{time_grain}', {column_expr})"
            return column_expr

        select_exprs: list[str] = []
        group_exprs: list[str] = []
        columns: list[str] = []
        for dim_name in group_by:
            sql_expr = resolve_dimension(dim_name)
            select_exprs.append(f"{sql_expr} AS {dim_name}")
            group_exprs.append(sql_expr)
            columns.append(dim_name)

        params: list[Any] = []
        where_clauses: list[str] = []
        for f in filters:
            if f.op not in _ALLOWED_OPS:
                raise SemanticLayerError(
                    f"Unsupported filter operator '{f.op}'. Valid operators: {sorted(_ALLOWED_OPS)}"
                )
            sql_expr = resolve_dimension(f.dimension)
            if f.op == "IN":
                values = f.value if isinstance(f.value, (list, tuple)) else [f.value]
                placeholders = ", ".join("?" for _ in values)
                where_clauses.append(f"{sql_expr} IN ({placeholders})")
                params.extend(values)
            else:
                where_clauses.append(f"{sql_expr} {f.op} ?")
                params.append(f.value)

        if metric.type == "simple":
            measure = sm.measures[metric.measure]
            agg_sql = _aggregate_sql(measure.agg, _qualify(measure.expr, "base"))
            select_exprs.append(f"{agg_sql} AS {metric_name}")
            columns.append(metric_name)
        else:
            numerator = sm.measures[metric.numerator_measure]
            denominator = sm.measures[metric.denominator_measure]
            num_sql = _aggregate_sql(numerator.agg, _qualify(numerator.expr, "base"))
            den_sql = _aggregate_sql(denominator.agg, _qualify(denominator.expr, "base"))
            select_exprs.append(f"{num_sql} AS {metric_name}__numerator")
            select_exprs.append(f"{den_sql} AS {metric_name}__denominator")
            select_exprs.append(
                f"CAST({num_sql} AS DOUBLE) / NULLIF({den_sql}, 0) AS {metric_name}"
            )
            columns.extend([f"{metric_name}__numerator", f"{metric_name}__denominator", metric_name])

        sql = "SELECT\n    " + ",\n    ".join(select_exprs) + f"\nFROM {base_table} AS base"
        for jc in join_clauses:
            sql += f"\n{jc}"
        if where_clauses:
            sql += "\nWHERE " + " AND ".join(where_clauses)
        if group_exprs:
            sql += "\nGROUP BY " + ", ".join(str(i + 1) for i in range(len(group_exprs)))
        sql += f"\nLIMIT {int(limit)}"

        return BuiltQuery(sql=sql, params=params, columns=columns)
