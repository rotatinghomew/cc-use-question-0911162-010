from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from indicator_registry.definitions.contract import (
    ContractError,
    Decision,
    DomainRecord,
    RuleResult,
    records_from_fixture,
    stable_hash,
    utc_now,
)
from indicator_registry.definitions.versions import DefinitionRegistry
from indicator_registry.registry.indicator_store import Repository
from indicator_registry.recalculation.runner import advance_for_outcome, decide
from indicator_registry.recalculation.plan import plan_recalculations
from indicator_registry.comparison.decomposition import export_bundle, verify_bundle
from indicator_registry.comparison.publication import (
    export_versioned_bundle,
    report_id_for,
    verify_versioned_bundle,
)
from indicator_registry.formula.evaluator import derive_context

from indicator_registry.definition_signal.definition_quality import augment_context


class Application:
    def __init__(self, database: str | Path, context: Mapping[str, Any] | None = None):
        self.repository = Repository(database)
        self.context = dict(context or {})
        self.deterministic_time: str | None = None

    def ingest(self, record: DomainRecord) -> DomainRecord:
        current = self.repository.get_record(record.record_id)
        if current is None:
            self.repository.save_record(record)
            return record
        if current.fingerprint == record.fingerprint:
            return current
        replacement = DomainRecord(record.record_id, record.payload, current.state,
                                   current.version + 1, record.occurred_at, record.source)
        self.repository.save_record(replacement, expected_version=current.version)
        return replacement

    def process(self, record: DomainRecord, cyclic_indicators: set[str] | None = None) -> tuple[DomainRecord, Decision]:
        stored = self.ingest(record)
        context = dict(self.context)
        context.update(derive_context(stored, self.repository))
        context.update(augment_context(stored, self.repository, cyclic_indicators))
        if self.deterministic_time is not None:
            context["decided_at"] = self.deterministic_time
        if cyclic_indicators and self._is_cyclic(stored, cyclic_indicators):
            context["domain_severity"] = "critical"
        decision = decide(stored, context)
        self.repository.save_decision(decision)
        advanced = advance_for_outcome(stored, decision)
        if advanced.fingerprint != stored.fingerprint:
            self.repository.save_record(advanced, expected_version=stored.version)
        return advanced, decision

    @staticmethod
    def _is_cyclic(record: DomainRecord, cyclic_indicators: set[str]) -> bool:
        payload = record.payload
        identifier = str(payload.get("definition_id") or payload.get("indicator_id") or record.record_id)
        return identifier in cyclic_indicators

    # ------------------------------------------------------------------
    # Legacy record fixture (no definition version metadata)
    # ------------------------------------------------------------------
    def _run_legacy(self, records: list[DomainRecord], fixture_hash: str,
                    output: str | Path, run_id: str) -> dict[str, Any]:
        decisions: dict[str, Decision] = {}
        final_records: list[DomainRecord] = []
        for record in records:
            final_record, decision = self.process(record)
            final_records.append(final_record)
            decisions[record.record_id] = decision
        snapshot = self.repository.snapshot()
        if snapshot["chain_errors"]:
            raise ContractError("audit chain verification failed")
        manifest = export_bundle(output, final_records, decisions, snapshot, self.repository.event_rows())
        result = {"run_id": run_id, "fixture_hash": fixture_hash, "records": len(final_records),
                  "decisions": len(decisions), "manifest": manifest, "snapshot": snapshot}
        self.repository.finish_run(run_id, result)
        return result

    # ------------------------------------------------------------------
    # Versioned definition fixture
    # ------------------------------------------------------------------
    def _run_versioned(self, fixture: Mapping[str, Any], records: list[DomainRecord],
                       fixture_hash: str, output: str | Path) -> dict[str, Any]:
        as_of = self.context.get("as_of") or fixture.get("as_of")
        issued_at = fixture.get("issued_at") or (
            f"{as_of}T00:00:00+00:00" if as_of else utc_now())
        registry = DefinitionRegistry.from_fixture(fixture, as_of=as_of)
        snapshot = registry.snapshot()
        # Capture the release this run builds on *before* registering the new
        # one, so change detection compares against the right baseline.
        previous_snapshot = self.repository.current_definition_snapshot()
        snapshot_hash = self.repository.save_definition_snapshot(snapshot)

        # Versioned runs are reproducible: a fixture which does not carry an
        # explicit occurrence time uses the deterministic issue time so that
        # re-running the same definition release produces the same rows.
        raw_records = fixture.get("records") or []
        normalized: list[DomainRecord] = []
        for record, raw in zip(records, raw_records):
            occurred_at = raw.get("occurred_at") if isinstance(raw, Mapping) else None
            normalized.append(DomainRecord(record.record_id, record.payload, record.state,
                                           int(raw.get("version") or 1) if isinstance(raw, Mapping) else 1,
                                           str(occurred_at or issued_at), record.source))
        records = normalized

        run_id = self.repository.begin_run(fixture_hash, len(records))
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            return completed

        report_id = report_id_for(snapshot_hash, snapshot.get("version_map") or {})
        existing = self.repository.report(report_id)
        if existing is not None:
            stored = dict(existing.get("result") or {})
            stored.setdefault("report_id", report_id)
            stored.setdefault("definition_snapshot_hash", snapshot_hash)
            stored.setdefault("version_map", snapshot.get("version_map") or {})
            stored.setdefault("status", existing.get("status"))
            stored.setdefault("publishable", bool(existing.get("publishable")))
            stored["reused_report"] = True
            if not _bundle_intact(output):
                # The issued numbers are re-exported unchanged.  Only the audit
                # log grows, so the report is still the same definition release.
                self._export(output, fixture, records, fixture_hash, snapshot,
                             existing.get("plan") or {}, existing.get("decisions") or {},
                             issued_at=existing.get("issued_at") or issued_at)
            self.repository.finish_run(run_id, stored)
            return stored

        decisions: dict[str, Decision] = {}
        final_records: list[DomainRecord] = []
        _, cycles = registry.topological_order(registry.latest_nodes())
        cyclic_ids = {member for component in cycles for member in component}
        self.deterministic_time = issued_at
        try:
            for record in records:
                final_record, decision = self.process(record, cyclic_ids)
                final_records.append(final_record)
                decisions[record.record_id] = decision
        finally:
            self.deterministic_time = None

        plan = plan_recalculations(registry, previous=self.repository.prior_computations(),
                                   previous_snapshot=previous_snapshot,
                                   context=self.context, as_of=as_of)
        self.repository.save_computations(plan["entries"])
        self.repository.record_definition_changes(snapshot_hash, plan.get("changed") or [],
                                                  plan.get("change_details") or {})

        chain = self.repository.snapshot()["chain_errors"]
        if chain:
            raise ContractError("audit chain verification failed")
        publishable = plan["status"] == "complete" and not plan["withheld"]
        manifest = self._export(output, fixture, final_records, fixture_hash, snapshot, plan, decisions,
                                issued_at=issued_at)
        result = {
            "run_id": run_id,
            "fixture_hash": fixture_hash,
            "records": len(final_records),
            "decisions": len(decisions),
            "report_id": report_id,
            "definition_snapshot_hash": snapshot_hash,
            "version_map": snapshot.get("version_map") or {},
            "status": plan["status"],
            "publishable": publishable,
            "order": plan["order"],
            "recalculation_order": plan.get("recalculation_order") or [],
            "affected": plan["affected"],
            "changed": plan.get("changed") or [],
            "change_details": plan.get("change_details") or {},
            "cycles": plan["cycles"],
            "not_computable": plan.get("not_computable") or [],
            "unavailable": plan["unavailable"],
            "observation_windows": plan.get("observation_windows") or {},
            "manifest": manifest,
            "snapshot": self.repository.snapshot(),
        }
        report = {
            "report_id": report_id,
            "definition_snapshot_hash": snapshot_hash,
            "version_map": snapshot.get("version_map") or {},
            "status": plan["status"],
            "publishable": publishable,
            "output_path": str(output),
            "issued_at": issued_at,
            "result": result,
            "plan": plan,
            "decisions": {record_id: decision.as_dict() for record_id, decision in decisions.items()},
        }
        result["issued_at"] = report["issued_at"]
        self.repository.save_report(report)
        self.repository.finish_run(run_id, result)
        return result

    def _export(self, output: str | Path, fixture: Mapping[str, Any], records: list[DomainRecord],
                fixture_hash: str, snapshot: Mapping[str, Any], plan: Mapping[str, Any],
                decisions: Mapping[str, Any], *, issued_at: str | None = None) -> dict[str, Any]:
        decision_objects: dict[str, Decision] = {}
        for record_id, value in decisions.items():
            if isinstance(value, Decision):
                decision_objects[record_id] = value
                continue
            decision_objects[record_id] = _decision_from_dict(value)
        return export_versioned_bundle(
            output, records, decision_objects, plan, snapshot,
            self.repository.event_rows(), fixture_hash=fixture_hash, issued_at=issued_at)

    def run_fixture(self, fixture: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
        records = records_from_fixture(fixture)
        fixture_hash = stable_hash(fixture)
        registry = DefinitionRegistry.from_fixture(fixture, as_of=self.context.get("as_of") or fixture.get("as_of"))
        if registry.versioned:
            return self._run_versioned(fixture, records, fixture_hash, output)
        run_id = self.repository.begin_run(fixture_hash, len(records))
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            return completed
        return self._run_legacy(records, fixture_hash, output, run_id)

    def inspect(self) -> dict[str, Any]:
        return {"snapshot": self.repository.snapshot(),
                "records": [record.__dict__ for record in self.repository.list_records()],
                "decisions": self.repository.decision_rows(),
                "reports": self.repository.reports()}

    def versions(self, definition_id: str | None = None) -> dict[str, Any]:
        snapshot = self.repository.current_definition_snapshot()
        if snapshot is None:
            return {"ok": True, "versions": [], "version_map": {}, "snapshot_hash": None}
        definitions = snapshot.get("definitions") or []
        if definition_id:
            definitions = [item for item in definitions if item.get("definition_id") == definition_id]
        return {"ok": True, "snapshot_hash": snapshot.get("snapshot_hash"),
                "version_map": snapshot.get("version_map") or {},
                "versions": definitions,
                "reports": self.repository.reports()}


def _bundle_intact(output: str | Path) -> bool:
    return (Path(output) / "manifest.json").is_file() and not verify_bundle(output)


def _decision_from_dict(value: Mapping[str, Any]) -> Decision:
    rules = tuple(RuleResult(**{key: item for key, item in rule.items()
                                if key in RuleResult.__dataclass_fields__})
                  for rule in value.get("rules") or [])
    return Decision(record_id=value["record_id"], outcome=value["outcome"], score=value["score"],
                    reasons=tuple(value.get("reasons") or ()), rule_results=rules,
                    metrics=dict(value.get("metrics") or {}),
                    decided_at=value.get("decided_at") or utc_now())


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read fixture: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value


def run(fixture_path: str | Path, database: str | Path, output: str | Path,
        context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return Application(database, context).run_fixture(load_fixture(fixture_path), output)


def verify(database: str | Path, output: str | Path, report_id: str | None = None) -> dict[str, Any]:
    repository = Repository(database)
    chain_errors = repository.verify_chain()
    output_path = Path(output)

    issued = repository.report(report_id) if report_id else None
    if report_id and issued is None:
        return {"ok": False, "chain_errors": chain_errors,
                "bundle_errors": [f"report {report_id} is not registered"], "snapshot": repository.snapshot()}

    if (output_path / "definitions.json").is_file():
        bundle_snapshot = _snapshot_from_bundle(output_path) or {}
        bundle_hash = bundle_snapshot.get("snapshot_hash")
        stored = repository.definition_snapshot(bundle_hash) if bundle_hash else None
        if issued is not None:
            registered_snapshot = repository.definition_snapshot(issued["definition_snapshot_hash"])
            if registered_snapshot is not None and registered_snapshot.get("snapshot_hash") != bundle_hash:
                return {
                    "ok": False, "chain_errors": chain_errors,
                    "bundle_errors": [f"bundle does not belong to issued report {report_id}"],
                    "report_id": report_id, "historical": None,
                    "repository": repository.snapshot(),
                }
            stored = registered_snapshot
        current = repository.current_definition_snapshot()
        result = verify_versioned_bundle(
            output_path,
            stored_snapshot=stored,
            current_version_map=(current or {}).get("version_map") if current else None,
        )
        errors = list(chain_errors) + list(result["errors"])
        issued_report = repository.report(result.get("report_id") or "") if result.get("report_id") else None
        if issued_report is not None:
            if issued_report["definition_snapshot_hash"] != result.get("definition_snapshot_hash"):
                errors.append("report is not registered against this definition snapshot")
            if bool(issued_report.get("publishable")) != bool(result.get("publishable")):
                errors.append("report publishability does not match its registry entry")
            if issued_report.get("version_map") != result.get("version_map"):
                errors.append("report definition versions do not match its registry entry")
        return {
            "ok": not errors,
            "chain_errors": chain_errors,
            "bundle_errors": result["errors"],
            "report_id": result.get("report_id"),
            "definition_snapshot_hash": result.get("definition_snapshot_hash"),
            "version_map": result.get("version_map"),
            "status": result.get("status"),
            "publishable": result.get("publishable"),
            "historical": result.get("historical", False),
            "registered": issued_report is not None,
            "verified_against_issued_definition": True,
            "repository": repository.snapshot(),
        }

    bundle_errors = verify_bundle(output)
    return {"ok": not chain_errors and not bundle_errors, "chain_errors": chain_errors,
            "bundle_errors": bundle_errors, "snapshot": repository.snapshot()}


def _snapshot_from_bundle(output: Path) -> dict[str, Any] | None:
    path = output / "definitions.json"
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value.get("snapshot")
