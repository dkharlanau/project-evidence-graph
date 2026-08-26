#!/usr/bin/env python3
"""Risk-weighted assurance coverage for Project Evidence Graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_graph import load_graph, traceability


DEFAULT_WEIGHTS = {
    "r0": 1.0,
    "r1": 2.0,
    "r2": 4.0,
    "r3": 8.0,
    "r4": 16.0,
    "low": 1.0,
    "medium": 2.0,
    "high": 5.0,
    "critical": 10.0,
}


def load_policy(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        policy = json.load(handle)
    if not isinstance(policy, dict):
        raise ValueError("policy must be a JSON object")
    return policy


def _node_index(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(node.get("id")): node for node in graph.get("nodes", []) if str(node.get("id", "")).strip()}


def _risk_value(node: dict[str, Any], field: str) -> str:
    value = node.get(field)
    if value is None and isinstance(node.get("fields"), dict):
        value = node["fields"].get(field)
    return str(value).strip() if value is not None else ""


def evaluate(graph: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    trace = traceability(graph)
    nodes = _node_index(graph)
    risk_field = str(policy.get("risk_field", "risk"))
    weights = {key.lower(): float(value) for key, value in DEFAULT_WEIGHTS.items()}
    weights.update({str(key).lower(): float(value) for key, value in policy.get("risk_weights", {}).items()})
    default_weight = float(policy.get("default_weight", 1.0))
    require_known_risk = bool(policy.get("require_known_risk", False))

    rows = []
    unknown_risks = []
    total_weight = 0.0
    tested_weight = 0.0
    evidenced_weight = 0.0
    uncovered_test_risk_score = 0.0
    uncovered_evidence_risk_score = 0.0

    for item in trace["matrix"]:
        requirement = item["requirement"]
        node = nodes.get(requirement, {})
        raw_risk = _risk_value(node, risk_field)
        lookup = raw_risk.lower()
        known = lookup in weights
        weight = weights[lookup] if known else default_weight
        if raw_risk and not known:
            unknown_risks.append({"requirement": requirement, "risk": raw_risk})
        elif not raw_risk and require_known_risk:
            unknown_risks.append({"requirement": requirement, "risk": None})

        test_covered = bool(item.get("tests"))
        evidence_covered = bool(item.get("evidence"))
        total_weight += weight
        if test_covered:
            tested_weight += weight
        else:
            uncovered_test_risk_score += weight
        if evidence_covered:
            evidenced_weight += weight
        else:
            uncovered_evidence_risk_score += weight

        rows.append({
            "requirement": requirement,
            "risk": raw_risk or None,
            "risk_known": known if raw_risk else False,
            "weight": weight,
            "test_covered": test_covered,
            "evidence_covered": evidence_covered,
        })

    weighted_test_coverage = 1.0 if total_weight == 0 else tested_weight / total_weight
    weighted_evidence_coverage = 1.0 if total_weight == 0 else evidenced_weight / total_weight
    checks = []

    def add(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({"name": name, "passed": passed, "actual": actual, "expected": expected})

    if require_known_risk:
        add("known_requirement_risk", not unknown_risks, unknown_risks, [])

    min_test = policy.get("min_weighted_test_coverage")
    if min_test is not None:
        threshold = float(min_test)
        add("weighted_test_coverage", weighted_test_coverage >= threshold, weighted_test_coverage, f">={threshold}")

    min_evidence = policy.get("min_weighted_evidence_coverage")
    if min_evidence is not None:
        threshold = float(min_evidence)
        add("weighted_evidence_coverage", weighted_evidence_coverage >= threshold, weighted_evidence_coverage, f">={threshold}")

    max_test_risk = policy.get("max_uncovered_test_risk_score")
    if max_test_risk is not None:
        threshold = float(max_test_risk)
        add("uncovered_test_risk_score", uncovered_test_risk_score <= threshold, uncovered_test_risk_score, f"<={threshold}")

    max_evidence_risk = policy.get("max_uncovered_evidence_risk_score")
    if max_evidence_risk is not None:
        threshold = float(max_evidence_risk)
        add("uncovered_evidence_risk_score", uncovered_evidence_risk_score <= threshold, uncovered_evidence_risk_score, f"<={threshold}")

    return {
        "passed": all(check["passed"] for check in checks),
        "risk_field": risk_field,
        "total_weight": total_weight,
        "weighted_test_coverage": weighted_test_coverage,
        "weighted_evidence_coverage": weighted_evidence_coverage,
        "uncovered_test_risk_score": uncovered_test_risk_score,
        "uncovered_evidence_risk_score": uncovered_evidence_risk_score,
        "unknown_risks": unknown_risks,
        "requirements": rows,
        "checks": checks,
        "failed_checks": [check["name"] for check in checks if not check["passed"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate risk-weighted project assurance")
    parser.add_argument("graph")
    parser.add_argument("policy")
    args = parser.parse_args()
    result = evaluate(load_graph(args.graph), load_policy(args.policy))
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
