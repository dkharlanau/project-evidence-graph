import unittest

from evidence_graph import validate
from workitem_adapter import DEFAULT_JIRA_PROFILE, build_graph


class WorkItemAdapterTests(unittest.TestCase):
    def test_jira_mapping_and_explicit_links(self):
        export = {
            "issues": [
                {
                    "key": "PRJ-1",
                    "self": "https://jira.example/rest/api/issue/PRJ-1",
                    "fields": {
                        "project": {"key": "PRJ"},
                        "issuetype": {"name": "Story"},
                        "summary": "Customer country requirement",
                        "status": {"name": "Done"},
                        "priority": {"name": "High"},
                        "updated": "2026-08-20T10:00:00+00:00",
                        "issuelinks": [
                            {
                                "type": {"name": "Blocks", "outward": "blocks", "inward": "is blocked by"},
                                "outwardIssue": {"key": "PRJ-2"}
                            }
                        ]
                    }
                },
                {
                    "key": "PRJ-2",
                    "fields": {
                        "project": {"key": "PRJ"},
                        "issuetype": {"name": "Bug"},
                        "summary": "Country replication defect",
                        "status": {"name": "Open"},
                        "issuelinks": []
                    }
                }
            ]
        }
        graph = build_graph(export, dict(DEFAULT_JIRA_PROFILE))
        self.assertEqual(graph["nodes"][0]["type"], "requirement")
        self.assertEqual(graph["nodes"][1]["type"], "defect")
        self.assertEqual(graph["nodes"][0]["risk"], "High")
        self.assertEqual(graph["links"], [{
            "from": "TRACKER:jira:PRJ:PRJ-1",
            "to": "TRACKER:jira:PRJ:PRJ-2",
            "type": "blocks"
        }])
        self.assertTrue(validate(graph)["valid"])

    def test_jira_unresolved_reference_is_diagnostic(self):
        export = {"issues": [{
            "key": "PRJ-1",
            "fields": {
                "project": {"key": "PRJ"},
                "issuetype": {"name": "Task"},
                "summary": "A",
                "status": {"name": "Open"},
                "issuelinks": [{
                    "type": {"outward": "blocks"},
                    "outwardIssue": {"key": "PRJ-99"}
                }]
            }
        }]}
        graph = build_graph(export, dict(DEFAULT_JIRA_PROFILE))
        self.assertEqual(graph["links"], [])
        self.assertEqual(graph["import_diagnostics"]["unresolved_references"][0]["target_external_id"], "PRJ-99")

    def test_generic_profile_for_alm_style_export(self):
        export = {"work_items": [
            {"id": "W1", "type": "requirement", "title": "Need reconciliation", "status": "done", "risk": "R3", "links": [{"target": "W2", "relation": "verified_by"}]},
            {"id": "W2", "type": "test", "title": "Reconciliation test", "status": "done", "risk": "R1", "links": []}
        ]}
        profile = {
            "source": "cloud-alm",
            "project_name": "TRANSFORM",
            "items_path": "work_items",
            "id": "id",
            "tracker_type": "type",
            "title": "title",
            "status": "status",
            "risk": "risk",
            "type_map": {"requirement": "requirement", "test": "test"},
            "default_artifact_type": "change",
            "links": {"path": "links", "target": "target", "type": "relation", "direction": "outward"}
        }
        graph = build_graph(export, profile)
        self.assertEqual(graph["nodes"][0]["id"], "TRACKER:cloud-alm:TRANSFORM:W1")
        self.assertEqual(graph["nodes"][0]["risk"], "R3")
        self.assertEqual(graph["links"][0]["type"], "verified_by")
        self.assertTrue(validate(graph)["valid"])

    def test_unknown_type_uses_explicit_default(self):
        export = {"work_items": [{"id": "1", "type": "mystery"}]}
        profile = {
            "source": "tracker",
            "items_path": "work_items",
            "id": "id",
            "tracker_type": "type",
            "default_artifact_type": "change"
        }
        graph = build_graph(export, profile)
        self.assertEqual(graph["nodes"][0]["type"], "change")

    def test_duplicate_external_id_is_reported(self):
        export = {"work_items": [{"id": "1"}, {"id": "1"}]}
        profile = {"source": "tracker", "items_path": "work_items", "id": "id"}
        graph = build_graph(export, profile)
        self.assertEqual(graph["import_diagnostics"]["duplicate_external_ids"], ["1"])


if __name__ == "__main__":
    unittest.main()
