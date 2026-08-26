import unittest

from risk_assurance import evaluate


class RiskAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "nodes": [
                {"id": "REQ-H", "type": "requirement", "risk": "high"},
                {"id": "REQ-L1", "type": "requirement", "risk": "low"},
                {"id": "REQ-L2", "type": "requirement", "risk": "low"},
                {"id": "TEST-1", "type": "test"},
                {"id": "TEST-2", "type": "test"},
                {"id": "EVID-1", "type": "evidence"},
                {"id": "EVID-2", "type": "evidence"},
            ],
            "links": [
                {"from": "REQ-L1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"},
                {"from": "REQ-L2", "to": "TEST-2", "type": "verified_by"},
                {"from": "TEST-2", "to": "EVID-2", "type": "produced"},
            ],
        }

    def test_high_risk_gap_dominates_weighted_coverage(self):
        result = evaluate(self.graph, {})
        self.assertAlmostEqual(result["weighted_test_coverage"], 2 / 7)
        self.assertAlmostEqual(result["weighted_evidence_coverage"], 2 / 7)
        self.assertEqual(result["uncovered_test_risk_score"], 5.0)

    def test_policy_can_fail_on_weighted_threshold(self):
        result = evaluate(self.graph, {"min_weighted_test_coverage": 0.8})
        self.assertFalse(result["passed"])
        self.assertEqual(result["failed_checks"], ["weighted_test_coverage"])

    def test_custom_weights(self):
        result = evaluate(self.graph, {"risk_weights": {"high": 20, "low": 1}})
        self.assertAlmostEqual(result["weighted_test_coverage"], 2 / 22)

    def test_unknown_risk_is_explicit(self):
        self.graph["nodes"][0]["risk"] = "severe"
        result = evaluate(self.graph, {"require_known_risk": True})
        self.assertFalse(result["passed"])
        self.assertEqual(result["unknown_risks"], [{"requirement": "REQ-H", "risk": "severe"}])

    def test_missing_risk_uses_default_but_can_be_required(self):
        del self.graph["nodes"][0]["risk"]
        permissive = evaluate(self.graph, {"default_weight": 3})
        high = next(row for row in permissive["requirements"] if row["requirement"] == "REQ-H")
        self.assertEqual(high["weight"], 3.0)
        strict = evaluate(self.graph, {"require_known_risk": True})
        self.assertFalse(strict["passed"])

    def test_uncovered_risk_score_gate(self):
        result = evaluate(self.graph, {"max_uncovered_evidence_risk_score": 4})
        self.assertFalse(result["passed"])
        self.assertEqual(result["uncovered_evidence_risk_score"], 5.0)


if __name__ == "__main__":
    unittest.main()
