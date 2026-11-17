from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from indicator_registry.definitions.contract import (
    Decision,
    DomainRecord,
    canonical_json,
    stable_hash,
    utc_now,
)
from indicator_registry.formula.evaluator import ALERT_FLOOR, ALERT_THRESHOLDS


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(body + "\n", encoding="utf-8")
    return stable_hash(value)


def write_records(path: Path, records: Iterable[DomainRecord], decisions: Mapping[str, Decision]) -> int:
    rows = []
    for record in records:
        decision = decisions.get(record.record_id)
        rows.append({"record_id": record.record_id, "state": record.state, "version": record.version,
                     "source": record.source, "fingerprint": record.fingerprint,
                     "outcome": decision.outcome if decision else "", "score": decision.score if decision else ""})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "state", "version", "source", "fingerprint", "outcome", "score"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_rules(path: Path, decisions: Mapping[str, Decision]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "code", "passed", "score", "severity", "message"])
        writer.writeheader()
        for record_id, decision in sorted(decisions.items()):
            for result in decision.rule_results:
                writer.writerow({"record_id": record_id, "code": result.code, "passed": result.passed,
                                 "score": result.score, "severity": result.severity, "message": result.message})
                count += 1
    return count


def build_summary(records: list[DomainRecord], decisions: Mapping[str, Decision], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    outcomes: dict[str, int] = {}
    for decision in decisions.values():
        outcomes[decision.outcome] = outcomes.get(decision.outcome, 0) + 1
    scores = [decision.score for decision in decisions.values()]
    return {"product": '人工智能治理指标口径版本与回算注册中心', "entity": 'indicator_definition', "generated_at": utc_now(),
            "record_count": len(records), "decision_count": len(decisions), "outcomes": outcomes,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "minimum_score": min(scores) if scores else 0.0, "maximum_score": max(scores) if scores else 0.0,
            "repository": snapshot}


def export_bundle(output: str | Path, records: list[DomainRecord], decisions: Mapping[str, Decision],
                  snapshot: Mapping[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    root = ensure_output(output)
    summary = build_summary(records, decisions, snapshot)
    record_count = write_records(root / "records.csv", records, decisions)
    rule_count = write_rules(root / "rules.csv", decisions)
    summary_hash = write_json(root / "summary.json", summary)
    decision_hash = write_json(root / "decisions.json", [value.as_dict() for _, value in sorted(decisions.items())])
    event_hash = write_json(root / "audit-events.json", events)
    manifest = {"files": {"summary.json": summary_hash, "decisions.json": decision_hash,
                           "audit-events.json": event_hash}, "record_rows": record_count,
                "rule_rows": rule_count, "created_at": utc_now()}
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


def verify_bundle(output: str | Path) -> list[str]:
    root = Path(output)
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return ["manifest.json is missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_hash = manifest.pop("manifest_hash", "")
    if stable_hash(manifest) != expected_manifest_hash:
        errors.append("manifest hash mismatch")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if stable_hash(value) != expected:
            errors.append(f"{name} hash mismatch")
    return errors


# ----------------------------------------------------------------------
# Versioned publication
# ----------------------------------------------------------------------
def report_id_for(snapshot_hash: str, version_map: Mapping[str, str],
                  fixture_hash: str | None = None) -> str:
    """Stable report identity for one published definition release.

    A re-run of the same definition snapshot and versions must produce the
    same report id; the fixture hash is intentionally *not* part of the
    identity because a re-run may legitimately carry a different audit log.
    """

    return stable_hash({"definition_snapshot_hash": snapshot_hash,
                        "version_map": dict(sorted(version_map.items()))})[:32]


def build_definition_summary(registry_snapshot: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    entries = list(plan.get("entries") or [])
    available = [entry for entry in entries if entry.get("available")]
    withheld = [entry for entry in entries if not entry.get("available")]
    alerts: dict[str, int] = {}
    for entry in entries:
        level = (entry.get("alert") or {}).get("level", "withheld")
        alerts[level] = alerts.get(level, 0) + 1
    return {
        "definition_snapshot_hash": registry_snapshot["snapshot_hash"],
        "version_map": dict(sorted((registry_snapshot.get("version_map") or {}).items())),
        "content_hashes": dict(sorted((registry_snapshot.get("content_hashes") or {}).items())),
        "status": plan.get("status"),
        "publishable": plan.get("status") == "complete" and not withheld,
        "definition_count": len(entries),
        "available_count": len(available),
        "withheld_count": len(withheld),
        "alerts": alerts,
        "unavailable": plan.get("unavailable") or [],
        "not_computable": plan.get("not_computable") or [],
        "cycles": plan.get("cycles") or [],
        "order": plan.get("order") or [],
        "recalculation_order": plan.get("recalculation_order") or [],
        "affected": plan.get("affected") or [],
        "changed": plan.get("changed") or [],
        "change_details": plan.get("change_details") or {},
        "observation_windows": plan.get("observation_windows") or {},
    }


def export_versioned_bundle(output: str | Path, records: list[DomainRecord],
                            decisions: Mapping[str, Decision], plan: Mapping[str, Any],
                            registry_snapshot: Mapping[str, Any], events: list[dict[str, Any]],
                            *, fixture_hash: str | None = None,
                            issued_at: str | None = None) -> dict[str, Any]:
    """Publish the definition snapshot and computed values together.

    Every definition gets a row in the numeric export; entries without a
    publishable value keep an empty value and also appear in
    ``unavailable.csv`` with their reasons, so a partial result can never
    look like a complete one.
    """

    root = ensure_output(output)
    summary = build_definition_summary(registry_snapshot, plan)
    report_id = report_id_for(registry_snapshot["snapshot_hash"], summary["version_map"], fixture_hash)
    snapshot_hash = registry_snapshot["snapshot_hash"]

    record_count = write_records(root / "records.csv", records, decisions)
    rule_count = write_rules(root / "rules.csv", decisions)

    available_rows: list[dict[str, Any]] = []
    unavailable_rows: list[dict[str, Any]] = []
    alert_rows: list[dict[str, Any]] = []
    for entry in plan.get("entries") or []:
        alert = entry.get("alert") or {}
        alert_rows.append({"definition_snapshot_hash": snapshot_hash,
                           "definition_id": entry["definition_id"], "version": entry["version"],
                           "indicator_id": entry["indicator_id"], "status": entry["status"],
                           "available": entry["available"], "level": alert.get("level"),
                           "severity": alert.get("severity"), "value": entry.get("value"),
                           "reasons": ";".join(entry.get("reasons") or [])})
        # Every definition gets a row in the value export.  Withheld entries
        # keep an empty value so a partial report can never look complete.
        available_rows.append({"definition_snapshot_hash": snapshot_hash,
                               "definition_id": entry["definition_id"], "version": entry["version"],
                               "indicator_id": entry["indicator_id"],
                               "value": "" if not entry["available"] else entry["value"],
                               "base_score": "" if not entry["available"] else entry.get("base_score"),
                               "status": entry["status"],
                               "alert_level": alert.get("level"), "alert_severity": alert.get("severity"),
                               "dependency_versions": canonical_json(entry.get("dependency_versions") or {}),
                               "window_days": (entry.get("window") or {}).get("window_days"),
                               "reasons": ";".join(entry.get("reasons") or [])})
        if not entry["available"]:
            unavailable_rows.append({"definition_snapshot_hash": snapshot_hash,
                                      "definition_id": entry["definition_id"], "version": entry["version"],
                                      "indicator_id": entry["indicator_id"],
                                      "reasons": ";".join(entry.get("reasons") or []),
                                      "messages": " | ".join(entry.get("messages") or [])})

    _write_csv(root / "indicator_values.csv", available_rows,
               ["definition_snapshot_hash", "definition_id", "version", "indicator_id", "value",
                "base_score", "status", "alert_level", "alert_severity", "dependency_versions",
                "window_days", "reasons"])
    _write_csv(root / "unavailable.csv", unavailable_rows,
               ["definition_snapshot_hash", "definition_id", "version", "indicator_id", "reasons", "messages"])
    _write_csv(root / "alerts.csv", alert_rows,
               ["definition_snapshot_hash", "definition_id", "version", "indicator_id", "status",
                "available", "level", "severity", "value", "reasons"])

    definition_export = {
        "report_id": report_id,
        "definition_snapshot_hash": registry_snapshot["snapshot_hash"],
        "version_map": summary["version_map"],
        "content_hashes": summary["content_hashes"],
        "status": plan.get("status"),
        "publishable": summary["publishable"],
        "order": summary["order"],
        "affected": summary["affected"],
        "cycles": summary["cycles"],
        "unavailable": summary["unavailable"],
        "entries": plan.get("entries") or [],
        "snapshot": registry_snapshot,
    }
    summary_hash = write_json(root / "summary.json", summary)
    definitions_hash = write_json(root / "definitions.json", definition_export)
    decision_hash = write_json(root / "decisions.json", [value.as_dict() for _, value in sorted(decisions.items())])
    event_hash = write_json(root / "audit-events.json", audit_projection(events))
    manifest = {
        "files": {"summary.json": summary_hash, "definitions.json": definitions_hash,
                  "decisions.json": decision_hash, "audit-events.json": event_hash},
        "csv_hashes": {
            "alerts.csv": _csv_content_hash(root / "alerts.csv"),
            "indicator_values.csv": _csv_content_hash(root / "indicator_values.csv"),
            "unavailable.csv": _csv_content_hash(root / "unavailable.csv"),
        },
        "record_rows": record_count,
        "rule_rows": rule_count,
        "report_id": report_id,
        "definition_snapshot_hash": registry_snapshot["snapshot_hash"],
        "version_map": summary["version_map"],
        "status": plan.get("status"),
        "publishable": summary["publishable"],
        "created_at": issued_at or utc_now(),
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


def _csv_content_hash(path: Path) -> str:
    with path.open(encoding="utf-8") as handle:
        return stable_hash(list(csv.DictReader(handle)))


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)


def audit_projection(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic projection of the audit log for publication.

    Wall-clock timestamps and per-event hashes make a re-run of the same
    definition version look different even when nothing changed.  The report
    publishes the auditable facts instead; the live chain stays in the
    database and is checked by ``verify``.
    """

    projected = []
    for event in events:
        projected.append({
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "aggregate_id": event.get("aggregate_id"),
            "aggregate_version": event.get("aggregate_version"),
            "payload": event.get("payload"),
        })
    return projected


def read_report(output: str | Path) -> dict[str, Any]:
    root = Path(output)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    definitions_path = root / "definitions.json"
    definitions = json.loads(definitions_path.read_text(encoding="utf-8")) if definitions_path.is_file() else {}
    return {"manifest": manifest, "definitions": definitions}


def verify_versioned_bundle(output: str | Path, *,
                            stored_snapshot: Mapping[str, Any] | None = None,
                            current_version_map: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Verify a bundle against the definition snapshot it was issued with.

    The bundle is always verified against its *own* embedded snapshot, so an
    already-issued historical report stays verifiable after definitions move
    on.  ``stale`` is reported separately when the bundle is not the newest
    definition snapshot in the database.
    """

    root = Path(output)
    errors = verify_bundle(root)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "errors": errors, "historical": False, "stale": None}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in (manifest.get("csv_hashes") or {}).items():
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
        elif _csv_content_hash(path) != expected:
            errors.append(f"{name} hash mismatch")
    definitions_path = root / "definitions.json"
    if not definitions_path.is_file():
        return {"ok": False, "errors": errors + ["definitions.json is missing"],
                "historical": False, "stale": None}
    definitions = json.loads(definitions_path.read_text(encoding="utf-8"))
    snapshot = definitions.get("snapshot") or {}
    snapshot_hash = definitions.get("definition_snapshot_hash")

    if snapshot.get("snapshot_hash") != snapshot_hash:
        errors.append("embedded definition snapshot hash mismatch")
    if manifest.get("definition_snapshot_hash") != snapshot_hash:
        errors.append("manifest definition snapshot hash mismatch")
    if manifest.get("version_map") != definitions.get("version_map"):
        errors.append("manifest definition versions do not match the report")

    snapshot_version_map = snapshot.get("version_map") or {}
    if definitions.get("version_map") != snapshot_version_map:
        errors.append("report definition versions do not match the issued snapshot")
    content_hashes = snapshot.get("content_hashes") or {}
    if definitions.get("content_hashes") != content_hashes:
        errors.append("report definition content hashes do not match the issued snapshot")

    if stored_snapshot is not None and stored_snapshot.get("snapshot_hash") != snapshot_hash:
        errors.append("issued snapshot is not registered in the database")
    elif stored_snapshot is None:
        errors.append("issued definition snapshot is not registered in the database")

    entries = definitions.get("entries") or []
    withheld_entries = [entry for entry in entries if entry.get("status") == "withheld"]
    if definitions.get("status") == "complete" and withheld_entries:
        errors.append("report claims to be complete but contains withheld definitions")
    if definitions.get("status") == "withheld" and definitions.get("publishable"):
        errors.append("report is withheld but marked publishable")
    if definitions.get("publishable") and withheld_entries:
        errors.append("publishable report contains withheld definitions")
    summary_path = root / "summary.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("definition_snapshot_hash") != snapshot_hash:
            errors.append("summary definition snapshot does not match the report")
        if summary.get("version_map") != definitions.get("version_map"):
            errors.append("summary definition versions do not match the report")
        if bool(summary.get("publishable")) != bool(definitions.get("publishable")):
            errors.append("summary publishable flag does not match the report")
    covered = {entry.get("definition_id") for entry in entries}
    missing_definitions = sorted(set(snapshot_version_map) - covered)
    unknown_definitions = sorted(covered - set(snapshot_version_map))
    if missing_definitions:
        errors.append("report is missing definitions from its snapshot: " + ", ".join(missing_definitions))
    if unknown_definitions:
        errors.append("report contains definitions not in its snapshot: " + ", ".join(unknown_definitions))
    for entry in entries:
        identity = f"{entry.get('definition_id')}@{entry.get('version')}"
        expected_version = snapshot_version_map.get(entry.get("definition_id"))
        if expected_version is not None and entry.get("version") != expected_version:
            errors.append(f"{identity} version does not match the issued snapshot")
        if entry.get("content_hash") != content_hashes.get(entry.get("definition_id")):
            errors.append(f"{identity} content hash does not match the issued definition")
        if entry.get("status") == "withheld" and entry.get("value") is not None:
            errors.append(f"{identity} is withheld but publishes a value")
        if entry.get("status") != "withheld" and entry.get("value") is None:
            errors.append(f"{identity} is available but has no value")
        for dependency_id, recorded_hash in (entry.get("dependency_hashes") or {}).items():
            expected_hash = content_hashes.get(dependency_id)
            if expected_hash is None:
                errors.append(f"{identity} has a dependency hash for {dependency_id}, "
                              f"which is not in the issued definition snapshot")
            elif expected_hash != recorded_hash:
                errors.append(f"{identity} was computed against an outdated definition of "
                              f"{dependency_id}")

        declared = (entry.get("dependency_versions") or {})
        for dependency_id, version in declared.items():
            expected = snapshot_version_map.get(dependency_id)
            if expected is None:
                errors.append(f"{identity} references {dependency_id}@{version}, "
                              f"which is not in the issued definition snapshot")
            elif expected != version:
                errors.append(f"{identity} references {dependency_id}@{version}, "
                              f"issued snapshot has {expected}")

        alert = entry.get("alert") or {}
        if entry.get("status") == "withheld":
            if alert.get("level") != "withheld":
                errors.append(f"{identity} withheld entry must not carry a numeric alert level")
        elif not isinstance(entry.get("value"), (int, float)):
            errors.append(f"{identity} alert cannot be derived from a non-numeric value")
        else:
            expected_level = _threshold_level(float(entry["value"]))
            if alert.get("level") != expected_level:
                errors.append(f"{identity} alert level does not match its own value")

    alerts_path = root / "alerts.csv"
    values_path = root / "indicator_values.csv"
    unavailable_path = root / "unavailable.csv"
    exported_withheld: set[tuple[str, str]] = set()
    if alerts_path.is_file() and values_path.is_file():
        with alerts_path.open(encoding="utf-8") as handle:
            alerts = list(csv.DictReader(handle))
        with values_path.open(encoding="utf-8") as handle:
            values = list(csv.DictReader(handle))
        for row in alerts + values:
            if row.get("definition_snapshot_hash") != snapshot_hash:
                errors.append(f"{row['definition_id']}@{row['version']} export row came from a "
                              f"different definition release")
                break
        alert_keys = {(row["definition_id"], row["version"]) for row in alerts}
        value_keys = {(row["definition_id"], row["version"]) for row in values}
        if not value_keys.issubset(alert_keys):
            errors.append("some published values are missing from the alert export")
        if value_keys != alert_keys:
            errors.append("alert export contains entries without a published value row")
        alert_by_key = {(row["definition_id"], row["version"]): row for row in alerts}
        for row in values:
            key = (row["definition_id"], row["version"])
            alert_row = alert_by_key.get(key) or {}
            if row.get("status") == "withheld":
                exported_withheld.add(key)
                if row.get("value") not in (None, ""):
                    errors.append(f"{row['definition_id']}@{row['version']} withheld entry publishes a value")
                if alert_row.get("level") != "withheld":
                    errors.append(f"{row['definition_id']}@{row['version']} withheld entry has a numeric alert")
                continue
            level = row.get("alert_level")
            threshold_level = _threshold_level(float(row["value"]))
            if level != threshold_level:
                errors.append(f"{row['definition_id']}@{row['version']} alert export disagrees with its value")
            if alert_row.get("level") != level:
                errors.append(f"{row['definition_id']}@{row['version']} alert exports disagree")
        for row in alerts:
            if row.get("available") == "False" and row.get("value") not in (None, ""):
                errors.append(f"{row['definition_id']}@{row['version']} unavailable entry publishes a value")

    expected_withheld = {(entry.get("definition_id"), entry.get("version"))
                         for entry in entries if entry.get("status") == "withheld"}
    if alerts_path.is_file() and exported_withheld != expected_withheld:
        errors.append("unavailable definitions are not fully listed in the exports")
    if unavailable_path.is_file():
        with unavailable_path.open(encoding="utf-8") as handle:
            listed = {(row["definition_id"], row["version"]) for row in csv.DictReader(handle)}
        if listed != expected_withheld:
            errors.append("unavailable.csv does not match the withheld definitions")
    elif expected_withheld:
        errors.append("unavailable.csv is missing while definitions are withheld")

    stale = None
    if current_version_map is not None and dict(current_version_map) != dict(snapshot_version_map):
        stale = True
    historical = bool(stale)
    return {"ok": not errors, "errors": errors, "report_id": definitions.get("report_id"),
            "definition_snapshot_hash": snapshot_hash, "version_map": snapshot_version_map,
            "publishable": bool(definitions.get("publishable")), "status": definitions.get("status"),
            "historical": historical, "stale": stale,
            "error_summary": _summarise(errors)}


def _summarise(errors: Sequence[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for error in errors:
        key = error.split(":", 1)[0].split(" ", 1)[0]
        summary[key] = summary.get(key, 0) + 1
    return dict(sorted(summary.items()))


def _threshold_level(value: float) -> str:
    for threshold, name in ALERT_THRESHOLDS:
        if value >= threshold:
            return name
    return ALERT_FLOOR
