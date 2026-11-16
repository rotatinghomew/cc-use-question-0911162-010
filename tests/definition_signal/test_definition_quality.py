from __future__ import annotations
import json
import unittest
from pathlib import Path
from indicator_registry.definition_signal.definition_quality import definition_quality, peer_distribution

class Record:
    def __init__(self,payload): self.payload=payload

class DomainSignalTests(unittest.TestCase):
    def setUp(self):
        fixture=json.loads((Path(__file__).resolve().parents[2]/'fixtures'/'acceptance.json').read_text(encoding='utf-8'))
        self.payload=fixture['records'][0]['payload']
    def test_signal_is_bounded_and_explainable(self):
        signal=definition_quality(self.payload)
        self.assertGreaterEqual(signal.score,0.0); self.assertLessEqual(signal.score,1.0)
        self.assertIn(signal.severity,{'info','warning','critical'}); self.assertTrue(signal.evidence)
    def test_peer_distribution_tracks_records(self):
        other=dict(self.payload); other['indicator_family']='group-b'
        result=peer_distribution([Record(self.payload),Record(other)])
        self.assertEqual(result['count'],2)
    def test_input_change_is_observable(self):
        base=definition_quality(self.payload); changed=dict(self.payload)
        changed['cycle_count']=2
        changed_signal=definition_quality(changed)
        self.assertTrue(base.score != changed_signal.score or base.severity != changed_signal.severity)

if __name__=='__main__': unittest.main()
