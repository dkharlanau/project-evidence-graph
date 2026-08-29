import unittest

from evidence_lifecycle import evaluate, superseded_artifact_ids


class EvidenceLifecycleTests(unittest.TestCase):
    def base_graph(self):
        return {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "MAP-1", "type": "mapping", "changed_at": "2026-08-24T09:00:00Z"},
                {"id": "TEST-1", "type": "test"},
                {"id": "E-OLD", "type": "evidence", "observed_at": "2026-08-20T09:00:00Z"},
                {"id": "E-NEW", "type": "evidence", "observed_at": "2026-08-25T09:00:00Z"},
            ],
            "links": [
                {"from": "REQ-1", "to": "MAP-1", "type": "implemented_by"},
                {"from": "MAP-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "E-OLD", "type": "produced"},
                {"from": "TEST-1", "to": "E-NEW", "type": "produced"},
                {"from": "E-NEW", "to": "E-OLD", "type": "supersedes"},
            ],
        }

    def test_new_evidence_supersedes_old_and_restores_current_assurance(self):
        graph = self.base_graph()
        result = evaluate(graph)
        self.assertTrue(result["passed"])
        self.assertEqual(result["active_evidence"], ["E-NEW"])
        self.assertEqual(result["superseded_evidence"], ["E-OLD"])
        self.assertEqual(result["stale_by_change"], [])
        self.assertEqual(result["requirement_current_evidence"]["REQ-1"], ["E-NEW"])
        self.assertEqual(superseded_artifact_ids(graph, {"evidence"}), {"E-OLD"})

    def test_active_evidence_before_implementation_change_is_stale_by_change(self):
        graph = self.base_graph()
        graph["nodes"] = [node for node in graph["nodes"] if node["id"] != "E-NEW"]
        graph["links"] = [link for link in graph["links"] if "E-NEW" not in {link["from"], link["to"]}]
        result = evaluate(graph)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["stale_by_change"]), 1)
        self.assertEqual(result["stale_by_change"][0]["evidence"], "E-OLD")
        self.assertEqual(result["stale_by_change"][0]["implementation"], "MAP-1")
        self.assertEqual(result["requirements_without_current_evidence"], ["REQ-1"])
        self.assertIn("active_evidence_stale_by_change", result["failed_checks"])

    def test_missing_evidence_timestamp_after_change_is_unknown_and_fails_by_default(self):
        graph = self.base_graph()
        graph["nodes"] = [
            {key: value for key, value in node.items() if key != "observed_at"}
            if node["id"] == "E-NEW" else node
            for node in graph["nodes"]
        ]
        result = evaluate(graph)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["unknown_by_change"]), 1)
        self.assertEqual(result["unknown_by_change"][0]["evidence"], "E-NEW")
        self.assertIn("unknown_evidence_age_after_change", result["failed_checks"])

    def test_unknown_by_change_can_be_warning_by_policy(self):
        graph = self.base_graph()
        graph["nodes"] = [
            {key: value for key, value in node.items() if key != "observed_at"}
            if node["id"] == "E-NEW" else node
            for node in graph["nodes"]
        ]
        result = evaluate(graph, {"unknown_by_change": "warn"})
        self.assertTrue(result["passed"])
        self.assertIn("unknown_evidence_age_after_change", result["warnings"])

    def test_replacement_cycle_is_invalid(self):
        graph = self.base_graph()
        graph["links"].append({"from": "E-OLD", "to": "E-NEW", "type": "replaces"})
        result = evaluate(graph)
        self.assertFalse(result["passed"])
        self.assertFalse(result["lifecycle_valid"])
        self.assertTrue(any(error["kind"] == "replacement_cycle" for error in result["lifecycle_errors"]))

    def test_cross_type_replacement_is_invalid(self):
        graph = self.base_graph()
        graph["nodes"].append({"id": "DEC-NEW", "type": "decision"})
        graph["links"].append({"from": "DEC-NEW", "to": "E-NEW", "type": "supersedes"})
        result = evaluate(graph)
        self.assertFalse(result["lifecycle_valid"])
        self.assertTrue(any(error["kind"] == "cross_type_replacement" for error in result["lifecycle_errors"]))

    def test_decision_lifecycle_is_retained_without_affecting_evidence_state(self):
        graph = self.base_graph()
        graph["nodes"] += [
            {"id": "DEC-OLD", "type": "decision"},
            {"id": "DEC-NEW", "type": "decision"},
        ]
        graph["links"].append({"from": "DEC-NEW", "to": "DEC-OLD", "type": "replaces"})
        result = evaluate(graph)
        states = {item["artifact"]: item for item in result["artifact_states"]}
        self.assertFalse(states["DEC-OLD"]["active"])
        self.assertTrue(states["DEC-NEW"]["active"])
        self.assertEqual(result["active_evidence"], ["E-NEW"])


if __name__ == "__main__":
    unittest.main()
