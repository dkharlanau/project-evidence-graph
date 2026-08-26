#!/usr/bin/env python3
"""Import Reconciliation-as-Code evidence schema v1 into Project Evidence Graph."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from cross_repo import canonical_ref


SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Reconciliation-as-Code evidence must be a JSON object")
    return value


def _ref(*segments: str) -> str:
    encoded = "/".join(quote(str(segment), safe="._-:@") for segment in segments)
    return canonical_ref(f"eac://dkharlanau/reconciliation-as-code/reconciliation/{encoded}")


def validate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    required = [
        "schema_version", "spec_version", "engine_version", "configuration_sha256",
        "run", "reconciliation", "status", "generated_at", "inputs", "summary", "checks",
    ]
    for field in required:
        if field not in evidence:
            errors.append(f"missing required field: {field}")

    if evidence.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if evidence.get("spec_version") != 1:
        errors.append("spec_version must be 1")
    if evidence.get("status") not in {"passed", "failed"}:
        errors.append("status must be passed or failed")
    if not str(evidence.get("reconciliation", "")).strip():
        errors.append("reconciliation must not be empty")
    if not str(evidence.get("generated_at", "")).strip():
        errors.append("generated_at must not be empty")

    configuration_sha = str(evidence.get("configuration_sha256", ""))
    if configuration_sha and not SHA256.fullmatch(configuration_sha):
        errors.append("configuration_sha256 must be lowercase SHA-256")

    run = evidence.get("run")
    if not isinstance(run, dict) or not str(run.get("id", "")).strip():
        errors.append("run.id is required")

    inputs = evidence.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("inputs must be an object")
    else:
        for required_input in ("source", "target"):
            item = inputs.get(required_input)
            if not isinstance(item, dict):
                errors.append(f"inputs.{required_input} is required")
                continue
            sha = str(item.get("sha256", ""))
            if not SHA256.fullmatch(sha):
                errors.append(f"inputs.{required_input}.sha256 must be lowercase SHA-256")
            if not str(item.get("path", "")).strip():
                errors.append(f"inputs.{required_input}.path is required")

    checks = evidence.get("checks")
    duplicate_check_ids: list[str] = []
    if not isinstance(checks, list):
        errors.append("checks must be an array")
        checks = []
    seen: set[str] = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            errors.append(f"checks[{index}] must be an object")
            continue
        check_id = str(check.get("id", "")).strip()
        if not check_id:
            errors.append(f"checks[{index}].id is required")
        elif check_id in seen:
            duplicate_check_ids.append(check_id)
        seen.add(check_id)
        if check.get("status") not in {"passed", "failed"}:
            errors.append(f"checks[{index}].status must be passed or failed")
        if check.get("severity") not in {"error", "warning"}:
            errors.append(f"checks[{index}].severity must be error or warning")
        if not str(check.get("type", "")).strip():
            errors.append(f"checks[{index}].type is required")

    return {
        "valid": not errors and not duplicate_check_ids,
        "errors": errors,
        "duplicate_check_ids": sorted(set(duplicate_check_ids)),
    }


def build_graph(evidence: dict[str, Any]) -> dict[str, Any]:
    validation = validate_evidence(evidence)
    if not validation["valid"]:
        return {"nodes": [], "links": [], "reconciliation_import_diagnostics": validation}

    name = str(evidence["reconciliation"]).strip()
    run_id = str(evidence["run"]["id"]).strip()
    observed_at = str(evidence["generated_at"]).strip()
    run_ref = _ref(name, "run", run_id)
    run_passed = evidence["status"] == "passed"

    run_node: dict[str, Any] = {
        "id": run_ref,
        "artifact_ref": run_ref,
        "type": "evidence" if run_passed else "defect",
        "title": f"Reconciliation {name} run {run_id}",
        "status": evidence["status"],
        "observed_at": observed_at,
        "external": True,
        "external_source": "reconciliation-as-code",
        "source": {
            "repository": "dkharlanau/reconciliation-as-code",
            "schema": "schema/evidence.schema.json",
            "schema_version": evidence["schema_version"],
            "spec_version": evidence["spec_version"],
            "engine_version": evidence["engine_version"],
        },
        "metadata": {
            "reconciliation": name,
            "run": evidence["run"],
            "configuration_sha256": evidence["configuration_sha256"],
            "inputs": evidence["inputs"],
            "summary": evidence["summary"],
        },
    }

    nodes = [run_node]
    links = []
    for check in evidence["checks"]:
        check_id = str(check["id"]).strip()
        check_ref = _ref(name, "run", run_id, "check", check_id)
        passed = check["status"] == "passed"
        check_node: dict[str, Any] = {
            "id": check_ref,
            "artifact_ref": check_ref,
            "type": "evidence" if passed else "defect",
            "title": f"Reconciliation check {check_id}",
            "status": check["status"],
            "observed_at": observed_at,
            "external": True,
            "external_source": "reconciliation-as-code",
            "metadata": {
                "reconciliation": name,
                "run_id": run_id,
                "check_id": check_id,
                "check_type": check["type"],
                "severity": check["severity"],
                "metrics": check.get("metrics", {}),
                "details_truncated": bool(check.get("details_truncated", False)),
            },
        }
        nodes.append(check_node)
        links.append({"from": run_ref, "to": check_ref, "type": "contains_check"})

    return {
        "nodes": nodes,
        "links": links,
        "reconciliation_import_diagnostics": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Reconciliation-as-Code evidence v1")
    parser.add_argument("evidence")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    graph = build_graph(load_json(args.evidence))
    payload = json.dumps(graph, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if graph["reconciliation_import_diagnostics"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
