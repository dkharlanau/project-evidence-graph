import unittest

from evidence_graph import shortest_path, validate
from graph_merge import merge_fragments


class GraphMergeTests(unittest.TestCase):
    def test_project_and_reconciliation_fragments_merge_with_bridge(self):
        project = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement"},
                {"id": "TEST-1", "type": "test"},
            ],
            "links": [{"from": "REQ-1", "to": "TEST-1", "type": "verified_by"}],
        }
        recon_ref = "eac://dkharlanau/reconciliation-as-code/reconciliation/customer/run/run-1"
        reconciliation = {
            "nodes": [{"id": recon_ref, "artifact_ref": recon_ref, "type": "evidence", "observed_at": "2026-08-26T10:00:00Z"}],
            "links": [],
            "reconciliation_import_diagnostics": {"valid": True, "errors": [], "duplicate_check_ids": []},
        }
        bridges = {"links": [{"from": "TEST-1", "to": recon_ref, "type": "produced"}]}
        merged = merge_fragments([("project", project), ("reconciliation", reconciliation)], bridges)
        self.assertTrue(merged["merge_diagnostics"]["valid"])
        self.assertTrue(validate(merged)["valid"])
        self.assertEqual(shortest_path(merged, "REQ-1", recon_ref), ["REQ-1", "TEST-1", recon_ref])
        self.assertIn("reconciliation", merged["merge_diagnostics"]["fragment_metadata"])

    def test_fragment_external_bridge_resolves_after_all_nodes_are_loaded(self):
        checkpoint_ref = "eac://dkharlanau/cutover-graph/checkpoint/reconcile"
        recon_ref = "eac://dkharlanau/reconciliation-as-code/reconciliation/customer/run/run-1"
        cutover = {
            "nodes": [{"id": checkpoint_ref, "type": "evidence"}],
            "links": [],
            "external_bridges": [{"from": checkpoint_ref, "to": recon_ref, "type": "substantiated_by"}],
            "cutover_import_diagnostics": {"valid": True},
        }
        reconciliation = {
            "nodes": [{"id": recon_ref, "type": "evidence"}],
            "links": [],
        }
        merged = merge_fragments([("cutover", cutover), ("reconciliation", reconciliation)])
        self.assertTrue(merged["merge_diagnostics"]["valid"])
        self.assertIn({"from": checkpoint_ref, "to": recon_ref, "type": "substantiated_by"}, merged["links"])
        self.assertNotIn("external_bridges", merged["merge_diagnostics"]["fragment_metadata"]["cutover"])

    def test_unresolved_fragment_external_bridge_fails(self):
        checkpoint_ref = "eac://dkharlanau/cutover-graph/checkpoint/reconcile"
        cutover = {
            "nodes": [{"id": checkpoint_ref, "type": "evidence"}],
            "links": [],
            "external_bridges": [{"from": checkpoint_ref, "to": "eac://dkharlanau/reconciliation-as-code/reconciliation/missing/run/1", "type": "substantiated_by"}],
        }
        merged = merge_fragments([("cutover", cutover)])
        self.assertFalse(merged["merge_diagnostics"]["valid"])
        finding = merged["merge_diagnostics"]["unresolved_bridges"][0]
        self.assertEqual(finding["source"], "fragment:cutover")
        self.assertTrue(finding["missing"])

    def test_identical_duplicate_node_collapses(self):
        node = {"id": "REQ-1", "type": "requirement", "title": "Same"}
        merged = merge_fragments([("a", {"nodes": [node], "links": []}), ("b", {"nodes": [dict(node)], "links": []})])
        self.assertTrue(merged["merge_diagnostics"]["valid"])
        self.assertEqual(len(merged["nodes"]), 1)
        self.assertEqual(merged["merge_diagnostics"]["identical_duplicate_nodes"][0]["id"], "REQ-1")

    def test_conflicting_duplicate_node_fails(self):
        merged = merge_fragments([
            ("a", {"nodes": [{"id": "REQ-1", "type": "requirement", "title": "A"}], "links": []}),
            ("b", {"nodes": [{"id": "REQ-1", "type": "requirement", "title": "B"}], "links": []}),
        ])
        self.assertFalse(merged["merge_diagnostics"]["valid"])
        self.assertEqual(merged["merge_diagnostics"]["conflicting_nodes"][0]["id"], "REQ-1")

    def test_unresolved_bridge_fails(self):
        merged = merge_fragments(
            [("a", {"nodes": [{"id": "REQ-1", "type": "requirement"}], "links": []})],
            {"links": [{"from": "REQ-1", "to": "MISSING", "type": "supports"}]},
        )
        self.assertFalse(merged["merge_diagnostics"]["valid"])
        self.assertEqual(merged["merge_diagnostics"]["unresolved_bridges"][0]["missing"], ["MISSING"])

    def test_output_is_independent_of_fragment_input_order(self):
        a = {"nodes": [{"id": "A", "type": "requirement"}], "links": []}
        b = {"nodes": [{"id": "B", "type": "test"}], "links": []}
        first = merge_fragments([("b", b), ("a", a)])
        second = merge_fragments([("a", a), ("b", b)])
        self.assertEqual(first, second)

    def test_conflicting_duplicate_link_fails(self):
        a = {"nodes": [{"id": "A", "type": "requirement"}, {"id": "B", "type": "test"}], "links": [{"from": "A", "to": "B", "type": "verified_by", "provenance": {"file": "a"}}]}
        b = {"nodes": [], "links": [{"from": "A", "to": "B", "type": "verified_by", "provenance": {"file": "b"}}]}
        merged = merge_fragments([("a", a), ("b", b)])
        self.assertFalse(merged["merge_diagnostics"]["valid"])
        self.assertEqual(len(merged["merge_diagnostics"]["conflicting_links"]), 1)


if __name__ == "__main__":
    unittest.main()
