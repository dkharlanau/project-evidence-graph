import unittest

from assurance_diff import compare, render_markdown


class AssuranceDiffTests(unittest.TestCase):
    def setUp(self):
        self.before = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement", "risk": "high", "title": "Country must replicate"},
                {"id": "MAP-1", "type": "mapping", "title": "Country mapping v1", "metadata": {"version": "v1"}},
                {"id": "TEST-1", "type": "test"},
                {"id": "EVID-1", "type": "evidence", "observed_at": "2026-08-20T10:00:00Z"},
            ],
            "links": [
                {"from": "REQ-1", "to": "MAP-1", "type": "implemented_by"},
                {"from": "MAP-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"},
            ],
        }
        self.after = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement", "risk": "high", "title": "Country must replicate"},
                {"id": "MAP-1", "type": "mapping", "title": "Country mapping v2", "metadata": {"version": "v2"}},
                {"id": "TEST-1", "type": "test"},
                {"id": "EVID-1", "type": "evidence", "observed_at": "2026-08-20T10:00:00Z"},
            ],
            "links": [
                {"from": "REQ-1", "to": "MAP-1", "type": "implemented_by"},
                {"from": "MAP-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"},
            ],
        }

    def test_changed_mapping_same_id_is_detected(self):
        result = compare(self.before, self.after)
        self.assertEqual(result["implementation_drift"]["changed"], ["MAP-1"])
        changed = next(item for item in result["nodes"]["changed"] if item["id"] == "MAP-1")
        self.assertEqual(changed["changed_fields"], ["metadata", "title"])

    def test_upstream_requirement_becomes_refresh_candidate(self):
        result = compare(self.before, self.after)
        self.assertEqual(len(result["assurance_refresh_candidates"]), 1)
        candidate = result["assurance_refresh_candidates"][0]
        self.assertEqual(candidate["requirement"], "REQ-1")
        self.assertEqual(candidate["implementation_changes"], ["MAP-1"])
        self.assertEqual(candidate["current_tests"], ["TEST-1"])
        self.assertEqual(candidate["current_evidence"], ["EVID-1"])

    def test_removed_evidence_link_creates_new_evidence_gap(self):
        after = {"nodes": self.after["nodes"], "links": self.after["links"][:-1]}
        result = compare(self.before, after)
        self.assertEqual(result["coverage"]["new_evidence_gaps"], ["REQ-1"])
        self.assertEqual(result["links"]["removed"], [{"from": "TEST-1", "type": "produced", "to": "EVID-1"}])
        self.assertLess(result["coverage"]["delta"]["evidence_coverage"], 0)

    def test_policy_decision_pass_to_fail_is_explicit(self):
        after = {"nodes": self.after["nodes"], "links": self.after["links"][:-1]}
        quality = {"min_test_coverage": 1.0, "min_evidence_coverage": 1.0}
        result = compare(self.before, after, quality_policy=quality)
        delta = result["assurance"]["delta"]
        self.assertEqual(delta["decision_before"], "PASS")
        self.assertEqual(delta["decision_after"], "FAIL")
        self.assertTrue(delta["decision_changed"])

    def test_freshness_and_risk_deltas_are_included(self):
        freshness = {
            "as_of": "2026-08-26T12:00:00Z",
            "max_age_days": 30,
            "missing_timestamp": "fail"
        }
        risk = {"require_known_risk": True}
        result = compare(self.before, self.after, freshness_policy=freshness, risk_policy=risk)
        delta = result["assurance"]["delta"]
        self.assertIn("fresh_evidence_coverage_delta", delta)
        self.assertIn("weighted_test_coverage_delta", delta)
        self.assertEqual(delta["fresh_evidence_coverage_delta"], 0.0)

    def test_input_order_does_not_change_comparison(self):
        shuffled_before = {
            "nodes": list(reversed(self.before["nodes"])),
            "links": list(reversed(self.before["links"])),
        }
        shuffled_after = {
            "nodes": list(reversed(self.after["nodes"])),
            "links": list(reversed(self.after["links"])),
        }
        self.assertEqual(compare(self.before, self.after), compare(shuffled_before, shuffled_after))

    def test_markdown_surfaces_refresh_candidate(self):
        result = compare(self.before, self.after)
        text = render_markdown(result)
        self.assertIn("Implementation drift", text)
        self.assertIn("REQ-1", text)
        self.assertIn("MAP-1", text)
        self.assertIn("Assurance refresh candidates", text)


if __name__ == "__main__":
    unittest.main()
