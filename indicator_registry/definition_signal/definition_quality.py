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

def definition_quality(payload:Mapping[str,Any], cyclic:bool|None=None)->DomainSignal:
    validity=ratio(payload,'formula_validity'); coverage=ratio(payload,'source_coverage'); verification=ratio(payload,'verification_rate'); missing=ratio(payload,'missing_policy'); dependencies=max(0.0,number(payload,'dependency_count')); cycles=max(0.0,number(payload,'cycle_count'))
    if cyclic:
        cycles=max(1.0,cycles)
    source_age=max(0.0,number(payload,'source_age_days'))
    acyclic=1.0 if cycles==0 else 0.0; freshness=max(0.0,1.0-min(1.0,source_age/365.0)); dependency_cost=min(1.0,dependencies/25.0)
    score=clamp(validity*.28+coverage*.24+verification*.20+acyclic*.16+freshness*.08+(1-dependency_cost)*.04)
    severity='critical' if cycles>0 or validity<.5 else 'warning' if coverage<.6 or source_age>180 else 'info'
    return DomainSignal('definition_quality',score,severity,{'cycle_count':cycles,'freshness':freshness,'dependency_cost':dependency_cost,'missing_policy':missing})

def peer_distribution(records:Iterable[Any],group_field:str='indicator_family',cyclic_ids:Iterable[str]|None=None)->dict[str,Any]:
    cyclic_ids={str(item) for item in (cyclic_ids or ())}
    rows=[]
    for record in records:
        payload=getattr(record,'payload',record)
        identifier=str(payload.get('definition_id') or payload.get('indicator_id') or getattr(record,'record_id',''))
        rows.append(definition_quality(payload, cyclic=identifier in cyclic_ids))
    return {'count':len(rows),'cyclic':sum(s.evidence['cycle_count']>0 for s in rows),'minimum':min((s.score for s in rows),default=0.0)}

def augment_context(record:Any,repository:Any,cyclic_indicators:Iterable[str]|None=None)->dict[str,Any]:
    cyclic_ids={str(item) for item in (cyclic_indicators or ())}
    identifier=str(getattr(record,'payload',{}).get('definition_id') or getattr(record,'payload',{}).get('indicator_id') or getattr(record,'record_id',''))
    signal=definition_quality(record.payload, cyclic=identifier in cyclic_ids)
    peers=peer_distribution(repository.list_records(),cyclic_ids=cyclic_ids)
    return {'domain_signal':signal.score,'domain_severity':signal.severity,'cyclic_indicators':peers['cyclic'],'minimum_quality':peers['minimum'],'definition_cycle':identifier in cyclic_ids}
