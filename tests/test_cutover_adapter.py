import unittest

from cutover_adapter import build_graph
from evidence_graph import validate


class CutoverAdapterTests(unittest.TestCase):
    def setUp(self):
        self.reconciliation_ref = "eac://dkharlanau/reconciliation-as-code/reconciliation/customer/run/run-1"
        self.index = {
            "schema_version": "0.1",
            "repository": "dkharlanau/cutover-graph",
            "valid": True,
            "validation": {"plan": {"valid": True}, "contingencies": {"valid": True}},
            "tasks": [
                {
                    "id": "load",
                    "artifact_ref": "eac://dkharlanau/cutover-graph/task/load",
                    "status": "done",
                    "complete": True,
                    "depends_on_refs": []
                },
                {
                    "id": "reconcile",
                    "artifact_ref": "eac://dkharlanau/cutover-graph/task/reconcile",
                    "status": "done",
                    "complete": True,
                    "owner": "data",
                    "workstream": "customer",
                    "risk": "high",
                    "depends_on_refs": ["eac://dkharlanau/cutover-graph/task/load"],
                    "checkpoint": {
                        "artifact_ref": "eac://dkharlanau/cutover-graph/checkpoint/reconcile",
                        "passed": True,
                        "missing_approvals": [],
                        "missing_evidence": [],
                        "duplicate_approvals": [],
                        "duplicate_evidence": [],
                        "required_approvals": ["business"],
                        "required_evidence": ["reconciliation"],
                        "evidence_refs": [self.reconciliation_ref, "local/report.json"]
                    }
                }
            ],
            "contingencies": [
                {
                    "id": "rollback",
                    "artifact_ref": "eac://dkharlanau/cutover-graph/contingency/rollback",
                    "active": False,
                    "activation": {"active": False, "mode": "any", "conditions": []},
                    "tasks": [
                        {
                            "id": "restore",
                            "artifact_ref": "eac://dkharlanau/cutover-graph/contingency/rollback/task/restore",
                            "status": "pending",
                            "depends_on_refs": []
                        }
                    ]
                }
            ]
        }

    def test_tasks_dependencies_and_checkpoint_semantics(self):
        graph = build_graph(self.index)
        self.assertTrue(graph["cutover_import_diagnostics"]["valid"])
        self.assertTrue(validate(graph)["valid"])
        nodes = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(nodes["eac://dkharlanau/cutover-graph/task/reconcile"]["type"], "change")
        checkpoint = nodes["eac://dkharlanau/cutover-graph/checkpoint/reconcile"]
        self.assertEqual(checkpoint["type"], "evidence")
        self.assertEqual(checkpoint["metadata"]["evidence_refs"], [self.reconciliation_ref, "local/report.json"])
        self.assertIn({
            "from": "eac://dkharlanau/cutover-graph/task/load",
            "to": "eac://dkharlanau/cutover-graph/task/reconcile",
            "type": "precedes"
        }, graph["links"])

    def test_eac_checkpoint_evidence_becomes_external_bridge_only(self):
        graph = build_graph(self.index)
        self.assertEqual(graph["external_bridges"], [{
            "from": "eac://dkharlanau/cutover-graph/checkpoint/reconcile",
            "to": self.reconciliation_ref,
            "type": "substantiated_by"
        }])
        ids = {node["id"] for node in graph["nodes"]}
        self.assertNotIn(self.reconciliation_ref, ids)
        self.assertNotIn("local/report.json", ids)

    def test_incomplete_checkpoint_is_defect(self):
        self.index["tasks"][1]["checkpoint"]["passed"] = False
        self.index["tasks"][1]["checkpoint"]["missing_approvals"] = ["business"]
        graph = build_graph(self.index)
        checkpoint = next(node for node in graph["nodes"] if node["id"].endswith("/checkpoint/reconcile"))
        self.assertEqual(checkpoint["type"], "defect")
        self.assertEqual(checkpoint["status"], "failed")

    def test_contingency_branch_and_task_are_separate_artifacts(self):
        graph = build_graph(self.index)
        nodes = {node["id"]: node for node in graph["nodes"]}
        branch_ref = "eac://dkharlanau/cutover-graph/contingency/rollback"
        task_ref = "eac://dkharlanau/cutover-graph/contingency/rollback/task/restore"
        self.assertEqual(nodes[branch_ref]["type"], "decision")
        self.assertEqual(nodes[task_ref]["type"], "change")
        self.assertIn({"from": branch_ref, "to": task_ref, "type": "contains_contingency_task"}, graph["links"])

    def test_invalid_source_index_is_rejected(self):
        self.index["valid"] = False
        graph = build_graph(self.index)
        self.assertFalse(graph["cutover_import_diagnostics"]["valid"])
        self.assertEqual(graph["nodes"], [])

    def test_invalid_artifact_ref_is_diagnostic(self):
        self.index["tasks"][0]["artifact_ref"] = "https://not-eac"
        graph = build_graph(self.index)
        self.assertFalse(graph["cutover_import_diagnostics"]["valid"])
        self.assertTrue(graph["cutover_import_diagnostics"]["invalid_refs"])


if __name__ == "__main__":
    unittest.main()
