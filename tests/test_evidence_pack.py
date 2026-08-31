import json
import tempfile
import unittest
from pathlib import Path

from evidence_pack import build_pack, verify_pack


class EvidencePackTests(unittest.TestCase):
    def setUp(self):
        self.recon_ref = "eac://dkharlanau/reconciliation-as-code/reconciliation/customer/run/run-1"
        self.graph = {
            "nodes": [
                {"id": "REQ-1", "type": "requirement", "risk": "high", "title": "Requirement"},
                {"id": "TEST-1", "type": "test", "title": "Test"},
                {
                    "id": self.recon_ref,
                    "artifact_ref": self.recon_ref,
                    "type": "evidence",
                    "observed_at": "2026-08-26T10:00:00Z",
                    "metadata": {"configuration_sha256": "a" * 64},
                },
                {"id": "UNRELATED", "type": "change", "title": "Unrelated"},
            ],
            "links": [
                {"from": "REQ-1", "to": "TEST-1", "type": "verified_by"},
                {"from": "TEST-1", "to": self.recon_ref, "type": "verified_by_reconciliation"},
            ],
            "merge_diagnostics": {"valid": True},
        }
        self.quality = {"min_test_coverage": 1.0, "min_evidence_coverage": 1.0}
        self.freshness = {
            "as_of": "2026-08-27T10:00:00Z",
            "max_age_days": 30,
            "missing_timestamp": "fail",
            "min_fresh_evidence_coverage": 1.0,
        }
        self.risk = {
            "require_known_risk": True,
            "min_weighted_test_coverage": 1.0,
            "min_weighted_evidence_coverage": 1.0,
        }

    def test_builds_bounded_integrity_verifiable_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = build_pack(
                self.graph, tmp, focus="REQ-1", depth=2,
                quality_policy=self.quality, freshness_policy=self.freshness, risk_policy=self.risk,
                source_graph_sha256="f" * 64,
            )
            self.assertEqual(manifest["decision"], "PASS")
            self.assertTrue(manifest["passed"])
            self.assertEqual(manifest["scope"]["node_count"], 3)
            for name in ("graph.json", "context.json", "review.md", "review.html", "manifest.json"):
                self.assertTrue((Path(tmp) / name).exists())
            graph = json.loads((Path(tmp) / "graph.json").read_text())
            ids = [node["id"] for node in graph["nodes"]]
            self.assertNotIn("UNRELATED", ids)
            recon = next(node for node in graph["nodes"] if node["id"] == self.recon_ref)
            self.assertEqual(recon["artifact_ref"], self.recon_ref)
            self.assertEqual(recon["metadata"]["configuration_sha256"], "a" * 64)
            self.assertTrue(verify_pack(tmp)["valid"])

    def test_same_semantic_pack_has_same_pack_id(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = build_pack(self.graph, first, focus="REQ-1", depth=2, quality_policy=self.quality)
            b = build_pack(self.graph, second, focus="REQ-1", depth=2, quality_policy=self.quality)
            self.assertEqual(a["pack_id"], b["pack_id"])

    def test_lifecycle_assurance_is_retained_and_fingerprinted(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = build_pack(self.graph, tmp, focus="REQ-1", depth=2, lifecycle_enabled=True)
            context = json.loads((Path(tmp) / "context.json").read_text())
            self.assertTrue(context["assurance"]["lifecycle_policy"]["passed"])
            self.assertEqual(context["assurance"]["lifecycle_policy"]["active_evidence"], [self.recon_ref])
            self.assertIsNotNone(manifest["policy_fingerprints"]["lifecycle"])
            self.assertIn("Lifecycle valid", (Path(tmp) / "review.md").read_text())

    def test_modified_file_breaks_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_pack(self.graph, tmp, focus="REQ-1", depth=2)
            review = Path(tmp) / "review.md"
            review.write_text(review.read_text() + "\nmodified\n")
            result = verify_pack(tmp)
            self.assertFalse(result["valid"])
            self.assertIn("file integrity mismatch: review.md", result["errors"])

    def test_missing_file_breaks_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_pack(self.graph, tmp, focus="REQ-1", depth=2)
            (Path(tmp) / "context.json").unlink()
            result = verify_pack(tmp)
            self.assertFalse(result["valid"])
            self.assertIn("missing file: context.json", result["errors"])

    def test_fail_decision_still_builds_pack(self):
        failing = {"nodes": [{"id": "REQ-1", "type": "requirement", "risk": "critical"}], "links": []}
        with tempfile.TemporaryDirectory() as tmp:
            manifest = build_pack(
                failing, tmp, focus="REQ-1", depth=0,
                quality_policy={"min_test_coverage": 1.0, "min_evidence_coverage": 1.0},
            )
            self.assertEqual(manifest["decision"], "FAIL")
            self.assertFalse(manifest["passed"])
            self.assertTrue(verify_pack(tmp)["valid"])
            self.assertIn("Decision: FAIL", (Path(tmp) / "review.md").read_text())

    def test_semantic_graph_change_changes_pack_id(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = build_pack(self.graph, first, focus="REQ-1", depth=2)
            changed = json.loads(json.dumps(self.graph))
            changed["nodes"][0]["title"] = "Changed requirement"
            b = build_pack(changed, second, focus="REQ-1", depth=2)
            self.assertNotEqual(a["pack_id"], b["pack_id"])


if __name__ == "__main__":
    unittest.main()
