import unittest

from evidence_graph import build_report
from quality_gate import evaluate


class QualityGateTests(unittest.TestCase):
    def setUp(self):
        graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "TEST-1", "type": "test"},
                {"id": "EVID-1", "type": "evidence"},
                {"id": "REQ-2", "type": "requirement"}
            ],
            "links": [
                {"from": "REQ-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"}
            ]
        }
        self.report = build_report(graph)

    def test_gate_passes_at_half_coverage(self):
        result = evaluate(self.report, {
            "require_valid_graph": True,
            "min_test_coverage": 0.5,
            "min_evidence_coverage": 0.5,
            "max_requirements_without_tests": 1,
            "max_requirements_without_evidence": 1
        })
        self.assertTrue(result["passed"])

    def test_gate_fails_when_strict(self):
        result = evaluate(self.report, {
            "require_valid_graph": True,
            "min_test_coverage": 1.0,
            "min_evidence_coverage": 1.0,
            "max_requirements_without_tests": 0,
            "max_requirements_without_evidence": 0
        })
        self.assertFalse(result["passed"])
        self.assertIn("test_coverage", result["failed_checks"])
        self.assertIn("evidence_coverage", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
