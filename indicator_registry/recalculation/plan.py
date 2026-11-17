from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

from indicator_registry.definitions.contract import bounded, finite_number, stable_hash
from indicator_registry.definitions.versions import (
    Change,
    DefinitionRegistry,
    DefinitionVersion,
    version_key,
)
from indicator_registry.dependencies.graph import record_score
from indicator_registry.formula.evaluator import ALERT_FLOOR, ALERT_THRESHOLDS

COMPUTED = "computed"
REUSED = "reused"
WITHHELD = "withheld"


def _as_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def observation_window(node: DefinitionVersion, as_of: str | None) -> dict[str, Any]:
    end = _as_date(as_of) or datetime.now(timezone.utc).date()
    start = end - timedelta(days=node.observation_window_days)
    age = node.source_age_days
    outside = age is not None and age > node.observation_window_days
    observations = node.source_observations
    if observations is None:
        payload_value = node.payload.get("observations", node.payload.get("observation_count"))
        if payload_value not in (None, ""):
            try:
                observations = max(0, int(finite_number(payload_value)))
            except Exception:  # noqa: BLE001 - payload is untrusted input
                observations = None
    if observations is None:
        # A registered definition record itself counts as one observation.
        observations = 1
    return {
        "as_of": end.isoformat(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "window_days": node.observation_window_days,
        "observations_in_window": observations,
        "min_observations": node.min_observations,
        "source_age_days": age,
        "outside_window": outside,
    }


def alert_for(status: str, value: float | None) -> dict[str, Any]:
    if status == WITHHELD or value is None:
        return {"level": "withheld", "severity": "error",
                "reason": "value is unavailable; no alert is raised from a missing number"}
    level = next((name for threshold, name in ALERT_THRESHOLDS if value >= threshold), ALERT_FLOOR)
    severity = {"superseded": "error", "active": "warning"}.get(level, "info")
    return {"level": level, "severity": severity, "reason": f"threshold band from computed value {value:.6f}"}


@dataclass(frozen=True)
class RecalculationEntry:
    definition_id: str
    version: str
    indicator_id: str
    content_hash: str
    snapshot_hash: str
    order: int
    status: str
    reasons: tuple[str, ...] = ()
    messages: tuple[str, ...] = ()
    value: float | None = None
    base_score: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    dependency_versions: dict[str, str] = field(default_factory=dict)
    dependency_hashes: dict[str, str] = field(default_factory=dict)
    dependency_values: dict[str, float] = field(default_factory=dict)
    dependency_snapshot_hashes: dict[str, str] = field(default_factory=dict)
    window: dict[str, Any] = field(default_factory=dict)
    alert: dict[str, Any] = field(default_factory=dict)
    record_id: str | None = None
    definition_state: str = "drafted"
    source_snapshot_hash: str | None = None

    @property
    def identity(self) -> str:
        return f"{self.definition_id}@{self.version}"

    @property
    def available(self) -> bool:
        return self.status != WITHHELD and self.value is not None

    @property
    def computation_key(self) -> str:
        return stable_hash({
            "definition_id": self.definition_id,
            "version": self.version,
            "content_hash": self.content_hash,
            "snapshot_hash": self.snapshot_hash,
            "dependency_versions": dict(sorted(self.dependency_versions.items())),
            "dependency_hashes": dict(sorted(self.dependency_hashes.items())),
            "window": self.window,
        })

    def stale_dependencies(self, content_hashes: Mapping[str, str] | None = None) -> list[str]:
        """Dependencies whose recorded content hash is not the issued one.

        A dependency may legitimately be reused from an earlier release; that
        is not stale.  What must never happen is a dependent referencing a
        dependency computation whose *definition content* has since moved.
        """

        if not content_hashes:
            return []
        stale = [definition_id for definition_id, content_hash in self.dependency_hashes.items()
                 if definition_id in content_hashes and content_hashes[definition_id] != content_hash]
        return sorted(stale)

    def as_dict(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "indicator_id": self.indicator_id,
            "version": self.version,
            "identity": self.identity,
            "content_hash": self.content_hash,
            "snapshot_hash": self.snapshot_hash,
            "computation_key": self.computation_key,
            "order": self.order,
            "status": self.status,
            "available": self.available,
            "reasons": list(self.reasons),
            "messages": list(self.messages),
            "value": self.value,
            "base_score": self.base_score,
            "metrics": dict(sorted(self.metrics.items())),
            "dependency_versions": dict(sorted(self.dependency_versions.items())),
            "dependency_hashes": dict(sorted(self.dependency_hashes.items())),
            "dependency_values": dict(sorted(self.dependency_values.items())),
            "dependency_snapshot_hashes": dict(sorted(self.dependency_snapshot_hashes.items())),
            "window": dict(self.window),
            "alert": dict(self.alert),
            "record_id": self.record_id,
            "state": self.definition_state,
            "source_snapshot_hash": self.source_snapshot_hash or self.snapshot_hash,
        }


def _node_for(registry: DefinitionRegistry, definition_id: str, version: str) -> DefinitionVersion:
    candidates = [node for node in registry.versions(definition_id) if node.version == version]
    return candidates[0] if candidates else registry.latest(definition_id)


def _changed_targets(registry: DefinitionRegistry) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for change in registry.changed:
        node = registry.latest(change.definition_ref)
        definition_id = node.definition_id if node else change.definition_ref
        if change.to_version:
            result[definition_id] = change.to_version
        else:
            result[definition_id] = node.version if node else None
    return result


def _dependency_resolution(registry: DefinitionRegistry, node: DefinitionVersion,
                           changes: Mapping[str, str | None]
                           ) -> tuple[dict[str, str], list[tuple[str, str]], list[str]]:
    """Resolve dependencies to the version that must be used for recalculation.

    A dependency is recalculated first, then every dependent must reference
    that *recalculated* version.  Declared pins that point at an older version
    are advanced and reported, never silently kept.
    """

    versions: dict[str, str] = {}
    missing: list[tuple[str, str]] = []
    notes: list[str] = []
    for reference in node.depends_on:
        pinned = node.dependency_pins.get(reference)
        candidates = registry.versions(reference)
        if not candidates:
            candidates = [candidate for nodes in registry.definitions.values()
                          for candidate in nodes if candidate.indicator_id == reference]
        resolved = registry.latest(candidates[0].definition_id) if candidates else None
        if resolved is None:
            missing.append((reference, pinned or "unresolved"))
            continue
        pinned_node = None
        if pinned:
            exact = [candidate for candidate in candidates if candidate.version == pinned]
            if not exact:
                # A pin to a version that is not registered must never silently
                # fall back to a different version, even if a newer change was
                # declared for the dependency.
                missing.append((reference, pinned))
                continue
            pinned_node = exact[0]
        target = changes.get(resolved.definition_id)
        if target:
            changed_node = registry.resolve(f"{resolved.definition_id}@{target}")
            if changed_node is not None:
                latest = registry.latest(resolved.definition_id)
                if latest is not None and version_key(latest.version) > version_key(changed_node.version):
                    changed_node = latest
                resolved = changed_node
        elif pinned_node is not None:
            resolved = pinned_node
            latest = registry.latest(resolved.definition_id)
            if latest is not None and version_key(latest.version) > version_key(pinned):
                notes.append(f"dependency_pin_stale:{reference}:{pinned}->{latest.version}")
                resolved = latest
        if pinned and version_key(pinned) != version_key(resolved.version):
            notes.append(f"dependency_pin_advanced:{reference}:{pinned}->{resolved.version}")
        versions[resolved.definition_id] = resolved.version
    return versions, missing, notes

def plan_recalculations(registry: DefinitionRegistry, *,
                        previous: Mapping[str, Mapping[str, Any]] | None = None,
                        previous_snapshot: Mapping[str, Any] | None = None,
                        context: Mapping[str, Any] | None = None,
                        as_of: str | None = None) -> dict[str, Any]:
    """Build the deterministic recalculation plan.

    ``previous`` maps ``definition_id`` to a stored computation entry.
    ``previous_snapshot`` is the last issued definition snapshot; when the
    fixture does not declare ``changes`` explicitly, the affected set is
    derived from the difference between the two snapshots and then propagated
    through the dependency graph.

    A stored entry is reused only when its content hash, dependency versions
    and observation window all match; otherwise the definition is recomputed.
    Unchanged definitions stay in the report as reused values so the annual
    view remains complete, while ``recalculation_order`` lists only the
    affected closure.
    """

    previous = previous or {}
    context = dict(context or {})
    moment = as_of or registry.as_of
    snapshot_hash = registry.snapshot()["snapshot_hash"]
    explicit_changes = bool(registry.changed)
    diff_ids, change_details = registry.changed_against(
        (previous_snapshot or {}).get("version_map") if previous_snapshot else None,
        (previous_snapshot or {}).get("content_hashes") if previous_snapshot else None)
    previous_map = (previous_snapshot or {}).get("version_map") or {}
    if previous_snapshot is None:
        # First issuance has no baseline; every definition is affected but
        # nothing is reported as a *change*.
        diff_ids, change_details = (), {}
    if explicit_changes:
        declared_starts: set[str] = set()
        for change in registry.changed:
            node = registry.latest(change.definition_ref)
            declared_starts.add(node.definition_id if node else change.definition_ref)
        changed_ids = tuple(sorted(set(diff_ids) | declared_starts))
        # A declared change is a *hint*, never a restriction: anything the
        # snapshot diff also sees must be recalculated too.
        affected = registry.propagate(changed_ids)
        current_map = registry.version_map()
        for definition_id in declared_starts:
            previous_version = previous_map.get(definition_id)
            if previous_version == current_map.get(definition_id) and definition_id in change_details:
                continue
            change_details.setdefault(definition_id, {"from": previous_version or "",
                                                      "to": current_map.get(definition_id, "")})
    else:
        changed_ids = diff_ids
        if previous_snapshot is None:
            affected = tuple(sorted(registry.latest_nodes()))
        else:
            affected = registry.propagate(changed_ids)
    order, cycles = registry.topological_order(registry.latest_nodes())
    cycle_members = {member for component in cycles for member in component}
    edges = registry.edges()

    # Anything downstream of a cycle is non-computable as well.
    downstream: set[str] = set()
    queue = sorted(cycle_members)
    while queue:
        current = queue.pop(0)
        for dependent in sorted(edges.get(current, ())):
            if dependent not in downstream and dependent not in cycle_members:
                downstream.add(dependent)
                queue.append(dependent)

    changed = {definition_id: registry.version_map().get(definition_id, "")
               for definition_id in changed_ids if definition_id in registry.latest_nodes()}
    changed.update({definition_id: version for definition_id, version in _changed_targets(registry).items()
                    if version})
    resolved_values: dict[str, float] = {}
    entries: dict[str, RecalculationEntry] = {}
    ordered_names: list[str] = []
    reuse_scope = affected

    order_index = 0
    for definition_id in order:
        node = registry.latest(definition_id)
        if node is None:
            continue
        ordered_names.append(definition_id)
        window = observation_window(node, moment)
        dependency_versions, missing, notes = _dependency_resolution(registry, node, changed)
        reasons: list[str] = []
        messages: list[str] = []

        def withhold(code: str, message: str) -> None:
            if code not in reasons:
                reasons.append(code)
                messages.append(message)

        if node.record is None:
            withhold("missing_source_record", "no source record is registered for this definition version")
        if definition_id in cycle_members:
            withhold("dependency_cycle", "definition participates in a dependency cycle")
        elif definition_id in downstream:
            withhold("dependency_cycle_downstream", "definition depends on a cycle and cannot be ordered")
        for reference, version in missing:
            withhold("unresolved_dependency", f"dependency {reference}@{version} is not registered")
        if window["outside_window"]:
            withhold("observations_outside_window",
                     f"latest source observation is outside the {window['window_days']:g}-day window")
        if window["observations_in_window"] < window["min_observations"]:
            withhold("insufficient_observations",
                     f"{window['observations_in_window']} observations available, "
                     f"{window['min_observations']} required in the observation window")
        for dependency_id in sorted(dependency_versions):
            dependency_entry = entries.get(dependency_id)
            if dependency_entry is None:
                # Dependencies are ordered first by the topological sort; a
                # missing entry means the dependency is outside the selected
                # set (for example an archived definition).
                continue
            if not dependency_entry.available:
                withhold("dependency_withheld",
                         f"dependency {dependency_entry.identity} has no publishable value")
        dependency_hashes = {dependency_id: _node_for(registry, dependency_id, version).content_hash
                             for dependency_id, version in dependency_versions.items()}
        dependency_snapshot_hashes = {dependency_id: entries[dependency_id].snapshot_hash
                                      for dependency_id in dependency_versions if dependency_id in entries}
        messages.extend(notes)

        dependency_values = {dependency_id: resolved_values[dependency_id]
                             for dependency_id in sorted(dependency_versions)
                             if dependency_id in resolved_values}

        status = COMPUTED
        value: float | None = None
        base_score: float | None = None
        metrics: dict[str, float] = {}
        source_snapshot_hash = snapshot_hash
        if not reasons and definition_id not in reuse_scope and definition_id in previous:
            stored = previous[definition_id]
            stored_dependencies = dict(stored.get("dependency_versions") or {})
            stored_hashes = dict(stored.get("dependency_hashes") or {})
            stored_window = dict(stored.get("window") or {})
            if (stored.get("content_hash") == node.content_hash
                    and stored_dependencies == dependency_versions
                    and stored_hashes == dependency_hashes
                    and stored_window.get("window_days") == window["window_days"]
                    and stored.get("status") in (COMPUTED, REUSED)
                    and stored.get("value") is not None):
                status = REUSED
                value = float(stored["value"])
                base_score = stored.get("base_score")
                metrics = {key: float(item) for key, item in (stored.get("metrics") or {}).items()}
                source_snapshot_hash = stored.get("source_snapshot_hash") or stored.get("snapshot_hash") or snapshot_hash
        if not reasons and status != REUSED:
            record = node.record
            if record is None:
                withhold("missing_source_record", "no source record is registered for this definition version")
            else:
                evaluation_context = dict(context)
                evaluation_context["definition_version"] = node.version
                evaluation_context["definition_identity"] = node.identity
                evaluation_context["definition_snapshot_hash"] = snapshot_hash
                evaluation_context["definition_dependency_signal"] = (
                    statistics.fmean(dependency_values.values()) if dependency_values else 0.0)
                scorecard = record_score(record, evaluation_context)
                base_score = scorecard["score"]
                if dependency_values:
                    value = bounded(base_score * 0.85 + statistics.fmean(dependency_values.values()) * 0.15)
                else:
                    value = base_score
                metrics = {key: float(item) for key, item in scorecard["metrics"].items()}

        if reasons:
            status = WITHHELD
            value = None
            base_score = None
            metrics = {}

        if value is not None:
            resolved_values[definition_id] = value
        alert = alert_for(status, value)
        if status == WITHHELD:
            alert["reasons"] = list(reasons)
        entry = RecalculationEntry(
            definition_id=definition_id,
            version=node.version,
            indicator_id=node.indicator_id,
            content_hash=node.content_hash,
            snapshot_hash=snapshot_hash,
            order=order_index,
            status=status,
            reasons=tuple(reasons),
            messages=tuple(messages),
            value=value,
            base_score=base_score,
            metrics=metrics,
            dependency_versions=dependency_versions,
            dependency_hashes=dependency_hashes,
            dependency_values=dependency_values,
            dependency_snapshot_hashes=dependency_snapshot_hashes,
            window=window,
            alert=alert,
            record_id=node.record_id,
            definition_state=node.state,
            source_snapshot_hash=source_snapshot_hash,
        )
        entries[definition_id] = entry
        order_index += 1

    # Any selected definition which did not appear in the topological order
    # (should not happen) is still reported, withheld.
    for definition_id in sorted(set(registry.latest_nodes()) - set(ordered_names)):
        node = registry.latest(definition_id)
        if node is None:
            continue
        order_index += 1
        entry = RecalculationEntry(
            definition_id=definition_id, version=node.version, indicator_id=node.indicator_id,
            content_hash=node.content_hash, snapshot_hash=snapshot_hash, order=order_index,
            status=WITHHELD, reasons=("unorderable_definition",),
            messages=("definition could not be placed in the recalculation order",),
            window=observation_window(node, moment), record_id=node.record_id,
            definition_state=node.state,
            alert=alert_for(WITHHELD, None),
        )
        entries[definition_id] = entry
        ordered_names.append(definition_id)

    ordered_entries = [entries[definition_id] for definition_id in ordered_names]
    withheld = [entry.identity for entry in ordered_entries if entry.status == WITHHELD]
    reused = [entry.identity for entry in ordered_entries if entry.status == REUSED]
    computed = [entry.identity for entry in ordered_entries if entry.status == COMPUTED]
    affected_set = set(affected)
    affected_order = [definition_id for definition_id in ordered_names if definition_id in affected_set]
    return {
        "snapshot_hash": snapshot_hash,
        "version_map": registry.version_map(),
        "content_hashes": registry.content_hashes(),
        "as_of": moment,
        "order": ordered_names,
        "recalculation_order": affected_order,
        "cycles": [list(component) for component in cycles],
        "affected": affected_order,
        "changed": sorted(changed_ids),
        "change_details": dict(sorted(change_details.items())),
        "entries": [entry.as_dict() for entry in ordered_entries],
        "observation_windows": {entry.definition_id: dict(entry.window) for entry in ordered_entries},
        "status": "withheld" if withheld else "complete",
        "computed": computed,
        "reused": reused,
        "withheld": withheld,
        "unavailable": [
            {"identity": entry.identity, "reasons": list(entry.reasons), "messages": list(entry.messages)}
            for entry in ordered_entries if entry.status == WITHHELD
        ],
        "not_computable": [
            {"identity": entry.identity, "definition_id": entry.definition_id, "version": entry.version,
             "reasons": list(entry.reasons), "messages": list(entry.messages)}
            for entry in ordered_entries if entry.status == WITHHELD
        ],
    }


def entry_objects(plan: Mapping[str, Any]) -> list[RecalculationEntry]:
    """Rebuild typed entries from a stored plan (used for publication/verify)."""

    return [RecalculationEntry(**{key: value for key, value in item.items()
                                  if key in RecalculationEntry.__dataclass_fields__})
            for item in plan.get("entries", [])]
