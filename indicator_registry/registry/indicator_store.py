from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from indicator_registry.definitions.contract import Decision, DomainRecord, ContractError, canonical_json, stable_hash, utc_now


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS records(
    record_id TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS record_versions(
    record_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    stored_at TEXT NOT NULL,
    PRIMARY KEY(record_id, version)
);
CREATE TABLE IF NOT EXISTS decisions(
    decision_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    score REAL NOT NULL,
    decision_json TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    FOREIGN KEY(record_id) REFERENCES records(record_id)
);
CREATE TABLE IF NOT EXISTS events(
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    UNIQUE(aggregate_id, aggregate_version, event_type)
);
CREATE TABLE IF NOT EXISTS runs(
    run_id TEXT PRIMARY KEY,
    fixture_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS definition_snapshots(
    snapshot_hash TEXT PRIMARY KEY,
    version_map_json TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS computations(
    definition_id TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    value REAL,
    entry_json TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    PRIMARY KEY(definition_id, version, content_hash, snapshot_hash)
);
CREATE TABLE IF NOT EXISTS reports(
    report_id TEXT PRIMARY KEY,
    definition_snapshot_hash TEXT NOT NULL,
    version_map_json TEXT NOT NULL,
    status TEXT NOT NULL,
    publishable INTEGER NOT NULL,
    output_path TEXT,
    report_json TEXT NOT NULL,
    issued_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_state ON records(state, updated_at);
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, event_id);
CREATE INDEX IF NOT EXISTS idx_decisions_record ON decisions(record_id, decided_at);
CREATE INDEX IF NOT EXISTS idx_computations_identity ON computations(definition_id, version, computed_at);
CREATE INDEX IF NOT EXISTS idx_reports_snapshot ON reports(definition_snapshot_hash, issued_at);
"""


class Repository:
    def __init__(self, database: str | Path):
        self.database = str(database)
        self._lock = threading.RLock()
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            connection = self.connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def _last_hash(self, connection: sqlite3.Connection) -> str:
        row = connection.execute("SELECT event_hash FROM events ORDER BY event_id DESC LIMIT 1").fetchone()
        return row[0] if row else "0" * 64

    def append_event(self, connection: sqlite3.Connection, event_type: str,
                     aggregate_id: str, aggregate_version: int, payload: Mapping[str, Any]) -> str:
        previous = self._last_hash(connection)
        created_at = utc_now()
        event_hash = stable_hash({"event_type": event_type, "aggregate_id": aggregate_id,
                                  "aggregate_version": aggregate_version, "payload": payload,
                                  "previous_hash": previous, "created_at": created_at})
        try:
            connection.execute("INSERT INTO events(event_type,aggregate_id,aggregate_version,payload_json,previous_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?)",
                               (event_type, aggregate_id, aggregate_version, canonical_json(payload),
                                previous, event_hash, created_at))
        except sqlite3.IntegrityError:
            row = connection.execute("SELECT event_hash,payload_json FROM events WHERE aggregate_id=? AND aggregate_version=? AND event_type=?",
                                     (aggregate_id, aggregate_version, event_type)).fetchone()
            if row and row[1] == canonical_json(payload):
                return row[0]
            raise ContractError("conflicting event registry") from None
        return event_hash

    def save_record(self, record: DomainRecord, expected_version: int | None = None) -> str:
        with self.transaction() as connection:
            current = connection.execute("SELECT version,fingerprint FROM records WHERE record_id=?", (record.record_id,)).fetchone()
            if current and expected_version is not None and current[0] != expected_version:
                raise ContractError("optimistic version conflict")
            if current and current[1] == record.fingerprint:
                return record.fingerprint
            if current and record.version <= current[0]:
                raise ContractError("record version must advance")
            payload = canonical_json(record.payload)
            connection.execute("INSERT INTO records(record_id,version,state,payload_json,fingerprint,occurred_at,source,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(record_id) DO UPDATE SET version=excluded.version,state=excluded.state,payload_json=excluded.payload_json,fingerprint=excluded.fingerprint,occurred_at=excluded.occurred_at,source=excluded.source,updated_at=excluded.updated_at",
                               (record.record_id, record.version, record.state, payload, record.fingerprint,
                                record.occurred_at, record.source, utc_now()))
            connection.execute("INSERT INTO record_versions(record_id,version,state,payload_json,fingerprint,stored_at) VALUES(?,?,?,?,?,?)",
                               (record.record_id, record.version, record.state, payload, record.fingerprint, utc_now()))
            self.append_event(connection, "record.saved", record.record_id, record.version,
                              {"state": record.state, "fingerprint": record.fingerprint})
            return record.fingerprint

    def get_record(self, record_id: str) -> DomainRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM records WHERE record_id=?", (record_id,)).fetchone()
        if not row:
            return None
        return DomainRecord(record_id=row["record_id"], payload=json.loads(row["payload_json"]),
                            state=row["state"], version=row["version"], occurred_at=row["occurred_at"],
                            source=row["source"])

    def list_records(self, state: str | None = None) -> list[DomainRecord]:
        query = "SELECT * FROM records"
        params: tuple[Any, ...] = ()
        if state:
            query += " WHERE state=?"
            params = (state,)
        query += " ORDER BY record_id"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [DomainRecord(record_id=row["record_id"], payload=json.loads(row["payload_json"]),
                             state=row["state"], version=row["version"], occurred_at=row["occurred_at"],
                             source=row["source"]) for row in rows]

    def save_decision(self, decision: Decision) -> str:
        decision_id = decision.fingerprint
        with self.transaction() as connection:
            if not connection.execute("SELECT 1 FROM records WHERE record_id=?", (decision.record_id,)).fetchone():
                raise ContractError("decision record does not exist")
            body = canonical_json(decision.as_dict())
            connection.execute("INSERT OR IGNORE INTO decisions(decision_id,record_id,outcome,score,decision_json,decided_at) VALUES(?,?,?,?,?,?)",
                               (decision_id, decision.record_id, decision.outcome, decision.score, body, decision.decided_at))
            self.append_event(connection, "decision.saved", decision.record_id,
                              self.event_count(decision.record_id, connection) + 1,
                              {"decision_id": decision_id, "outcome": decision.outcome, "score": decision.score})
        return decision_id

    def event_count(self, aggregate_id: str, connection: sqlite3.Connection | None = None) -> int:
        owns = connection is None
        connection = connection or self.connect()
        try:
            row = connection.execute("SELECT COUNT(*) FROM events WHERE aggregate_id=?", (aggregate_id,)).fetchone()
            return int(row[0])
        finally:
            if owns:
                connection.close()

    def begin_run(self, fixture_hash: str, record_count: int) -> str:
        run_id = stable_hash({"fixture_hash": fixture_hash, "record_count": record_count})[:24]
        with self.transaction() as connection:
            row = connection.execute("SELECT fixture_hash,record_count FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if row and (row[0] != fixture_hash or row[1] != record_count):
                raise ContractError("run identifier collision")
            connection.execute("INSERT OR IGNORE INTO runs(run_id,fixture_hash,status,record_count,result_json,started_at) VALUES(?,?,?,?,?,?)",
                               (run_id, fixture_hash, "running", record_count, "{}", utc_now()))
        return run_id

    def completed_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT status,result_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row or row["status"] != "finished":
            return None
        result = json.loads(row["result_json"])
        if not isinstance(result, dict):
            raise ContractError("stored run result is invalid")
        return result

    def finish_run(self, run_id: str, result: Mapping[str, Any]) -> None:
        with self.transaction() as connection:
            changed = connection.execute("UPDATE runs SET status='finished',result_json=?,finished_at=? WHERE run_id=?",
                                         (canonical_json(result), utc_now(), run_id)).rowcount
            if changed != 1:
                raise ContractError("unknown run")
            self.append_event(connection, "run.finished", run_id, 1, dict(result))

    def verify_chain(self) -> list[str]:
        errors: list[str] = []
        previous = "0" * 64
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
        for row in rows:
            payload = json.loads(row["payload_json"])
            expected = stable_hash({"event_type": row["event_type"], "aggregate_id": row["aggregate_id"],
                                    "aggregate_version": row["aggregate_version"], "payload": payload,
                                    "previous_hash": row["previous_hash"], "created_at": row["created_at"]})
            if row["previous_hash"] != previous:
                errors.append(f"event {row['event_id']} previous hash mismatch")
            if row["event_hash"] != expected:
                errors.append(f"event {row['event_id']} content hash mismatch")
            previous = row["event_hash"]
        return errors

    def snapshot(self) -> dict[str, Any]:
        with self.connect() as connection:
            counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                      for table in ("records", "record_versions", "decisions", "events", "runs",
                                    "definition_snapshots", "computations", "reports")}
            states = {row[0]: row[1] for row in connection.execute("SELECT state,COUNT(*) FROM records GROUP BY state")}
        return {"counts": counts, "states": states, "chain_errors": self.verify_chain()}

    # ------------------------------------------------------------------
    # Definition versions, computations and issued reports
    # ------------------------------------------------------------------
    def save_definition_snapshot(self, snapshot: Mapping[str, Any]) -> str:
        snapshot_hash = str(snapshot["snapshot_hash"])
        body = canonical_json(snapshot)
        with self.transaction() as connection:
            row = connection.execute("SELECT snapshot_json FROM definition_snapshots WHERE snapshot_hash=?",
                                     (snapshot_hash,)).fetchone()
            if row and row[0] != body:
                raise ContractError("conflicting definition snapshot")
            connection.execute("INSERT OR IGNORE INTO definition_snapshots(snapshot_hash,version_map_json,snapshot_json,created_at) VALUES(?,?,?,?)",
                               (snapshot_hash, canonical_json(snapshot.get("version_map") or {}), body, utc_now()))
            self.append_event(connection, "definitions.snapshot", snapshot_hash, 1,
                              {"snapshot_hash": snapshot_hash, "version_map": snapshot.get("version_map") or {}})
        return snapshot_hash

    def definition_snapshot(self, snapshot_hash: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT snapshot_json FROM definition_snapshots WHERE snapshot_hash=?",
                                     (snapshot_hash,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_computations(self, entries: Sequence[Mapping[str, Any]]) -> int:
        saved = 0
        with self.transaction() as connection:
            for entry in entries:
                connection.execute(
                    "INSERT OR REPLACE INTO computations(definition_id,version,content_hash,snapshot_hash,status,value,entry_json,computed_at) VALUES(?,?,?,?,?,?,?,?)",
                    (entry["definition_id"], entry["version"], entry["content_hash"], entry["snapshot_hash"],
                     entry["status"], entry.get("value"), canonical_json(entry), utc_now()))
                saved += 1
            self.append_event(connection, "computations.saved", "recalculation",
                              self.event_count("recalculation", connection) + 1,
                              {"count": saved, "snapshot_hash": entries[0]["snapshot_hash"] if entries else None})
        return saved

    def record_definition_changes(self, snapshot_hash: str, changed: Sequence[str],
                                  details: Mapping[str, Mapping[str, str]] | None = None) -> None:
        if not changed:
            return
        with self.transaction() as connection:
            version = self.event_count("definitions", connection) + 1
            self.append_event(connection, "definitions.changed", "definitions", version,
                              {"snapshot_hash": snapshot_hash, "changed": list(changed),
                               "details": dict(sorted((details or {}).items()))})

    def computations_for(self, snapshot_hash: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT entry_json FROM computations WHERE snapshot_hash=? ORDER BY definition_id",
                                      (snapshot_hash,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def prior_computations(self) -> dict[str, dict[str, Any]]:
        """Latest stored computation per definition id (used for reuse)."""

        with self.connect() as connection:
            rows = connection.execute(
                "SELECT definition_id,entry_json FROM computations ORDER BY computed_at DESC, rowid DESC").fetchall()
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            result.setdefault(row[0], json.loads(row[1]))
        return result

    def save_report(self, report: Mapping[str, Any]) -> str:
        report_id = str(report["report_id"])
        with self.transaction() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO reports(report_id,definition_snapshot_hash,version_map_json,status,publishable,output_path,report_json,issued_at) VALUES(?,?,?,?,?,?,?,?)",
                (report_id, report["definition_snapshot_hash"],
                 canonical_json(report.get("version_map") or {}), report["status"],
                 1 if report.get("publishable") else 0, report.get("output_path"),
                 canonical_json(report), report["issued_at"]))
            self.append_event(connection, "report.issued", report_id, 1,
                              {"report_id": report_id, "status": report["status"],
                               "definition_snapshot_hash": report["definition_snapshot_hash"],
                               "publishable": bool(report.get("publishable"))})
        return report_id

    def report(self, report_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT report_json FROM reports WHERE report_id=?", (report_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def report_for_snapshot(self, snapshot_hash: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT report_json FROM reports WHERE definition_snapshot_hash=? ORDER BY issued_at, report_id LIMIT 1",
                (snapshot_hash,)).fetchone()
        return json.loads(row[0]) if row else None

    def reports(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT report_json FROM reports ORDER BY issued_at, report_id").fetchall()
        return [json.loads(row[0]) for row in rows]

    def current_definition_snapshot(self) -> dict[str, Any] | None:
        """Newest definition snapshot, used to flag an old report as historical."""

        with self.connect() as connection:
            row = connection.execute(
                "SELECT snapshot_hash FROM definition_snapshots ORDER BY created_at DESC, rowid DESC LIMIT 1").fetchone()
        return self.definition_snapshot(row[0]) if row else None

    def decision_rows(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT decision_json FROM decisions ORDER BY record_id,decided_at").fetchall()
        return [json.loads(row[0]) for row in rows]

    def event_rows(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
        return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in rows]
