import unittest

from project_context import build_context


class ProjectContextTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement", "risk": "high", "title": "Requirement"},
                {"id": "MAP-1", "type": "mapping", "title": "Mapping"},
                {"id": "TEST-1", "type": "test", "title": "Test"},
                {"id": "EVID-1", "type": "evidence", "observed_at": "2026-08-20T10:00:00Z", "provenance": {"file": "test.json"}},
                {"id": "UNRELATED", "type": "change", "title": "Far away"},
            ],
            "links": [
                {"from": "REQ-1", "to": "MAP-1", "type": "implemented_by"},
                {"from": "MAP-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"},
            ],
        }

    def test_bounded_context_includes_upstream_and_downstream(self):
        context = build_context(self.graph, focus="MAP-1", depth=1)
        ids = [node["id"] for node in context["nodes"]]
        self.assertEqual(ids, ["MAP-1", "REQ-1", "TEST-1"])
        self.assertNotIn("EVID-1", ids)
        self.assertNotIn("UNRELATED", ids)

    def test_same_input_scope_has_stable_context_id(self):
        first = build_context(self.graph, focus="MAP-1", depth=2)
        second = build_context(self.graph, focus="MAP-1", depth=2)
        self.assertEqual(first["context_id"], second["context_id"])

    def test_different_depth_changes_context_id(self):
        first = build_context(self.graph, focus="MAP-1", depth=1)
        second = build_context(self.graph, focus="MAP-1", depth=2)
        self.assertNotEqual(first["context_id"], second["context_id"])

    def test_provenance_and_evidence_timestamp_are_preserved(self):
        context = build_context(self.graph, focus="TEST-1", depth=1)
        evidence = next(node for node in context["nodes"] if node["id"] == "EVID-1")
        self.assertEqual(evidence["observed_at"], "2026-08-20T10:00:00Z")
        self.assertEqual(evidence["provenance"], {"file": "test.json"})

    def test_cross_repo_ref_survives_unchanged(self):
        ref = "eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3"
        graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": ref, "artifact_ref": ref, "type": "mapping", "external": True},
            ],
            "links": [{"from": "REQ-1", "to": ref, "type": "implemented_by"}],
        }
        context = build_context(graph, focus="REQ-1", depth=1)
        self.assertEqual(context["scope"]["external_artifact_refs"], [ref])
        self.assertEqual(next(node for node in context["nodes"] if node["id"] == ref)["artifact_ref"], ref)

    def test_optional_assurance_is_embedded(self):
        quality = {"min_test_coverage": 1.0, "min_evidence_coverage": 1.0}
        context = build_context(self.graph, focus="TEST-1", depth=1, quality_policy=quality)
        self.assertIsNotNone(context["assurance"])
        self.assertTrue(context["assurance"]["quality_policy"]["passed"])

    def test_unknown_focus(self):
        context = build_context(self.graph, focus="MISSING", depth=2)
        self.assertFalse(context["found"])
        self.assertIsNone(context["context_id"])


if __name__ == "__main__":
    unittest.main()
