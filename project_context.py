#!/usr/bin/env python3
"""Build compact bounded machine-readable project context for agents and tools."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from evidence_freshness import load_policy as load_freshness_policy
from evidence_graph import _index, load_graph
from evidence_lifecycle import load_policy as load_lifecycle_policy
from project_review import build_summary
from quality_gate import load_policy as load_quality_policy
from risk_assurance import load_policy as load_risk_policy


CONTEXT_FIELDS = {
    "id", "type", "title", "risk", "status", "artifact_ref", "source", "provenance",
    "observed_at", "updated_at", "created_at", "external", "external_source", "external_project", "external_id"
}


def _adjacency(graph: dict[str, Any]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    forward: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    for link in graph.get("links", []):
        source = str(link.get("from", ""))
        target = str(link.get("to", ""))
        if source and target:
            forward[source].add(target)
            reverse[target].add(source)
    return forward, reverse


def bounded_ids(graph: dict[str, Any], focus: str | None, depth: int) -> set[str]:
    nodes, _ = _index(graph)
    if focus is None:
        return set(nodes)
    if focus not in nodes:
        return set()
    if depth < 0:
        raise ValueError("depth must be >= 0")
    forward, reverse = _adjacency(graph)
    visited = {focus}
    queue = deque([(focus, 0)])
    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        neighbors = sorted(forward.get(current, set()) | reverse.get(current, set()))
        for neighbor in neighbors:
            if neighbor in nodes and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, current_depth + 1))
    return visited


def _compact_node(node: dict[str, Any]) -> dict[str, Any]:
    return {key: node[key] for key in node if key in CONTEXT_FIELDS}


def _context_id(focus: str | None, depth: int, nodes: list[dict[str, Any]], links: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        {
            "focus": focus,
            "depth": depth,
            "nodes": nodes,
            "links": links,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "ctx-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_context(
    graph: dict[str, Any],
    focus: str | None = None,
    depth: int = 2,
    quality_policy: dict[str, Any] | None = None,
    freshness_policy: dict[str, Any] | None = None,
    risk_policy: dict[str, Any] | None = None,
    lifecycle_enabled: bool = False,
    lifecycle_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    nodes, _ = _index(graph)
    selected = bounded_ids(graph, focus, depth)
    if focus is not None and not selected:
        return {
            "schema_version": "0.1",
            "context_id": None,
            "focus": focus,
            "found": False,
            "depth": depth,
            "nodes": [],
            "links": [],
        }

    compact_nodes = [_compact_node(nodes[node_id]) for node_id in sorted(selected)]
    compact_links = []
    for link in graph.get("links", []):
        source = str(link.get("from", ""))
        target = str(link.get("to", ""))
        if source in selected and target in selected:
            item = {key: link[key] for key in ("from", "to", "type", "provenance") if key in link}
            compact_links.append(item)
    compact_links.sort(key=lambda item: (str(item.get("from")), str(item.get("type")), str(item.get("to"))))

    counts = Counter(str(node.get("type", "other")) for node in compact_nodes)
    external_refs = sorted(
        str(node.get("artifact_ref"))
        for node in compact_nodes
        if str(node.get("artifact_ref", "")).startswith("eac://")
    )

    assurance = None
    if any(policy is not None for policy in (quality_policy, freshness_policy, risk_policy, lifecycle_policy)) or lifecycle_enabled:
        assurance = build_summary(
            graph,
            quality_policy,
            freshness_policy,
            risk_policy,
            lifecycle_enabled,
            lifecycle_policy,
        )

    context_id = _context_id(focus, depth, compact_nodes, compact_links)
    return {
        "schema_version": "0.1",
        "context_id": context_id,
        "focus": focus,
        "found": True,
        "depth": depth,
        "scope": {
            "node_count": len(compact_nodes),
            "link_count": len(compact_links),
            "artifact_types": dict(sorted(counts.items())),
            "external_artifact_refs": external_refs,
        },
        "nodes": compact_nodes,
        "links": compact_links,
        "assurance": assurance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build compact bounded project context")
    parser.add_argument("graph")
    parser.add_argument("--focus")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--quality-policy")
    parser.add_argument("--freshness-policy")
    parser.add_argument("--risk-policy")
    parser.add_argument("--lifecycle", action="store_true", help="embed lifecycle and stale-by-change assurance with default policy")
    parser.add_argument("--lifecycle-policy", help="embed lifecycle assurance with a JSON policy")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    graph = load_graph(args.graph)
    context = build_context(
        graph,
        args.focus,
        args.depth,
        load_quality_policy(args.quality_policy) if args.quality_policy else None,
        load_freshness_policy(args.freshness_policy) if args.freshness_policy else None,
        load_risk_policy(args.risk_policy) if args.risk_policy else None,
        args.lifecycle or bool(args.lifecycle_policy),
        load_lifecycle_policy(args.lifecycle_policy) if args.lifecycle_policy else None,
    )
    payload = json.dumps(context, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if context.get("found") else 2


if __name__ == "__main__":
    raise SystemExit(main())
