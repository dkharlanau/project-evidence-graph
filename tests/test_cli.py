import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import peg_cli


class UnifiedCliTests(unittest.TestCase):
    def test_help_lists_assurance_commands(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = peg_cli.main(["--help"])
        self.assertEqual(result, 0)
        self.assertIn("review", output.getvalue())
        self.assertIn("history", output.getvalue())
        self.assertIn("lifecycle", output.getvalue())
        self.assertIn("pack", output.getvalue())
        self.assertIn("import-relationship", output.getvalue())

    def test_analyze_dispatches_to_core(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = peg_cli.main(["analyze", "examples/customer-change.json"])
        self.assertEqual(result, 0)
        self.assertIn('"traceability"', output.getvalue())

    def test_path_dispatches_to_core(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = peg_cli.main(["path", "examples/customer-change.json", "REQ-001", "EVID-001"])
        self.assertEqual(result, 0)
        self.assertIn("REQ-001", output.getvalue())
        self.assertIn("EVID-001", output.getvalue())

    def test_relationship_import_dispatches_to_adapter(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = peg_cli.main(["import-relationship", "examples/relationship/artifact-index.json"])
        self.assertEqual(result, 0)
        self.assertIn('"external_source": "data-relationship-map"', output.getvalue())
        self.assertIn('"type": "defect"', output.getvalue())

    def test_lifecycle_dispatches_to_evaluator(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = peg_cli.main(["lifecycle", "examples/evidence-lifecycle.json"])
        self.assertEqual(result, 0)
        self.assertIn('"superseded_evidence"', output.getvalue())
        self.assertIn('"EVID-CUSTOMER-OLD"', output.getvalue())

    def test_unknown_command_fails_loudly(self):
        error = io.StringIO()
        with redirect_stderr(error):
            result = peg_cli.main(["unknown"])
        self.assertEqual(result, 2)
        self.assertIn("Unknown command", error.getvalue())


if __name__ == "__main__":
    unittest.main()
