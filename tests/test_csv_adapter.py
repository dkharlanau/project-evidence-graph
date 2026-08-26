import tempfile
import unittest
from pathlib import Path

from csv_adapter import build_graph
from evidence_graph import traceability, validate


class CsvAdapterTests(unittest.TestCase):
    def test_imports_artifacts_links_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "requirements.csv").write_text("ID,TITLE\nREQ-1,Replicate customer\n", encoding="utf-8")
            (base / "tests.csv").write_text("ID,TITLE\nTEST-1,Replication test\n", encoding="utf-8")
            (base / "links.csv").write_text("FROM,TO\nREQ-1,TEST-1\n", encoding="utf-8")
            manifest = {
                "artifact_sources": [
                    {"file": "requirements.csv", "id": "{ID}", "type": "requirement", "title": "{TITLE}"},
                    {"file": "tests.csv", "id": "{ID}", "type": "test", "title": "{TITLE}"},
                ],
                "link_sources": [
                    {"file": "links.csv", "from": "{FROM}", "to": "{TO}", "type": "verified_by"}
                ],
            }
            graph = build_graph(manifest, base)
            self.assertTrue(validate(graph)["valid"])
            self.assertEqual(graph["nodes"][0]["provenance"], {"file": "requirements.csv", "row": 2})
            self.assertEqual(graph["links"][0]["provenance"], {"file": "links.csv", "row": 2})
            self.assertEqual(traceability(graph)["test_coverage"], 1.0)

    def test_duplicate_ids_remain_visible_to_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "requirements.csv").write_text("ID\nREQ-1\nREQ-1\n", encoding="utf-8")
            graph = build_graph({"artifact_sources": [{"file": "requirements.csv", "id": "{ID}", "type": "requirement"}]}, base)
            result = validate(graph)
            self.assertFalse(result["valid"])
            self.assertEqual(result["duplicate_nodes"], ["REQ-1"])

    def test_missing_column_is_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "source.csv").write_text("ID\nREQ-1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing CSV column"):
                build_graph({"artifact_sources": [{"file": "source.csv", "id": "{MISSING}", "type": "requirement"}]}, base)


if __name__ == "__main__":
    unittest.main()
