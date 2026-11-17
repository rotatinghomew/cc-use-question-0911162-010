from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from indicator_registry.definitions.contract import (
    ContractError,
    DomainRecord,
    finite_number,
    stable_hash,
)

DEFAULT_OBSERVATION_WINDOW_DAYS = 365.0
DEFAULT_MIN_OBSERVATIONS = 1

# Payload keys which explicitly turn a fixture into a versioned definition
# fixture.  The original acceptance fixture remains a plain record fixture and
# keeps its previous behaviour.
DEPENDENCY_KEYS = (
    "depends_on",
    "dependencies",
    "dependency_ids",
    "dependency_indicators",
    "depends_on_indicators",
    "dependency_definitions",
    "upstream",
    "requires",
)
WINDOW_KEYS = (
    "observation_window_days",
    "observation_window",
    "source_window_days",
    "window_days",
    "lookback_days",
    "observation_period_days",
)
VERSIONED_KEYS = frozenset({
    "definition_id",
    "definition_version",
    "definition_version_id",
    "definition_versions",
    "dependency_versions",
    "min_observations",
    "minimum_observations",
    "required_observations",
    "source_observations",
    "effective_from",
    *DEPENDENCY_KEYS,
    *WINDOW_KEYS,
})


def _token(value: Any, *, default: str = "") -> str:
    text = str(value if value is not None else "").strip().casefold()
    text = re.sub(r"\s+", "-", text)
    if not text:
        return default
    return text[:160]


def _version_text(value: Any, default: str = "1") -> str:
    if value is None or value == "":
        return default
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return _token(value, default=default)


def _number(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return finite_number(value)
    except ContractError:
        return default


def _integer(value: Any, default: int) -> int:
    number = _number(value, None)
    if number is None:
        return default
    return max(0, int(number))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item for item in re.split(r"[,;|\s]+", value.strip()) if item]
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def version_key(value: str) -> tuple[Any, ...]:
    """Deterministic version ordering which also handles ``2024.1`` style ids."""

    text = _version_text(value)
    parts = re.split(r"[.\-_:]+", text)
    result: list[Any] = []
    for part in parts:
        match = re.fullmatch(r"v?(\d+)", part)
        if match:
            result.append((0, int(match.group(1))))
        elif part:
            result.append((1, part))
    return tuple(result)


def _in_period(node: "DefinitionVersion", as_of: str | None) -> bool:
    if not as_of:
        return True
    if node.effective_from and as_of < node.effective_from:
        return False
    if node.effective_to and as_of >= node.effective_to:
        return False
    return True


def _dependency_items(value: Any) -> list[tuple[str, str | None]]:
    """Normalise the many accepted dependency spellings.

    ``dependency_count`` is deliberately *not* accepted here: it is a numeric
    payload field in the legacy fixture, not a dependency declaration.
    """

    items: list[tuple[str, str | None]] = []

    if value is None:
        return items

    if isinstance(value, Mapping):
        nested = value.get("depends_on")
        if nested is not None:
            return _dependency_items(nested)
        for key, item in value.items():
            if isinstance(item, Mapping):
                version = item.get("version", item.get("definition_version"))
                ref = item.get("definition_id") or item.get("indicator_id") or item.get("id") or key
                items.append((_token(ref), _version_text(version, "") or None))
            else:
                items.append((_token(key), _version_text(item, "") or None))
        return items

    for entry in _sequence(value):
        if isinstance(entry, Mapping):
            ref = entry.get("definition_id") or entry.get("indicator_id") or entry.get("id") or entry.get("ref")
            version = entry.get("version", entry.get("definition_version"))
            if ref is not None:
                items.append((_token(ref), _version_text(version, "") or None))
        elif entry is not None:
            raw = str(entry).strip()
            if not raw:
                continue
            if "@" in raw:
                ref, _, version = raw.partition("@")
                items.append((_token(ref), _version_text(version, "") or None))
            else:
                items.append((_token(raw), None))
    return items


def _first_present(payload: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def _dependency_pins(payload: Mapping[str, Any]) -> dict[str, str]:
    pins: dict[str, str] = {}
    explicit = payload.get("dependency_versions")
    if isinstance(explicit, Mapping):
        for key, value in explicit.items():
            version = _version_text(value, "")
            if version:
                pins[_token(key)] = version
    for ref, version in _dependency_items(_first_present(payload, DEPENDENCY_KEYS)):
        if version:
            pins[ref] = version
    return pins


def _window_days(value: Any, default: float = DEFAULT_OBSERVATION_WINDOW_DAYS) -> float:
    if isinstance(value, Mapping):
        for key in ("days", "window_days", "observation_window_days"):
            if key in value:
                number = _number(value.get(key), None)
                if number is not None:
                    return max(0.0, number)
        value = None
    number = _number(value, None)
    if number is None:
        return default
    return max(0.0, number)


@dataclass(frozen=True)
class DefinitionVersion:
    definition_id: str
    version: str
    indicator_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    dependency_pins: dict[str, str] = field(default_factory=dict)
    observation_window_days: float = DEFAULT_OBSERVATION_WINDOW_DAYS
    min_observations: int = DEFAULT_MIN_OBSERVATIONS
    source_observations: int | None = None
    source_age_days: float | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    state: str = "drafted"
    record_id: str | None = None
    record: DomainRecord | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        definition_id = _token(self.definition_id)
        indicator_id = _token(self.indicator_id or definition_id)
        version = _version_text(self.version)
        if not definition_id:
            raise ContractError("definition identifier is empty")
        if not version:
            raise ContractError("definition version is empty")
        object.__setattr__(self, "definition_id", definition_id)
        object.__setattr__(self, "indicator_id", indicator_id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "depends_on", tuple(dict.fromkeys(_token(item) for item in self.depends_on if _token(item))))
        object.__setattr__(self, "dependency_pins", {_token(k): _version_text(v, "")
                                                     for k, v in self.dependency_pins.items()
                                                     if _version_text(v, "")})
        object.__setattr__(self, "observation_window_days", max(0.0, float(self.observation_window_days)))
        object.__setattr__(self, "min_observations", max(0, int(self.min_observations)))

    @property
    def identity(self) -> str:
        return f"{self.definition_id}@{self.version}"

    @property
    def content(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "version": self.version,
            "indicator_id": self.indicator_id,
            "payload": self.payload,
            "depends_on": list(self.depends_on),
            "dependency_pins": dict(sorted(self.dependency_pins.items())),
            "observation_window_days": self.observation_window_days,
            "min_observations": self.min_observations,
            "source_observations": self.source_observations,
            "source_age_days": self.source_age_days,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "state": self.state,
        }

    @property
    def content_hash(self) -> str:
        return stable_hash(self.content)

    def with_updates(self, updates: Mapping[str, Any]) -> "DefinitionVersion":
        payload = dict(self.payload)
        payload.update(_mapping(updates.get("payload")))
        values = {key: value for key, value in updates.items() if key != "payload" and hasattr(self, key)}
        return DefinitionVersion(**({**self.__dict__, **values, "payload": payload}))

    def to_dict(self) -> dict[str, Any]:
        body = dict(self.content)
        body["identity"] = self.identity
        body["content_hash"] = self.content_hash
        body["record_id"] = self.record_id
        return body


@dataclass(frozen=True)
class Change:
    definition_ref: str
    to_version: str | None = None
    from_version: str | None = None

    @classmethod
    def from_value(cls, value: Any) -> "Change | None":
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return None
            if "@" in raw:
                ref, _, version = raw.partition("@")
                return cls(_token(ref), _version_text(version, "") or None)
            return cls(_token(raw), None)
        if isinstance(value, Mapping):
            ref = value.get("definition_id") or value.get("indicator_id") or value.get("id") or value.get("ref")
            if ref is None:
                return None
            to_version = value.get("to_version", value.get("version", value.get("definition_version")))
            from_version = value.get("from_version")
            return cls(_token(ref), _version_text(to_version, "") or None,
                       _version_text(from_version, "") or None)
        return None


def _definition_entries(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        # Accept {"def-a": {...}} as well as {"def-a": {"1": {...}}}.
        entries: list[Mapping[str, Any]] = []
        for key, item in value.items():
            if isinstance(item, Mapping) and any(
                    isinstance(inner, Mapping) and ("version" in inner or "payload" in inner)
                    for inner in item.values()):
                for version, inner in item.items():
                    if isinstance(inner, Mapping):
                        entries.append({"definition_id": key, "version": version, **dict(inner)})
            elif isinstance(item, Mapping):
                entries.append({"definition_id": key, **dict(item)})
        return entries
    return [item for item in _sequence(value) if isinstance(item, Mapping)]


def _metadata_from_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(_mapping(entry.get("payload")))
    for key, value in entry.items():
        if key in {"payload", "definition_id", "id", "indicator_id", "version", "definition_version",
                   "definition_version_id"}:
            continue
        payload.setdefault(key, value)
    return payload


def _declared_dependencies(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(ref for ref, _ in _dependency_items(_first_present(payload, DEPENDENCY_KEYS)))


def _build_from_record(record: DomainRecord, order: int) -> DefinitionVersion:
    payload = dict(record.payload)
    definition_id = payload.get("definition_id") or record.record_id
    indicator_id = payload.get("indicator_id") or definition_id
    version = payload.get("definition_version",
                          payload.get("definition_version_id",
                                      payload.get("version", record.version)))
    return DefinitionVersion(
        definition_id=_token(definition_id),
        version=_version_text(version),
        indicator_id=_token(indicator_id),
        payload=payload,
        depends_on=_declared_dependencies(payload),
        dependency_pins=_dependency_pins(payload),
        observation_window_days=_window_days(_first_present(payload, WINDOW_KEYS)),
        min_observations=_integer(
            payload.get("min_observations",
                        payload.get("minimum_observations", payload.get("required_observations"))),
            DEFAULT_MIN_OBSERVATIONS),
        source_observations=(None if payload.get("source_observations") in (None, "")
                             else _integer(payload.get("source_observations"), 0)),
        source_age_days=_number(payload.get("source_age_days"), None),
        effective_from=(payload.get("effective_from") or payload.get("valid_from")
                        or payload.get("period_start") or None),
        effective_to=(payload.get("effective_to") or payload.get("valid_to")
                      or payload.get("period_end") or None),
        state=str(payload.get("state") or payload.get("status") or record.state),
        record_id=record.record_id,
        record=record,
    )


class DefinitionRegistry:
    """Versioned definition catalog plus its dependency graph.

    A record is one definition version.  The legacy fixture has no explicit
    version metadata, so ``versioned`` is false and the application keeps its
    historical behaviour.  Fixtures which declare ``definitions``,
    ``definition_versions`` or ``changes`` (or carry version metadata in a
    payload) take the new recalculation path.
    """

    def __init__(self, definitions: Iterable[DefinitionVersion], *,
                 changed: Iterable[Change] = (), versioned: bool = False,
                 as_of: str | None = None):
        grouped: dict[str, list[DefinitionVersion]] = {}
        for node in definitions:
            grouped.setdefault(node.definition_id, []).append(node)
        for nodes in grouped.values():
            nodes.sort(key=lambda item: version_key(item.version))
        self.definitions = grouped
        self.changed = tuple(change for change in changed if change is not None)
        self.versioned = bool(versioned)
        self.as_of = as_of
        self._records: dict[str, list[DefinitionVersion]] = {}
        for nodes in grouped.values():
            for node in nodes:
                if node.record_id:
                    self._records.setdefault(node.record_id, []).append(node)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    @classmethod
    def from_fixture(cls, fixture: Mapping[str, Any], *, as_of: str | None = None) -> "DefinitionRegistry":
        records = [DomainRecord.from_dict(item) for item in (fixture.get("records") or [])]
        nodes: dict[tuple[str, str], DefinitionVersion] = {}
        order = 0
        for record in records:
            node = _build_from_record(record, order)
            key = (node.definition_id, node.version)
            if key in nodes:
                raise ContractError(f"duplicate definition version: {node.identity}")
            nodes[key] = node
            order += 1

        metadata = _definition_entries(fixture.get("definitions")) + \
            _definition_entries(fixture.get("definition_versions"))
        for entry in metadata:
            ref = _token(entry.get("definition_id") or entry.get("id") or entry.get("indicator_id"))
            version_raw = entry.get("version", entry.get("definition_version", entry.get("definition_version_id")))
            version = _version_text(version_raw, "") or None
            target_key: tuple[str, str] | None = None
            if version:
                target_key = (ref, version)
            else:
                candidates = [(key, node) for key, node in nodes.items()
                              if key[0] == ref or node.indicator_id == ref]
                if candidates:
                    target_key = max(candidates, key=lambda item: version_key(item[0][1]))[0]
            payload_updates = _metadata_from_entry(entry)
            if target_key is None or target_key not in nodes:
                # A definition may be declared without a record (or pin a
                # version not carried by one); it is then explicitly
                # non-computable rather than silently skipped.
                new_version = (target_key[1] if target_key else version) or "1"
                target_key = (ref, new_version)
                nodes[target_key] = DefinitionVersion(
                    definition_id=ref,
                    version=new_version,
                    indicator_id=_token(entry.get("indicator_id") or ref),
                    payload=payload_updates,
                    depends_on=_declared_dependencies(payload_updates),
                    dependency_pins=_dependency_pins(payload_updates),
                    observation_window_days=_window_days(
                        _first_present(payload_updates, WINDOW_KEYS)),
                    min_observations=_integer(
                        payload_updates.get("min_observations",
                                            payload_updates.get("minimum_observations")),
                        DEFAULT_MIN_OBSERVATIONS),
                    source_observations=(None if payload_updates.get("source_observations") in (None, "")
                                         else _integer(payload_updates.get("source_observations"), 0)),
                    source_age_days=_number(payload_updates.get("source_age_days"), None),
                    effective_from=(payload_updates.get("effective_from")
                                    or payload_updates.get("valid_from") or None),
                    effective_to=(payload_updates.get("effective_to")
                                  or payload_updates.get("valid_to") or None),
                    state=str(payload_updates.get("state") or payload_updates.get("status") or "drafted"),
                )
            else:
                node = nodes[target_key]
                nodes[target_key] = node.with_updates({
                    "payload": payload_updates,
                    "indicator_id": _token(entry.get("indicator_id") or node.indicator_id),
                    "depends_on": _declared_dependencies(payload_updates) or node.depends_on,
                    "dependency_pins": {**node.dependency_pins, **_dependency_pins(payload_updates)},
                    "observation_window_days": _window_days(
                        _first_present(payload_updates, WINDOW_KEYS),
                        node.observation_window_days),
                    "min_observations": _integer(
                        payload_updates.get("min_observations",
                                            payload_updates.get("minimum_observations",
                                                                payload_updates.get("required_observations"))),
                        node.min_observations),
                    "source_observations": (node.source_observations
                                            if payload_updates.get("source_observations") in (None, "")
                                            else _integer(payload_updates.get("source_observations"), 0)),
                    "source_age_days": (_number(payload_updates.get("source_age_days"), None)
                                        if payload_updates.get("source_age_days") is not None
                                        else node.source_age_days),
                    "effective_from": payload_updates.get("effective_from") or payload_updates.get("valid_from") or node.effective_from,
                    "effective_to": payload_updates.get("effective_to") or payload_updates.get("valid_to") or node.effective_to,
                    "state": str(payload_updates.get("state") or payload_updates.get("status") or node.state),
                })

        raw_changes = fixture.get("changes", fixture.get("definition_changes"))
        changes: list[Change] = []
        if raw_changes is not None:
            if isinstance(raw_changes, Mapping):
                raw_changes = [{"definition_id": key, "version": value}
                               for key, value in raw_changes.items()]
            for item in _sequence(raw_changes):
                change = Change.from_value(item)
                if change is not None:
                    changes.append(change)

        versioned = bool(metadata) or raw_changes is not None or any(
            any(key in record.payload for key in VERSIONED_KEYS) for record in records)
        return cls(nodes.values(), changed=changes, versioned=versioned,
                   as_of=as_of or fixture.get("as_of"))

    # ------------------------------------------------------------------
    # Catalog access
    # ------------------------------------------------------------------
    def all_versions(self) -> list[DefinitionVersion]:
        return sorted((node for nodes in self.definitions.values() for node in nodes),
                      key=lambda item: (item.definition_id, version_key(item.version)))

    def versions(self, definition_id: str) -> tuple[DefinitionVersion, ...]:
        key = _token(definition_id)
        return tuple(self.definitions.get(key, ()))

    def latest(self, definition_id: str, *, as_of: str | None = None) -> DefinitionVersion | None:
        candidates = list(self.versions(definition_id))
        if not candidates:
            return None
        moment = as_of if as_of is not None else self.as_of
        if moment:
            in_period = [node for node in candidates if _in_period(node, moment)]
            if in_period:
                candidates = in_period
        return max(candidates, key=lambda item: version_key(item.version))

    def latest_nodes(self) -> dict[str, DefinitionVersion]:
        result: dict[str, DefinitionVersion] = {}
        for definition_id in self.definitions:
            node = self.latest(definition_id)
            if node is not None:
                result[definition_id] = node
        return result

    def version_map(self) -> dict[str, str]:
        return {definition_id: node.version for definition_id, node in sorted(self.latest_nodes().items())}

    def content_hashes(self) -> dict[str, str]:
        return {definition_id: node.content_hash for definition_id, node in sorted(self.latest_nodes().items())}

    def node_for_record(self, record_id: str) -> DefinitionVersion | None:
        nodes = self._records.get(record_id) or []
        if not nodes:
            return None
        latest = self.latest(nodes[0].definition_id)
        return latest or max(nodes, key=lambda item: version_key(item.version))

    def resolve(self, reference: str, pins: Mapping[str, str] | None = None) -> DefinitionVersion | None:
        raw = str(reference or "").strip()
        if not raw:
            return None
        pins = pins or {}
        if "@" in raw:
            ref, _, explicit = raw.partition("@")
            base = _token(ref)
            pinned = _version_text(explicit, "") or None
            candidates = [node for node in self.versions(base) if node.version == pinned] if pinned else []
            if candidates:
                return candidates[0]
            base_ref = base
        else:
            base_ref = _token(raw)
        pinned = pins.get(base_ref) or pins.get(_token(raw))
        candidates = self.versions(base_ref)
        if not candidates:
            # Dependencies may be declared by indicator id rather than by
            # definition id.
            candidates = [node for nodes in self.definitions.values() for node in nodes
                          if node.indicator_id == base_ref]
        if not candidates:
            return None
        if pinned:
            exact = [node for node in candidates if node.version == pinned]
            return exact[0] if exact else None
        # More than one definition can share an indicator id; pick the
        # deterministic newest definition id, but keep the choice stable.
        by_definition = sorted({node.definition_id for node in candidates})
        if len(by_definition) > 1:
            chosen = by_definition[0]
        else:
            chosen = by_definition[0]
        return self.latest(chosen)

    def dependencies(self, node: DefinitionVersion) -> list[tuple[str, DefinitionVersion | None]]:
        result: list[tuple[str, DefinitionVersion | None]] = []
        for ref in node.depends_on:
            result.append((ref, self.resolve(ref, node.dependency_pins)))
        return result

    # ------------------------------------------------------------------
    # Graph operations
    # ------------------------------------------------------------------
    def edges(self) -> dict[str, set[str]]:
        """Return ``dependency -> dependents`` edges over latest definitions."""

        latest = self.latest_nodes()
        result: dict[str, set[str]] = {definition_id: set() for definition_id in latest}
        for definition_id, node in latest.items():
            for _, dependency in self.dependencies(node):
                if dependency is None:
                    continue
                if dependency.definition_id == definition_id:
                    result.setdefault(definition_id, set()).add(definition_id)
                else:
                    result.setdefault(dependency.definition_id, set()).add(definition_id)
        return result

    def propagate(self, start_ids: Iterable[str]) -> tuple[str, ...]:
        edges = self.edges()
        seen = {item for item in start_ids if item in self.definitions}
        queue = sorted(seen)
        while queue:
            current = queue.pop(0)
            for dependent in sorted(edges.get(current, ())):
                if dependent not in seen:
                    seen.add(dependent)
                    queue.append(dependent)
        return tuple(sorted(seen))

    def affected(self, changed: Iterable[Change] | None = None) -> tuple[str, ...]:
        changes = list(self.changed if changed is None else changed)
        if not changes:
            return tuple(sorted(self.latest_nodes()))
        starts: set[str] = set()
        for change in changes:
            if change.to_version:
                node = self.resolve(f"{change.definition_ref}@{change.to_version}")
                if node is not None:
                    starts.add(node.definition_id)
                    continue
            nodes = [node for nodes in self.definitions.values() for node in nodes
                     if node.definition_id == change.definition_ref
                     or node.indicator_id == change.definition_ref]
            for node in nodes:
                latest = self.latest(node.definition_id)
                if latest is not None:
                    starts.add(latest.definition_id)
        return self.propagate(starts)

    def changed_against(self, previous_version_map: Mapping[str, str] | None,
                        previous_hashes: Mapping[str, str] | None = None
                        ) -> tuple[tuple[str, ...], dict[str, dict[str, str]]]:
        """Definitions whose version or content moved since a prior snapshot."""

        if previous_version_map is None:
            return tuple(sorted(self.latest_nodes())), {}
        current = self.version_map()
        changes: dict[str, dict[str, str]] = {}
        for definition_id, version in current.items():
            old = previous_version_map.get(definition_id)
            if old is None:
                changes[definition_id] = {"from": "", "to": version}
            elif old != version:
                changes[definition_id] = {"from": old, "to": version}
        for definition_id, old in previous_version_map.items():
            if definition_id not in current:
                changes[definition_id] = {"from": old, "to": ""}
        if previous_hashes:
            for definition_id, content_hash in self.content_hashes().items():
                old = previous_hashes.get(definition_id)
                if old is not None and old != content_hash and definition_id not in changes:
                    changes[definition_id] = {"from": current.get(definition_id, ""),
                                              "to": current.get(definition_id, "")}
        return tuple(sorted(changes)), changes

    def topological_order(self, definition_ids: Iterable[str]) -> tuple[list[str], list[tuple[str, ...]]]:
        selected = set(definition_ids)
        edges = self.edges()
        dependencies: dict[str, set[str]] = {item: set() for item in selected}
        dependents: dict[str, set[str]] = {item: set() for item in selected}
        for dependency, items in edges.items():
            for dependent in items:
                if dependency in selected and dependent in selected and dependency != dependent:
                    dependencies[dependent].add(dependency)
                elif dependency == dependent and dependency in selected:
                    dependencies[dependent].add(dependency)
        for dependent, items in dependencies.items():
            for dependency in items:
                dependents.setdefault(dependency, set()).add(dependent)

        indegree = {item: len(dependencies[item]) for item in selected}
        ready = sorted(item for item, count in indegree.items() if count == 0)
        order: list[str] = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for dependent in sorted(dependents.get(current, ())):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
            ready.sort()

        remaining = selected - set(order)
        cycles = self._cycles(remaining, dependencies) if remaining else []
        # Cycle members and anything downstream of a cycle still need a
        # deterministic position in the processing order; they are reported as
        # withheld rather than silently dropped.
        for scc in cycles:
            for member in scc:
                if member not in order:
                    order.append(member)
        for member in sorted(remaining - {item for scc in cycles for item in scc}):
            order.append(member)
        return order, cycles

    def _cycles(self, selected: set[str], dependencies: Mapping[str, set[str]]) -> list[tuple[str, ...]]:
        # Kosaraju, iterative and sorted for deterministic output.
        adjacency = {item: sorted(dependencies.get(item, set()) & selected) for item in selected}
        visited: set[str] = set()
        finish: list[str] = []
        for start in sorted(selected):
            if start in visited:
                continue
            stack: list[tuple[str, int]] = [(start, 0)]
            visited.add(start)
            while stack:
                current, index = stack[-1]
                neighbours = adjacency[current]
                if index < len(neighbours):
                    stack[-1] = (current, index + 1)
                    neighbour = neighbours[index]
                    if neighbour not in visited:
                        visited.add(neighbour)
                        stack.append((neighbour, 0))
                else:
                    stack.pop()
                    finish.append(current)
        reverse: dict[str, list[str]] = {item: [] for item in selected}
        for item, neighbours in adjacency.items():
            for neighbour in neighbours:
                reverse[neighbour].append(item)
        components: list[tuple[str, ...]] = []
        assigned: set[str] = set()
        for start in reversed(finish):
            if start in assigned:
                continue
            component: list[str] = []
            stack = [start]
            assigned.add(start)
            while stack:
                current = stack.pop()
                component.append(current)
                for neighbour in sorted(reverse[current], reverse=True):
                    if neighbour not in assigned:
                        assigned.add(neighbour)
                        stack.append(neighbour)
            if len(component) > 1 or start in adjacency.get(start, ()):
                components.append(tuple(sorted(component)))
        return sorted(components)

    def snapshot(self) -> dict[str, Any]:
        entries = [node.to_dict() for node in self.all_versions()]
        base = {
            "schema": 1,
            "as_of": self.as_of,
            "version_map": self.version_map(),
            "content_hashes": self.content_hashes(),
            "definitions": entries,
        }
        base["snapshot_hash"] = stable_hash(base)
        return base


def definition_snapshot(registry: DefinitionRegistry) -> dict[str, Any]:
    return registry.snapshot()
