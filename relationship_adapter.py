#!/usr/bin/env python3
"""Import Data Relationship Map artifact indexes into Project Evidence Graph fragments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cross_repo import canonical_ref
from evidence_freshness import parse_iso

EXPECTED_REPOSITORY = "dkharlanau/data-relationship-map"
EXPECTED_SCHEMA_VERSION = "0.1"


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Data Relationship Map artifact index must be a JSON object")
    return value


def _ref(raw: Any, diagnostics: list[dict[str, Any]], location: str) -> str | None:
    value = str(raw or "").strip()
    try:
        return canonical_ref(value)
    except ValueError as exc:
        diagnostics.append({"location": location, "ref": value, "error": str(exc)})
        return None


def _copy_if_present(source: dict[str, Any], target: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        if source.get(field) is not None:
            target[field] = source[field]


def _observed_at(index: dict[str, Any], diagnostics: dict[str, Any]) -> str | None:
    raw = index.get("observed_at")
    if raw is None or str(raw).strip() == "":
        diagnostics["source_observed_at"] = None
        diagnostics["observation_time_status"] = "missing"
        return None
    try:
        parsed = parse_iso(str(raw))
    except ValueError as exc:
        diagnostics["source_observed_at"] = str(raw)
        diagnostics["observation_time_status"] = "invalid"
        diagnostics["observation_time_error"] = str(exc)
        return None
    canonical = parsed.isoformat().replace("+00:00", "Z")
    diagnostics["source_observed_at"] = canonical
    diagnostics["observation_time_status"] = "valid"
    return canonical


def _external_node_base(ref: str, *, observed_at: str | None) -> dict[str, Any]:
    node: dict[str, Any] = {
        "id": ref,
        "artifact_ref": ref,
        "external": True,
        "external_source": "data-relationship-map",
        "source": {
            "repository": EXPECTED_REPOSITORY,
            "schema_version": EXPECTED_SCHEMA_VERSION,
        },
    }
    if observed_at is not None:
        node["observed_at"] = observed_at
    return node


def build_graph(index: dict[str, Any]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "source_index_valid": bool(index.get("valid")),
        "source_policy_evaluated": bool(index.get("policy_evaluated")),
        "source_policy_passed": index.get("policy_passed"),
        "invalid_refs": [],
        "duplicate_refs": [],
        "unresolved_object_refs": [],
    }

    if index.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        diagnostics["schema_error"] = f"schema_version must be {EXPECTED_SCHEMA_VERSION}"
    if index.get("repository") != EXPECTED_REPOSITORY:
        diagnostics["repository_error"] = f"repository must be {EXPECTED_REPOSITORY}"

    observed_at = _observed_at(index, diagnostics)

    if (
        not diagnostics["source_index_valid"]
        or diagnostics.get("schema_error")
        or diagnostics.get("repository_error")
        or diagnostics.get("observation_time_status") == "invalid"
    ):
        diagnostics["valid"] = False
        return {"nodes": [], "links": [], "relationship_import_diagnostics": diagnostics}

    nodes: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    seen_refs: set[str] = set()
    object_refs_by_id: dict[str, str] = {}

    def add_node(node: dict[str, Any], location: str) -> None:
        ref = str(node.get("id", ""))
        if ref in seen_refs:
            diagnostics["duplicate_refs"].append({"location": location, "ref": ref})
            return
        seen_refs.add(ref)
        nodes.append(node)

    for position, item in enumerate(index.get("objects", [])):
        if not isinstance(item, dict):
            diagnostics["invalid_refs"].append({"location": f"objects[{position}]", "error": "object is not an object"})
            continue
        ref = _ref(item.get("artifact_ref"), diagnostics["invalid_refs"], f"objects[{position}].artifact_ref")
        if ref is None:
            continue
        object_id = str(item.get("id", "")).strip()
        if object_id:
            object_refs_by_id[object_id] = ref
        metadata: dict[str, Any] = {
            "relationship_object_id": object_id or None,
            "system": item.get("system"),
            "object_type": item.get("object"),
        }
        _copy_if_present(item, metadata, ("provenance", "conflicts", "identity_collisions"))
        node = {
            **_external_node_base(ref, observed_at=observed_at),
            "type": "evidence",
            "title": item.get("label") or f"Observed relationship object {object_id or ref}",
            "status": "observed",
            "metadata": metadata,
        }
        add_node(node, f"objects[{position}]")

    for position, relation in enumerate(index.get("relationships", [])):
        if not isinstance(relation, dict):
            diagnostics["invalid_refs"].append({"location": f"relationships[{position}]", "error": "relationship is not an object"})
            continue
        ref = _ref(relation.get("artifact_ref"), diagnostics["invalid_refs"], f"relationships[{position}].artifact_ref")
        if ref is None:
            continue
        source_id = str(relation.get("from", "")).strip()
        target_id = str(relation.get("to", "")).strip()
        source_ref = _ref(relation.get("from_ref"), diagnostics["invalid_refs"], f"relationships[{position}].from_ref") if relation.get("from_ref") else object_refs_by_id.get(source_id)
        target_ref = _ref(relation.get("to_ref"), diagnostics["invalid_refs"], f"relationships[{position}].to_ref") if relation.get("to_ref") else object_refs_by_id.get(target_id)
        relation_type = str(relation.get("type", "related_to")).strip() or "related_to"

        metadata: dict[str, Any] = {
            "from": source_id,
            "to": target_id,
            "relationship_type": relation_type,
            "from_ref": source_ref,
            "to_ref": target_ref,
        }
        _copy_if_present(relation, metadata, ("provenance",))
        add_node(
            {
                **_external_node_base(ref, observed_at=observed_at),
                "type": "evidence",
                "title": f"Observed relationship {source_id} {relation_type} {target_id}",
                "status": "observed",
                "metadata": metadata,
            },
            f"relationships[{position}]",
        )

        if source_ref and source_ref in seen_refs:
            links.append({"from": source_ref, "to": ref, "type": "relationship_source"})
        else:
            diagnostics["unresolved_object_refs"].append({"location": f"relationships[{position}].from", "object_id": source_id, "ref": source_ref})
        if target_ref and target_ref in seen_refs:
            links.append({"from": ref, "to": target_ref, "type": "relationship_target"})
        else:
            diagnostics["unresolved_object_refs"].append({"location": f"relationships[{position}].to", "object_id": target_id, "ref": target_ref})

    for position, finding in enumerate(index.get("findings", [])):
        if not isinstance(finding, dict):
            diagnostics["invalid_refs"].append({"location": f"findings[{position}]", "error": "finding is not an object"})
            continue
        ref = _ref(finding.get("artifact_ref"), diagnostics["invalid_refs"], f"findings[{position}].artifact_ref")
        if ref is None:
            continue
        kind = str(finding.get("kind", "relationship_finding")).strip() or "relationship_finding"
        severity = str(finding.get("severity", "warning")).strip() or "warning"
        node_ref = _ref(finding.get("node_ref"), diagnostics["invalid_refs"], f"findings[{position}].node_ref") if finding.get("node_ref") else object_refs_by_id.get(str(finding.get("node", "")).strip())
        metadata = {key: value for key, value in finding.items() if key not in {"artifact_ref", "node_ref"}}
        add_node(
            {
                **_external_node_base(ref, observed_at=observed_at),
                "type": "defect",
                "title": f"Data relationship finding: {kind}",
                "status": "open",
                "risk": "high" if severity == "error" else "medium",
                "metadata": metadata,
            },
            f"findings[{position}]",
        )
        if node_ref and node_ref in seen_refs:
            links.append({"from": node_ref, "to": ref, "type": "has_relationship_finding"})
        elif finding.get("node") or finding.get("node_ref"):
            diagnostics["unresolved_object_refs"].append({"location": f"findings[{position}].node", "object_id": finding.get("node"), "ref": node_ref})

        for related_position, related_id in enumerate(finding.get("related", [])):
            related_ref = object_refs_by_id.get(str(related_id))
            if related_ref and related_ref in seen_refs:
                links.append({"from": ref, "to": related_ref, "type": "involves_relationship_object"})
            else:
                diagnostics["unresolved_object_refs"].append({
                    "location": f"findings[{position}].related[{related_position}]",
                    "object_id": related_id,
                    "ref": related_ref,
                })

    diagnostics["invalid_refs"] = sorted(diagnostics["invalid_refs"], key=lambda item: (str(item.get("location", "")), str(item.get("ref", ""))))
    diagnostics["duplicate_refs"] = sorted(diagnostics["duplicate_refs"], key=lambda item: (str(item.get("ref", "")), str(item.get("location", ""))))
    diagnostics["unresolved_object_refs"] = sorted(diagnostics["unresolved_object_refs"], key=lambda item: (str(item.get("location", "")), str(item.get("object_id", ""))))
    diagnostics["valid"] = not diagnostics["invalid_refs"] and not diagnostics["duplicate_refs"] and not diagnostics["unresolved_object_refs"]

    nodes = sorted(nodes, key=lambda item: item["id"])
    links = sorted(links, key=lambda item: (item["from"], item["type"], item["to"]))
    return {
        "nodes": nodes,
        "links": links,
        "relationship_import_diagnostics": diagnostics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Data Relationship Map artifact index")
    parser.add_argument("index")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()
    graph = build_graph(load_json(args.index))
    payload = json.dumps(graph, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if graph["relationship_import_diagnostics"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
