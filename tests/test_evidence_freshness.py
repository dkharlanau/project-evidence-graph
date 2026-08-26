import unittest

from evidence_freshness import evaluate


class EvidenceFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "as_of": "2026-08-26T12:00:00Z",
            "max_age_days": 30,
            "missing_timestamp": "fail",
            "fail_on_stale": False,
            "fail_on_future": True,
            "min_fresh_evidence_coverage": 0.5,
        }

    def test_fresh_stale_and_requirement_coverage(self):
        graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "REQ-2", "type": "requirement"},
                {"id": "E1", "type": "evidence", "observed_at": "2026-08-20T12:00:00Z"},
                {"id": "E2", "type": "evidence", "observed_at": "2026-05-01T12:00:00Z"},
            ],
            "links": [
                {"from": "REQ-1", "to": "E1", "type": "verified_by"},
                {"from": "REQ-2", "to": "E2", "type": "verified_by"},
            ],
        }
        result = evaluate(graph, self.policy)
        self.assertTrue(result["passed"])
        self.assertEqual([item["evidence"] for item in result["fresh"]], ["E1"])
        self.assertEqual([item["evidence"] for item in result["stale"]], ["E2"])
        self.assertEqual(result["fresh_evidence_coverage"], 0.5)
        self.assertEqual(result["requirements_without_fresh_evidence"], ["REQ-2"])

    def test_strict_stale_policy_fails(self):
        graph = {
            "nodes": [{"id": "E1", "type": "evidence", "observed_at": "2026-01-01T00:00:00Z"}],
            "links": [],
        }
        result = evaluate(graph, dict(self.policy, fail_on_stale=True))
        self.assertFalse(result["passed"])
        self.assertIn("stale_evidence", result["failed_checks"])

    def test_missing_timestamp_can_fail_or_warn(self):
        graph = {"nodes": [{"id": "E1", "type": "evidence"}], "links": []}
        failed = evaluate(graph, self.policy)
        self.assertFalse(failed["passed"])
        self.assertIn("missing_evidence_timestamp", failed["failed_checks"])
        warned = evaluate(graph, dict(self.policy, missing_timestamp="warn"))
        self.assertTrue(warned["passed"])
        self.assertEqual(warned["warnings"], ["missing_evidence_timestamp"])

    def test_future_evidence_fails(self):
        graph = {
            "nodes": [{"id": "E1", "type": "evidence", "observed_at": "2026-08-27T00:00:00Z"}],
            "links": [],
        }
        result = evaluate(graph, self.policy)
        self.assertFalse(result["passed"])
        self.assertIn("future_evidence", result["failed_checks"])

    def test_timestamp_must_include_timezone(self):
        graph = {
            "nodes": [{"id": "E1", "type": "evidence", "observed_at": "2026-08-20T12:00:00"}],
            "links": [],
        }
        with self.assertRaisesRegex(ValueError, "timezone"):
            evaluate(graph, self.policy)

    def test_minimum_fresh_coverage_can_fail(self):
        graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "E1", "type": "evidence", "observed_at": "2026-05-01T12:00:00Z"},
            ],
            "links": [{"from": "REQ-1", "to": "E1", "type": "verified_by"}],
        }
        result = evaluate(graph, dict(self.policy, min_fresh_evidence_coverage=1.0))
        self.assertFalse(result["passed"])
        self.assertIn("fresh_evidence_coverage", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
