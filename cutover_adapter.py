#!/usr/bin/env python3
"""Import Cutover Graph artifact indexes into Project Evidence Graph fragments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cross_repo import canonical_ref


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Cutover artifact index must be a JSON object")
    return value


def _ref(raw: Any, diagnostics: list[dict[str, Any]], location: str) -> str | None:
    value = str(raw or "").strip()
    try:
        return canonical_ref(value)
    except ValueError as exc:
        diagnostics.append({"location": location, "ref": value, "error": str(exc)})
        return None


def _external_refs(checkpoint: dict[str, Any]) -> list[str]:
    return sorted(
        {
            str(value).strip()
            for value in checkpoint.get("evidence_refs", [])
            if str(value).strip().startswith("eac://")
        }
    )


def _checkpoint_assurance(
    task: dict[str, Any], checkpoint: dict[str, Any], diagnostics: dict[str, Any]
) -> tuple[bool, str]:
    declared_passed = bool(checkpoint.get("passed"))
    external_refs = _external_refs(checkpoint)
    if not external_refs:
        return declared_passed, "native"

    verification_mode = str(checkpoint.get("verification_mode", "")).strip()
    external_evidence_passed = checkpoint.get("external_evidence_passed") is True
    verified = verification_mode == "external_registry" and external_evidence_passed
    assurance_passed = declared_passed and verified
    if not verified:
        diagnostics["unverified_external_checkpoints"].append(
            {
                "task": str(task.get("id", "")),
                "checkpoint_ref": checkpoint.get("artifact_ref"),
                "evidence_refs": external_refs,
                "declared_passed": declared_passed,
                "verification_mode": verification_mode or None,
                "external_evidence_passed": checkpoint.get("external_evidence_passed"),
                "reason": (
                    "missing_external_verification_metadata"
                    if not verification_mode
                    else "external_evidence_not_verified"
                ),
            }
        )
    return assurance_passed, "external_registry" if verified else "unverified_external"


def build_graph(index: dict[str, Any]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "source_index_valid": bool(index.get("valid")),
        "invalid_refs": [],
        "duplicate_refs": [],
        "unverified_external_checkpoints": [],
    }
    if index.get("schema_version") != "0.1":
        diagnostics["schema_error"] = "schema_version must be 0.1"
    if not diagnostics["source_index_valid"] or diagnostics.get("schema_error"):
        diagnostics["valid"] = False
        diagnostics["assurance_complete"] = False
        return {"nodes": [], "links": [], "external_bridges": [], "cutover_import_diagnostics": diagnostics}

    nodes: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    external_bridges: list[dict[str, Any]] = []
    seen_refs: set[str] = set()

    def add_node(node: dict[str, Any], location: str) -> None:
        ref = str(node.get("id", ""))
        if ref in seen_refs:
            diagnostics["duplicate_refs"].append({"location": location, "ref": ref})
            return
        seen_refs.add(ref)
        nodes.append(node)

    task_refs: set[str] = set()
    for position, task in enumerate(index.get("tasks", [])):
        if not isinstance(task, dict):
            diagnostics["invalid_refs"].append({"location": f"tasks[{position}]", "error": "task is not an object"})
            continue
        ref = _ref(task.get("artifact_ref"), diagnostics["invalid_refs"], f"tasks[{position}].artifact_ref")
        if ref is None:
            continue
        task_refs.add(ref)
        node: dict[str, Any] = {
            "id": ref,
            "artifact_ref": ref,
            "type": "change",
            "title": f"Cutover task {task.get('id', ref)}",
            "status": task.get("status"),
            "external": True,
            "external_source": "cutover-graph",
            "source": {"repository": "dkharlanau/cutover-graph"},
            "metadata": {
                "cutover_task_id": task.get("id"),
                "complete": bool(task.get("complete")),
                "owner": task.get("owner"),
                "workstream": task.get("workstream"),
                "duration_minutes": task.get("duration_minutes"),
            },
        }
        if task.get("risk") is not None:
            node["risk"] = task["risk"]
        if task.get("actual_end") is not None:
            node["updated_at"] = task["actual_end"]
        add_node(node, f"tasks[{position}]")

        checkpoint = task.get("checkpoint")
        if isinstance(checkpoint, dict):
            checkpoint_ref = _ref(checkpoint.get("artifact_ref"), diagnostics["invalid_refs"], f"tasks[{position}].checkpoint.artifact_ref")
            if checkpoint_ref is not None:
                assurance_passed, assurance_mode = _checkpoint_assurance(task, checkpoint, diagnostics)
                declared_passed = bool(checkpoint.get("passed"))
                external_refs = _external_refs(checkpoint)
                if assurance_passed:
                    status = "passed"
                elif declared_passed and external_refs:
                    status = "unverified"
                else:
                    status = "failed"
                checkpoint_node: dict[str, Any] = {
                    "id": checkpoint_ref,
                    "artifact_ref": checkpoint_ref,
                    "type": "evidence" if assurance_passed else "defect",
                    "title": f"Cutover checkpoint {task.get('id', checkpoint_ref)}",
                    "status": status,
                    "external": True,
                    "external_source": "cutover-graph",
                    "source": {"repository": "dkharlanau/cutover-graph"},
                    "metadata": {
                        "task_ref": ref,
                        "cutover_declared_passed": declared_passed,
                        "assurance_passed": assurance_passed,
                        "assurance_mode": assurance_mode,
                        "native_passed": checkpoint.get("native_passed"),
                        "verification_mode": checkpoint.get("verification_mode"),
                        "external_evidence_required": bool(external_refs),
                        "external_evidence_passed": checkpoint.get("external_evidence_passed"),
                        "verifications": checkpoint.get("verifications", []),
                        "required_approvals": checkpoint.get("required_approvals", []),
                        "required_evidence": checkpoint.get("required_evidence", []),
                        "missing_approvals": checkpoint.get("missing_approvals", []),
                        "missing_evidence": checkpoint.get("missing_evidence", []),
                        "duplicate_approvals": checkpoint.get("duplicate_approvals", []),
                        "duplicate_evidence": checkpoint.get("duplicate_evidence", []),
                        "evidence_refs": checkpoint.get("evidence_refs", []),
                    },
                }
                if task.get("actual_end") is not None:
                    checkpoint_node["observed_at"] = task["actual_end"]
                add_node(checkpoint_node, f"tasks[{position}].checkpoint")
                links.append({"from": ref, "to": checkpoint_ref, "type": "verified_by_checkpoint"})
                for evidence_position, evidence_ref in enumerate(checkpoint.get("evidence_refs", [])):
                    value = str(evidence_ref).strip()
                    if not value.startswith("eac://"):
                        continue
                    target = _ref(value, diagnostics["invalid_refs"], f"tasks[{position}].checkpoint.evidence_refs[{evidence_position}]")
                    if target is not None:
                        external_bridges.append({"from": checkpoint_ref, "to": target, "type": "substantiated_by"})

    for position, task in enumerate(index.get("tasks", [])):
        if not isinstance(task, dict):
            continue
        target = _ref(task.get("artifact_ref"), diagnostics["invalid_refs"], f"tasks[{position}].artifact_ref.dependencies")
        if target is None:
            continue
        for dependency_position, raw_dependency in enumerate(task.get("depends_on_refs", [])):
            dependency = _ref(raw_dependency, diagnostics["invalid_refs"], f"tasks[{position}].depends_on_refs[{dependency_position}]")
            if dependency is not None:
                links.append({"from": dependency, "to": target, "type": "precedes"})

    for branch_position, branch in enumerate(index.get("contingencies", [])):
        if not isinstance(branch, dict):
            continue
        branch_ref = _ref(branch.get("artifact_ref"), diagnostics["invalid_refs"], f"contingencies[{branch_position}].artifact_ref")
        if branch_ref is None:
            continue
        add_node({
            "id": branch_ref,
            "artifact_ref": branch_ref,
            "type": "decision",
            "title": f"Cutover contingency {branch.get('id', branch_ref)}",
            "status": "active" if branch.get("active") else "inactive",
            "external": True,
            "external_source": "cutover-graph",
            "source": {"repository": "dkharlanau/cutover-graph"},
            "metadata": {"activation": branch.get("activation")},
        }, f"contingencies[{branch_position}]")

        branch_task_refs: set[str] = set()
        for task_position, task in enumerate(branch.get("tasks", [])):
            if not isinstance(task, dict):
                continue
            ref = _ref(task.get("artifact_ref"), diagnostics["invalid_refs"], f"contingencies[{branch_position}].tasks[{task_position}].artifact_ref")
            if ref is None:
                continue
            branch_task_refs.add(ref)
            add_node({
                "id": ref,
                "artifact_ref": ref,
                "type": "change",
                "title": f"Contingency task {task.get('id', ref)}",
                "status": task.get("status"),
                "external": True,
                "external_source": "cutover-graph",
                "source": {"repository": "dkharlanau/cutover-graph"},
                "metadata": {
                    "contingency_ref": branch_ref,
                    "owner": task.get("owner"),
                    "workstream": task.get("workstream"),
                    "duration_minutes": task.get("duration_minutes"),
                },
            }, f"contingencies[{branch_position}].tasks[{task_position}]")
            links.append({"from": branch_ref, "to": ref, "type": "contains_contingency_task"})

        for task_position, task in enumerate(branch.get("tasks", [])):
            if not isinstance(task, dict):
                continue
            target = _ref(task.get("artifact_ref"), diagnostics["invalid_refs"], f"contingencies[{branch_position}].tasks[{task_position}].artifact_ref.dependencies")
            if target is None:
                continue
            for dependency_position, raw_dependency in enumerate(task.get("depends_on_refs", [])):
                dependency = _ref(raw_dependency, diagnostics["invalid_refs"], f"contingencies[{branch_position}].tasks[{task_position}].depends_on_refs[{dependency_position}]")
                if dependency is not None:
                    links.append({"from": dependency, "to": target, "type": "precedes"})

    diagnostics["duplicate_refs"] = sorted(diagnostics["duplicate_refs"], key=lambda item: (item.get("ref", ""), item.get("location", "")))
    diagnostics["unverified_external_checkpoints"] = sorted(
        diagnostics["unverified_external_checkpoints"],
        key=lambda item: (str(item.get("checkpoint_ref", "")), str(item.get("task", ""))),
    )
    diagnostics["valid"] = not diagnostics["invalid_refs"] and not diagnostics["duplicate_refs"]
    diagnostics["assurance_complete"] = not diagnostics["unverified_external_checkpoints"]
    links = sorted(links, key=lambda item: (item["from"], item["type"], item["to"]))
    external_bridges = sorted(external_bridges, key=lambda item: (item["from"], item["type"], item["to"]))
    nodes = sorted(nodes, key=lambda item: item["id"])
    return {
        "nodes": nodes,
        "links": links,
        "external_bridges": external_bridges,
        "cutover_import_diagnostics": diagnostics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Cutover Graph artifact index")
    parser.add_argument("index")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()
    graph = build_graph(load_json(args.index))
    payload = json.dumps(graph, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if graph["cutover_import_diagnostics"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
