from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from indicator_registry.definitions.versions import (
    Change,
    DefinitionRegistry,
    version_key,
)
from indicator_registry.recalculation.plan import (
    COMPUTED,
    REUSED,
    WITHHELD,
    plan_recalculations,
)
from indicator_registry.statistics_office import Application, run, verify


ROOT = Path(__file__).resolve().parents[2]
VERSIONED = ROOT / "fixtures" / "versioned_acceptance.json"
NEXT = ROOT / "fixtures" / "versioned_next.json"


def fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entries(out: Path) -> dict[str, dict]:
    payload = json.loads((out / "definitions.json").read_text(encoding="utf-8"))
    return {item["identity"]: item for item in payload["entries"]}


class DefinitionRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = DefinitionRegistry.from_fixture(fixture(VERSIONED))

    def test_fixture_is_recognised_as_versioned(self):
        self.assertTrue(self.registry.versioned)
        self.assertEqual(self.registry.latest("gov-a").version, "2")
        self.assertEqual(self.registry.latest("gov-b").depends_on, ("gov-a",))

    def test_legacy_fixture_is_not_versioned(self):
        legacy = DefinitionRegistry.from_fixture(fixture(ROOT / "fixtures" / "acceptance.json"))
        self.assertFalse(legacy.versioned)

    def test_cycles_are_detected_and_ordered_deterministically(self):
        order, cycles = self.registry.topological_order(self.registry.latest_nodes())
        self.assertEqual([list(item) for item in cycles], [["gov-e"]])
        self.assertLess(order.index("gov-a"), order.index("gov-b"))
        self.assertLess(order.index("gov-b"), order.index("gov-c"))
        self.assertLess(order.index("gov-c"), order.index("gov-d"))
        self.assertEqual(order, self.registry.topological_order(self.registry.latest_nodes())[0])

    def test_affected_set_is_the_dependency_closure(self):
        self.assertEqual(self.registry.affected(), ("gov-a", "gov-b", "gov-c", "gov-d"))
        self.assertEqual(self.registry.propagate(["gov-b"]), ("gov-b", "gov-c", "gov-d"))

    def test_version_ordering_handles_decimal_versions(self):
        self.assertLess(version_key("2"), version_key("10"))
        self.assertLess(version_key("1.9"), version_key("1.10"))

    def test_snapshot_hash_is_stable(self):
        first = self.registry.snapshot()
        second = DefinitionRegistry.from_fixture(fixture(VERSIONED)).snapshot()
        self.assertEqual(first["snapshot_hash"], second["snapshot_hash"])

    def test_snapshot_hash_changes_when_a_definition_changes(self):
        base = self.registry.snapshot()["snapshot_hash"]
        changed = fixture(NEXT)
        self.assertNotEqual(base, DefinitionRegistry.from_fixture(changed).snapshot()["snapshot_hash"])


class RecalculationPlanTests(unittest.TestCase):
    def setUp(self):
        self.registry = DefinitionRegistry.from_fixture(fixture(VERSIONED))
        self.plan = plan_recalculations(self.registry)

    def test_order_is_dependency_first(self):
        order = self.plan["order"]
        self.assertLess(order.index("gov-a"), order.index("gov-b"))
        self.assertLess(order.index("gov-b"), order.index("gov-c"))
        self.assertLess(order.index("gov-c"), order.index("gov-d"))
        self.assertEqual(self.plan["recalculation_order"],
                         [item for item in order if item in self.plan["affected"]])

    def test_dependency_pins_follow_the_recalculated_version(self):
        entry = next(item for item in self.plan["entries"] if item["definition_id"] == "gov-b")
        self.assertEqual(entry["dependency_versions"], {"gov-a": "2"})
        self.assertIn("dependency_pin_advanced:gov-a:1->2", entry["messages"])

    def test_cycle_is_withheld_not_published(self):
        entries = {item["identity"]: item for item in self.plan["entries"]}
        self.assertEqual(entries["gov-e@1"]["status"], WITHHELD)
        self.assertIn("dependency_cycle", entries["gov-e@1"]["reasons"])
        self.assertIsNone(entries["gov-e@1"]["value"])
        self.assertEqual(entries["gov-e@1"]["alert"]["level"], "withheld")

    def test_downstream_of_cycle_is_withheld(self):
        entries = {item["identity"]: item for item in self.plan["entries"]}
        self.assertEqual(entries["gov-f@1"]["status"], WITHHELD)
        self.assertIn("dependency_cycle_downstream", entries["gov-f@1"]["reasons"])

    def test_unresolved_dependency_is_explained(self):
        entries = {item["identity"]: item for item in self.plan["entries"]}
        self.assertEqual(entries["gov-g@1"]["status"], WITHHELD)
        self.assertIn("unresolved_dependency", entries["gov-g@1"]["reasons"])

    def test_observation_window_shortfall_is_explained(self):
        entries = {item["identity"]: item for item in self.plan["entries"]}
        entry = entries["gov-h@1"]
        self.assertEqual(entry["status"], WITHHELD)
        self.assertIn("insufficient_observations", entry["reasons"])
        self.assertEqual(entry["window"]["window_days"], 90.0)
        self.assertEqual(entry["window"]["min_observations"], 3)

    def test_withheld_entries_have_no_numeric_alert(self):
        for entry in self.plan["entries"]:
            if entry["status"] == WITHHELD:
                self.assertIsNone(entry["value"])
                self.assertEqual(entry["alert"]["level"], "withheld")
                self.assertNotEqual(entry["alert"]["severity"], "info")

    def test_plan_is_deterministic(self):
        again = plan_recalculations(DefinitionRegistry.from_fixture(fixture(VERSIONED)))
        self.assertEqual(self.plan["entries"], again["entries"])
        self.assertEqual(self.plan["order"], again["order"])

    def test_unchanged_definition_can_be_reused(self):
        previous = {item["definition_id"]: item for item in self.plan["entries"]}
        next_registry = DefinitionRegistry.from_fixture(fixture(NEXT))
        next_plan = plan_recalculations(next_registry, previous=previous,
                                        previous_snapshot=self.registry.snapshot())
        statuses = {item["identity"]: item["status"] for item in next_plan["entries"]}
        self.assertEqual(statuses["gov-a@3"], COMPUTED)
        self.assertEqual(statuses["gov-b@1"], COMPUTED)
        self.assertEqual(next_plan["changed"], ["gov-a"])

    def test_reuse_requires_matching_observation_window(self):
        previous = {item["definition_id"]: item for item in self.plan["entries"]}
        changed = fixture(VERSIONED)
        for record in changed["records"]:
            if record["payload"]["definition_id"] == "gov-a" and record["payload"]["definition_version"] == "2":
                record["payload"]["observation_window_days"] = 30
        registry = DefinitionRegistry.from_fixture(changed)
        plan = plan_recalculations(registry, previous=previous, previous_snapshot=self.registry.snapshot())
        entry = next(item for item in plan["entries"] if item["definition_id"] == "gov-a")
        self.assertNotEqual(entry["status"], REUSED)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "registry.sqlite3"
        self.output = self.root / "out"

    def test_publishable_report_has_no_withheld_definitions(self):
        result = run(VERSIONED, self.database, self.output)
        self.assertFalse(result["publishable"])
        self.assertEqual(result["status"], "withheld")
        self.assertEqual({item["identity"] for item in result["not_computable"]},
                         {"gov-e@1", "gov-f@1", "gov-g@1", "gov-h@1"})

    def test_withheld_rows_never_carry_numbers(self):
        run(VERSIONED, self.database, self.output)
        with (self.output / "indicator_values.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        withheld = [row for row in rows if row["status"] == "withheld"]
        self.assertTrue(withheld)
        self.assertTrue(all(row["value"] == "" for row in withheld))
        self.assertTrue(all(row["alert_level"] == "withheld" for row in withheld))

    def test_alerts_and_values_share_the_same_definition_release(self):
        result = run(VERSIONED, self.database, self.output)
        with (self.output / "alerts.csv").open(encoding="utf-8") as handle:
            alerts = list(csv.DictReader(handle))
        self.assertTrue(alerts)
        self.assertTrue(all(row["definition_snapshot_hash"] == result["definition_snapshot_hash"]
                            for row in alerts))

    def test_alert_level_matches_the_published_value(self):
        run(VERSIONED, self.database, self.output)
        with (self.output / "alerts.csv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row["available"] == "True":
                    value = float(row["value"])
                    expected = ("superseded" if value >= 0.80 else "active" if value >= 0.60
                                else "validated" if value >= 0.40 else "drafted")
                    self.assertEqual(row["level"], expected)

    def test_verify_against_issued_definition(self):
        result = run(VERSIONED, self.database, self.output)
        checked = verify(self.database, self.output, report_id=result["report_id"])
        self.assertTrue(checked["ok"], checked["bundle_errors"])
        self.assertFalse(checked["historical"])

    def test_historical_report_stays_verifiable(self):
        first = run(VERSIONED, self.database, self.output)
        run(NEXT, self.database, self.root / "next")
        checked = verify(self.database, self.output, report_id=first["report_id"])
        self.assertTrue(checked["ok"], checked["bundle_errors"])
        self.assertTrue(checked["historical"])
        self.assertEqual(checked["version_map"]["gov-a"], "2")

    def test_new_release_is_not_historical(self):
        run(VERSIONED, self.database, self.output)
        run(NEXT, self.database, self.root / "next")
        checked = verify(self.database, self.root / "next")
        self.assertTrue(checked["ok"], checked["bundle_errors"])
        self.assertFalse(checked["historical"])
        self.assertEqual(checked["version_map"]["gov-a"], "3")

    def test_rerun_produces_identical_bundle(self):
        first = run(VERSIONED, self.database, self.output)
        snapshot = {path.name: path.read_bytes() for path in self.output.iterdir()}
        second = run(VERSIONED, self.database, self.output)
        again = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.assertEqual(first["report_id"], second["report_id"])
        self.assertEqual(snapshot, again)

    def test_tampering_with_a_published_value_is_detected(self):
        run(VERSIONED, self.database, self.output)
        path = self.output / "definitions.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload["entries"]:
            if entry["status"] != WITHHELD:
                entry["value"] = 0.99
                break
        path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
        checked = verify(self.database, self.output)
        self.assertFalse(checked["ok"])

    def test_tampering_with_an_export_alert_is_detected(self):
        run(VERSIONED, self.database, self.output)
        path = self.output / "alerts.csv"
        rows = path.read_text(encoding="utf-8").splitlines()
        for index, row in enumerate(rows):
            fields = row.split(",")
            if len(fields) > 8 and fields[5] == "True":
                fields[6] = "superseded"
                rows[index] = ",".join(fields)
                break
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        checked = verify(self.database, self.output)
        self.assertFalse(checked["ok"])

    def test_verify_rejects_bundle_for_a_different_issued_report(self):
        first = run(VERSIONED, self.database, self.output)
        run(NEXT, self.database, self.root / "next")
        checked = verify(self.database, self.root / "next", report_id=first["report_id"])
        self.assertFalse(checked["ok"])

    def test_unregistered_pin_never_falls_back(self):
        fixture_value = fixture(VERSIONED)
        for record in fixture_value["records"]:
            if record["payload"]["definition_id"] == "gov-b":
                record["payload"]["depends_on"] = ["gov-a"]
                record["payload"]["dependency_versions"] = {"gov-a": "9"}
        from indicator_registry.definitions.versions import DefinitionRegistry
        from indicator_registry.recalculation.plan import plan_recalculations
        plan = plan_recalculations(DefinitionRegistry.from_fixture(fixture_value))
        entry = next(item for item in plan["entries"] if item["definition_id"] == "gov-b")
        self.assertEqual(entry["status"], WITHHELD)
        self.assertIn("unresolved_dependency", entry["reasons"])

    def test_verify_rejects_a_value_from_a_stale_dependency(self):
        run(VERSIONED, self.database, self.output)
        path = self.output / "definitions.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload["entries"]:
            if entry["definition_id"] == "gov-b":
                entry["dependency_versions"] = {"gov-a": "1"}
        path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
        checked = verify(self.database, self.output)
        self.assertFalse(checked["ok"])
        self.assertTrue(any("gov-a@1" in error for error in checked["bundle_errors"]))

    def test_verify_rejects_registered_report_without_stored_snapshot(self):
        result = run(VERSIONED, self.database, self.output)
        import sqlite3
        with sqlite3.connect(self.database) as connection:
            connection.execute("DELETE FROM definition_snapshots")
        checked = verify(self.database, self.output, report_id=result["report_id"])
        self.assertFalse(checked["ok"])

    def test_inspect_exposes_reports_and_versions(self):
        result = run(VERSIONED, self.database, self.output)
        application = Application(self.database)
        inspected = application.inspect()
        self.assertEqual(inspected["reports"][0]["report_id"], result["report_id"])
        versions = application.versions("gov-a")
        self.assertEqual(versions["version_map"]["gov-a"], "2")
        self.assertEqual(len(versions["versions"]), 2)

    def test_legacy_fixture_keeps_its_bundle(self):
        result = run(ROOT / "fixtures" / "acceptance.json", self.database, self.output)
        self.assertEqual(result["records"], 8)
        self.assertEqual(set(result["manifest"]["files"]),
                         {"summary.json", "decisions.json", "audit-events.json"})
        self.assertTrue(verify(self.database, self.output)["ok"])


if __name__ == "__main__":
    unittest.main()
