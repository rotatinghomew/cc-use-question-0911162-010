from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from indicator_registry.definitions.contract import ContractError, Decision, DomainRecord, RuleResult, bounded
from indicator_registry.dependencies.graph import grouped_metrics, record_score
from indicator_registry.formula.parser import evaluate

STATES = ['drafted', 'validated', 'active', 'superseded', 'retired', 'archived']
TRANSITIONS = {state: tuple(STATES[i + 1:i + 3]) for i, state in enumerate(STATES)}

@dataclass(frozen=True)
class TransitionPlan:
    from_state: str
    to_state: str
    allowed: bool
    reasons: tuple[str, ...]
    score: float

def allowed_targets(state: str) -> tuple[str, ...]:
    if state not in TRANSITIONS:
        raise ContractError('unknown workflow state')
    return TRANSITIONS[state]

def plan_transition(record: DomainRecord, target: str, context: Mapping[str, Any] | None = None) -> TransitionPlan:
    context = context or {}
    if target not in STATES:
        raise ContractError('unknown target state')
    scorecard = record_score(record, context)
    reasons: list[str] = []
    structurally_allowed = target in allowed_targets(record.state)
    if not structurally_allowed:
        reasons.append('transition is not adjacent in the lifecycle')
    threshold = float(context.get('transition_threshold', 0.42))
    if scorecard['score'] < threshold:
        reasons.append('record score is below the transition threshold')
    return TransitionPlan(record.state, target, structurally_allowed and not reasons, tuple(reasons or ['eligible']), scorecard['score'])

def apply_transition(record: DomainRecord, target: str, context: Mapping[str, Any] | None = None) -> DomainRecord:
    plan = plan_transition(record, target, context)
    if not plan.allowed:
        raise ContractError('; '.join(plan.reasons))
    return record.with_state(target)

def guard_indicator_id_formula_confidence_01(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_indicator_id_formula_confidence_01_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_formula_confidence_01' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_lead_time_02(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_formula_complexity_lead_time_02_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_lead_time_02' + (':passed' if allowed else ':blocked')

def guard_unit_rank_false_alarm_cost_03(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_unit_rank_false_alarm_cost_03_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_false_alarm_cost_03' + (':passed' if allowed else ':blocked')

def guard_dependency_count_miss_risk_04(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_dependency_count_miss_risk_04_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_miss_risk_04' + (':passed' if allowed else ':blocked')

def guard_coverage_share_delivery_reach_05(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_coverage_share_delivery_reach_05_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_delivery_reach_05' + (':passed' if allowed else ':blocked')

def guard_effective_days_station_disagreement_06(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_effective_days_station_disagreement_06_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_station_disagreement_06' + (':passed' if allowed else ':blocked')

def guard_source_age_days_clearance_stability_07(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_source_age_days_clearance_stability_07_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_clearance_stability_07' + (':passed' if allowed else ':blocked')

def guard_missing_policy_comparison_completeness_08(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_missing_policy_comparison_completeness_08_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_comparison_completeness_08' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_formula_confidence_09(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_recalculation_delay_formula_confidence_09_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_formula_confidence_09' + (':passed' if allowed else ':blocked')

def guard_affected_members_lead_time_10(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_affected_members_lead_time_10_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_lead_time_10' + (':passed' if allowed else ':blocked')

def guard_dimensions_false_alarm_cost_11(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_dimensions_false_alarm_cost_11_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_false_alarm_cost_11' + (':passed' if allowed else ':blocked')

def guard_validation_rate_miss_risk_12(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_validation_rate_miss_risk_12_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_miss_risk_12' + (':passed' if allowed else ':blocked')

def guard_indicator_id_delivery_reach_13(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_indicator_id_delivery_reach_13_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_delivery_reach_13' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_station_disagreement_14(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_formula_complexity_station_disagreement_14_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_station_disagreement_14' + (':passed' if allowed else ':blocked')

def guard_unit_rank_clearance_stability_15(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_unit_rank_clearance_stability_15_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_clearance_stability_15' + (':passed' if allowed else ':blocked')

def guard_dependency_count_comparison_completeness_16(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_dependency_count_comparison_completeness_16_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_comparison_completeness_16' + (':passed' if allowed else ':blocked')

def guard_coverage_share_formula_confidence_17(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_coverage_share_formula_confidence_17_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_formula_confidence_17' + (':passed' if allowed else ':blocked')

def guard_effective_days_lead_time_18(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_effective_days_lead_time_18_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_lead_time_18' + (':passed' if allowed else ':blocked')

def guard_source_age_days_false_alarm_cost_19(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_source_age_days_false_alarm_cost_19_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_false_alarm_cost_19' + (':passed' if allowed else ':blocked')

def guard_missing_policy_miss_risk_20(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_missing_policy_miss_risk_20_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_miss_risk_20' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_delivery_reach_21(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_recalculation_delay_delivery_reach_21_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_delivery_reach_21' + (':passed' if allowed else ':blocked')

def guard_affected_members_station_disagreement_22(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_affected_members_station_disagreement_22_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_station_disagreement_22' + (':passed' if allowed else ':blocked')

def guard_dimensions_clearance_stability_23(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_dimensions_clearance_stability_23_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_clearance_stability_23' + (':passed' if allowed else ':blocked')

def guard_validation_rate_comparison_completeness_24(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_validation_rate_comparison_completeness_24_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_comparison_completeness_24' + (':passed' if allowed else ':blocked')

def guard_indicator_id_formula_confidence_25(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_indicator_id_formula_confidence_25_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_formula_confidence_25' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_lead_time_26(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_formula_complexity_lead_time_26_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_lead_time_26' + (':passed' if allowed else ':blocked')

def guard_unit_rank_false_alarm_cost_27(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_unit_rank_false_alarm_cost_27_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_false_alarm_cost_27' + (':passed' if allowed else ':blocked')

def guard_dependency_count_miss_risk_28(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_dependency_count_miss_risk_28_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_miss_risk_28' + (':passed' if allowed else ':blocked')

def guard_coverage_share_delivery_reach_29(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_coverage_share_delivery_reach_29_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_delivery_reach_29' + (':passed' if allowed else ':blocked')

def guard_effective_days_station_disagreement_30(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_effective_days_station_disagreement_30_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_station_disagreement_30' + (':passed' if allowed else ':blocked')

def guard_source_age_days_clearance_stability_31(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_source_age_days_clearance_stability_31_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_clearance_stability_31' + (':passed' if allowed else ':blocked')

def guard_missing_policy_comparison_completeness_32(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_missing_policy_comparison_completeness_32_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_comparison_completeness_32' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_formula_confidence_33(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_recalculation_delay_formula_confidence_33_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_formula_confidence_33' + (':passed' if allowed else ':blocked')

def guard_affected_members_lead_time_34(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_affected_members_lead_time_34_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_lead_time_34' + (':passed' if allowed else ':blocked')

def guard_dimensions_false_alarm_cost_35(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_dimensions_false_alarm_cost_35_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_false_alarm_cost_35' + (':passed' if allowed else ':blocked')

def guard_validation_rate_miss_risk_36(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_validation_rate_miss_risk_36_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_miss_risk_36' + (':passed' if allowed else ':blocked')

def guard_indicator_id_delivery_reach_37(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_indicator_id_delivery_reach_37_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_delivery_reach_37' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_station_disagreement_38(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_formula_complexity_station_disagreement_38_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_station_disagreement_38' + (':passed' if allowed else ':blocked')

def guard_unit_rank_clearance_stability_39(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_unit_rank_clearance_stability_39_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_clearance_stability_39' + (':passed' if allowed else ':blocked')

def guard_dependency_count_comparison_completeness_40(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_dependency_count_comparison_completeness_40_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_comparison_completeness_40' + (':passed' if allowed else ':blocked')

def guard_coverage_share_formula_confidence_41(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_coverage_share_formula_confidence_41_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_formula_confidence_41' + (':passed' if allowed else ':blocked')

def guard_effective_days_lead_time_42(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_effective_days_lead_time_42_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_lead_time_42' + (':passed' if allowed else ':blocked')

def guard_source_age_days_false_alarm_cost_43(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_source_age_days_false_alarm_cost_43_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_false_alarm_cost_43' + (':passed' if allowed else ':blocked')

def guard_missing_policy_miss_risk_44(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_missing_policy_miss_risk_44_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_miss_risk_44' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_delivery_reach_45(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_recalculation_delay_delivery_reach_45_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_delivery_reach_45' + (':passed' if allowed else ':blocked')

def guard_affected_members_station_disagreement_46(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_affected_members_station_disagreement_46_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_station_disagreement_46' + (':passed' if allowed else ':blocked')

def guard_dimensions_clearance_stability_47(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_dimensions_clearance_stability_47_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_clearance_stability_47' + (':passed' if allowed else ':blocked')

def guard_validation_rate_comparison_completeness_48(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_validation_rate_comparison_completeness_48_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_comparison_completeness_48' + (':passed' if allowed else ':blocked')

def guard_indicator_id_formula_confidence_49(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_indicator_id_formula_confidence_49_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_formula_confidence_49' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_lead_time_50(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_formula_complexity_lead_time_50_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_lead_time_50' + (':passed' if allowed else ':blocked')

def guard_unit_rank_false_alarm_cost_51(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_unit_rank_false_alarm_cost_51_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_false_alarm_cost_51' + (':passed' if allowed else ':blocked')

def guard_dependency_count_miss_risk_52(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_dependency_count_miss_risk_52_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_miss_risk_52' + (':passed' if allowed else ':blocked')

def guard_coverage_share_delivery_reach_53(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_coverage_share_delivery_reach_53_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_delivery_reach_53' + (':passed' if allowed else ':blocked')

def guard_effective_days_station_disagreement_54(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_effective_days_station_disagreement_54_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_station_disagreement_54' + (':passed' if allowed else ':blocked')

def guard_source_age_days_clearance_stability_55(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_source_age_days_clearance_stability_55_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_clearance_stability_55' + (':passed' if allowed else ':blocked')

def guard_missing_policy_comparison_completeness_56(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_missing_policy_comparison_completeness_56_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_comparison_completeness_56' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_formula_confidence_57(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_recalculation_delay_formula_confidence_57_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_formula_confidence_57' + (':passed' if allowed else ':blocked')

def guard_affected_members_lead_time_58(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_affected_members_lead_time_58_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_lead_time_58' + (':passed' if allowed else ':blocked')

def guard_dimensions_false_alarm_cost_59(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_dimensions_false_alarm_cost_59_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_false_alarm_cost_59' + (':passed' if allowed else ':blocked')

def guard_validation_rate_miss_risk_60(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_validation_rate_miss_risk_60_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_miss_risk_60' + (':passed' if allowed else ':blocked')

def guard_indicator_id_delivery_reach_61(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_indicator_id_delivery_reach_61_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_delivery_reach_61' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_station_disagreement_62(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_formula_complexity_station_disagreement_62_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_station_disagreement_62' + (':passed' if allowed else ':blocked')

def guard_unit_rank_clearance_stability_63(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_unit_rank_clearance_stability_63_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_clearance_stability_63' + (':passed' if allowed else ':blocked')

def guard_dependency_count_comparison_completeness_64(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_dependency_count_comparison_completeness_64_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_comparison_completeness_64' + (':passed' if allowed else ':blocked')

def guard_coverage_share_formula_confidence_65(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_coverage_share_formula_confidence_65_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_formula_confidence_65' + (':passed' if allowed else ':blocked')

def guard_effective_days_lead_time_66(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_effective_days_lead_time_66_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_lead_time_66' + (':passed' if allowed else ':blocked')

def guard_source_age_days_false_alarm_cost_67(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_source_age_days_false_alarm_cost_67_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_false_alarm_cost_67' + (':passed' if allowed else ':blocked')

def guard_missing_policy_miss_risk_68(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_missing_policy_miss_risk_68_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_miss_risk_68' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_delivery_reach_69(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_recalculation_delay_delivery_reach_69_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_delivery_reach_69' + (':passed' if allowed else ':blocked')

def guard_affected_members_station_disagreement_70(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_affected_members_station_disagreement_70_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_station_disagreement_70' + (':passed' if allowed else ':blocked')

def guard_dimensions_clearance_stability_71(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_dimensions_clearance_stability_71_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_clearance_stability_71' + (':passed' if allowed else ':blocked')

def guard_validation_rate_comparison_completeness_72(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_validation_rate_comparison_completeness_72_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_comparison_completeness_72' + (':passed' if allowed else ':blocked')

def guard_indicator_id_formula_confidence_73(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_indicator_id_formula_confidence_73_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_formula_confidence_73' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_lead_time_74(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_formula_complexity_lead_time_74_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_lead_time_74' + (':passed' if allowed else ':blocked')

def guard_unit_rank_false_alarm_cost_75(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_unit_rank_false_alarm_cost_75_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_false_alarm_cost_75' + (':passed' if allowed else ':blocked')

def guard_dependency_count_miss_risk_76(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_dependency_count_miss_risk_76_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_miss_risk_76' + (':passed' if allowed else ':blocked')

def guard_coverage_share_delivery_reach_77(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_coverage_share_delivery_reach_77_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_delivery_reach_77' + (':passed' if allowed else ':blocked')

def guard_effective_days_station_disagreement_78(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_effective_days_station_disagreement_78_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_station_disagreement_78' + (':passed' if allowed else ':blocked')

def guard_source_age_days_clearance_stability_79(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_source_age_days_clearance_stability_79_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_clearance_stability_79' + (':passed' if allowed else ':blocked')

def guard_missing_policy_comparison_completeness_80(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_missing_policy_comparison_completeness_80_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_comparison_completeness_80' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_formula_confidence_81(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_recalculation_delay_formula_confidence_81_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_formula_confidence_81' + (':passed' if allowed else ':blocked')

def guard_affected_members_lead_time_82(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_affected_members_lead_time_82_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_lead_time_82' + (':passed' if allowed else ':blocked')

def guard_dimensions_false_alarm_cost_83(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_dimensions_false_alarm_cost_83_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_false_alarm_cost_83' + (':passed' if allowed else ':blocked')

def guard_validation_rate_miss_risk_84(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_validation_rate_miss_risk_84_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_miss_risk_84' + (':passed' if allowed else ':blocked')

def guard_indicator_id_delivery_reach_85(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_indicator_id_delivery_reach_85_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_delivery_reach_85' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_station_disagreement_86(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_formula_complexity_station_disagreement_86_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_station_disagreement_86' + (':passed' if allowed else ':blocked')

def guard_unit_rank_clearance_stability_87(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_unit_rank_clearance_stability_87_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_clearance_stability_87' + (':passed' if allowed else ':blocked')

def guard_dependency_count_comparison_completeness_88(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_dependency_count_comparison_completeness_88_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_comparison_completeness_88' + (':passed' if allowed else ':blocked')

def guard_coverage_share_formula_confidence_89(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_coverage_share_formula_confidence_89_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_formula_confidence_89' + (':passed' if allowed else ':blocked')

def guard_effective_days_lead_time_90(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_effective_days_lead_time_90_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_lead_time_90' + (':passed' if allowed else ':blocked')

def guard_source_age_days_false_alarm_cost_91(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_source_age_days_false_alarm_cost_91_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_false_alarm_cost_91' + (':passed' if allowed else ':blocked')

def guard_missing_policy_miss_risk_92(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_missing_policy_miss_risk_92_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_miss_risk_92' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_delivery_reach_93(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_recalculation_delay_delivery_reach_93_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_delivery_reach_93' + (':passed' if allowed else ':blocked')

def guard_affected_members_station_disagreement_94(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_affected_members_station_disagreement_94_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_station_disagreement_94' + (':passed' if allowed else ':blocked')

def guard_dimensions_clearance_stability_95(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_dimensions_clearance_stability_95_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_clearance_stability_95' + (':passed' if allowed else ':blocked')

def guard_validation_rate_comparison_completeness_96(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_validation_rate_comparison_completeness_96_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_comparison_completeness_96' + (':passed' if allowed else ':blocked')

def guard_indicator_id_formula_confidence_97(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_indicator_id_formula_confidence_97_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_formula_confidence_97' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_lead_time_98(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_formula_complexity_lead_time_98_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_lead_time_98' + (':passed' if allowed else ':blocked')

def guard_unit_rank_false_alarm_cost_99(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_unit_rank_false_alarm_cost_99_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_false_alarm_cost_99' + (':passed' if allowed else ':blocked')

def guard_dependency_count_miss_risk_100(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_dependency_count_miss_risk_100_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_miss_risk_100' + (':passed' if allowed else ':blocked')

def guard_coverage_share_delivery_reach_101(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_coverage_share_delivery_reach_101_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_delivery_reach_101' + (':passed' if allowed else ':blocked')

def guard_effective_days_station_disagreement_102(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_effective_days_station_disagreement_102_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_station_disagreement_102' + (':passed' if allowed else ':blocked')

def guard_source_age_days_clearance_stability_103(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_source_age_days_clearance_stability_103_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_clearance_stability_103' + (':passed' if allowed else ':blocked')

def guard_missing_policy_comparison_completeness_104(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_missing_policy_comparison_completeness_104_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_comparison_completeness_104' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_formula_confidence_105(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_recalculation_delay_formula_confidence_105_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_formula_confidence_105' + (':passed' if allowed else ':blocked')

def guard_affected_members_lead_time_106(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_affected_members_lead_time_106_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_lead_time_106' + (':passed' if allowed else ':blocked')

def guard_dimensions_false_alarm_cost_107(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_dimensions_false_alarm_cost_107_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_false_alarm_cost_107' + (':passed' if allowed else ':blocked')

def guard_validation_rate_miss_risk_108(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_validation_rate_miss_risk_108_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_miss_risk_108' + (':passed' if allowed else ':blocked')

def guard_indicator_id_delivery_reach_109(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_indicator_id_delivery_reach_109_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_indicator_id_delivery_reach_109' + (':passed' if allowed else ':blocked')

def guard_formula_complexity_station_disagreement_110(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_formula_complexity_station_disagreement_110_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_formula_complexity_station_disagreement_110' + (':passed' if allowed else ':blocked')

def guard_unit_rank_clearance_stability_111(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_unit_rank_clearance_stability_111_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_unit_rank_clearance_stability_111' + (':passed' if allowed else ':blocked')

def guard_dependency_count_comparison_completeness_112(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_dependency_count_comparison_completeness_112_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dependency_count_comparison_completeness_112' + (':passed' if allowed else ':blocked')

def guard_coverage_share_formula_confidence_113(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('formula_confidence', 0.0)
    floor = float(context.get('guard_coverage_share_formula_confidence_113_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_coverage_share_formula_confidence_113' + (':passed' if allowed else ':blocked')

def guard_effective_days_lead_time_114(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lead_time', 0.0)
    floor = float(context.get('guard_effective_days_lead_time_114_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_effective_days_lead_time_114' + (':passed' if allowed else ':blocked')

def guard_source_age_days_false_alarm_cost_115(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_alarm_cost', 0.0)
    floor = float(context.get('guard_source_age_days_false_alarm_cost_115_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_source_age_days_false_alarm_cost_115' + (':passed' if allowed else ':blocked')

def guard_missing_policy_miss_risk_116(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('miss_risk', 0.0)
    floor = float(context.get('guard_missing_policy_miss_risk_116_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('validated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_missing_policy_miss_risk_116' + (':passed' if allowed else ':blocked')

def guard_recalculation_delay_delivery_reach_117(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('delivery_reach', 0.0)
    floor = float(context.get('guard_recalculation_delay_delivery_reach_117_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('active')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_recalculation_delay_delivery_reach_117' + (':passed' if allowed else ':blocked')

def guard_affected_members_station_disagreement_118(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('station_disagreement', 0.0)
    floor = float(context.get('guard_affected_members_station_disagreement_118_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('superseded')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_affected_members_station_disagreement_118' + (':passed' if allowed else ':blocked')

def guard_dimensions_clearance_stability_119(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('clearance_stability', 0.0)
    floor = float(context.get('guard_dimensions_clearance_stability_119_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('retired')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_dimensions_clearance_stability_119' + (':passed' if allowed else ':blocked')

def guard_validation_rate_comparison_completeness_120(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('comparison_completeness', 0.0)
    floor = float(context.get('guard_validation_rate_comparison_completeness_120_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('archived')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_validation_rate_comparison_completeness_120' + (':passed' if allowed else ':blocked')

GUARDS: tuple[Callable[[DomainRecord, Mapping[str, Any]], tuple[bool, str]], ...] = (
    guard_indicator_id_formula_confidence_01,
    guard_formula_complexity_lead_time_02,
    guard_unit_rank_false_alarm_cost_03,
    guard_dependency_count_miss_risk_04,
    guard_coverage_share_delivery_reach_05,
    guard_effective_days_station_disagreement_06,
    guard_source_age_days_clearance_stability_07,
    guard_missing_policy_comparison_completeness_08,
    guard_recalculation_delay_formula_confidence_09,
    guard_affected_members_lead_time_10,
    guard_dimensions_false_alarm_cost_11,
    guard_validation_rate_miss_risk_12,
    guard_indicator_id_delivery_reach_13,
    guard_formula_complexity_station_disagreement_14,
    guard_unit_rank_clearance_stability_15,
    guard_dependency_count_comparison_completeness_16,
    guard_coverage_share_formula_confidence_17,
    guard_effective_days_lead_time_18,
    guard_source_age_days_false_alarm_cost_19,
    guard_missing_policy_miss_risk_20,
    guard_recalculation_delay_delivery_reach_21,
    guard_affected_members_station_disagreement_22,
    guard_dimensions_clearance_stability_23,
    guard_validation_rate_comparison_completeness_24,
    guard_indicator_id_formula_confidence_25,
    guard_formula_complexity_lead_time_26,
    guard_unit_rank_false_alarm_cost_27,
    guard_dependency_count_miss_risk_28,
    guard_coverage_share_delivery_reach_29,
    guard_effective_days_station_disagreement_30,
    guard_source_age_days_clearance_stability_31,
    guard_missing_policy_comparison_completeness_32,
    guard_recalculation_delay_formula_confidence_33,
    guard_affected_members_lead_time_34,
    guard_dimensions_false_alarm_cost_35,
    guard_validation_rate_miss_risk_36,
    guard_indicator_id_delivery_reach_37,
    guard_formula_complexity_station_disagreement_38,
    guard_unit_rank_clearance_stability_39,
    guard_dependency_count_comparison_completeness_40,
    guard_coverage_share_formula_confidence_41,
    guard_effective_days_lead_time_42,
    guard_source_age_days_false_alarm_cost_43,
    guard_missing_policy_miss_risk_44,
    guard_recalculation_delay_delivery_reach_45,
    guard_affected_members_station_disagreement_46,
    guard_dimensions_clearance_stability_47,
    guard_validation_rate_comparison_completeness_48,
    guard_indicator_id_formula_confidence_49,
    guard_formula_complexity_lead_time_50,
    guard_unit_rank_false_alarm_cost_51,
    guard_dependency_count_miss_risk_52,
    guard_coverage_share_delivery_reach_53,
    guard_effective_days_station_disagreement_54,
    guard_source_age_days_clearance_stability_55,
    guard_missing_policy_comparison_completeness_56,
    guard_recalculation_delay_formula_confidence_57,
    guard_affected_members_lead_time_58,
    guard_dimensions_false_alarm_cost_59,
    guard_validation_rate_miss_risk_60,
    guard_indicator_id_delivery_reach_61,
    guard_formula_complexity_station_disagreement_62,
    guard_unit_rank_clearance_stability_63,
    guard_dependency_count_comparison_completeness_64,
    guard_coverage_share_formula_confidence_65,
    guard_effective_days_lead_time_66,
    guard_source_age_days_false_alarm_cost_67,
    guard_missing_policy_miss_risk_68,
    guard_recalculation_delay_delivery_reach_69,
    guard_affected_members_station_disagreement_70,
    guard_dimensions_clearance_stability_71,
    guard_validation_rate_comparison_completeness_72,
    guard_indicator_id_formula_confidence_73,
    guard_formula_complexity_lead_time_74,
    guard_unit_rank_false_alarm_cost_75,
    guard_dependency_count_miss_risk_76,
    guard_coverage_share_delivery_reach_77,
    guard_effective_days_station_disagreement_78,
    guard_source_age_days_clearance_stability_79,
    guard_missing_policy_comparison_completeness_80,
    guard_recalculation_delay_formula_confidence_81,
    guard_affected_members_lead_time_82,
    guard_dimensions_false_alarm_cost_83,
    guard_validation_rate_miss_risk_84,
    guard_indicator_id_delivery_reach_85,
    guard_formula_complexity_station_disagreement_86,
    guard_unit_rank_clearance_stability_87,
    guard_dependency_count_comparison_completeness_88,
    guard_coverage_share_formula_confidence_89,
    guard_effective_days_lead_time_90,
    guard_source_age_days_false_alarm_cost_91,
    guard_missing_policy_miss_risk_92,
    guard_recalculation_delay_delivery_reach_93,
    guard_affected_members_station_disagreement_94,
    guard_dimensions_clearance_stability_95,
    guard_validation_rate_comparison_completeness_96,
    guard_indicator_id_formula_confidence_97,
    guard_formula_complexity_lead_time_98,
    guard_unit_rank_false_alarm_cost_99,
    guard_dependency_count_miss_risk_100,
    guard_coverage_share_delivery_reach_101,
    guard_effective_days_station_disagreement_102,
    guard_source_age_days_clearance_stability_103,
    guard_missing_policy_comparison_completeness_104,
    guard_recalculation_delay_formula_confidence_105,
    guard_affected_members_lead_time_106,
    guard_dimensions_false_alarm_cost_107,
    guard_validation_rate_miss_risk_108,
    guard_indicator_id_delivery_reach_109,
    guard_formula_complexity_station_disagreement_110,
    guard_unit_rank_clearance_stability_111,
    guard_dependency_count_comparison_completeness_112,
    guard_coverage_share_formula_confidence_113,
    guard_effective_days_lead_time_114,
    guard_source_age_days_false_alarm_cost_115,
    guard_missing_policy_miss_risk_116,
    guard_recalculation_delay_delivery_reach_117,
    guard_affected_members_station_disagreement_118,
    guard_dimensions_clearance_stability_119,
    guard_validation_rate_comparison_completeness_120,
)

def guard_report(record: DomainRecord, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    context = dict(context or {})
    context['_metrics'] = grouped_metrics(record, context)
    results = [guard(record, context) for guard in GUARDS]
    return {'passed': sum(item[0] for item in results), 'failed': sum(not item[0] for item in results),
            'messages': [item[1] for item in results]}

def decide(record: DomainRecord, context: Mapping[str, Any] | None = None) -> Decision:
    context = context or {}
    rules = evaluate(record, context)
    scorecard = record_score(record, context)
    guards = guard_report(record, context)
    effective_score = scorecard['score'] * 0.65 + float(context.get('domain_signal', 0.5)) * 0.35
    superseded = sum(item.severity == 'superseded' for item in rules)
    if context.get('domain_severity') == 'critical':
        outcome = 'hold'
    elif superseded:
        outcome = 'hold'
    elif effective_score >= float(context.get('approve_threshold', 0.62)) and guards['passed'] >= guards['failed']:
        outcome = 'approve'
    elif effective_score >= float(context.get('comparison_threshold', 0.38)):
        outcome = 'comparison'
    else:
        outcome = 'reject'
    reasons = (f"score={effective_score:.6f}", f"superseded={superseded}",
               f"guards={guards['passed']}/{guards['passed'] + guards['failed']}")
    decided_at = context.get("decided_at")
    if decided_at:
        return Decision(record.record_id, outcome, effective_score, reasons, rules,
                        scorecard['metrics'], decided_at=str(decided_at))
    return Decision(record.record_id, outcome, effective_score, reasons, rules, scorecard['metrics'])

def advance_for_outcome(record: DomainRecord, decision: Decision) -> DomainRecord:
    current = STATES.index(record.state)
    if decision.outcome == 'approve' and current + 1 < len(STATES):
        return record.with_state(STATES[current + 1])
    if decision.outcome == 'hold' and STATES[-1] != record.state:
        return record.with_state(STATES[-1])
    return record
