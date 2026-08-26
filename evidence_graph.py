#!/usr/bin/env python3
"""Project evidence and traceability graph with zero runtime dependencies."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


TRACE_TYPES = {"requirement", "decision", "mapping", "interface", "test", "defect", "change", "evidence"}


def load_graph(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        graph = json.load(handle)
    if not isinstance(graph, dict):
        raise ValueError("graph must be a JSON object")
    return graph


def _index(graph: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    nodes: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for node in graph.get("nodes", []):
        node_id = str(node.get("id", ""))
        if not node_id:
            continue
        if node_id in nodes:
            duplicates.append(node_id)
        nodes[node_id] = node
    return nodes, sorted(set(duplicates))


def validate(graph: dict[str, Any]) -> dict[str, Any]:
    nodes, duplicate_nodes = _index(graph)
    broken_links = []
    duplicate_links = []
    seen: set[tuple[str, str, str]] = set()
    invalid_types = []

    for node_id, node in nodes.items():
        node_type = str(node.get("type", ""))
        if node_type and node_type not in TRACE_TYPES:
            invalid_types.append({"id": node_id, "type": node_type})

    for index, link in enumerate(graph.get("links", [])):
        source = str(link.get("from", ""))
        target = str(link.get("to", ""))
        link_type = str(link.get("type", "supports"))
        key = (source, link_type, target)
        if key in seen:
            duplicate_links.append({"index": index, "from": source, "type": link_type, "to": target})
        seen.add(key)
        missing = [node_id for node_id in (source, target) if node_id not in nodes]
        if missing:
            broken_links.append({"index": index, "from": source, "to": target, "missing": missing})

    return {
        "node_count": len(graph.get("nodes", [])),
        "link_count": len(graph.get("links", [])),
        "duplicate_nodes": duplicate_nodes,
        "duplicate_links": duplicate_links,
        "broken_links": broken_links,
        "invalid_types": invalid_types,
        "valid": not duplicate_nodes and not duplicate_links and not broken_links and not invalid_types,
    }


def _adjacency(graph: dict[str, Any], reverse: bool = False) -> dict[str, list[str]]:
    nodes, _ = _index(graph)
    adjacency: dict[str, list[str]] = defaultdict(list)
    for link in graph.get("links", []):
        source = str(link.get("from", ""))
        target = str(link.get("to", ""))
        if source in nodes and target in nodes:
            left, right = (target, source) if reverse else (source, target)
            adjacency[left].append(right)
    return adjacency


def reachable(graph: dict[str, Any], start: str, reverse: bool = False) -> set[str]:
    nodes, _ = _index(graph)
    adjacency = _adjacency(graph, reverse=reverse)
    visited = {start} if start in nodes else set()
    queue = deque(visited)
    while queue:
        current = queue.popleft()
        for target in adjacency[current]:
            if target not in visited:
                visited.add(target)
                queue.append(target)
    return visited


def shortest_path(graph: dict[str, Any], start: str, end: str) -> list[str]:
    nodes, _ = _index(graph)
    if start not in nodes or end not in nodes:
        return []
    adjacency = _adjacency(graph)

    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        current, path = queue.popleft()
        if current == end:
            return path
        for target in adjacency[current]:
            if target not in visited:
                visited.add(target)
                queue.append((target, path + [target]))
    return []


def impact(graph: dict[str, Any], node_id: str) -> dict[str, Any]:
    nodes, _ = _index(graph)
    if node_id not in nodes:
        return {"node": node_id, "found": False, "upstream": [], "downstream": []}

    upstream = sorted(reachable(graph, node_id, reverse=True) - {node_id})
    downstream = sorted(reachable(graph, node_id) - {node_id})

    def group(ids: list[str]) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item_id in ids:
            grouped[str(nodes[item_id].get("type", "other"))].append(item_id)
        return dict(sorted(grouped.items()))

    return {
        "node": node_id,
        "found": True,
        "upstream": upstream,
        "downstream": downstream,
        "upstream_by_type": group(upstream),
        "downstream_by_type": group(downstream),
    }


def traceability(graph: dict[str, Any]) -> dict[str, Any]:
    nodes, _ = _index(graph)
    requirements = sorted(node_id for node_id, node in nodes.items() if node.get("type") == "requirement")
    rows = []
    requirements_without_tests = []
    requirements_without_evidence = []

    for requirement in requirements:
        linked = reachable(graph, requirement)
        grouped: dict[str, list[str]] = defaultdict(list)
        for node_id in sorted(linked - {requirement}):
            node_type = str(nodes[node_id].get("type", "other"))
            grouped[node_type].append(node_id)
        tests = grouped.get("test", [])
        evidence = grouped.get("evidence", [])
        if not tests:
            requirements_without_tests.append(requirement)
        if not evidence:
            requirements_without_evidence.append(requirement)
        rows.append({
            "requirement": requirement,
            "decisions": grouped.get("decision", []),
            "mappings": grouped.get("mapping", []),
            "interfaces": grouped.get("interface", []),
            "tests": tests,
            "defects": grouped.get("defect", []),
            "changes": grouped.get("change", []),
            "evidence": evidence,
        })

    return {
        "requirements": len(requirements),
        "requirements_without_tests": requirements_without_tests,
        "requirements_without_evidence": requirements_without_evidence,
        "test_coverage": 1.0 if not requirements else (len(requirements) - len(requirements_without_tests)) / len(requirements),
        "evidence_coverage": 1.0 if not requirements else (len(requirements) - len(requirements_without_evidence)) / len(requirements),
        "matrix": rows,
    }


def build_report(graph: dict[str, Any]) -> dict[str, Any]:
    return {"validation": validate(graph), "traceability": traceability(graph)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze project evidence and traceability")
    parser.add_argument("graph", help="Path to project evidence JSON")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("analyze")
    path_parser = sub.add_parser("path")
    path_parser.add_argument("from_id")
    path_parser.add_argument("to_id")
    impact_parser = sub.add_parser("impact")
    impact_parser.add_argument("node_id")
    args = parser.parse_args()

    graph = load_graph(args.graph)
    if args.command == "path":
        path = shortest_path(graph, args.from_id, args.to_id)
        print(" -> ".join(path) if path else "NO_PATH")
        return 0 if path else 2
    if args.command == "impact":
        result = impact(graph, args.node_id)
        print(json.dumps(result, indent=2))
        return 0 if result["found"] else 2

    result = build_report(graph)
    print(json.dumps(result, indent=2))
    return 0 if result["validation"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
