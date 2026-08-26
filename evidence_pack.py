#!/usr/bin/env python3
"""Build and verify integrity-protected Project Evidence Graph review packs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from evidence_freshness import load_policy as load_freshness_policy
from evidence_graph import _index, load_graph
from project_context import bounded_ids, build_context
from project_review import build_summary, render_html, render_markdown
from quality_gate import load_policy as load_quality_policy
from risk_assurance import load_policy as load_risk_policy


PACK_FILES = ("graph.json", "context.json", "review.md", "review.html")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _semantic_sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_info(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slice_graph(graph: dict[str, Any], focus: str | None, depth: int) -> dict[str, Any]:
    selected = bounded_ids(graph, focus, depth)
    if focus is not None and not selected:
        raise ValueError(f"focus artifact not found: {focus}")
    nodes, _ = _index(graph)
    result = {key: value for key, value in graph.items() if key not in {"nodes", "links"}}
    result["nodes"] = [nodes[node_id] for node_id in sorted(selected)]
    result["links"] = sorted(
        [
            dict(link)
            for link in graph.get("links", [])
            if str(link.get("from", "")) in selected and str(link.get("to", "")) in selected
        ],
        key=lambda item: (str(item.get("from")), str(item.get("type", "supports")), str(item.get("to")), json.dumps(item, sort_keys=True)),
    )
    return result


def _policy_fingerprints(
    quality_policy: dict[str, Any] | None,
    freshness_policy: dict[str, Any] | None,
    risk_policy: dict[str, Any] | None,
) -> dict[str, str | None]:
    return {
        "quality": _semantic_sha(quality_policy) if quality_policy is not None else None,
        "freshness": _semantic_sha(freshness_policy) if freshness_policy is not None else None,
        "risk": _semantic_sha(risk_policy) if risk_policy is not None else None,
    }


def _pack_id(graph: dict[str, Any], focus: str | None, depth: int, policy_fingerprints: dict[str, str | None]) -> str:
    semantic = {
        "focus": focus,
        "depth": depth,
        "nodes": graph.get("nodes", []),
        "links": graph.get("links", []),
        "policy_fingerprints": policy_fingerprints,
    }
    return "pack-" + _semantic_sha(semantic)[:20]


def build_pack(
    graph: dict[str, Any],
    output_dir: str | Path,
    focus: str | None = None,
    depth: int = 3,
    quality_policy: dict[str, Any] | None = None,
    freshness_policy: dict[str, Any] | None = None,
    risk_policy: dict[str, Any] | None = None,
    source_graph_sha256: str | None = None,
) -> dict[str, Any]:
    if depth < 0:
        raise ValueError("depth must be >= 0")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    bounded = slice_graph(graph, focus, depth)
    summary = build_summary(bounded, quality_policy, freshness_policy, risk_policy)
    context = build_context(bounded, focus, depth, quality_policy, freshness_policy, risk_policy)
    policy_fingerprints = _policy_fingerprints(quality_policy, freshness_policy, risk_policy)
    pack_id = _pack_id(bounded, focus, depth, policy_fingerprints)

    graph_path = output / "graph.json"
    context_path = output / "context.json"
    markdown_path = output / "review.md"
    html_path = output / "review.html"

    _write_json(graph_path, bounded)
    _write_json(context_path, context)
    markdown_path.write_text(render_markdown(summary, "Project Evidence Pack Review"), encoding="utf-8")
    html_path.write_text(render_html(summary, "Project Evidence Pack Review"), encoding="utf-8")

    files = {name: _file_info(output / name) for name in PACK_FILES}
    manifest = {
        "format_version": "1.0",
        "pack_id": pack_id,
        "focus": focus,
        "depth": depth,
        "decision": summary["decision"],
        "passed": summary["passed"],
        "source_graph_sha256": source_graph_sha256,
        "policy_fingerprints": policy_fingerprints,
        "scope": {
            "node_count": len(bounded.get("nodes", [])),
            "link_count": len(bounded.get("links", [])),
            "context_id": context.get("context_id"),
        },
        "files": files,
    }
    _write_json(output / "manifest.json", manifest)
    return manifest


def verify_pack(pack_dir: str | Path) -> dict[str, Any]:
    root = Path(pack_dir)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        return {"valid": False, "errors": ["manifest.json is missing"], "files": {}}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"valid": False, "errors": [f"cannot read manifest.json: {exc}"], "files": {}}

    errors: list[str] = []
    file_results: dict[str, Any] = {}
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        return {"valid": False, "errors": ["manifest.files must be an object"], "files": {}}

    for name in sorted(files):
        expected = files[name]
        path = root / name
        if not path.exists():
            errors.append(f"missing file: {name}")
            file_results[name] = {"valid": False, "error": "missing"}
            continue
        actual = _file_info(path)
        valid = actual == expected
        file_results[name] = {"valid": valid, "expected": expected, "actual": actual}
        if not valid:
            errors.append(f"file integrity mismatch: {name}")

    graph_path = root / "graph.json"
    if graph_path.exists():
        try:
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            expected_pack_id = _pack_id(
                graph,
                manifest.get("focus"),
                int(manifest.get("depth", 0)),
                manifest.get("policy_fingerprints", {}),
            )
            if expected_pack_id != manifest.get("pack_id"):
                errors.append("pack_id does not match semantic graph/scope/policy identity")
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append(f"cannot validate pack_id: {exc}")

    return {"valid": not errors, "errors": errors, "files": file_results, "pack_id": manifest.get("pack_id")}


def _source_sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify Project Evidence Graph evidence packs")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("graph")
    build.add_argument("output_dir")
    build.add_argument("--focus")
    build.add_argument("--depth", type=int, default=3)
    build.add_argument("--quality-policy")
    build.add_argument("--freshness-policy")
    build.add_argument("--risk-policy")

    verify = sub.add_parser("verify")
    verify.add_argument("pack_dir")

    args = parser.parse_args()
    if args.command == "verify":
        result = verify_pack(args.pack_dir)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1

    graph = load_graph(args.graph)
    manifest = build_pack(
        graph,
        args.output_dir,
        args.focus,
        args.depth,
        load_quality_policy(args.quality_policy) if args.quality_policy else None,
        load_freshness_policy(args.freshness_policy) if args.freshness_policy else None,
        load_risk_policy(args.risk_policy) if args.risk_policy else None,
        _source_sha(args.graph),
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
