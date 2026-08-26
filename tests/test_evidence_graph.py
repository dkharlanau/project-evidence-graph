import unittest

from evidence_graph import build_report, impact, shortest_path, traceability, validate


class EvidenceGraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "DEC-1", "type": "decision"},
                {"id": "TEST-1", "type": "test"},
                {"id": "EVID-1", "type": "evidence"},
                {"id": "REQ-2", "type": "requirement"},
            ],
            "links": [
                {"from": "REQ-1", "to": "DEC-1", "type": "resolved_by"},
                {"from": "DEC-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"},
            ],
        }

    def test_validation(self):
        self.assertTrue(validate(self.graph)["valid"])

    def test_traceability_coverage(self):
        result = traceability(self.graph)
        self.assertEqual(result["requirements"], 2)
        self.assertEqual(result["requirements_without_tests"], ["REQ-2"])
        self.assertEqual(result["requirements_without_evidence"], ["REQ-2"])
        self.assertEqual(result["test_coverage"], 0.5)
        self.assertEqual(result["evidence_coverage"], 0.5)

    def test_path(self):
        self.assertEqual(shortest_path(self.graph, "REQ-1", "EVID-1"), ["REQ-1", "DEC-1", "TEST-1", "EVID-1"])

    def test_impact(self):
        result = impact(self.graph, "TEST-1")
        self.assertTrue(result["found"])
        self.assertEqual(result["upstream"], ["DEC-1", "REQ-1"])
        self.assertEqual(result["downstream"], ["EVID-1"])
        self.assertEqual(result["upstream_by_type"], {"decision": ["DEC-1"], "requirement": ["REQ-1"]})
        self.assertEqual(result["downstream_by_type"], {"evidence": ["EVID-1"]})

    def test_missing_impact_node(self):
        self.assertFalse(impact(self.graph, "MISSING")["found"])

    def test_broken_link(self):
        graph = dict(self.graph)
        graph["links"] = self.graph["links"] + [{"from": "REQ-2", "to": "MISSING"}]
        self.assertFalse(validate(graph)["valid"])

    def test_report(self):
        report = build_report(self.graph)
        self.assertTrue(report["validation"]["valid"])
        self.assertEqual(report["traceability"]["requirements"], 2)


if __name__ == "__main__":
    unittest.main()
