from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from indicator_registry.definitions.contract import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
        return float(min(100, len(text) + len(set(tokens)) * 5))

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    severity = 'info' if passed else ('superseded' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, severity, message, evidence)

def check_indicator_id_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_indicator_id_presence_threshold', 10.333)
    return _result('check_indicator_id_presence', adjusted, threshold, True, 'validates indicator_id presence',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_indicator_id_range_threshold', 12.667)
    return _result('check_indicator_id_range', adjusted, threshold, True, 'validates indicator_id range',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_indicator_id_stability_threshold', 15.0)
    return _result('check_indicator_id_stability', adjusted, threshold, False, 'validates indicator_id stability',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_indicator_id_freshness_threshold', 17.333)
    return _result('check_indicator_id_freshness', adjusted, threshold, True, 'validates indicator_id freshness',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_indicator_id_coverage_threshold', 19.667)
    return _result('check_indicator_id_coverage', adjusted, threshold, True, 'validates indicator_id coverage',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_indicator_id_consistency_threshold', 22.0)
    return _result('check_indicator_id_consistency', adjusted, threshold, False, 'validates indicator_id consistency',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_indicator_id_risk_threshold', 24.333)
    return _result('check_indicator_id_risk', adjusted, threshold, True, 'validates indicator_id risk',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_indicator_id_confidence_threshold', 26.667)
    return _result('check_indicator_id_confidence', adjusted, threshold, True, 'validates indicator_id confidence',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_indicator_id_dependency_threshold', 29.0)
    return _result('check_indicator_id_dependency', adjusted, threshold, False, 'validates indicator_id dependency',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_indicator_id_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'indicator_id')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_indicator_id_readiness_threshold', 31.333)
    return _result('check_indicator_id_readiness', adjusted, threshold, True, 'validates indicator_id readiness',
                   {'field': 'indicator_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_formula_complexity_presence_threshold', 9.333)
    return _result('check_formula_complexity_presence', adjusted, threshold, True, 'validates formula_complexity presence',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_formula_complexity_range_threshold', 11.667)
    return _result('check_formula_complexity_range', adjusted, threshold, False, 'validates formula_complexity range',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_formula_complexity_stability_threshold', 14.0)
    return _result('check_formula_complexity_stability', adjusted, threshold, True, 'validates formula_complexity stability',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_formula_complexity_freshness_threshold', 16.333)
    return _result('check_formula_complexity_freshness', adjusted, threshold, True, 'validates formula_complexity freshness',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_formula_complexity_coverage_threshold', 18.667)
    return _result('check_formula_complexity_coverage', adjusted, threshold, False, 'validates formula_complexity coverage',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_formula_complexity_consistency_threshold', 21.0)
    return _result('check_formula_complexity_consistency', adjusted, threshold, True, 'validates formula_complexity consistency',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_formula_complexity_risk_threshold', 23.333)
    return _result('check_formula_complexity_risk', adjusted, threshold, True, 'validates formula_complexity risk',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_formula_complexity_confidence_threshold', 25.667)
    return _result('check_formula_complexity_confidence', adjusted, threshold, False, 'validates formula_complexity confidence',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_formula_complexity_dependency_threshold', 28.0)
    return _result('check_formula_complexity_dependency', adjusted, threshold, True, 'validates formula_complexity dependency',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_formula_complexity_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'formula_complexity')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_formula_complexity_readiness_threshold', 30.333)
    return _result('check_formula_complexity_readiness', adjusted, threshold, True, 'validates formula_complexity readiness',
                   {'field': 'formula_complexity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_unit_rank_presence_threshold', 8.333)
    return _result('check_unit_rank_presence', adjusted, threshold, False, 'validates unit_rank presence',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_unit_rank_range_threshold', 10.667)
    return _result('check_unit_rank_range', adjusted, threshold, True, 'validates unit_rank range',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_unit_rank_stability_threshold', 13.0)
    return _result('check_unit_rank_stability', adjusted, threshold, True, 'validates unit_rank stability',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_unit_rank_freshness_threshold', 15.333)
    return _result('check_unit_rank_freshness', adjusted, threshold, False, 'validates unit_rank freshness',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_unit_rank_coverage_threshold', 17.667)
    return _result('check_unit_rank_coverage', adjusted, threshold, True, 'validates unit_rank coverage',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_unit_rank_consistency_threshold', 20.0)
    return _result('check_unit_rank_consistency', adjusted, threshold, True, 'validates unit_rank consistency',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_unit_rank_risk_threshold', 22.333)
    return _result('check_unit_rank_risk', adjusted, threshold, False, 'validates unit_rank risk',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_unit_rank_confidence_threshold', 24.667)
    return _result('check_unit_rank_confidence', adjusted, threshold, True, 'validates unit_rank confidence',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_unit_rank_dependency_threshold', 27.0)
    return _result('check_unit_rank_dependency', adjusted, threshold, True, 'validates unit_rank dependency',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_unit_rank_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'unit_rank')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_unit_rank_readiness_threshold', 29.333)
    return _result('check_unit_rank_readiness', adjusted, threshold, False, 'validates unit_rank readiness',
                   {'field': 'unit_rank', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_dependency_count_presence_threshold', 31.667)
    return _result('check_dependency_count_presence', adjusted, threshold, True, 'validates dependency_count presence',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_dependency_count_range_threshold', 9.667)
    return _result('check_dependency_count_range', adjusted, threshold, True, 'validates dependency_count range',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_dependency_count_stability_threshold', 12.0)
    return _result('check_dependency_count_stability', adjusted, threshold, False, 'validates dependency_count stability',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_dependency_count_freshness_threshold', 14.333)
    return _result('check_dependency_count_freshness', adjusted, threshold, True, 'validates dependency_count freshness',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_dependency_count_coverage_threshold', 16.667)
    return _result('check_dependency_count_coverage', adjusted, threshold, True, 'validates dependency_count coverage',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_dependency_count_consistency_threshold', 19.0)
    return _result('check_dependency_count_consistency', adjusted, threshold, False, 'validates dependency_count consistency',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_dependency_count_risk_threshold', 21.333)
    return _result('check_dependency_count_risk', adjusted, threshold, True, 'validates dependency_count risk',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_dependency_count_confidence_threshold', 23.667)
    return _result('check_dependency_count_confidence', adjusted, threshold, True, 'validates dependency_count confidence',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_dependency_count_dependency_threshold', 26.0)
    return _result('check_dependency_count_dependency', adjusted, threshold, False, 'validates dependency_count dependency',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dependency_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dependency_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_dependency_count_readiness_threshold', 28.333)
    return _result('check_dependency_count_readiness', adjusted, threshold, True, 'validates dependency_count readiness',
                   {'field': 'dependency_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_coverage_share_presence_threshold', 30.667)
    return _result('check_coverage_share_presence', adjusted, threshold, True, 'validates coverage_share presence',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_coverage_share_range_threshold', 8.667)
    return _result('check_coverage_share_range', adjusted, threshold, False, 'validates coverage_share range',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_coverage_share_stability_threshold', 11.0)
    return _result('check_coverage_share_stability', adjusted, threshold, True, 'validates coverage_share stability',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_coverage_share_freshness_threshold', 13.333)
    return _result('check_coverage_share_freshness', adjusted, threshold, True, 'validates coverage_share freshness',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_coverage_share_coverage_threshold', 15.667)
    return _result('check_coverage_share_coverage', adjusted, threshold, False, 'validates coverage_share coverage',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_coverage_share_consistency_threshold', 18.0)
    return _result('check_coverage_share_consistency', adjusted, threshold, True, 'validates coverage_share consistency',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_coverage_share_risk_threshold', 20.333)
    return _result('check_coverage_share_risk', adjusted, threshold, True, 'validates coverage_share risk',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_coverage_share_confidence_threshold', 22.667)
    return _result('check_coverage_share_confidence', adjusted, threshold, False, 'validates coverage_share confidence',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_coverage_share_dependency_threshold', 25.0)
    return _result('check_coverage_share_dependency', adjusted, threshold, True, 'validates coverage_share dependency',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_coverage_share_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'coverage_share')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_coverage_share_readiness_threshold', 27.333)
    return _result('check_coverage_share_readiness', adjusted, threshold, True, 'validates coverage_share readiness',
                   {'field': 'coverage_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_effective_days_presence_threshold', 29.667)
    return _result('check_effective_days_presence', adjusted, threshold, False, 'validates effective_days presence',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_effective_days_range_threshold', 32.0)
    return _result('check_effective_days_range', adjusted, threshold, True, 'validates effective_days range',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_effective_days_stability_threshold', 10.0)
    return _result('check_effective_days_stability', adjusted, threshold, True, 'validates effective_days stability',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_effective_days_freshness_threshold', 12.333)
    return _result('check_effective_days_freshness', adjusted, threshold, False, 'validates effective_days freshness',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_effective_days_coverage_threshold', 14.667)
    return _result('check_effective_days_coverage', adjusted, threshold, True, 'validates effective_days coverage',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_effective_days_consistency_threshold', 17.0)
    return _result('check_effective_days_consistency', adjusted, threshold, True, 'validates effective_days consistency',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_effective_days_risk_threshold', 19.333)
    return _result('check_effective_days_risk', adjusted, threshold, False, 'validates effective_days risk',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_effective_days_confidence_threshold', 21.667)
    return _result('check_effective_days_confidence', adjusted, threshold, True, 'validates effective_days confidence',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_effective_days_dependency_threshold', 24.0)
    return _result('check_effective_days_dependency', adjusted, threshold, True, 'validates effective_days dependency',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_effective_days_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'effective_days')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_effective_days_readiness_threshold', 26.333)
    return _result('check_effective_days_readiness', adjusted, threshold, False, 'validates effective_days readiness',
                   {'field': 'effective_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_source_age_days_presence_threshold', 28.667)
    return _result('check_source_age_days_presence', adjusted, threshold, True, 'validates source_age_days presence',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_source_age_days_range_threshold', 31.0)
    return _result('check_source_age_days_range', adjusted, threshold, True, 'validates source_age_days range',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_source_age_days_stability_threshold', 9.0)
    return _result('check_source_age_days_stability', adjusted, threshold, False, 'validates source_age_days stability',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_source_age_days_freshness_threshold', 11.333)
    return _result('check_source_age_days_freshness', adjusted, threshold, True, 'validates source_age_days freshness',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_source_age_days_coverage_threshold', 13.667)
    return _result('check_source_age_days_coverage', adjusted, threshold, True, 'validates source_age_days coverage',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_source_age_days_consistency_threshold', 16.0)
    return _result('check_source_age_days_consistency', adjusted, threshold, False, 'validates source_age_days consistency',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_source_age_days_risk_threshold', 18.333)
    return _result('check_source_age_days_risk', adjusted, threshold, True, 'validates source_age_days risk',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_source_age_days_confidence_threshold', 20.667)
    return _result('check_source_age_days_confidence', adjusted, threshold, True, 'validates source_age_days confidence',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_source_age_days_dependency_threshold', 23.0)
    return _result('check_source_age_days_dependency', adjusted, threshold, False, 'validates source_age_days dependency',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_age_days_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_age_days')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_source_age_days_readiness_threshold', 25.333)
    return _result('check_source_age_days_readiness', adjusted, threshold, True, 'validates source_age_days readiness',
                   {'field': 'source_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_missing_policy_presence_threshold', 27.667)
    return _result('check_missing_policy_presence', adjusted, threshold, True, 'validates missing_policy presence',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_missing_policy_range_threshold', 30.0)
    return _result('check_missing_policy_range', adjusted, threshold, False, 'validates missing_policy range',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_missing_policy_stability_threshold', 8.0)
    return _result('check_missing_policy_stability', adjusted, threshold, True, 'validates missing_policy stability',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_missing_policy_freshness_threshold', 10.333)
    return _result('check_missing_policy_freshness', adjusted, threshold, True, 'validates missing_policy freshness',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_missing_policy_coverage_threshold', 12.667)
    return _result('check_missing_policy_coverage', adjusted, threshold, False, 'validates missing_policy coverage',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_missing_policy_consistency_threshold', 15.0)
    return _result('check_missing_policy_consistency', adjusted, threshold, True, 'validates missing_policy consistency',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_missing_policy_risk_threshold', 17.333)
    return _result('check_missing_policy_risk', adjusted, threshold, True, 'validates missing_policy risk',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_missing_policy_confidence_threshold', 19.667)
    return _result('check_missing_policy_confidence', adjusted, threshold, False, 'validates missing_policy confidence',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_missing_policy_dependency_threshold', 22.0)
    return _result('check_missing_policy_dependency', adjusted, threshold, True, 'validates missing_policy dependency',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missing_policy_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missing_policy')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_missing_policy_readiness_threshold', 24.333)
    return _result('check_missing_policy_readiness', adjusted, threshold, True, 'validates missing_policy readiness',
                   {'field': 'missing_policy', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_recalculation_delay_presence_threshold', 26.667)
    return _result('check_recalculation_delay_presence', adjusted, threshold, False, 'validates recalculation_delay presence',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_recalculation_delay_range_threshold', 29.0)
    return _result('check_recalculation_delay_range', adjusted, threshold, True, 'validates recalculation_delay range',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_recalculation_delay_stability_threshold', 31.333)
    return _result('check_recalculation_delay_stability', adjusted, threshold, True, 'validates recalculation_delay stability',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_recalculation_delay_freshness_threshold', 9.333)
    return _result('check_recalculation_delay_freshness', adjusted, threshold, False, 'validates recalculation_delay freshness',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_recalculation_delay_coverage_threshold', 11.667)
    return _result('check_recalculation_delay_coverage', adjusted, threshold, True, 'validates recalculation_delay coverage',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_recalculation_delay_consistency_threshold', 14.0)
    return _result('check_recalculation_delay_consistency', adjusted, threshold, True, 'validates recalculation_delay consistency',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_recalculation_delay_risk_threshold', 16.333)
    return _result('check_recalculation_delay_risk', adjusted, threshold, False, 'validates recalculation_delay risk',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_recalculation_delay_confidence_threshold', 18.667)
    return _result('check_recalculation_delay_confidence', adjusted, threshold, True, 'validates recalculation_delay confidence',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_recalculation_delay_dependency_threshold', 21.0)
    return _result('check_recalculation_delay_dependency', adjusted, threshold, True, 'validates recalculation_delay dependency',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_recalculation_delay_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'recalculation_delay')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_recalculation_delay_readiness_threshold', 23.333)
    return _result('check_recalculation_delay_readiness', adjusted, threshold, False, 'validates recalculation_delay readiness',
                   {'field': 'recalculation_delay', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_affected_members_presence_threshold', 25.667)
    return _result('check_affected_members_presence', adjusted, threshold, True, 'validates affected_members presence',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_affected_members_range_threshold', 28.0)
    return _result('check_affected_members_range', adjusted, threshold, True, 'validates affected_members range',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_affected_members_stability_threshold', 30.333)
    return _result('check_affected_members_stability', adjusted, threshold, False, 'validates affected_members stability',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_affected_members_freshness_threshold', 8.333)
    return _result('check_affected_members_freshness', adjusted, threshold, True, 'validates affected_members freshness',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_affected_members_coverage_threshold', 10.667)
    return _result('check_affected_members_coverage', adjusted, threshold, True, 'validates affected_members coverage',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_affected_members_consistency_threshold', 13.0)
    return _result('check_affected_members_consistency', adjusted, threshold, False, 'validates affected_members consistency',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_affected_members_risk_threshold', 15.333)
    return _result('check_affected_members_risk', adjusted, threshold, True, 'validates affected_members risk',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_affected_members_confidence_threshold', 17.667)
    return _result('check_affected_members_confidence', adjusted, threshold, True, 'validates affected_members confidence',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_affected_members_dependency_threshold', 20.0)
    return _result('check_affected_members_dependency', adjusted, threshold, False, 'validates affected_members dependency',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_affected_members_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'affected_members')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_affected_members_readiness_threshold', 22.333)
    return _result('check_affected_members_readiness', adjusted, threshold, True, 'validates affected_members readiness',
                   {'field': 'affected_members', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_dimensions_presence_threshold', 24.667)
    return _result('check_dimensions_presence', adjusted, threshold, True, 'validates dimensions presence',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_dimensions_range_threshold', 27.0)
    return _result('check_dimensions_range', adjusted, threshold, False, 'validates dimensions range',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_dimensions_stability_threshold', 29.333)
    return _result('check_dimensions_stability', adjusted, threshold, True, 'validates dimensions stability',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_dimensions_freshness_threshold', 31.667)
    return _result('check_dimensions_freshness', adjusted, threshold, True, 'validates dimensions freshness',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_dimensions_coverage_threshold', 9.667)
    return _result('check_dimensions_coverage', adjusted, threshold, False, 'validates dimensions coverage',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_dimensions_consistency_threshold', 12.0)
    return _result('check_dimensions_consistency', adjusted, threshold, True, 'validates dimensions consistency',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_dimensions_risk_threshold', 14.333)
    return _result('check_dimensions_risk', adjusted, threshold, True, 'validates dimensions risk',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_dimensions_confidence_threshold', 16.667)
    return _result('check_dimensions_confidence', adjusted, threshold, False, 'validates dimensions confidence',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_dimensions_dependency_threshold', 19.0)
    return _result('check_dimensions_dependency', adjusted, threshold, True, 'validates dimensions dependency',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_dimensions_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'dimensions')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_dimensions_readiness_threshold', 21.333)
    return _result('check_dimensions_readiness', adjusted, threshold, True, 'validates dimensions readiness',
                   {'field': 'dimensions', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_validation_rate_presence_threshold', 23.667)
    return _result('check_validation_rate_presence', adjusted, threshold, False, 'validates validation_rate presence',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_validation_rate_range_threshold', 26.0)
    return _result('check_validation_rate_range', adjusted, threshold, True, 'validates validation_rate range',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_validation_rate_stability_threshold', 28.333)
    return _result('check_validation_rate_stability', adjusted, threshold, True, 'validates validation_rate stability',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_validation_rate_freshness_threshold', 30.667)
    return _result('check_validation_rate_freshness', adjusted, threshold, False, 'validates validation_rate freshness',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_validation_rate_coverage_threshold', 8.667)
    return _result('check_validation_rate_coverage', adjusted, threshold, True, 'validates validation_rate coverage',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_validation_rate_consistency_threshold', 11.0)
    return _result('check_validation_rate_consistency', adjusted, threshold, True, 'validates validation_rate consistency',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_validation_rate_risk_threshold', 13.333)
    return _result('check_validation_rate_risk', adjusted, threshold, False, 'validates validation_rate risk',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_validation_rate_confidence_threshold', 15.667)
    return _result('check_validation_rate_confidence', adjusted, threshold, True, 'validates validation_rate confidence',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_validation_rate_dependency_threshold', 18.0)
    return _result('check_validation_rate_dependency', adjusted, threshold, True, 'validates validation_rate dependency',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_validation_rate_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'validation_rate')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_validation_rate_readiness_threshold', 20.333)
    return _result('check_validation_rate_readiness', adjusted, threshold, False, 'validates validation_rate readiness',
                   {'field': 'validation_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_indicator_id_presence,
    check_indicator_id_range,
    check_indicator_id_stability,
    check_indicator_id_freshness,
    check_indicator_id_coverage,
    check_indicator_id_consistency,
    check_indicator_id_risk,
    check_indicator_id_confidence,
    check_indicator_id_dependency,
    check_indicator_id_readiness,
    check_formula_complexity_presence,
    check_formula_complexity_range,
    check_formula_complexity_stability,
    check_formula_complexity_freshness,
    check_formula_complexity_coverage,
    check_formula_complexity_consistency,
    check_formula_complexity_risk,
    check_formula_complexity_confidence,
    check_formula_complexity_dependency,
    check_formula_complexity_readiness,
    check_unit_rank_presence,
    check_unit_rank_range,
    check_unit_rank_stability,
    check_unit_rank_freshness,
    check_unit_rank_coverage,
    check_unit_rank_consistency,
    check_unit_rank_risk,
    check_unit_rank_confidence,
    check_unit_rank_dependency,
    check_unit_rank_readiness,
    check_dependency_count_presence,
    check_dependency_count_range,
    check_dependency_count_stability,
    check_dependency_count_freshness,
    check_dependency_count_coverage,
    check_dependency_count_consistency,
    check_dependency_count_risk,
    check_dependency_count_confidence,
    check_dependency_count_dependency,
    check_dependency_count_readiness,
    check_coverage_share_presence,
    check_coverage_share_range,
    check_coverage_share_stability,
    check_coverage_share_freshness,
    check_coverage_share_coverage,
    check_coverage_share_consistency,
    check_coverage_share_risk,
    check_coverage_share_confidence,
    check_coverage_share_dependency,
    check_coverage_share_readiness,
    check_effective_days_presence,
    check_effective_days_range,
    check_effective_days_stability,
    check_effective_days_freshness,
    check_effective_days_coverage,
    check_effective_days_consistency,
    check_effective_days_risk,
    check_effective_days_confidence,
    check_effective_days_dependency,
    check_effective_days_readiness,
    check_source_age_days_presence,
    check_source_age_days_range,
    check_source_age_days_stability,
    check_source_age_days_freshness,
    check_source_age_days_coverage,
    check_source_age_days_consistency,
    check_source_age_days_risk,
    check_source_age_days_confidence,
    check_source_age_days_dependency,
    check_source_age_days_readiness,
    check_missing_policy_presence,
    check_missing_policy_range,
    check_missing_policy_stability,
    check_missing_policy_freshness,
    check_missing_policy_coverage,
    check_missing_policy_consistency,
    check_missing_policy_risk,
    check_missing_policy_confidence,
    check_missing_policy_dependency,
    check_missing_policy_readiness,
    check_recalculation_delay_presence,
    check_recalculation_delay_range,
    check_recalculation_delay_stability,
    check_recalculation_delay_freshness,
    check_recalculation_delay_coverage,
    check_recalculation_delay_consistency,
    check_recalculation_delay_risk,
    check_recalculation_delay_confidence,
    check_recalculation_delay_dependency,
    check_recalculation_delay_readiness,
    check_affected_members_presence,
    check_affected_members_range,
    check_affected_members_stability,
    check_affected_members_freshness,
    check_affected_members_coverage,
    check_affected_members_consistency,
    check_affected_members_risk,
    check_affected_members_confidence,
    check_affected_members_dependency,
    check_affected_members_readiness,
    check_dimensions_presence,
    check_dimensions_range,
    check_dimensions_stability,
    check_dimensions_freshness,
    check_dimensions_coverage,
    check_dimensions_consistency,
    check_dimensions_risk,
    check_dimensions_confidence,
    check_dimensions_dependency,
    check_dimensions_readiness,
    check_validation_rate_presence,
    check_validation_rate_range,
    check_validation_rate_stability,
    check_validation_rate_freshness,
    check_validation_rate_coverage,
    check_validation_rate_consistency,
    check_validation_rate_risk,
    check_validation_rate_confidence,
    check_validation_rate_dependency,
    check_validation_rate_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'superseded': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'superseded': sum(item.severity == 'superseded' for item in results)}
