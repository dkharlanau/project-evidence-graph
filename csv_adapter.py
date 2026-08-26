#!/usr/bin/env python3
"""Convert ordinary CSV project exports into a canonical Project Evidence Graph."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def render(template: str, row: dict[str, str]) -> str:
    try:
        return template.format_map(row)
    except KeyError as exc:
        raise ValueError(f"missing CSV column {exc.args[0]!r} required by template {template!r}") from exc


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            yield row_number, dict(row)


def build_graph(manifest: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    nodes = []
    links = []

    for source in manifest.get("artifact_sources", []):
        source_path = base_dir / source["file"]
        for row_number, row in rows(source_path):
            node_id = render(source["id"], row).strip()
            if not node_id:
                continue
            node = {
                "id": node_id,
                "type": render(source["type"], row).strip(),
                "provenance": {"file": source["file"], "row": row_number},
            }
            if source.get("title"):
                node["title"] = render(source["title"], row).strip()
            for target_field, template in source.get("fields", {}).items():
                node[str(target_field)] = render(str(template), row).strip()
            nodes.append(node)

    for source in manifest.get("link_sources", []):
        source_path = base_dir / source["file"]
        for row_number, row in rows(source_path):
            from_id = render(source["from"], row).strip()
            to_id = render(source["to"], row).strip()
            if not from_id or not to_id:
                continue
            links.append({
                "from": from_id,
                "to": to_id,
                "type": render(source.get("type", "supports"), row).strip() or "supports",
                "provenance": {"file": source["file"], "row": row_number},
            })

    return {"nodes": nodes, "links": links}


def load_manifest(path: str | Path) -> tuple[dict[str, Any], Path]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    return manifest, manifest_path.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert CSV project exports into a Project Evidence Graph")
    parser.add_argument("manifest")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    manifest, base_dir = load_manifest(args.manifest)
    graph = build_graph(manifest, base_dir)
    payload = json.dumps(graph, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
