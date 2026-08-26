#!/usr/bin/env python3
"""Deterministically merge Project Evidence Graph fragments and explicit bridge links."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_graph(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"graph fragment must be a JSON object: {path}")
    return value


def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _link_key(link: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(link.get("from", "")),
        str(link.get("type", "supports")),
        str(link.get("to", "")),
    )


def merge_fragments(
    fragments: list[tuple[str, dict[str, Any]]],
    bridges: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fragments = sorted(fragments, key=lambda item: item[0])
    nodes: dict[str, dict[str, Any]] = {}
    node_sources: dict[str, str] = {}
    links: dict[tuple[str, str, str], dict[str, Any]] = {}
    link_sources: dict[tuple[str, str, str], str] = {}

    identical_duplicate_nodes: list[dict[str, str]] = []
    conflicting_nodes: list[dict[str, Any]] = []
    identical_duplicate_links: list[dict[str, str]] = []
    conflicting_links: list[dict[str, Any]] = []
    fragment_metadata: dict[str, dict[str, Any]] = {}

    for label, fragment in fragments:
        metadata = {key: value for key, value in fragment.items() if key not in {"nodes", "links"}}
        if metadata:
            fragment_metadata[label] = metadata

        for node in fragment.get("nodes", []):
            if not isinstance(node, dict):
                conflicting_nodes.append({"id": None, "fragment": label, "error": "node is not an object"})
                continue
            node_id = str(node.get("id", "")).strip()
            if not node_id:
                conflicting_nodes.append({"id": None, "fragment": label, "error": "node id is missing"})
                continue
            if node_id not in nodes:
                nodes[node_id] = dict(node)
                node_sources[node_id] = label
                continue
            if _stable(nodes[node_id]) == _stable(node):
                identical_duplicate_nodes.append({"id": node_id, "fragments": ",".join(sorted({node_sources[node_id], label}))})
            else:
                conflicting_nodes.append({
                    "id": node_id,
                    "first_fragment": node_sources[node_id],
                    "second_fragment": label,
                    "first": nodes[node_id],
                    "second": node,
                })

        for link in fragment.get("links", []):
            if not isinstance(link, dict):
                conflicting_links.append({"key": None, "fragment": label, "error": "link is not an object"})
                continue
            key = _link_key(link)
            if not key[0] or not key[2]:
                conflicting_links.append({"key": list(key), "fragment": label, "error": "link endpoint is missing"})
                continue
            if key not in links:
                links[key] = dict(link)
                link_sources[key] = label
                continue
            if _stable(links[key]) == _stable(link):
                identical_duplicate_links.append({"key": "|".join(key), "fragments": ",".join(sorted({link_sources[key], label}))})
            else:
                conflicting_links.append({
                    "key": list(key),
                    "first_fragment": link_sources[key],
                    "second_fragment": label,
                    "first": links[key],
                    "second": link,
                })

    unresolved_bridges: list[dict[str, Any]] = []
    invalid_bridges: list[dict[str, Any]] = []
    if bridges is not None:
        bridge_links = bridges.get("links", []) if isinstance(bridges, dict) else []
        if not isinstance(bridge_links, list):
            invalid_bridges.append({"error": "bridges.links must be an array"})
            bridge_links = []
        for index, link in enumerate(bridge_links):
            if not isinstance(link, dict):
                invalid_bridges.append({"index": index, "error": "bridge link is not an object"})
                continue
            key = _link_key(link)
            missing = [node_id for node_id in (key[0], key[2]) if node_id not in nodes]
            if missing:
                unresolved_bridges.append({"index": index, "from": key[0], "to": key[2], "missing": missing})
                continue
            if key not in links:
                links[key] = dict(link)
                link_sources[key] = "bridges"
            elif _stable(links[key]) != _stable(link):
                conflicting_links.append({
                    "key": list(key),
                    "first_fragment": link_sources[key],
                    "second_fragment": "bridges",
                    "first": links[key],
                    "second": link,
                })

    diagnostics = {
        "fragments": [label for label, _ in fragments],
        "fragment_metadata": {key: fragment_metadata[key] for key in sorted(fragment_metadata)},
        "identical_duplicate_nodes": sorted(identical_duplicate_nodes, key=lambda item: (str(item.get("id")), item.get("fragments", ""))),
        "conflicting_nodes": sorted(conflicting_nodes, key=lambda item: (str(item.get("id")), str(item.get("second_fragment", item.get("fragment", ""))))),
        "identical_duplicate_links": sorted(identical_duplicate_links, key=lambda item: (item.get("key", ""), item.get("fragments", ""))),
        "conflicting_links": sorted(conflicting_links, key=lambda item: (_stable(item.get("key")), str(item.get("second_fragment", item.get("fragment", ""))))),
        "invalid_bridges": invalid_bridges,
        "unresolved_bridges": unresolved_bridges,
    }
    diagnostics["valid"] = not any(
        diagnostics[key]
        for key in ("conflicting_nodes", "conflicting_links", "invalid_bridges", "unresolved_bridges")
    )

    return {
        "nodes": [nodes[node_id] for node_id in sorted(nodes)],
        "links": [links[key] for key in sorted(links)],
        "merge_diagnostics": diagnostics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge Project Evidence Graph fragments")
    parser.add_argument("fragments", nargs="+")
    parser.add_argument("--bridges")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    fragments = [(str(Path(path)), load_graph(path)) for path in args.fragments]
    bridges = load_graph(args.bridges) if args.bridges else None
    graph = merge_fragments(fragments, bridges)
    payload = json.dumps(graph, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if graph["merge_diagnostics"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
