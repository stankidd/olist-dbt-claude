"""Parses semantic_models.yml and metrics.yml into an in-memory metric catalog.

This is the single source of truth the MCP server queries. No metric math is
written here or in query_builder.py -- every aggregation, filter, and join is
read straight from the governed dbt YAML.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SEMANTIC_MODELS_PATH = REPO_ROOT / "models" / "olist" / "gold" / "semantic_models.yml"
METRICS_PATH = REPO_ROOT / "models" / "olist" / "gold" / "metrics.yml"

# The one synthetic dimension in semantic_models.yml (sem_sellers.parse_time_placeholder)
# that exists only to satisfy MetricFlow's dbt-parse requirement that every semantic
# model with measures declare an aggregation time dimension. mart_sellers has no date
# column, so this constant has no business meaning and must never reach the catalog.
_PARSE_ONLY_DIMENSIONS = {"parse_time_placeholder"}

_REF_RE = re.compile(r"ref\(\s*['\"](\w+)['\"]\s*\)")


class SemanticLayerError(ValueError):
    """Raised when the governed YAML can't be parsed into a valid catalog."""


@dataclass(frozen=True)
class Dimension:
    name: str
    type: str
    expr: str
    time_granularity: str | None = None


@dataclass(frozen=True)
class Measure:
    name: str
    agg: str
    expr: str


@dataclass(frozen=True)
class Entity:
    name: str
    type: str
    expr: str


@dataclass(frozen=True)
class SemanticModel:
    name: str
    description: str
    mart: str
    primary_entity: str
    entities: dict[str, Entity]
    dimensions: dict[str, Dimension]
    measures: dict[str, Measure]


@dataclass(frozen=True)
class MetricDef:
    name: str
    type: str  # "simple" | "ratio"
    label: str
    description: str
    semantic_model: str
    measure: str | None = None
    numerator_measure: str | None = None
    denominator_measure: str | None = None
    component: bool = False  # internal ratio-component metric; not part of the governed 11


class SemanticCatalog:
    def __init__(self, semantic_models: dict[str, SemanticModel], metrics: dict[str, MetricDef]):
        self.semantic_models = semantic_models
        self.metrics = metrics

    def governed_metrics(self) -> dict[str, MetricDef]:
        """The business-facing metrics this server exposes -- excludes ratio-component helpers."""
        return {name: m for name, m in self.metrics.items() if not m.component}

    def require_metric(self, metric_name: str) -> MetricDef:
        metric = self.metrics.get(metric_name)
        if metric is None or metric.component:
            raise SemanticLayerError(
                f"Unknown metric '{metric_name}'. Call list_metrics() for the governed catalog."
            )
        return metric

    def valid_dimensions(self, metric_name: str) -> dict[str, tuple[Dimension, SemanticModel | None]]:
        """Dimensions a metric can be grouped/filtered by.

        Maps dimension_name -> (Dimension, owning SemanticModel if it must be
        joined in, else None for a dimension native to the metric's own mart).
        One hop only: a foreign entity on the metric's semantic model whose
        target model is some other model's primary entity. This mirrors
        MetricFlow's own join-path tracing, scoped down to what this project
        actually needs.
        """
        metric = self.require_metric(metric_name)
        sm = self.semantic_models[metric.semantic_model]
        result: dict[str, tuple[Dimension, SemanticModel | None]] = {}

        for dim in sm.dimensions.values():
            result[dim.name] = (dim, None)

        for entity in sm.entities.values():
            if entity.type != "foreign":
                continue
            joined = self._find_by_primary_entity(entity.name)
            if joined is None or joined.name == sm.name:
                continue
            for dim in joined.dimensions.values():
                result.setdefault(dim.name, (dim, joined))

        return result

    def _find_by_primary_entity(self, entity_name: str) -> SemanticModel | None:
        for sm in self.semantic_models.values():
            if sm.primary_entity == entity_name:
                return sm
        return None


def _extract_ref(model_field: str) -> str:
    match = _REF_RE.search(model_field)
    if not match:
        raise SemanticLayerError(f"Could not parse a model name out of: {model_field!r}")
    return match.group(1)


def _load_semantic_models(doc: dict) -> dict[str, SemanticModel]:
    semantic_models: dict[str, SemanticModel] = {}

    for raw in doc.get("semantic_models", []):
        entities: dict[str, Entity] = {}
        primary_entity = None
        for ent in raw.get("entities", []):
            entity = Entity(name=ent["name"], type=ent["type"], expr=ent.get("expr", ent["name"]))
            entities[entity.name] = entity
            if entity.type == "primary":
                primary_entity = entity.name

        if primary_entity is None:
            raise SemanticLayerError(f"Semantic model '{raw['name']}' has no primary entity")

        dimensions: dict[str, Dimension] = {}
        for dim in raw.get("dimensions", []):
            if dim["name"] in _PARSE_ONLY_DIMENSIONS:
                continue
            type_params = dim.get("type_params") or {}
            dimensions[dim["name"]] = Dimension(
                name=dim["name"],
                type=dim["type"],
                expr=dim.get("expr", dim["name"]),
                time_granularity=type_params.get("time_granularity"),
            )

        measures: dict[str, Measure] = {}
        for meas in raw.get("measures", []):
            measures[meas["name"]] = Measure(
                name=meas["name"], agg=meas["agg"], expr=meas.get("expr", meas["name"])
            )

        semantic_models[raw["name"]] = SemanticModel(
            name=raw["name"],
            description=raw.get("description", ""),
            mart=_extract_ref(raw["model"]),
            primary_entity=primary_entity,
            entities=entities,
            dimensions=dimensions,
            measures=measures,
        )

    return semantic_models


def _is_component(raw_metric: dict) -> bool:
    return bool(((raw_metric.get("config") or {}).get("meta") or {}).get("component"))


def _load_metrics(doc: dict, measure_owner: dict[str, str]) -> dict[str, MetricDef]:
    raw_by_name = {m["name"]: m for m in doc.get("metrics", [])}

    def resolve_component_measure(component_metric_name: str) -> tuple[str, str]:
        component = raw_by_name.get(component_metric_name)
        if component is None:
            raise SemanticLayerError(
                f"Ratio component '{component_metric_name}' is not defined as a metric"
            )
        if component["type"] != "simple":
            raise SemanticLayerError(
                f"Ratio component '{component_metric_name}' must be a simple metric"
            )
        measure_name = component["type_params"]["measure"]
        owner = measure_owner.get(measure_name)
        if owner is None:
            raise SemanticLayerError(f"Measure '{measure_name}' is not defined on any semantic model")
        return measure_name, owner

    metrics: dict[str, MetricDef] = {}
    for raw in raw_by_name.values():
        name = raw["name"]
        mtype = raw["type"]
        type_params = raw.get("type_params", {})
        is_component = _is_component(raw)

        if mtype == "simple":
            measure_name = type_params["measure"]
            owner = measure_owner.get(measure_name)
            if owner is None:
                raise SemanticLayerError(f"Metric '{name}' references unknown measure '{measure_name}'")
            metrics[name] = MetricDef(
                name=name,
                type="simple",
                label=raw.get("label", name),
                description=raw.get("description", ""),
                semantic_model=owner,
                measure=measure_name,
                component=is_component,
            )
        elif mtype == "ratio":
            num_measure, num_owner = resolve_component_measure(type_params["numerator"])
            den_measure, den_owner = resolve_component_measure(type_params["denominator"])
            if num_owner != den_owner:
                raise SemanticLayerError(
                    f"Ratio metric '{name}' mixes semantic models ({num_owner} vs {den_owner}); "
                    "cross-model ratios aren't supported"
                )
            metrics[name] = MetricDef(
                name=name,
                type="ratio",
                label=raw.get("label", name),
                description=raw.get("description", ""),
                semantic_model=num_owner,
                numerator_measure=num_measure,
                denominator_measure=den_measure,
                component=is_component,
            )
        else:
            raise SemanticLayerError(f"Unsupported metric type '{mtype}' for metric '{name}'")

    return metrics


def load_catalog(
    semantic_models_path: Path = SEMANTIC_MODELS_PATH,
    metrics_path: Path = METRICS_PATH,
) -> SemanticCatalog:
    sm_doc = yaml.safe_load(semantic_models_path.read_text(encoding="utf-8"))
    metrics_doc = yaml.safe_load(metrics_path.read_text(encoding="utf-8"))

    semantic_models = _load_semantic_models(sm_doc)

    measure_owner: dict[str, str] = {}
    for sm in semantic_models.values():
        for measure_name in sm.measures:
            measure_owner[measure_name] = sm.name

    metrics = _load_metrics(metrics_doc, measure_owner)

    return SemanticCatalog(semantic_models, metrics)
