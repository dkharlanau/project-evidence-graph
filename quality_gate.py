#!/usr/bin/env python3
"""Policy gates for Project Evidence Graph reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_graph import build_report, load_graph


def load_policy(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        policy = json.load(handle)
    if not isinstance(policy, dict):
        raise ValueError("policy must be a JSON object")
    return policy


def evaluate(report: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    validation = report["validation"]
    trace = report["traceability"]
    checks = []

    def add(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({"name": name, "passed": passed, "actual": actual, "expected": expected})

    if policy.get("require_valid_graph", True):
        add("valid_graph", validation["valid"], validation["valid"], True)

    min_test = float(policy.get("min_test_coverage", 0.0))
    add("test_coverage", trace["test_coverage"] >= min_test, trace["test_coverage"], f">={min_test}")

    min_evidence = float(policy.get("min_evidence_coverage", 0.0))
    add("evidence_coverage", trace["evidence_coverage"] >= min_evidence, trace["evidence_coverage"], f">={min_evidence}")

    max_no_tests = policy.get("max_requirements_without_tests")
    if max_no_tests is not None:
        actual = len(trace["requirements_without_tests"])
        add("requirements_without_tests", actual <= int(max_no_tests), actual, f"<={int(max_no_tests)}")

    max_no_evidence = policy.get("max_requirements_without_evidence")
    if max_no_evidence is not None:
        actual = len(trace["requirements_without_evidence"])
        add("requirements_without_evidence", actual <= int(max_no_evidence), actual, f"<={int(max_no_evidence)}")

    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "failed_checks": [check["name"] for check in checks if not check["passed"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a project evidence graph against a quality policy")
    parser.add_argument("graph")
    parser.add_argument("policy")
    args = parser.parse_args()

    report = build_report(load_graph(args.graph))
    result = evaluate(report, load_policy(args.policy))
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
