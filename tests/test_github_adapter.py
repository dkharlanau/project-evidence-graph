import unittest

from evidence_graph import impact, validate
from github_adapter import build_graph


class GithubAdapterTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "label_type_map": {"requirement": "requirement", "bug": "defect"},
            "default_issue_type": "requirement",
            "pull_request_type": "change",
            "link_type_by_issue_type": {"requirement": "implemented_by", "defect": "fixed_by"},
        }
        self.export = {
            "repository": "acme/platform",
            "issues": [
                {"number": 1, "title": "Replicate country", "state": "closed", "labels": [{"name": "requirement"}]},
                {"number": 2, "title": "Retry loses country", "state": "closed", "labels": ["bug"]},
            ],
            "pull_requests": [
                {"number": 10, "title": "Retry-safe country", "state": "closed", "body": "Fixes #2 and implements #1; see also #999"}
            ],
        }

    def test_imports_nodes_explicit_links_and_unresolved_refs(self):
        graph = build_graph(self.export, self.config)
        self.assertTrue(validate(graph)["valid"])
        self.assertEqual(len(graph["nodes"]), 3)
        self.assertEqual(graph["links"], [
            {
                "from": "GH:acme/platform:ISSUE:1",
                "to": "GH:acme/platform:PR:10",
                "type": "implemented_by",
                "provenance": {"source": "explicit-github-reference", "pull_request": 10, "issue": 1},
            },
            {
                "from": "GH:acme/platform:ISSUE:2",
                "to": "GH:acme/platform:PR:10",
                "type": "fixed_by",
                "provenance": {"source": "explicit-github-reference", "pull_request": 10, "issue": 2},
            },
        ])
        self.assertEqual(graph["import_diagnostics"]["unresolved_issue_references"], [{"pull_request": 10, "issue": 999}])

    def test_imported_graph_supports_impact_analysis(self):
        graph = build_graph(self.export, self.config)
        result = impact(graph, "GH:acme/platform:PR:10")
        self.assertEqual(result["upstream_by_type"], {
            "defect": ["GH:acme/platform:ISSUE:2"],
            "requirement": ["GH:acme/platform:ISSUE:1"],
        })

    def test_linked_issues_array_is_explicit_reference(self):
        export = {
            "repository": "acme/platform",
            "issues": [{"number": 1, "title": "Requirement", "labels": ["requirement"]}],
            "pull_requests": [{"number": 10, "title": "Change", "linked_issues": [1]}],
        }
        graph = build_graph(export, self.config)
        self.assertEqual(len(graph["links"]), 1)

    def test_duplicate_issue_ids_remain_visible_to_validator(self):
        export = {
            "repository": "acme/platform",
            "issues": [
                {"number": 1, "title": "A", "labels": ["requirement"]},
                {"number": 1, "title": "B", "labels": ["requirement"]},
            ],
        }
        graph = build_graph(export, self.config)
        self.assertFalse(validate(graph)["valid"])
        self.assertEqual(validate(graph)["duplicate_nodes"], ["GH:acme/platform:ISSUE:1"])

    def test_repository_is_required(self):
        with self.assertRaisesRegex(ValueError, "repository"):
            build_graph({"issues": []}, self.config)


if __name__ == "__main__":
    unittest.main()
