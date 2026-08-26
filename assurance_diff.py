#!/usr/bin/env python3
"""Compare historical Project Evidence Graph assurance and traceability state."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from evidence_freshness import load_policy as load_freshness_policy
from evidence_graph import _index, impact, load_graph, traceability, validate
from project_review import build_summary
from quality_gate import load_policy as load_quality_policy
from risk_assurance import load_policy as load_risk_policy


IMPLEMENTATION_TYPES = {"mapping", "interface", "change"}
RATIONALE_TYPES = {"requirement", "decision"}


def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    return sorted(key for key in set(before) | set(after) if _stable(before.get(key)) != _stable(after.get(key)))


def _link_key(link: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(link.get("from", "")),
        str(link.get("type", "supports")),
        str(link.get("to", "")),
    )


def _link_map(graph: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for link in graph.get("links", []):
        if isinstance(link, dict):
            result[_link_key(link)] = link
    return result


def _node_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_nodes, _ = _index(before)
    after_nodes, _ = _index(after)
    before_ids = set(before_nodes)
    after_ids = set(after_nodes)
    changed = []
    for node_id in sorted(before_ids & after_ids):
        if _stable(before_nodes[node_id]) != _stable(after_nodes[node_id]):
            changed.append({
                "id": node_id,
                "type_before": before_nodes[node_id].get("type"),
                "type_after": after_nodes[node_id].get("type"),
                "changed_fields": _changed_fields(before_nodes[node_id], after_nodes[node_id]),
            })
    return {
        "added": [{"id": node_id, "type": after_nodes[node_id].get("type")} for node_id in sorted(after_ids - before_ids)],
        "removed": [{"id": node_id, "type": before_nodes[node_id].get("type")} for node_id in sorted(before_ids - after_ids)],
        "changed": changed,
    }


def _link_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_links = _link_map(before)
    after_links = _link_map(after)
    before_keys = set(before_links)
    after_keys = set(after_links)
    changed = []
    for key in sorted(before_keys & after_keys):
        if _stable(before_links[key]) != _stable(after_links[key]):
            changed.append({
                "from": key[0],
                "type": key[1],
                "to": key[2],
                "changed_fields": _changed_fields(before_links[key], after_links[key]),
            })
    return {
        "added": [{"from": key[0], "type": key[1], "to": key[2]} for key in sorted(after_keys - before_keys)],
        "removed": [{"from": key[0], "type": key[1], "to": key[2]} for key in sorted(before_keys - after_keys)],
        "changed": changed,
    }


def _coverage_movement(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_trace = traceability(before)
    after_trace = traceability(after)
    before_test_gaps = set(before_trace["requirements_without_tests"])
    after_test_gaps = set(after_trace["requirements_without_tests"])
    before_evidence_gaps = set(before_trace["requirements_without_evidence"])
    after_evidence_gaps = set(after_trace["requirements_without_evidence"])
    return {
        "before": {
            "requirements": before_trace["requirements"],
            "test_coverage": before_trace["test_coverage"],
            "evidence_coverage": before_trace["evidence_coverage"],
        },
        "after": {
            "requirements": after_trace["requirements"],
            "test_coverage": after_trace["test_coverage"],
            "evidence_coverage": after_trace["evidence_coverage"],
        },
        "delta": {
            "test_coverage": after_trace["test_coverage"] - before_trace["test_coverage"],
            "evidence_coverage": after_trace["evidence_coverage"] - before_trace["evidence_coverage"],
        },
        "new_test_gaps": sorted(after_test_gaps - before_test_gaps),
        "resolved_test_gaps": sorted(before_test_gaps - after_test_gaps),
        "new_evidence_gaps": sorted(after_evidence_gaps - before_evidence_gaps),
        "resolved_evidence_gaps": sorted(before_evidence_gaps - after_evidence_gaps),
    }


def _typed_drift(node_diff: dict[str, Any], types: set[str]) -> dict[str, list[str]]:
    added = sorted(item["id"] for item in node_diff["added"] if item.get("type") in types)
    removed = sorted(item["id"] for item in node_diff["removed"] if item.get("type") in types)
    changed = sorted(
        item["id"]
        for item in node_diff["changed"]
        if item.get("type_before") in types or item.get("type_after") in types
    )
    return {"added": added, "removed": removed, "changed": changed}


def _refresh_candidates(
    before: dict[str, Any],
    after: dict[str, Any],
    implementation_drift: dict[str, list[str]],
) -> list[dict[str, Any]]:
    before_nodes, _ = _index(before)
    after_nodes, _ = _index(after)
    changed_impl = sorted(set(implementation_drift["added"] + implementation_drift["removed"] + implementation_drift["changed"]))
    requirement_triggers: dict[str, set[str]] = defaultdict(set)

    for artifact_id in changed_impl:
        if artifact_id in after_nodes:
            for requirement in impact(after, artifact_id).get("upstream_by_type", {}).get("requirement", []):
                requirement_triggers[requirement].add(artifact_id)
        if artifact_id in before_nodes:
            for requirement in impact(before, artifact_id).get("upstream_by_type", {}).get("requirement", []):
                requirement_triggers[requirement].add(artifact_id)

    after_trace = {row["requirement"]: row for row in traceability(after)["matrix"]}
    rows = []
    for requirement in sorted(requirement_triggers):
        current = after_trace.get(requirement)
        rows.append({
            "requirement": requirement,
            "implementation_changes": sorted(requirement_triggers[requirement]),
            "requirement_present_after": requirement in after_nodes and after_nodes[requirement].get("type") == "requirement",
            "current_tests": current.get("tests", []) if current else [],
            "current_evidence": current.get("evidence", []) if current else [],
            "reason": "linked implementation changed; review whether existing tests/evidence must be refreshed",
        })
    return rows


def _assurance_delta(before_summary: dict[str, Any], after_summary: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "decision_before": before_summary["decision"],
        "decision_after": after_summary["decision"],
        "decision_changed": before_summary["decision"] != after_summary["decision"],
        "raw_test_coverage_delta": after_summary["raw_coverage"]["test_coverage"] - before_summary["raw_coverage"]["test_coverage"],
        "raw_evidence_coverage_delta": after_summary["raw_coverage"]["evidence_coverage"] - before_summary["raw_coverage"]["evidence_coverage"],
    }
    before_fresh = before_summary.get("freshness_policy")
    after_fresh = after_summary.get("freshness_policy")
    if before_fresh is not None and after_fresh is not None:
        result["fresh_evidence_coverage_delta"] = after_fresh["fresh_evidence_coverage"] - before_fresh["fresh_evidence_coverage"]
        result["stale_evidence_count_delta"] = len(after_fresh["stale"]) - len(before_fresh["stale"])
    before_risk = before_summary.get("risk_policy")
    after_risk = after_summary.get("risk_policy")
    if before_risk is not None and after_risk is not None:
        result["weighted_test_coverage_delta"] = after_risk["weighted_test_coverage"] - before_risk["weighted_test_coverage"]
        result["weighted_evidence_coverage_delta"] = after_risk["weighted_evidence_coverage"] - before_risk["weighted_evidence_coverage"]
        result["uncovered_test_risk_score_delta"] = after_risk["uncovered_test_risk_score"] - before_risk["uncovered_test_risk_score"]
        result["uncovered_evidence_risk_score_delta"] = after_risk["uncovered_evidence_risk_score"] - before_risk["uncovered_evidence_risk_score"]
    return result


def compare(
    before: dict[str, Any],
    after: dict[str, Any],
    quality_policy: dict[str, Any] | None = None,
    freshness_policy: dict[str, Any] | None = None,
    risk_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    before_validation = validate(before)
    after_validation = validate(after)
    nodes = _node_diff(before, after)
    links = _link_diff(before, after)
    coverage = _coverage_movement(before, after)
    rationale_drift = _typed_drift(nodes, RATIONALE_TYPES)
    implementation_drift = _typed_drift(nodes, IMPLEMENTATION_TYPES)
    before_summary = build_summary(before, quality_policy, freshness_policy, risk_policy)
    after_summary = build_summary(after, quality_policy, freshness_policy, risk_policy)

    return {
        "valid": before_validation["valid"] and after_validation["valid"],
        "validation": {"before": before_validation, "after": after_validation},
        "nodes": nodes,
        "links": links,
        "coverage": coverage,
        "rationale_drift": rationale_drift,
        "implementation_drift": implementation_drift,
        "assurance_refresh_candidates": _refresh_candidates(before, after, implementation_drift),
        "assurance": {
            "before": before_summary,
            "after": after_summary,
            "delta": _assurance_delta(before_summary, after_summary),
        },
    }


def _pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.1f} pp"


def _items(values: list[Any]) -> str:
    return ", ".join(str(value) for value in values) if values else "none"


def render_markdown(result: dict[str, Any], title: str = "Historical Project Assurance") -> str:
    assurance = result["assurance"]
    delta = assurance["delta"]
    coverage = result["coverage"]
    lines = [
        f"# {title}",
        "",
        f"**Decision: {delta['decision_before']} → {delta['decision_after']}**",
        "",
        "## Assurance movement",
        "",
        f"- Raw test coverage: {coverage['before']['test_coverage'] * 100:.1f}% → {coverage['after']['test_coverage'] * 100:.1f}% ({_pct(delta['raw_test_coverage_delta'])})",
        f"- Raw evidence coverage: {coverage['before']['evidence_coverage'] * 100:.1f}% → {coverage['after']['evidence_coverage'] * 100:.1f}% ({_pct(delta['raw_evidence_coverage_delta'])})",
    ]
    if "fresh_evidence_coverage_delta" in delta:
        before_fresh = assurance["before"]["freshness_policy"]["fresh_evidence_coverage"]
        after_fresh = assurance["after"]["freshness_policy"]["fresh_evidence_coverage"]
        lines.append(f"- Fresh evidence coverage: {before_fresh * 100:.1f}% → {after_fresh * 100:.1f}% ({_pct(delta['fresh_evidence_coverage_delta'])})")
    if "weighted_test_coverage_delta" in delta:
        before_risk = assurance["before"]["risk_policy"]
        after_risk = assurance["after"]["risk_policy"]
        lines.append(f"- Risk-weighted test coverage: {before_risk['weighted_test_coverage'] * 100:.1f}% → {after_risk['weighted_test_coverage'] * 100:.1f}% ({_pct(delta['weighted_test_coverage_delta'])})")
        lines.append(f"- Risk-weighted evidence coverage: {before_risk['weighted_evidence_coverage'] * 100:.1f}% → {after_risk['weighted_evidence_coverage'] * 100:.1f}% ({_pct(delta['weighted_evidence_coverage_delta'])})")

    lines += [
        "",
        "## Traceability gaps",
        "",
        f"- New test gaps: {_items(coverage['new_test_gaps'])}",
        f"- Resolved test gaps: {_items(coverage['resolved_test_gaps'])}",
        f"- New evidence gaps: {_items(coverage['new_evidence_gaps'])}",
        f"- Resolved evidence gaps: {_items(coverage['resolved_evidence_gaps'])}",
        "",
        "## Rationale drift",
        "",
        f"- Added: {_items(result['rationale_drift']['added'])}",
        f"- Removed: {_items(result['rationale_drift']['removed'])}",
        f"- Changed: {_items(result['rationale_drift']['changed'])}",
        "",
        "## Implementation drift",
        "",
        f"- Added: {_items(result['implementation_drift']['added'])}",
        f"- Removed: {_items(result['implementation_drift']['removed'])}",
        f"- Changed: {_items(result['implementation_drift']['changed'])}",
        "",
        "## Assurance refresh candidates",
        "",
    ]
    if result["assurance_refresh_candidates"]:
        for item in result["assurance_refresh_candidates"]:
            lines.append(
                f"- `{item['requirement']}` — implementation changed: {_items(item['implementation_changes'])}; "
                f"current tests: {_items(item['current_tests'])}; current evidence: {_items(item['current_evidence'])}"
            )
    else:
        lines.append("- none")

    lines += [
        "",
        "## Machine comparison",
        "",
        "```json",
        json.dumps(result, indent=2, sort_keys=True),
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare historical Project Evidence Graph assurance")
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--quality-policy")
    parser.add_argument("--freshness-policy")
    parser.add_argument("--risk-policy")
    parser.add_argument("--json-output")
    parser.add_argument("--markdown")
    parser.add_argument("--title", default="Historical Project Assurance")
    args = parser.parse_args()

    result = compare(
        load_graph(args.before),
        load_graph(args.after),
        load_quality_policy(args.quality_policy) if args.quality_policy else None,
        load_freshness_policy(args.freshness_policy) if args.freshness_policy else None,
        load_risk_policy(args.risk_policy) if args.risk_policy else None,
    )
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(result, args.title), encoding="utf-8")
    if not args.json_output and not args.markdown:
        print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
