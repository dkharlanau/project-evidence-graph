#!/usr/bin/env python3
"""Convert a saved GitHub Issues/PR export into a canonical Project Evidence Graph."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from evidence_graph import TRACE_TYPES


ISSUE_REF = re.compile(r"(?<![\w/])#(\d+)\b")


def _labels(item: dict[str, Any]) -> list[str]:
    values = []
    for label in item.get("labels", []) or []:
        if isinstance(label, str):
            values.append(label)
        elif isinstance(label, dict) and label.get("name"):
            values.append(str(label["name"]))
    return values


def _issue_type(issue: dict[str, Any], config: dict[str, Any]) -> str:
    explicit = issue.get("artifact_type")
    if explicit:
        artifact_type = str(explicit)
    else:
        mapping = {str(k).lower(): str(v) for k, v in config.get("label_type_map", {}).items()}
        artifact_type = ""
        for label in _labels(issue):
            if label.lower() in mapping:
                artifact_type = mapping[label.lower()]
                break
        if not artifact_type:
            artifact_type = str(config.get("default_issue_type", "requirement"))
    if artifact_type not in TRACE_TYPES:
        raise ValueError(f"unsupported issue artifact type: {artifact_type!r}")
    return artifact_type


def _item_id(repository: str, kind: str, number: int | str) -> str:
    return f"GH:{repository}:{kind}:{int(number)}"


def _provenance(repository: str, kind: str, number: int, url: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {"source": "github-export", "repository": repository, "kind": kind, "number": number}
    if url:
        result["url"] = url
    return result


def _explicit_issue_refs(pr: dict[str, Any]) -> list[int]:
    refs = set()
    for value in pr.get("linked_issues", []) or []:
        if isinstance(value, dict):
            value = value.get("number")
        if value is not None:
            refs.add(int(value))
    body = str(pr.get("body") or "")
    refs.update(int(match) for match in ISSUE_REF.findall(body))
    return sorted(refs)


def build_graph(export: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or {}
    repository = str(export.get("repository") or config.get("repository") or "").strip()
    if not repository or "/" not in repository:
        raise ValueError("repository must be supplied as 'owner/name'")

    nodes = []
    links = []
    issue_types: dict[int, str] = {}
    issue_numbers: set[int] = set()
    unresolved = []

    for issue in export.get("issues", []) or []:
        number = int(issue["number"])
        artifact_type = _issue_type(issue, config)
        issue_types[number] = artifact_type
        issue_numbers.add(number)
        node = {
            "id": _item_id(repository, "ISSUE", number),
            "type": artifact_type,
            "title": str(issue.get("title") or f"Issue #{number}"),
            "state": str(issue.get("state") or ""),
            "labels": _labels(issue),
            "provenance": _provenance(repository, "issue", number, issue.get("html_url") or issue.get("url")),
        }
        for field in ("created_at", "updated_at", "closed_at"):
            if issue.get(field):
                node[field] = issue[field]
        nodes.append(node)

    pr_type = str(config.get("pull_request_type", "change"))
    if pr_type not in TRACE_TYPES:
        raise ValueError(f"unsupported pull request artifact type: {pr_type!r}")
    link_type_map = {str(k): str(v) for k, v in config.get("link_type_by_issue_type", {}).items()}

    for pr in export.get("pull_requests", []) or []:
        number = int(pr["number"])
        pr_id = _item_id(repository, "PR", number)
        node = {
            "id": pr_id,
            "type": pr_type,
            "title": str(pr.get("title") or f"Pull request #{number}"),
            "state": str(pr.get("state") or ""),
            "provenance": _provenance(repository, "pull_request", number, pr.get("html_url") or pr.get("url")),
        }
        for field in ("created_at", "updated_at", "closed_at", "merged_at"):
            if pr.get(field):
                node[field] = pr[field]
        if pr.get("head_sha"):
            node["head_sha"] = str(pr["head_sha"])
        nodes.append(node)

        for issue_number in _explicit_issue_refs(pr):
            if issue_number not in issue_numbers:
                unresolved.append({"pull_request": number, "issue": issue_number})
                continue
            issue_id = _item_id(repository, "ISSUE", issue_number)
            issue_type = issue_types[issue_number]
            relation = link_type_map.get(issue_type, "implemented_by" if issue_type != "defect" else "fixed_by")
            links.append({
                "from": issue_id,
                "to": pr_id,
                "type": relation,
                "provenance": {"source": "explicit-github-reference", "pull_request": number, "issue": issue_number},
            })

    return {
        "nodes": nodes,
        "links": links,
        "import_diagnostics": {"unresolved_issue_references": unresolved},
    }


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert GitHub issue/PR export JSON into Project Evidence Graph")
    parser.add_argument("export")
    parser.add_argument("--config")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    export = load_json(args.export)
    config = load_json(args.config) if args.config else {}
    graph = build_graph(export, config)
    payload = json.dumps(graph, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
