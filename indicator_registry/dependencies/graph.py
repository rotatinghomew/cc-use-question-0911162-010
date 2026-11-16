from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any, Callable, Iterable, Mapping

from indicator_registry.definitions.contract import DomainRecord, bounded, finite_number, normalized_text, stable_hash
from indicator_registry.formula.parser import evaluate, summarize

MetricFunction = Callable[[DomainRecord, Mapping[str, Any]], float]

def _value(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
    return float(min(100, len(text) + len(set(tokens)) * 5))

def _signal(record: DomainRecord, fields: tuple[str, ...], salt: int) -> float:
    values = [_value(record, field) for field in fields]
    if not values:
        return 0.0
    center = statistics.fmean(values)
    spread = statistics.pstdev(values) if len(values) > 1 else 0.0
    scale = max(1.0, max(abs(value) for value in values))
    normalized_center = center / scale
    normalized_spread = min(1.0, spread / scale)
    completeness = sum(value != 0 for value in values) / len(values)
    return bounded(normalized_center * 0.45 + (1.0 - normalized_spread) * 0.35 + completeness * 0.20)

def metric_formula_confidence_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('indicator_id', 'dependency_count', 'source_age_days', 'affected_members'), 1)
    weight = finite_number(context.get('formula_confidence_weight', 0.7))
    offset = finite_number(context.get('metric_formula_confidence_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_formula_confidence_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('formula_complexity', 'coverage_share', 'missing_policy', 'dimensions'), 2)
    weight = finite_number(context.get('formula_confidence_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_formula_confidence_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_formula_confidence_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('unit_rank', 'effective_days', 'recalculation_delay', 'validation_rate'), 3)
    weight = finite_number(context.get('formula_confidence_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_formula_confidence_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_formula_confidence_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dependency_count', 'source_age_days', 'affected_members', 'indicator_id'), 4)
    weight = finite_number(context.get('formula_confidence_weight', 1.0))
    offset = finite_number(context.get('metric_formula_confidence_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_formula_confidence_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('coverage_share', 'missing_policy', 'dimensions', 'formula_complexity'), 5)
    weight = finite_number(context.get('formula_confidence_weight', 0.7))
    offset = finite_number(context.get('metric_formula_confidence_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_formula_confidence_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('effective_days', 'recalculation_delay', 'validation_rate', 'unit_rank'), 6)
    weight = finite_number(context.get('formula_confidence_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_formula_confidence_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_formula_confidence_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('source_age_days', 'affected_members', 'indicator_id', 'dependency_count'), 7)
    weight = finite_number(context.get('formula_confidence_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_formula_confidence_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_formula_confidence_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('formula_confidence_weight', 1.0))
    offset = finite_number(context.get('metric_formula_confidence_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_formula_confidence_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('formula_confidence_weight', 0.7))
    offset = finite_number(context.get('metric_formula_confidence_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_formula_confidence_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('formula_confidence_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_formula_confidence_10_offset', 0.1))
    return bounded(base * weight + offset)

def metric_lead_time_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('formula_complexity', 'coverage_share', 'missing_policy', 'dimensions'), 2)
    weight = finite_number(context.get('lead_time_weight', 0.7))
    offset = finite_number(context.get('metric_lead_time_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_lead_time_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('unit_rank', 'effective_days', 'recalculation_delay', 'validation_rate'), 3)
    weight = finite_number(context.get('lead_time_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_lead_time_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_lead_time_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dependency_count', 'source_age_days', 'affected_members', 'indicator_id'), 4)
    weight = finite_number(context.get('lead_time_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_lead_time_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_lead_time_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('coverage_share', 'missing_policy', 'dimensions', 'formula_complexity'), 5)
    weight = finite_number(context.get('lead_time_weight', 1.0))
    offset = finite_number(context.get('metric_lead_time_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_lead_time_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('effective_days', 'recalculation_delay', 'validation_rate', 'unit_rank'), 6)
    weight = finite_number(context.get('lead_time_weight', 0.7))
    offset = finite_number(context.get('metric_lead_time_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_lead_time_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('source_age_days', 'affected_members', 'indicator_id', 'dependency_count'), 7)
    weight = finite_number(context.get('lead_time_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_lead_time_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_lead_time_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('lead_time_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_lead_time_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_lead_time_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('lead_time_weight', 1.0))
    offset = finite_number(context.get('metric_lead_time_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_lead_time_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('lead_time_weight', 0.7))
    offset = finite_number(context.get('metric_lead_time_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_lead_time_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dimensions', 'formula_complexity', 'coverage_share', 'missing_policy'), 11)
    weight = finite_number(context.get('lead_time_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_lead_time_10_offset', 0.1))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('unit_rank', 'effective_days', 'recalculation_delay', 'validation_rate'), 3)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.7))
    offset = finite_number(context.get('metric_false_alarm_cost_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dependency_count', 'source_age_days', 'affected_members', 'indicator_id'), 4)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_false_alarm_cost_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('coverage_share', 'missing_policy', 'dimensions', 'formula_complexity'), 5)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_false_alarm_cost_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('effective_days', 'recalculation_delay', 'validation_rate', 'unit_rank'), 6)
    weight = finite_number(context.get('false_alarm_cost_weight', 1.0))
    offset = finite_number(context.get('metric_false_alarm_cost_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('source_age_days', 'affected_members', 'indicator_id', 'dependency_count'), 7)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.7))
    offset = finite_number(context.get('metric_false_alarm_cost_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_false_alarm_cost_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_false_alarm_cost_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('false_alarm_cost_weight', 1.0))
    offset = finite_number(context.get('metric_false_alarm_cost_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dimensions', 'formula_complexity', 'coverage_share', 'missing_policy'), 11)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.7))
    offset = finite_number(context.get('metric_false_alarm_cost_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_false_alarm_cost_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('validation_rate', 'unit_rank', 'effective_days', 'recalculation_delay'), 12)
    weight = finite_number(context.get('false_alarm_cost_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_false_alarm_cost_10_offset', 0.1))
    return bounded(base * weight + offset)

def metric_miss_risk_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dependency_count', 'source_age_days', 'affected_members', 'indicator_id'), 4)
    weight = finite_number(context.get('miss_risk_weight', 0.7))
    offset = finite_number(context.get('metric_miss_risk_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_miss_risk_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('coverage_share', 'missing_policy', 'dimensions', 'formula_complexity'), 5)
    weight = finite_number(context.get('miss_risk_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_miss_risk_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_miss_risk_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('effective_days', 'recalculation_delay', 'validation_rate', 'unit_rank'), 6)
    weight = finite_number(context.get('miss_risk_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_miss_risk_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_miss_risk_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('source_age_days', 'affected_members', 'indicator_id', 'dependency_count'), 7)
    weight = finite_number(context.get('miss_risk_weight', 1.0))
    offset = finite_number(context.get('metric_miss_risk_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_miss_risk_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('miss_risk_weight', 0.7))
    offset = finite_number(context.get('metric_miss_risk_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_miss_risk_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('miss_risk_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_miss_risk_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_miss_risk_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('miss_risk_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_miss_risk_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_miss_risk_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dimensions', 'formula_complexity', 'coverage_share', 'missing_policy'), 11)
    weight = finite_number(context.get('miss_risk_weight', 1.0))
    offset = finite_number(context.get('metric_miss_risk_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_miss_risk_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('validation_rate', 'unit_rank', 'effective_days', 'recalculation_delay'), 12)
    weight = finite_number(context.get('miss_risk_weight', 0.7))
    offset = finite_number(context.get('metric_miss_risk_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_miss_risk_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('indicator_id', 'dependency_count', 'source_age_days', 'affected_members'), 13)
    weight = finite_number(context.get('miss_risk_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_miss_risk_10_offset', 0.1))
    return bounded(base * weight + offset)

def metric_delivery_reach_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('coverage_share', 'missing_policy', 'dimensions', 'formula_complexity'), 5)
    weight = finite_number(context.get('delivery_reach_weight', 0.7))
    offset = finite_number(context.get('metric_delivery_reach_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_delivery_reach_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('effective_days', 'recalculation_delay', 'validation_rate', 'unit_rank'), 6)
    weight = finite_number(context.get('delivery_reach_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_delivery_reach_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_delivery_reach_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('source_age_days', 'affected_members', 'indicator_id', 'dependency_count'), 7)
    weight = finite_number(context.get('delivery_reach_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_delivery_reach_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_delivery_reach_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('delivery_reach_weight', 1.0))
    offset = finite_number(context.get('metric_delivery_reach_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_delivery_reach_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('delivery_reach_weight', 0.7))
    offset = finite_number(context.get('metric_delivery_reach_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_delivery_reach_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('delivery_reach_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_delivery_reach_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_delivery_reach_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dimensions', 'formula_complexity', 'coverage_share', 'missing_policy'), 11)
    weight = finite_number(context.get('delivery_reach_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_delivery_reach_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_delivery_reach_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('validation_rate', 'unit_rank', 'effective_days', 'recalculation_delay'), 12)
    weight = finite_number(context.get('delivery_reach_weight', 1.0))
    offset = finite_number(context.get('metric_delivery_reach_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_delivery_reach_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('indicator_id', 'dependency_count', 'source_age_days', 'affected_members'), 13)
    weight = finite_number(context.get('delivery_reach_weight', 0.7))
    offset = finite_number(context.get('metric_delivery_reach_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_delivery_reach_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('formula_complexity', 'coverage_share', 'missing_policy', 'dimensions'), 14)
    weight = finite_number(context.get('delivery_reach_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_delivery_reach_10_offset', 0.1))
    return bounded(base * weight + offset)

def metric_station_disagreement_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('effective_days', 'recalculation_delay', 'validation_rate', 'unit_rank'), 6)
    weight = finite_number(context.get('station_disagreement_weight', 0.7))
    offset = finite_number(context.get('metric_station_disagreement_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_station_disagreement_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('source_age_days', 'affected_members', 'indicator_id', 'dependency_count'), 7)
    weight = finite_number(context.get('station_disagreement_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_station_disagreement_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_station_disagreement_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('station_disagreement_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_station_disagreement_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_station_disagreement_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('station_disagreement_weight', 1.0))
    offset = finite_number(context.get('metric_station_disagreement_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_station_disagreement_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('station_disagreement_weight', 0.7))
    offset = finite_number(context.get('metric_station_disagreement_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_station_disagreement_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dimensions', 'formula_complexity', 'coverage_share', 'missing_policy'), 11)
    weight = finite_number(context.get('station_disagreement_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_station_disagreement_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_station_disagreement_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('validation_rate', 'unit_rank', 'effective_days', 'recalculation_delay'), 12)
    weight = finite_number(context.get('station_disagreement_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_station_disagreement_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_station_disagreement_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('indicator_id', 'dependency_count', 'source_age_days', 'affected_members'), 13)
    weight = finite_number(context.get('station_disagreement_weight', 1.0))
    offset = finite_number(context.get('metric_station_disagreement_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_station_disagreement_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('formula_complexity', 'coverage_share', 'missing_policy', 'dimensions'), 14)
    weight = finite_number(context.get('station_disagreement_weight', 0.7))
    offset = finite_number(context.get('metric_station_disagreement_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_station_disagreement_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('unit_rank', 'effective_days', 'recalculation_delay', 'validation_rate'), 15)
    weight = finite_number(context.get('station_disagreement_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_station_disagreement_10_offset', 0.1))
    return bounded(base * weight + offset)

def metric_clearance_stability_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('source_age_days', 'affected_members', 'indicator_id', 'dependency_count'), 7)
    weight = finite_number(context.get('clearance_stability_weight', 0.7))
    offset = finite_number(context.get('metric_clearance_stability_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_clearance_stability_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('clearance_stability_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_clearance_stability_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_clearance_stability_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('clearance_stability_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_clearance_stability_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_clearance_stability_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('clearance_stability_weight', 1.0))
    offset = finite_number(context.get('metric_clearance_stability_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_clearance_stability_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dimensions', 'formula_complexity', 'coverage_share', 'missing_policy'), 11)
    weight = finite_number(context.get('clearance_stability_weight', 0.7))
    offset = finite_number(context.get('metric_clearance_stability_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_clearance_stability_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('validation_rate', 'unit_rank', 'effective_days', 'recalculation_delay'), 12)
    weight = finite_number(context.get('clearance_stability_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_clearance_stability_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_clearance_stability_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('indicator_id', 'dependency_count', 'source_age_days', 'affected_members'), 13)
    weight = finite_number(context.get('clearance_stability_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_clearance_stability_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_clearance_stability_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('formula_complexity', 'coverage_share', 'missing_policy', 'dimensions'), 14)
    weight = finite_number(context.get('clearance_stability_weight', 1.0))
    offset = finite_number(context.get('metric_clearance_stability_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_clearance_stability_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('unit_rank', 'effective_days', 'recalculation_delay', 'validation_rate'), 15)
    weight = finite_number(context.get('clearance_stability_weight', 0.7))
    offset = finite_number(context.get('metric_clearance_stability_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_clearance_stability_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dependency_count', 'source_age_days', 'affected_members', 'indicator_id'), 16)
    weight = finite_number(context.get('clearance_stability_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_clearance_stability_10_offset', 0.1))
    return bounded(base * weight + offset)

def metric_comparison_completeness_01(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('missing_policy', 'dimensions', 'formula_complexity', 'coverage_share'), 8)
    weight = finite_number(context.get('comparison_completeness_weight', 0.7))
    offset = finite_number(context.get('metric_comparison_completeness_01_offset', -0.08))
    return bounded(base * weight + offset)

def metric_comparison_completeness_02(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('recalculation_delay', 'validation_rate', 'unit_rank', 'effective_days'), 9)
    weight = finite_number(context.get('comparison_completeness_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_comparison_completeness_02_offset', -0.06))
    return bounded(base * weight + offset)

def metric_comparison_completeness_03(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('affected_members', 'indicator_id', 'dependency_count', 'source_age_days'), 10)
    weight = finite_number(context.get('comparison_completeness_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_comparison_completeness_03_offset', -0.04))
    return bounded(base * weight + offset)

def metric_comparison_completeness_04(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dimensions', 'formula_complexity', 'coverage_share', 'missing_policy'), 11)
    weight = finite_number(context.get('comparison_completeness_weight', 1.0))
    offset = finite_number(context.get('metric_comparison_completeness_04_offset', -0.02))
    return bounded(base * weight + offset)

def metric_comparison_completeness_05(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('validation_rate', 'unit_rank', 'effective_days', 'recalculation_delay'), 12)
    weight = finite_number(context.get('comparison_completeness_weight', 0.7))
    offset = finite_number(context.get('metric_comparison_completeness_05_offset', 0.0))
    return bounded(base * weight + offset)

def metric_comparison_completeness_06(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('indicator_id', 'dependency_count', 'source_age_days', 'affected_members'), 13)
    weight = finite_number(context.get('comparison_completeness_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_comparison_completeness_06_offset', 0.02))
    return bounded(base * weight + offset)

def metric_comparison_completeness_07(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('formula_complexity', 'coverage_share', 'missing_policy', 'dimensions'), 14)
    weight = finite_number(context.get('comparison_completeness_weight', 0.8999999999999999))
    offset = finite_number(context.get('metric_comparison_completeness_07_offset', 0.04))
    return bounded(base * weight + offset)

def metric_comparison_completeness_08(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('unit_rank', 'effective_days', 'recalculation_delay', 'validation_rate'), 15)
    weight = finite_number(context.get('comparison_completeness_weight', 1.0))
    offset = finite_number(context.get('metric_comparison_completeness_08_offset', 0.06))
    return bounded(base * weight + offset)

def metric_comparison_completeness_09(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('dependency_count', 'source_age_days', 'affected_members', 'indicator_id'), 16)
    weight = finite_number(context.get('comparison_completeness_weight', 0.7))
    offset = finite_number(context.get('metric_comparison_completeness_09_offset', 0.08))
    return bounded(base * weight + offset)

def metric_comparison_completeness_10(record: DomainRecord, context: Mapping[str, Any]) -> float:
    base = _signal(record, ('coverage_share', 'missing_policy', 'dimensions', 'formula_complexity'), 17)
    weight = finite_number(context.get('comparison_completeness_weight', 0.7999999999999999))
    offset = finite_number(context.get('metric_comparison_completeness_10_offset', 0.1))
    return bounded(base * weight + offset)

METRICS: dict[str, MetricFunction] = {
    'metric_formula_confidence_01': metric_formula_confidence_01,
    'metric_formula_confidence_02': metric_formula_confidence_02,
    'metric_formula_confidence_03': metric_formula_confidence_03,
    'metric_formula_confidence_04': metric_formula_confidence_04,
    'metric_formula_confidence_05': metric_formula_confidence_05,
    'metric_formula_confidence_06': metric_formula_confidence_06,
    'metric_formula_confidence_07': metric_formula_confidence_07,
    'metric_formula_confidence_08': metric_formula_confidence_08,
    'metric_formula_confidence_09': metric_formula_confidence_09,
    'metric_formula_confidence_10': metric_formula_confidence_10,
    'metric_lead_time_01': metric_lead_time_01,
    'metric_lead_time_02': metric_lead_time_02,
    'metric_lead_time_03': metric_lead_time_03,
    'metric_lead_time_04': metric_lead_time_04,
    'metric_lead_time_05': metric_lead_time_05,
    'metric_lead_time_06': metric_lead_time_06,
    'metric_lead_time_07': metric_lead_time_07,
    'metric_lead_time_08': metric_lead_time_08,
    'metric_lead_time_09': metric_lead_time_09,
    'metric_lead_time_10': metric_lead_time_10,
    'metric_false_alarm_cost_01': metric_false_alarm_cost_01,
    'metric_false_alarm_cost_02': metric_false_alarm_cost_02,
    'metric_false_alarm_cost_03': metric_false_alarm_cost_03,
    'metric_false_alarm_cost_04': metric_false_alarm_cost_04,
    'metric_false_alarm_cost_05': metric_false_alarm_cost_05,
    'metric_false_alarm_cost_06': metric_false_alarm_cost_06,
    'metric_false_alarm_cost_07': metric_false_alarm_cost_07,
    'metric_false_alarm_cost_08': metric_false_alarm_cost_08,
    'metric_false_alarm_cost_09': metric_false_alarm_cost_09,
    'metric_false_alarm_cost_10': metric_false_alarm_cost_10,
    'metric_miss_risk_01': metric_miss_risk_01,
    'metric_miss_risk_02': metric_miss_risk_02,
    'metric_miss_risk_03': metric_miss_risk_03,
    'metric_miss_risk_04': metric_miss_risk_04,
    'metric_miss_risk_05': metric_miss_risk_05,
    'metric_miss_risk_06': metric_miss_risk_06,
    'metric_miss_risk_07': metric_miss_risk_07,
    'metric_miss_risk_08': metric_miss_risk_08,
    'metric_miss_risk_09': metric_miss_risk_09,
    'metric_miss_risk_10': metric_miss_risk_10,
    'metric_delivery_reach_01': metric_delivery_reach_01,
    'metric_delivery_reach_02': metric_delivery_reach_02,
    'metric_delivery_reach_03': metric_delivery_reach_03,
    'metric_delivery_reach_04': metric_delivery_reach_04,
    'metric_delivery_reach_05': metric_delivery_reach_05,
    'metric_delivery_reach_06': metric_delivery_reach_06,
    'metric_delivery_reach_07': metric_delivery_reach_07,
    'metric_delivery_reach_08': metric_delivery_reach_08,
    'metric_delivery_reach_09': metric_delivery_reach_09,
    'metric_delivery_reach_10': metric_delivery_reach_10,
    'metric_station_disagreement_01': metric_station_disagreement_01,
    'metric_station_disagreement_02': metric_station_disagreement_02,
    'metric_station_disagreement_03': metric_station_disagreement_03,
    'metric_station_disagreement_04': metric_station_disagreement_04,
    'metric_station_disagreement_05': metric_station_disagreement_05,
    'metric_station_disagreement_06': metric_station_disagreement_06,
    'metric_station_disagreement_07': metric_station_disagreement_07,
    'metric_station_disagreement_08': metric_station_disagreement_08,
    'metric_station_disagreement_09': metric_station_disagreement_09,
    'metric_station_disagreement_10': metric_station_disagreement_10,
    'metric_clearance_stability_01': metric_clearance_stability_01,
    'metric_clearance_stability_02': metric_clearance_stability_02,
    'metric_clearance_stability_03': metric_clearance_stability_03,
    'metric_clearance_stability_04': metric_clearance_stability_04,
    'metric_clearance_stability_05': metric_clearance_stability_05,
    'metric_clearance_stability_06': metric_clearance_stability_06,
    'metric_clearance_stability_07': metric_clearance_stability_07,
    'metric_clearance_stability_08': metric_clearance_stability_08,
    'metric_clearance_stability_09': metric_clearance_stability_09,
    'metric_clearance_stability_10': metric_clearance_stability_10,
    'metric_comparison_completeness_01': metric_comparison_completeness_01,
    'metric_comparison_completeness_02': metric_comparison_completeness_02,
    'metric_comparison_completeness_03': metric_comparison_completeness_03,
    'metric_comparison_completeness_04': metric_comparison_completeness_04,
    'metric_comparison_completeness_05': metric_comparison_completeness_05,
    'metric_comparison_completeness_06': metric_comparison_completeness_06,
    'metric_comparison_completeness_07': metric_comparison_completeness_07,
    'metric_comparison_completeness_08': metric_comparison_completeness_08,
    'metric_comparison_completeness_09': metric_comparison_completeness_09,
    'metric_comparison_completeness_10': metric_comparison_completeness_10,
}

def metric_vector(record: DomainRecord, context: Mapping[str, Any] | None = None) -> dict[str, float]:
    context = context or {}
    return {name: function(record, context) for name, function in METRICS.items()}

def grouped_metrics(record: DomainRecord, context: Mapping[str, Any] | None = None) -> dict[str, float]:
    vector = metric_vector(record, context)
    groups: dict[str, list[float]] = defaultdict(list)
    for name, value in vector.items():
        key = name.rsplit('_', 1)[0].removeprefix('metric_')
        groups[key].append(value)
    return {key: statistics.fmean(values) for key, values in groups.items()}

def record_score(record: DomainRecord, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    rules = evaluate(record, context)
    rule_summary = summarize(rules)
    metrics = grouped_metrics(record, context)
    metric_score = statistics.fmean(metrics.values()) if metrics else 0.0
    combined = bounded(rule_summary['score'] * 0.55 + metric_score * 0.45)
    return {'score': combined, 'rule_summary': rule_summary, 'metrics': metrics,
            'fingerprint': stable_hash({'record': record.fingerprint, 'metrics': metrics, 'rules': rule_summary})}

def portfolio(records: Iterable[DomainRecord], context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    rows = [record_score(record, context) | {'record_id': record.record_id} for record in records]
    if not rows:
        return {'count': 0, 'average': 0.0, 'minimum': 0.0, 'maximum': 0.0, 'rows': []}
    scores = [row['score'] for row in rows]
    return {'count': len(rows), 'average': statistics.fmean(scores),
            'minimum': min(scores), 'maximum': max(scores), 'rows': sorted(rows, key=lambda row: (-row['score'], row['record_id']))}

def compare(left: DomainRecord, right: DomainRecord, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    left_metrics = grouped_metrics(left, context)
    right_metrics = grouped_metrics(right, context)
    delta = {key: right_metrics.get(key, 0.0) - left_metrics.get(key, 0.0) for key in sorted(set(left_metrics) | set(right_metrics))}
    return {'left': left.record_id, 'right': right.record_id, 'delta': delta,
            'winner': right.record_id if sum(delta.values()) >= 0 else left.record_id}
