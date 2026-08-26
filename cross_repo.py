#!/usr/bin/env python3
"""Materialize explicit eac:// cross-repository refs into Project Evidence Graph nodes."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit

from evidence_graph import TRACE_TYPES


TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _token(name: str, value: str) -> None:
    if not value or not TOKEN.fullmatch(value):
        raise ValueError(f"{name} must match {TOKEN.pattern}: {value!r}")


def canonical_ref(uri: str) -> str:
    parts = urlsplit(uri)
    if parts.scheme != "eac":
        raise ValueError("scheme must be eac")
    owner = unquote(parts.netloc)
    _token("owner", owner)
    segments = [unquote(segment) for segment in parts.path.split("/") if segment]
    if len(segments) < 3:
        raise ValueError("path must include repository/kind/local-id")
    repository, kind = segments[0], segments[1]
    _token("repository", repository)
    _token("kind", kind)
    local_segments = segments[2:]
    if any(not segment for segment in local_segments):
        raise ValueError("local-id contains empty segment")
    query = parse_qs(parts.query, keep_blank_values=True)
    unsupported = sorted(set(query) - {"version"})
    if unsupported:
        raise ValueError(f"unsupported query parameter(s): {unsupported}")
    versions = query.get("version", [])
    if len(versions) > 1:
        raise ValueError("version may be provided at most once")
    version = versions[0] if versions else None
    if version is not None and not version:
        raise ValueError("version must not be blank")
    path = "/".join([
        quote(repository, safe="._-"),
        quote(kind, safe="._-"),
        *[quote(segment, safe="._-:@") for segment in local_segments],
    ])
    suffix = f"?{urlencode({'version': version})}" if version else ""
    return f"eac://{quote(owner, safe='._-')}/{path}{suffix}"


def materialize(pack: dict[str, Any]) -> dict[str, Any]:
    nodes = [dict(node) for node in pack.get("nodes", [])]
    known_ids = {str(node.get("id")) for node in nodes if str(node.get("id", "")).strip()}
    external_ids: set[str] = set()
    duplicate_refs = []
    invalid_refs = []

    for index, artifact in enumerate(pack.get("external_artifacts", [])):
        raw_ref = str(artifact.get("ref", "")).strip()
        try:
            ref = canonical_ref(raw_ref)
        except ValueError as exc:
            invalid_refs.append({"index": index, "ref": raw_ref, "error": str(exc)})
            continue
        artifact_type = str(artifact.get("type", "")).strip()
        if artifact_type not in TRACE_TYPES:
            invalid_refs.append({"index": index, "ref": raw_ref, "error": f"unsupported evidence-graph type: {artifact_type!r}"})
            continue
        if ref in external_ids or ref in known_ids:
            duplicate_refs.append(ref)
            continue
        external_ids.add(ref)
        known_ids.add(ref)
        node: dict[str, Any] = {
            "id": ref,
            "artifact_ref": ref,
            "type": artifact_type,
            "external": True,
        }
        for field in ("title", "risk", "status", "observed_at", "updated_at"):
            if artifact.get(field) is not None:
                node[field] = artifact[field]
        if artifact.get("source") is not None:
            node["source"] = artifact["source"]
        if artifact.get("metadata") is not None:
            node["metadata"] = artifact["metadata"]
        nodes.append(node)

    links = []
    unresolved_refs = []
    invalid_link_refs = []
    seen: set[tuple[str, str, str]] = set()
    for index, link in enumerate(pack.get("links", [])):
        source = str(link.get("from", "")).strip()
        target = str(link.get("to", "")).strip()
        if link.get("from_ref") is not None:
            raw = str(link.get("from_ref", "")).strip()
            try:
                source = canonical_ref(raw)
            except ValueError as exc:
                invalid_link_refs.append({"index": index, "side": "from_ref", "ref": raw, "error": str(exc)})
                continue
        if link.get("to_ref") is not None:
            raw = str(link.get("to_ref", "")).strip()
            try:
                target = canonical_ref(raw)
            except ValueError as exc:
                invalid_link_refs.append({"index": index, "side": "to_ref", "ref": raw, "error": str(exc)})
                continue

        missing = [node_id for node_id in (source, target) if node_id not in known_ids]
        if missing:
            unresolved_refs.append({"index": index, "from": source, "to": target, "missing": missing})
            continue
        relation = str(link.get("type", "supports")).strip() or "supports"
        key = (source, relation, target)
        if key in seen:
            continue
        seen.add(key)
        resolved = {"from": source, "to": target, "type": relation}
        if link.get("provenance") is not None:
            resolved["provenance"] = link["provenance"]
        links.append(resolved)

    diagnostics = {
        "invalid_refs": invalid_refs,
        "duplicate_refs": sorted(set(duplicate_refs)),
        "invalid_link_refs": invalid_link_refs,
        "unresolved_refs": unresolved_refs,
    }
    return {"nodes": nodes, "links": links, "cross_repo_diagnostics": diagnostics}


def load_pack(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("cross-repository pack must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize eac:// cross-repository artifacts into an evidence graph")
    parser.add_argument("pack")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()
    graph = materialize(load_pack(args.pack))
    payload = json.dumps(graph, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    diagnostics = graph["cross_repo_diagnostics"]
    failed = any(diagnostics[key] for key in diagnostics)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
