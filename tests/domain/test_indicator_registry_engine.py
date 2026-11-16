from __future__ import annotations

import unittest
from indicator_registry.definitions.contract import DomainRecord
from indicator_registry.formula.evaluator import alert_level, delivery_risk, event_evaluator, station_signal


class WatermarkTests(unittest.TestCase):
    def record(self, key, water=5, age=5):
        return DomainRecord(key, {"indicator_id": key, "formula_complexity": 120, "unit_rank": water, "dependency_count": 900,
            "coverage_share": .4, "effective_days": 24, "source_age_days": age, "missing_policy": .9,
            "recalculation_delay": 2, "affected_members": 20000, "dimensions": 3, "validation_rate": .8})

    def test_evaluator_and_hysteresis(self):
        result = event_evaluator([self.record("a"), self.record("b", water=12)])
        self.assertGreater(result["risk"], 0.0)
        self.assertIn(alert_level(result), {"drafted", "validated", "active", "superseded"})
        self.assertGreater(station_signal(self.record("a")).freshness, station_signal(self.record("b", age=170)).freshness)

    def test_delivery_risk_is_bounded(self):
        self.assertTrue(0.0 <= delivery_risk(self.record("a")) <= 1.0)
