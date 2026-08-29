import json
import unittest
from pathlib import Path

from evidence_graph import validate
from relationship_adapter import build_graph


FIXTURE = Path("examples/relationship/artifact-index.json")


class RelationshipAdapterTests(unittest.TestCase):
    def load_fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_policy_findings_import_as_defects_without_invalidating_contract(self):
        graph = build_graph(self.load_fixture())
        diagnostics = graph["relationship_import_diagnostics"]
        self.assertTrue(diagnostics["valid"])
        self.assertFalse(diagnostics["source_policy_passed"])
        self.assertEqual(len(graph["nodes"]), 6)
        self.assertEqual(len(graph["links"]), 7)

        findings = [node for node in graph["nodes"] if node["type"] == "defect"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["external_source"], "data-relationship-map")
        self.assertEqual(findings[0]["risk"], "high")
        self.assertEqual(findings[0]["metadata"]["actual"], 2)
        self.assertEqual(findings[0]["metadata"]["allowed"], 1)
        self.assertTrue(validate(graph)["valid"])

    def test_relationship_provenance_is_retained(self):
        graph = build_graph(self.load_fixture())
        relation_nodes = [
            node for node in graph["nodes"]
            if node["type"] == "evidence" and node["metadata"].get("relationship_type") == "mapped_to"
        ]
        self.assertEqual(len(relation_nodes), 2)
        self.assertEqual(
            relation_nodes[0]["metadata"]["provenance"]["file"],
            "customer-crosswalk.xlsx",
        )

    def test_wrong_repository_fails_loudly(self):
        index = self.load_fixture()
        index["repository"] = "someone/other-repo"
        graph = build_graph(index)
        self.assertFalse(graph["relationship_import_diagnostics"]["valid"])
        self.assertEqual(graph["nodes"], [])
        self.assertIn("repository_error", graph["relationship_import_diagnostics"])

    def test_unresolved_relationship_object_ref_is_invalid(self):
        index = self.load_fixture()
        index["relationships"][0]["to_ref"] = "eac://dkharlanau/data-relationship-map/object/MISSING"
        graph = build_graph(index)
        self.assertFalse(graph["relationship_import_diagnostics"]["valid"])
        self.assertEqual(len(graph["relationship_import_diagnostics"]["unresolved_object_refs"]), 1)

    def test_invalid_source_index_is_rejected(self):
        index = self.load_fixture()
        index["valid"] = False
        graph = build_graph(index)
        self.assertFalse(graph["relationship_import_diagnostics"]["valid"])
        self.assertEqual(graph["nodes"], [])
        self.assertEqual(graph["links"], [])


if __name__ == "__main__":
    unittest.main()
