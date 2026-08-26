#!/usr/bin/env python3
"""Evaluate evidence freshness and fresh-evidence requirement coverage."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_graph import _index, load_graph, reachable


def parse_iso(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid ISO-8601 timestamp: {value!r}") from exc
    if result.tzinfo is None:
        raise ValueError(f"timestamp must include timezone: {value!r}")
    return result.astimezone(timezone.utc)


def load_policy(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        policy = json.load(handle)
    if not isinstance(policy, dict):
        raise ValueError("policy must be a JSON object")
    return policy


def evaluate(graph: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if not policy.get("as_of"):
        raise ValueError("policy.as_of is required")
    as_of = parse_iso(str(policy["as_of"]))
    max_age_days = float(policy.get("max_age_days", 30))
    if max_age_days < 0:
        raise ValueError("max_age_days must be >= 0")
    timestamp_fields = [str(field) for field in policy.get("timestamp_fields", ["observed_at", "updated_at", "created_at"])]
    missing_mode = str(policy.get("missing_timestamp", "fail")).lower()
    if missing_mode not in {"fail", "warn", "ignore"}:
        raise ValueError("missing_timestamp must be one of: fail, warn, ignore")

    nodes, _ = _index(graph)
    evidence_ids = sorted(node_id for node_id, node in nodes.items() if node.get("type") == "evidence")
    fresh: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    future: list[dict[str, Any]] = []
    fresh_ids: set[str] = set()

    for evidence_id in evidence_ids:
        node = nodes[evidence_id]
        field = next((name for name in timestamp_fields if node.get(name)), None)
        if field is None:
            missing.append({"evidence": evidence_id, "checked_fields": timestamp_fields})
            continue
        timestamp = parse_iso(str(node[field]))
        age_days = (as_of - timestamp).total_seconds() / 86400
        item = {
            "evidence": evidence_id,
            "timestamp_field": field,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "age_days": round(age_days, 3),
        }
        if age_days < 0:
            future.append(item)
        elif age_days > max_age_days:
            stale.append(item)
        else:
            fresh.append(item)
            fresh_ids.add(evidence_id)

    requirements = sorted(node_id for node_id, node in nodes.items() if node.get("type") == "requirement")
    requirement_rows = []
    requirements_without_fresh_evidence = []
    for requirement_id in requirements:
        downstream = reachable(graph, requirement_id) - {requirement_id}
        all_evidence = sorted(node_id for node_id in downstream if node_id in evidence_ids)
        fresh_evidence = sorted(node_id for node_id in all_evidence if node_id in fresh_ids)
        if not fresh_evidence:
            requirements_without_fresh_evidence.append(requirement_id)
        requirement_rows.append({
            "requirement": requirement_id,
            "evidence": all_evidence,
            "fresh_evidence": fresh_evidence,
        })

    coverage = 1.0 if not requirements else (len(requirements) - len(requirements_without_fresh_evidence)) / len(requirements)
    min_coverage = float(policy.get("min_fresh_evidence_coverage", 0.0))
    fail_on_stale = bool(policy.get("fail_on_stale", False))
    fail_on_future = bool(policy.get("fail_on_future", True))

    failed_checks = []
    if coverage < min_coverage:
        failed_checks.append("fresh_evidence_coverage")
    if fail_on_stale and stale:
        failed_checks.append("stale_evidence")
    if fail_on_future and future:
        failed_checks.append("future_evidence")
    if missing_mode == "fail" and missing:
        failed_checks.append("missing_evidence_timestamp")

    return {
        "passed": not failed_checks,
        "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "max_age_days": max_age_days,
        "fresh": fresh,
        "stale": stale,
        "future": future,
        "missing_timestamp": missing,
        "fresh_evidence_coverage": coverage,
        "minimum_fresh_evidence_coverage": min_coverage,
        "requirements_without_fresh_evidence": requirements_without_fresh_evidence,
        "requirements": requirement_rows,
        "failed_checks": failed_checks,
        "warnings": ["missing_evidence_timestamp"] if missing_mode == "warn" and missing else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate evidence freshness and fresh-evidence coverage")
    parser.add_argument("graph")
    parser.add_argument("policy")
    args = parser.parse_args()
    result = evaluate(load_graph(args.graph), load_policy(args.policy))
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
