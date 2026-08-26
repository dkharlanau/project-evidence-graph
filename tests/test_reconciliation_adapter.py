import unittest

from evidence_freshness import evaluate as evaluate_freshness
from evidence_graph import validate
from reconciliation_adapter import build_graph, validate_evidence


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def sample(status="passed", check_status="passed"):
    return {
        "schema_version": "1.0",
        "spec_version": 1,
        "engine_version": "0.3.0",
        "configuration_sha256": SHA_A,
        "run": {
            "id": "run-001",
            "started_at": "2026-08-26T09:59:00Z",
            "finished_at": "2026-08-26T10:00:00Z",
            "duration_ms": 60000,
            "python_version": "3.12",
            "platform": "linux"
        },
        "reconciliation": "customer-country",
        "status": status,
        "generated_at": "2026-08-26T10:00:01Z",
        "inputs": {
            "source": {"path": "legacy.csv", "sha256": SHA_B},
            "target": {"path": "s4.csv", "sha256": SHA_C}
        },
        "summary": {
            "source_records": 10,
            "target_records": 10,
            "matched_records": 10 if status == "passed" else 9,
            "missing_in_target": 0 if status == "passed" else 1,
            "unexpected_in_target": 0,
            "checks_total": 1,
            "checks_failed": 0 if check_status == "passed" else 1,
            "warnings_failed": 0
        },
        "checks": [
            {
                "id": "country-match",
                "type": "field_match",
                "severity": "error",
                "status": check_status,
                "metrics": {"mismatches": 0 if check_status == "passed" else 1},
                "details": [],
                "details_truncated": False
            }
        ]
    }


class ReconciliationAdapterTests(unittest.TestCase):
    def test_passed_run_and_check_are_evidence(self):
        graph = build_graph(sample())
        self.assertTrue(graph["reconciliation_import_diagnostics"]["valid"])
        self.assertEqual([node["type"] for node in graph["nodes"]], ["evidence", "evidence"])
        self.assertTrue(validate(graph)["valid"])
        self.assertTrue(graph["nodes"][0]["id"].startswith("eac://dkharlanau/reconciliation-as-code/reconciliation/customer-country/run/run-001"))

    def test_failed_run_and_check_are_defects(self):
        graph = build_graph(sample(status="failed", check_status="failed"))
        self.assertEqual([node["type"] for node in graph["nodes"]], ["defect", "defect"])
        self.assertNotIn("evidence", [node["type"] for node in graph["nodes"]])

    def test_generated_at_supports_freshness_policy(self):
        graph = build_graph(sample())
        result = evaluate_freshness(graph, {
            "as_of": "2026-08-27T10:00:00Z",
            "max_age_days": 2,
            "missing_timestamp": "fail"
        })
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["fresh"]), 2)

    def test_fingerprints_and_summary_preserved(self):
        graph = build_graph(sample())
        run = graph["nodes"][0]
        self.assertEqual(run["metadata"]["configuration_sha256"], SHA_A)
        self.assertEqual(run["metadata"]["inputs"]["source"]["sha256"], SHA_B)
        self.assertEqual(run["metadata"]["summary"]["matched_records"], 10)

    def test_duplicate_check_id_fails_validation(self):
        evidence = sample()
        evidence["checks"].append(dict(evidence["checks"][0]))
        result = validate_evidence(evidence)
        self.assertFalse(result["valid"])
        self.assertEqual(result["duplicate_check_ids"], ["country-match"])

    def test_invalid_sha_is_rejected(self):
        evidence = sample()
        evidence["configuration_sha256"] = "bad"
        result = validate_evidence(evidence)
        self.assertFalse(result["valid"])
        self.assertIn("configuration_sha256 must be lowercase SHA-256", result["errors"])


if __name__ == "__main__":
    unittest.main()
