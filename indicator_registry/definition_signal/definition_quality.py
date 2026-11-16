from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class DomainSignal:
    code: str
    score: float
    severity: str
    evidence: dict[str, Any]

def number(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
    return default if value != value or value in (float('inf'), float('-inf')) else value

def ratio(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = number(payload, key, default)
    if value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))

def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

def definition_quality(payload:Mapping[str,Any])->DomainSignal:
    validity=ratio(payload,'formula_validity'); coverage=ratio(payload,'source_coverage'); verification=ratio(payload,'verification_rate'); missing=ratio(payload,'missing_policy'); dependencies=max(0.0,number(payload,'dependency_count')); cycles=max(0.0,number(payload,'cycle_count')); source_age=max(0.0,number(payload,'source_age_days'))
    acyclic=1.0 if cycles==0 else 0.0; freshness=max(0.0,1.0-min(1.0,source_age/365.0)); dependency_cost=min(1.0,dependencies/25.0)
    score=clamp(validity*.28+coverage*.24+verification*.20+acyclic*.16+freshness*.08+(1-dependency_cost)*.04)
    severity='critical' if cycles>0 or validity<.5 else 'warning' if coverage<.6 or source_age>180 else 'info'
    return DomainSignal('definition_quality',score,severity,{'cycle_count':cycles,'freshness':freshness,'dependency_cost':dependency_cost,'missing_policy':missing})

def peer_distribution(records:Iterable[Any],group_field:str='indicator_family')->dict[str,Any]:
    rows=[definition_quality(getattr(r,'payload',r)) for r in records]
    return {'count':len(rows),'cyclic':sum(s.evidence['cycle_count']>0 for s in rows),'minimum':min((s.score for s in rows),default=0.0)}

def augment_context(record:Any,repository:Any)->dict[str,Any]:
    signal=definition_quality(record.payload); peers=peer_distribution(repository.list_records())
    return {'domain_signal':signal.score,'domain_severity':signal.severity,'cyclic_indicators':peers['cyclic'],'minimum_quality':peers['minimum']}
