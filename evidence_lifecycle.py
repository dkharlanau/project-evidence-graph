#!/usr/bin/env python3
"""Evaluate explicit evidence/decision lifecycle and stale-by-change assurance."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from evidence_graph import reachable, validate

LIFECYCLE_LINK_TYPES = {"supersedes", "replaces"}
LIFECYCLE_ARTIFACT_TYPES = {"evidence", "decision"}
DEFAULT_IMPLEMENTATION_TYPES = {"mapping", "interface", "decision", "change"}
DEFAULT_IMPLEMENTATION_TIMESTAMP_FIELDS = ("changed_at",)
DEFAULT_EVIDENCE_TIMESTAMP_FIELDS = ("observed_at", "updated_at", "created_at")


def parse_iso(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must include timezone: {value!r}")
    return parsed


def _first_timestamp(node: dict[str, Any], fields: tuple[str, ...]) -> tuple[str | None, str | None, datetime | None]:
    for field in fields:
        value = node.get(field)
        if value is None or str(value).strip() == "":
            continue
        text = str(value).strip()
        return field, text, parse_iso(text)
    return None, None, None


def lifecycle_links(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        link
        for link in graph.get("links", [])
        if isinstance(link, dict) and str(link.get("type", "")) in LIFECYCLE_LINK_TYPES
    ]


def superseded_artifact_ids(graph: dict[str, Any], artifact_types: set[str] | None = None) -> set[str]:
    """Return targets of validly shaped lifecycle links.

    This helper is intentionally conservative: only same-type evidence/decision links
    count. Full lifecycle validation is performed by ``evaluate``.
    """
    nodes = {str(node.get("id", "")): node for node in graph.get("nodes", []) if isinstance(node, dict)}
    result: set[str] = set()
    for link in lifecycle_links(graph):
        source = str(link.get("from", ""))
        target = str(link.get("to", ""))
        source_type = str(nodes.get(source, {}).get("type", ""))
        target_type = str(nodes.get(target, {}).get("type", ""))
        if source_type not in LIFECYCLE_ARTIFACT_TYPES or source_type != target_type:
            continue
        if artifact_types is not None and target_type not in artifact_types:
            continue
        if source and target and source != target:
            result.add(target)
    return result


def _lifecycle_validation(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = {str(node.get("id", "")): node for node in graph.get("nodes", []) if isinstance(node, dict)}
    errors: list[dict[str, Any]] = []
    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)

    for position, link in enumerate(lifecycle_links(graph)):
        source = str(link.get("from", ""))
        target = str(link.get("to", ""))
        source_node = nodes.get(source)
        target_node = nodes.get(target)
        if source_node is None or target_node is None:
            errors.append({"kind": "missing_endpoint", "position": position, "from": source, "to": target})
            continue
        source_type = str(source_node.get("type", ""))
        target_type = str(target_node.get("type", ""))
        if source == target:
            errors.append({"kind": "self_replacement", "position": position, "artifact": source})
            continue
        if source_type not in LIFECYCLE_ARTIFACT_TYPES or target_type not in LIFECYCLE_ARTIFACT_TYPES:
            errors.append({
                "kind": "unsupported_artifact_type",
                "position": position,
                "from": source,
                "from_type": source_type,
                "to": target,
                "to_type": target_type,
            })
            continue
        if source_type != target_type:
            errors.append({
                "kind": "cross_type_replacement",
                "position": position,
                "from": source,
                "from_type": source_type,
                "to": target,
                "to_type": target_type,
            })
            continue
        incoming[target].append(source)
        outgoing[source].append(target)

    for target, successors in sorted(incoming.items()):
        if len(set(successors)) > 1:
            errors.append({
                "kind": "ambiguous_replacement",
                "artifact": target,
                "superseded_by": sorted(set(successors)),
            })

    # Lifecycle edges are newer -> older. Any directed cycle is impossible history.
    state: dict[str, int] = {}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node_id: str) -> None:
        marker = state.get(node_id, 0)
        if marker == 2:
            return
        if marker == 1:
            if node_id in stack:
                start = stack.index(node_id)
                cycle = stack[start:] + [node_id]
                if cycle not in cycles:
                    cycles.append(cycle)
            return
        state[node_id] = 1
        stack.append(node_id)
        for target in sorted(set(outgoing.get(node_id, []))):
            visit(target)
        stack.pop()
        state[node_id] = 2

    for node_id in sorted(outgoing):
        visit(node_id)
    for cycle in cycles:
        errors.append({"kind": "replacement_cycle", "path": cycle})

    return {
        "valid": not errors,
        "errors": sorted(errors, key=lambda item: json.dumps(item, sort_keys=True)),
        "incoming": {key: sorted(set(value)) for key, value in sorted(incoming.items())},
        "outgoing": {key: sorted(set(value)) for key, value in sorted(outgoing.items())},
    }


def _artifact_states(graph: dict[str, Any], lifecycle: dict[str, Any]) -> list[dict[str, Any]]:
    incoming = lifecycle["incoming"]
    outgoing = lifecycle["outgoing"]
    states = []
    for node in sorted(graph.get("nodes", []), key=lambda item: str(item.get("id", ""))):
        artifact_type = str(node.get("type", ""))
        if artifact_type not in LIFECYCLE_ARTIFACT_TYPES:
            continue
        artifact_id = str(node.get("id", ""))
        superseded_by = incoming.get(artifact_id, [])
        states.append({
            "artifact": artifact_id,
            "type": artifact_type,
            "active": not superseded_by,
            "superseded_by": superseded_by,
            "supersedes": outgoing.get(artifact_id, []),
        })
    return states


def evaluate(graph: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = dict(policy or {})
    graph_validation = validate(graph)
    lifecycle = _lifecycle_validation(graph)
    nodes = {str(node.get("id", "")): node for node in graph.get("nodes", []) if isinstance(node, dict)}
    states = _artifact_states(graph, lifecycle)
    active_evidence = {
        item["artifact"] for item in states if item["type"] == "evidence" and item["active"]
    }
    superseded_evidence = {
        item["artifact"] for item in states if item["type"] == "evidence" and not item["active"]
    }

    implementation_types = set(policy.get("implementation_types", sorted(DEFAULT_IMPLEMENTATION_TYPES)))
    implementation_timestamp_fields = tuple(policy.get("implementation_timestamp_fields", DEFAULT_IMPLEMENTATION_TIMESTAMP_FIELDS))
    evidence_timestamp_fields = tuple(policy.get("evidence_timestamp_fields", DEFAULT_EVIDENCE_TIMESTAMP_FIELDS))

    stale_by_change: list[dict[str, Any]] = []
    unknown_by_change: list[dict[str, Any]] = []
    requirement_current_evidence: dict[str, list[str]] = {}

    requirements = sorted(
        str(node.get("id", ""))
        for node in graph.get("nodes", [])
        if node.get("type") == "requirement"
    )

    for requirement_id in requirements:
        req_reachable = reachable(graph, requirement_id)
        candidate_evidence = sorted(active_evidence & req_reachable)
        stale_for_requirement: set[str] = set()
        unknown_for_requirement: set[str] = set()

        implementations = sorted(
            node_id
            for node_id in req_reachable
            if node_id in nodes and str(nodes[node_id].get("type", "")) in implementation_types
        )
        implementation_reachability = {
            implementation_id: reachable(graph, implementation_id)
            for implementation_id in implementations
        }

        for evidence_id in candidate_evidence:
            evidence_node = nodes[evidence_id]
            evidence_field, evidence_text, evidence_time = _first_timestamp(evidence_node, evidence_timestamp_fields)
            for implementation_id in implementations:
                # Only compare an implementation that is actually upstream of this evidence.
                if evidence_id not in implementation_reachability[implementation_id]:
                    continue
                implementation_node = nodes[implementation_id]
                change_field, change_text, change_time = _first_timestamp(
                    implementation_node,
                    implementation_timestamp_fields,
                )
                if change_time is None:
                    continue
                if evidence_time is None:
                    unknown_for_requirement.add(evidence_id)
                    unknown_by_change.append({
                        "requirement": requirement_id,
                        "evidence": evidence_id,
                        "implementation": implementation_id,
                        "reason": "evidence_timestamp_missing",
                        "implementation_timestamp_field": change_field,
                        "implementation_changed_at": change_text,
                    })
                    continue
                if change_time > evidence_time:
                    stale_for_requirement.add(evidence_id)
                    stale_by_change.append({
                        "requirement": requirement_id,
                        "evidence": evidence_id,
                        "implementation": implementation_id,
                        "evidence_timestamp_field": evidence_field,
                        "evidence_observed_at": evidence_text,
                        "implementation_timestamp_field": change_field,
                        "implementation_changed_at": change_text,
                    })

        current = sorted(
            evidence_id
            for evidence_id in candidate_evidence
            if evidence_id not in stale_for_requirement and evidence_id not in unknown_for_requirement
        )
        requirement_current_evidence[requirement_id] = current

    stale_by_change = sorted(
        stale_by_change,
        key=lambda item: (item["requirement"], item["evidence"], item["implementation"]),
    )
    unknown_by_change = sorted(
        unknown_by_change,
        key=lambda item: (item["requirement"], item["evidence"], item["implementation"]),
    )
    requirements_without_current_evidence = sorted(
        requirement_id
        for requirement_id, evidence_ids in requirement_current_evidence.items()
        if not evidence_ids
    )

    failed_checks: list[str] = []
    warnings: list[str] = []
    if not graph_validation["valid"]:
        failed_checks.append("invalid_graph")
    if not lifecycle["valid"]:
        failed_checks.append("invalid_lifecycle")
    if stale_by_change:
        if policy.get("fail_on_active_stale_by_change", True):
            failed_checks.append("active_evidence_stale_by_change")
        else:
            warnings.append("active_evidence_stale_by_change")
    if unknown_by_change:
        unknown_mode = str(policy.get("unknown_by_change", "fail"))
        if unknown_mode == "fail":
            failed_checks.append("unknown_evidence_age_after_change")
        elif unknown_mode == "warn":
            warnings.append("unknown_evidence_age_after_change")
    if requirements_without_current_evidence and policy.get("fail_on_requirements_without_current_evidence", False):
        failed_checks.append("requirements_without_current_evidence")

    return {
        "passed": not failed_checks,
        "graph_valid": graph_validation["valid"],
        "lifecycle_valid": lifecycle["valid"],
        "lifecycle_errors": lifecycle["errors"],
        "artifact_states": states,
        "active_evidence": sorted(active_evidence),
        "superseded_evidence": sorted(superseded_evidence),
        "stale_by_change": stale_by_change,
        "unknown_by_change": unknown_by_change,
        "requirement_current_evidence": requirement_current_evidence,
        "requirements_without_current_evidence": requirements_without_current_evidence,
        "failed_checks": sorted(set(failed_checks)),
        "warnings": sorted(set(warnings)),
        "policy": {
            "implementation_types": sorted(implementation_types),
            "implementation_timestamp_fields": list(implementation_timestamp_fields),
            "evidence_timestamp_fields": list(evidence_timestamp_fields),
            "fail_on_active_stale_by_change": bool(policy.get("fail_on_active_stale_by_change", True)),
            "unknown_by_change": str(policy.get("unknown_by_change", "fail")),
            "fail_on_requirements_without_current_evidence": bool(policy.get("fail_on_requirements_without_current_evidence", False)),
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Evidence Lifecycle",
        "",
        f"**Decision:** {'PASS' if result['passed'] else 'FAIL'}",
        "",
        f"- Lifecycle valid: **{result['lifecycle_valid']}**",
        f"- Active evidence: **{len(result['active_evidence'])}**",
        f"- Superseded evidence retained: **{len(result['superseded_evidence'])}**",
        f"- Active evidence stale by change: **{len(result['stale_by_change'])}**",
        f"- Unknown age after upstream change: **{len(result['unknown_by_change'])}**",
        f"- Requirements without current evidence: **{len(result['requirements_without_current_evidence'])}**",
    ]
    if result["lifecycle_errors"]:
        lines += ["", "## Lifecycle contract errors", ""]
        for item in result["lifecycle_errors"]:
            lines.append(f"- `{json.dumps(item, sort_keys=True)}`")
    if result["stale_by_change"]:
        lines += ["", "## Active evidence stale by change", ""]
        for item in result["stale_by_change"]:
            lines.append(
                f"- `{item['requirement']}`: `{item['evidence']}` observed `{item['evidence_observed_at']}` "
                f"is older than `{item['implementation']}` change `{item['implementation_changed_at']}`."
            )
    if result["unknown_by_change"]:
        lines += ["", "## Unknown evidence age after change", ""]
        for item in result["unknown_by_change"]:
            lines.append(
                f"- `{item['requirement']}`: `{item['evidence']}` has no usable timestamp after "
                f"`{item['implementation']}` changed at `{item['implementation_changed_at']}`."
            )
    if result["superseded_evidence"]:
        lines += ["", "## Retained but inactive evidence", ""]
        lines.extend(f"- `{evidence_id}`" for evidence_id in result["superseded_evidence"])
    lines += ["", "## Boundary", "", "Lifecycle is explicit. The evaluator does not delete historical evidence, infer replacements, or invent implementation change times.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate evidence lifecycle and stale-by-change assurance")
    parser.add_argument("graph")
    parser.add_argument("--policy")
    parser.add_argument("--json-output")
    parser.add_argument("--markdown")
    args = parser.parse_args()

    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8")) if args.policy else None
    result = evaluate(graph, policy)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(payload + "\n", encoding="utf-8")
    if args.markdown:
        Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown).write_text(render_markdown(result), encoding="utf-8")
    if not args.json_output and not args.markdown:
        print(payload)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
