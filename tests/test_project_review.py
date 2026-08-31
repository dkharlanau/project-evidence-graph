import unittest

from project_review import build_summary, render_html, render_markdown


class ProjectReviewTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement", "risk": "high"},
                {"id": "TEST-1", "type": "test"},
                {"id": "EVID-1", "type": "evidence", "observed_at": "2026-08-20T10:00:00Z"},
            ],
            "links": [
                {"from": "REQ-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"},
            ],
        }
        self.quality = {"min_test_coverage": 1, "min_evidence_coverage": 1}
        self.freshness = {
            "as_of": "2026-08-26T12:00:00Z",
            "max_age_days": 30,
            "missing_timestamp": "fail",
            "min_fresh_evidence_coverage": 1,
        }
        self.risk = {
            "require_known_risk": True,
            "min_weighted_test_coverage": 1,
            "min_weighted_evidence_coverage": 1,
        }

    def test_passing_consolidated_review(self):
        result = build_summary(self.graph, self.quality, self.freshness, self.risk)
        self.assertTrue(result["passed"])
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["freshness_policy"]["fresh_evidence_coverage"], 1.0)
        self.assertEqual(result["risk_policy"]["weighted_test_coverage"], 1.0)

    def test_failing_review_when_high_risk_requirement_uncovered(self):
        graph = {"nodes": self.graph["nodes"] + [{"id": "REQ-2", "type": "requirement", "risk": "critical"}], "links": self.graph["links"]}
        result = build_summary(graph, self.quality, self.freshness, self.risk)
        self.assertFalse(result["passed"])
        self.assertEqual(result["decision"], "FAIL")
        self.assertIn("REQ-2", result["raw_coverage"]["requirements_without_tests"])
        self.assertLess(result["risk_policy"]["weighted_test_coverage"], 1.0)

    def test_optional_policies_are_optional(self):
        result = build_summary(self.graph)
        self.assertTrue(result["passed"])
        self.assertIsNone(result["quality_policy"])
        self.assertIsNone(result["freshness_policy"])
        self.assertIsNone(result["risk_policy"])
        self.assertIsNone(result["lifecycle_policy"])

    def test_lifecycle_gate_fails_when_active_evidence_predates_change(self):
        graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "MAP-1", "type": "mapping", "changed_at": "2026-08-21T10:00:00Z"},
                {"id": "TEST-1", "type": "test"},
                {"id": "EVID-1", "type": "evidence", "observed_at": "2026-08-20T10:00:00Z"},
            ],
            "links": [
                {"from": "REQ-1", "to": "MAP-1", "type": "implemented_by"},
                {"from": "MAP-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"},
            ],
        }
        result = build_summary(graph, lifecycle_enabled=True)
        self.assertFalse(result["passed"])
        self.assertEqual(result["decision"], "FAIL")
        self.assertIn("active_evidence_stale_by_change", result["lifecycle_policy"]["failed_checks"])
        self.assertIn("Active evidence stale by change", render_markdown(result))

    def test_markdown_contains_distinct_coverage_signals(self):
        summary = build_summary(self.graph, self.quality, self.freshness, self.risk)
        text = render_markdown(summary)
        self.assertIn("Raw test coverage", text)
        self.assertIn("Fresh evidence coverage", text)
        self.assertIn("Risk-weighted test coverage", text)
        self.assertIn("Machine summary", text)

    def test_html_is_self_contained_review(self):
        summary = build_summary(self.graph, self.quality, self.freshness, self.risk)
        text = render_html(summary)
        self.assertIn("<!doctype html>", text)
        self.assertIn("Project Assurance Review", text)
        self.assertIn("PASS", text)
        self.assertIn("Machine summary", text)


if __name__ == "__main__":
    unittest.main()
