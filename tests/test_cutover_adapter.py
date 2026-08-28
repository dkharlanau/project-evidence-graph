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
            "assurance": {
                "external_registry_supplied": True,
                "external_checkpoints": 1,
                "external_checkpoints_verified": 1,
                "passed": True,
            },
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
                        "native_passed": True,
                        "verification_mode": "external_registry",
                        "external_evidence_required": True,
                        "external_evidence_passed": True,
                        "verifications": [
                            {
                                "type": "reconciliation",
                                "ref": self.reconciliation_ref,
                                "verified": True,
                                "reason": "passed",
                                "status": "passed",
                                "document_sha256": "d" * 64,
                                "configuration_sha256": "c" * 64,
                                "observed_at": "2026-08-28T05:00:00Z",
                                "kind": "reconciliation-as-code-run",
                            }
                        ],
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
        self.assertTrue(graph["cutover_import_diagnostics"]["assurance_complete"])
        self.assertTrue(validate(graph)["valid"])
        nodes = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(nodes["eac://dkharlanau/cutover-graph/task/reconcile"]["type"], "change")
        checkpoint = nodes["eac://dkharlanau/cutover-graph/checkpoint/reconcile"]
        self.assertEqual(checkpoint["type"], "evidence")
        self.assertEqual(checkpoint["status"], "passed")
        self.assertTrue(checkpoint["metadata"]["assurance_passed"])
        self.assertEqual(checkpoint["metadata"]["assurance_mode"], "external_registry")
        self.assertEqual(checkpoint["metadata"]["evidence_refs"], [self.reconciliation_ref, "local/report.json"])
        verification = checkpoint["metadata"]["verifications"][0]
        self.assertEqual(verification["document_sha256"], "d" * 64)
        self.assertEqual(verification["configuration_sha256"], "c" * 64)
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

    def test_legacy_passed_external_checkpoint_without_verification_is_not_evidence(self):
        checkpoint = self.index["tasks"][1]["checkpoint"]
        checkpoint.pop("verification_mode")
        checkpoint.pop("external_evidence_passed")
        checkpoint.pop("verifications")
        graph = build_graph(self.index)
        node = next(item for item in graph["nodes"] if item["id"].endswith("/checkpoint/reconcile"))
        self.assertEqual(node["type"], "defect")
        self.assertEqual(node["status"], "unverified")
        self.assertFalse(node["metadata"]["assurance_passed"])
        self.assertEqual(node["metadata"]["assurance_mode"], "unverified_external")
        diagnostics = graph["cutover_import_diagnostics"]
        self.assertTrue(diagnostics["valid"])
        self.assertFalse(diagnostics["assurance_complete"])
        self.assertEqual(diagnostics["unverified_external_checkpoints"][0]["reason"], "missing_external_verification_metadata")
        self.assertEqual(graph["external_bridges"][0]["to"], self.reconciliation_ref)

    def test_incomplete_checkpoint_is_defect(self):
        checkpoint = self.index["tasks"][1]["checkpoint"]
        checkpoint["passed"] = False
        checkpoint["native_passed"] = False
        checkpoint["external_evidence_passed"] = False
        checkpoint["missing_approvals"] = ["business"]
        graph = build_graph(self.index)
        node = next(item for item in graph["nodes"] if item["id"].endswith("/checkpoint/reconcile"))
        self.assertEqual(node["type"], "defect")
        self.assertEqual(node["status"], "failed")

    def test_local_passed_checkpoint_keeps_native_semantics(self):
        checkpoint = self.index["tasks"][1]["checkpoint"]
        checkpoint["evidence_refs"] = ["local/report.json"]
        checkpoint.pop("verification_mode")
        checkpoint.pop("external_evidence_passed")
        checkpoint.pop("verifications")
        graph = build_graph(self.index)
        node = next(item for item in graph["nodes"] if item["id"].endswith("/checkpoint/reconcile"))
        self.assertEqual(node["type"], "evidence")
        self.assertEqual(node["status"], "passed")
        self.assertEqual(node["metadata"]["assurance_mode"], "native")
        self.assertTrue(graph["cutover_import_diagnostics"]["assurance_complete"])

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
