#!/usr/bin/env python3
"""Profile-driven work-item export importer for Project Evidence Graph."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_JIRA_PROFILE = {
    "source": "jira",
    "items_path": "issues",
    "id": "key",
    "project": "fields.project.key",
    "tracker_type": "fields.issuetype.name",
    "title": "fields.summary",
    "status": "fields.status.name",
    "risk": "fields.priority.name",
    "updated_at": "fields.updated",
    "url": "self",
    "type_map": {
        "story": "requirement",
        "epic": "requirement",
        "requirement": "requirement",
        "bug": "defect",
        "defect": "defect",
        "test": "test",
        "test case": "test",
        "decision": "decision",
        "change": "change",
        "task": "change"
    },
    "default_artifact_type": "change",
    "jira_issue_links": True
}


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_path(value: Any, path: str | None, default: Any = None) -> Any:
    if not path:
        return default
    current = value
    for segment in path.split("."):
        if isinstance(current, dict):
            if segment not in current:
                return default
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            if index >= len(current):
                return default
            current = current[index]
        else:
            return default
    return current


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").lower()
    return text or "related_to"


def _canonical_id(source: str, project: str, external_id: str) -> str:
    return f"TRACKER:{source}:{project or '_'}:{external_id}"


def _artifact_type(raw: Any, profile: dict[str, Any]) -> str:
    type_map = {str(key).lower(): str(value) for key, value in profile.get("type_map", {}).items()}
    raw_text = str(raw or "").strip()
    return type_map.get(raw_text.lower(), str(profile.get("default_artifact_type", "change")))


def _base_node(item: dict[str, Any], profile: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    source = str(profile.get("source", "tracker")).strip().lower() or "tracker"
    external_id = str(get_path(item, profile.get("id"), "")).strip()
    if not external_id:
        raise ValueError("work item is missing configured external ID")
    project = str(get_path(item, profile.get("project"), profile.get("project_name", "")) or "").strip()
    raw_type = get_path(item, profile.get("tracker_type"))
    node_id = _canonical_id(source, project, external_id)
    node: dict[str, Any] = {
        "id": node_id,
        "type": _artifact_type(raw_type, profile),
        "external_source": source,
        "external_project": project or None,
        "external_id": external_id,
        "external_type": str(raw_type).strip() if raw_type is not None else None,
    }
    for target, key in (
        ("title", "title"),
        ("status", "status"),
        ("risk", "risk"),
        ("updated_at", "updated_at"),
        ("url", "url"),
    ):
        raw = get_path(item, profile.get(key))
        if raw is not None and str(raw).strip():
            node[target] = str(raw).strip()
    return node_id, node


def _generic_links(item: dict[str, Any], item_id: str, profile: dict[str, Any], id_map: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config = profile.get("links")
    if not isinstance(config, dict):
        return [], []
    records = get_path(item, config.get("path"), [])
    if not isinstance(records, list):
        return [], []
    links = []
    unresolved = []
    direction = str(config.get("direction", "outward")).lower()
    for record in records:
        if not isinstance(record, dict):
            continue
        target_external = str(get_path(record, config.get("target"), "")).strip()
        if not target_external:
            continue
        relation = _slug(str(get_path(record, config.get("type"), "related_to")))
        target_id = id_map.get(target_external)
        if not target_id:
            unresolved.append({"from": item_id, "target_external_id": target_external, "type": relation})
            continue
        if direction == "inward":
            links.append({"from": target_id, "to": item_id, "type": relation})
        else:
            links.append({"from": item_id, "to": target_id, "type": relation})
    return links, unresolved


def _jira_links(item: dict[str, Any], item_id: str, id_map: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = get_path(item, "fields.issuelinks", [])
    if not isinstance(records, list):
        return [], []
    links = []
    unresolved = []
    for record in records:
        if not isinstance(record, dict):
            continue
        relation_type = record.get("type") if isinstance(record.get("type"), dict) else {}
        if isinstance(record.get("outwardIssue"), dict):
            target_external = str(record["outwardIssue"].get("key", "")).strip()
            relation = _slug(str(relation_type.get("outward") or relation_type.get("name") or "related_to"))
            target_id = id_map.get(target_external)
            if target_id:
                links.append({"from": item_id, "to": target_id, "type": relation})
            elif target_external:
                unresolved.append({"from": item_id, "target_external_id": target_external, "type": relation})
        if isinstance(record.get("inwardIssue"), dict):
            source_external = str(record["inwardIssue"].get("key", "")).strip()
            relation = _slug(str(relation_type.get("inward") or relation_type.get("name") or "related_to"))
            source_id = id_map.get(source_external)
            if source_id:
                links.append({"from": source_id, "to": item_id, "type": relation})
            elif source_external:
                unresolved.append({"to": item_id, "source_external_id": source_external, "type": relation})
    return links, unresolved


def build_graph(export: Any, profile: dict[str, Any]) -> dict[str, Any]:
    items = get_path(export, profile.get("items_path"), export if isinstance(export, list) else [])
    if not isinstance(items, list):
        raise ValueError("configured items_path does not resolve to a list")

    nodes = []
    item_pairs: list[tuple[dict[str, Any], str]] = []
    id_map: dict[str, str] = {}
    duplicate_external_ids = []

    for item in items:
        if not isinstance(item, dict):
            continue
        node_id, node = _base_node(item, profile)
        external_id = node["external_id"]
        if external_id in id_map:
            duplicate_external_ids.append(external_id)
        id_map[external_id] = node_id
        nodes.append(node)
        item_pairs.append((item, node_id))

    links = []
    unresolved = []
    seen: set[tuple[str, str, str]] = set()
    for item, node_id in item_pairs:
        if profile.get("jira_issue_links"):
            item_links, item_unresolved = _jira_links(item, node_id, id_map)
        else:
            item_links, item_unresolved = _generic_links(item, node_id, profile, id_map)
        unresolved.extend(item_unresolved)
        for link in item_links:
            key = (link["from"], link["type"], link["to"])
            if key not in seen:
                links.append(link)
                seen.add(key)

    return {
        "nodes": nodes,
        "links": links,
        "import_diagnostics": {
            "source": profile.get("source", "tracker"),
            "duplicate_external_ids": sorted(set(duplicate_external_ids)),
            "unresolved_references": unresolved,
        },
    }


def load_profile(profile_arg: str) -> dict[str, Any]:
    if profile_arg.lower() == "jira":
        return dict(DEFAULT_JIRA_PROFILE)
    profile = load_json(profile_arg)
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object")
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Jira/ALM/work-item JSON exports into Project Evidence Graph")
    parser.add_argument("export")
    parser.add_argument("--profile", required=True, help="'jira' or path to profile JSON")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    graph = build_graph(load_json(args.export), load_profile(args.profile))
    payload = json.dumps(graph, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if not graph["import_diagnostics"]["duplicate_external_ids"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
