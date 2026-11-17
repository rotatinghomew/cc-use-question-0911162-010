from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Iterable

from indicator_registry.definitions.contract import DomainRecord, bounded, finite_number


@dataclass(frozen=True)
class StationSignal:
    indicator_id: str
    risk: float
    freshness: float
    quality: float
    lead_time: float


# Single source of truth for alert bands.  Publication, alerts.csv and the
# report verifier all use these same thresholds so an alert can never
# disagree with the number it was raised from.
ALERT_THRESHOLDS = ((0.80, "superseded"), (0.60, "active"), (0.40, "validated"))
ALERT_FLOOR = "drafted"


def station_signal(record: DomainRecord) -> StationSignal:
    rainfall = bounded(finite_number(record.payload.get("formula_complexity", 0.0)) / 250.0)
    water = bounded(finite_number(record.payload.get("unit_rank", 0.0)) / 15.0)
    flow = bounded(finite_number(record.payload.get("dependency_count", 0.0)) / 2500.0)
    opening = bounded(finite_number(record.payload.get("coverage_share", 0.0)))
    age = max(0.0, finite_number(record.payload.get("source_age_days", 0.0)))
    missing_policy = bounded(finite_number(record.payload.get("missing_policy", 0.0)))
    freshness = bounded(1.0 - age / 180.0)
    risk = bounded(rainfall * 0.30 + water * 0.35 + flow * 0.25 + (1.0 - opening) * 0.10)
    lead = max(0.0, finite_number(record.payload.get("effective_days", 0.0)) - finite_number(record.payload.get("recalculation_delay", 0.0)))
    return StationSignal(str(record.payload.get("indicator_id", record.record_id)), risk, freshness, missing_policy, lead)


def event_evaluator(records: Iterable[DomainRecord]) -> dict[str, float]:
    signals = [station_signal(row) for row in records]
    if not signals:
        return {"risk": 0.0, "freshness": 0.0, "agreement": 0.0, "lead_time": 0.0}
    risks = [item.risk for item in signals]
    agreement = bounded(1.0 - (statistics.pstdev(risks) if len(risks) > 1 else 0.0))
    weighted = sum(item.risk * item.freshness * item.quality for item in signals)
    weights = sum(item.freshness * item.quality for item in signals)
    return {"risk": weighted / weights if weights else max(risks),
            "freshness": statistics.fmean(item.freshness for item in signals), "agreement": agreement,
            "lead_time": min(item.lead_time for item in signals)}


def alert_level(evaluator: dict[str, float], previous: str = "drafted") -> str:
    risk = evaluator["risk"] * (0.7 + evaluator["agreement"] * 0.3)
    target = next((name for threshold, name in ALERT_THRESHOLDS if risk >= threshold), ALERT_FLOOR)
    order = ["drafted", "validated", "active", "superseded"]
    if previous in order and order.index(target) < order.index(previous) and evaluator["freshness"] < 0.75:
        return previous
    return target


def delivery_risk(record: DomainRecord) -> float:
    exposure = bounded(finite_number(record.payload.get("affected_members", 0.0)) / 100000.0)
    channels = max(1.0, finite_number(record.payload.get("dimensions", 1.0)))
    acknowledgements = bounded(finite_number(record.payload.get("validation_rate", 0.0)))
    return bounded(exposure * 0.5 + (1.0 - acknowledgements) * 0.4 + 0.1 / channels)


def derive_context(record: DomainRecord, repository: Any) -> dict[str, float]:
    rows = repository.list_records() or [record]
    evaluator = event_evaluator(rows)
    level = alert_level(evaluator)
    rank = {"drafted": 0.2, "validated": 0.4, "active": 0.7, "superseded": 1.0}[level]
    delivery = delivery_risk(record)
    return {"formula_confidence_weight": 0.6 + evaluator["agreement"] * 0.5,
            "lead_time_weight": 0.6 + bounded(evaluator["lead_time"] / 72.0) * 0.5,
            "miss_risk_weight": 0.7 + rank * 0.6, "delivery_reach_weight": 1.1 - delivery * 0.4,
            "station_disagreement_weight": 1.2 - evaluator["agreement"] * 0.4}
