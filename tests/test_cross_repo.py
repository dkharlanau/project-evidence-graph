import unittest

from cross_repo import canonical_ref, materialize
from evidence_graph import shortest_path, traceability, validate


class CrossRepoTests(unittest.TestCase):
    def setUp(self):
        self.pack = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "TEST-1", "type": "test"},
                {"id": "EVID-1", "type": "evidence"},
            ],
            "external_artifacts": [
                {
                    "ref": "eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3",
                    "type": "mapping",
                    "title": "Customer country mapping",
                    "source": {"repository": "dkharlanau/mapping-as-code", "path": "examples/customer-country.yaml", "revision": "abc123"}
                },
                {
                    "ref": "eac://dkharlanau/interface-as-code/interface/mdg-s4/customer?version=v2",
                    "type": "interface",
                    "title": "MDG to S4 customer interface"
                }
            ],
            "links": [
                {"from": "REQ-1", "to_ref": "eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3", "type": "implemented_by"},
                {"from_ref": "eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3", "to_ref": "eac://dkharlanau/interface-as-code/interface/mdg-s4/customer?version=v2", "type": "used_by"},
                {"from_ref": "eac://dkharlanau/interface-as-code/interface/mdg-s4/customer?version=v2", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": "EVID-1", "type": "produced"}
            ]
        }

    def test_materialized_external_refs_work_with_traceability(self):
        graph = materialize(self.pack)
        self.assertTrue(validate(graph)["valid"])
        self.assertEqual(graph["cross_repo_diagnostics"], {
            "invalid_refs": [], "duplicate_refs": [], "invalid_link_refs": [], "unresolved_refs": []
        })
        path = shortest_path(graph, "REQ-1", "EVID-1")
        self.assertEqual(path[0], "REQ-1")
        self.assertIn("eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3", path)
        self.assertEqual(path[-1], "EVID-1")
        trace = traceability(graph)
        self.assertEqual(trace["test_coverage"], 1.0)
        self.assertEqual(trace["evidence_coverage"], 1.0)

    def test_source_location_is_metadata_not_identity(self):
        graph = materialize(self.pack)
        mapping = next(node for node in graph["nodes"] if node.get("type") == "mapping")
        self.assertEqual(mapping["id"], mapping["artifact_ref"])
        self.assertEqual(mapping["source"]["revision"], "abc123")
        self.assertNotIn("abc123", mapping["artifact_ref"])

    def test_duplicate_ref_diagnostic(self):
        self.pack["external_artifacts"].append(dict(self.pack["external_artifacts"][0]))
        graph = materialize(self.pack)
        self.assertEqual(graph["cross_repo_diagnostics"]["duplicate_refs"], [
            "eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3"
        ])

    def test_unresolved_ref_diagnostic(self):
        self.pack["links"].append({
            "from": "REQ-1",
            "to_ref": "eac://dkharlanau/cutover-graph/task/wave-3/missing-task",
            "type": "depends_on"
        })
        graph = materialize(self.pack)
        self.assertEqual(len(graph["cross_repo_diagnostics"]["unresolved_refs"]), 1)

    def test_invalid_ref_diagnostic(self):
        self.pack["external_artifacts"][0]["ref"] = "https://github.com/not-logical"
        graph = materialize(self.pack)
        self.assertEqual(len(graph["cross_repo_diagnostics"]["invalid_refs"]), 1)

    def test_canonicalizes_percent_encoding(self):
        self.assertEqual(
            canonical_ref("eac://dkharlanau/mapping-as-code/mapping/customer%20country"),
            "eac://dkharlanau/mapping-as-code/mapping/customer%20country"
        )


if __name__ == "__main__":
    unittest.main()
