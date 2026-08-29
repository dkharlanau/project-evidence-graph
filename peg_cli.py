#!/usr/bin/env python3
"""Unified command dispatcher for Project Evidence Graph."""

from __future__ import annotations

import sys
from collections.abc import Callable

import assurance_diff
import cross_repo
import csv_adapter
import cutover_adapter
import evidence_freshness
import evidence_graph
import evidence_pack
import github_adapter
import graph_merge
import project_context
import project_review
import quality_gate
import reconciliation_adapter
import risk_assurance
import workitem_adapter


Main = Callable[[], int]


COMMANDS: dict[str, tuple[Main, str]] = {
    "review": (project_review.main, "Generate the consolidated project assurance review"),
    "history": (assurance_diff.main, "Compare historical assurance and traceability state"),
    "context": (project_context.main, "Build bounded project context for a focus artifact"),
    "pack": (evidence_pack.main, "Build or verify a deterministic evidence pack"),
    "quality": (quality_gate.main, "Evaluate project traceability quality policy"),
    "freshness": (evidence_freshness.main, "Evaluate evidence freshness policy"),
    "risk": (risk_assurance.main, "Evaluate risk-weighted assurance policy"),
    "merge": (graph_merge.main, "Merge independently owned evidence fragments"),
    "cross-repo": (cross_repo.main, "Build explicit cross-repository traceability"),
    "import-csv": (csv_adapter.main, "Import CSV requirements, tests and explicit links"),
    "import-github": (github_adapter.main, "Import saved GitHub issue/PR exports"),
    "import-workitems": (workitem_adapter.main, "Import Jira or profile-driven ALM work items"),
    "import-reconciliation": (reconciliation_adapter.main, "Import Reconciliation-as-Code evidence"),
    "import-cutover": (cutover_adapter.main, "Import Cutover Graph artifact/evidence state"),
}


def _usage() -> str:
    rows = [
        "Project Evidence Graph — traceability and evidence-backed project assurance",
        "",
        "Usage:",
        "  project-evidence-graph analyze GRAPH",
        "  project-evidence-graph path GRAPH FROM_ID TO_ID",
        "  project-evidence-graph impact GRAPH NODE_ID",
        "  project-evidence-graph COMMAND [ARGS...]",
        "",
        "Commands:",
        "  analyze                  Validate and summarize traceability coverage",
        "  path                     Trace an explicit evidence/traceability path",
        "  impact                   Show upstream/downstream impact for an artifact",
    ]
    width = max(len(name) for name in COMMANDS)
    for name, (_, description) in COMMANDS.items():
        rows.append(f"  {name.ljust(width)}  {description}")
    rows += ["", "Use `project-evidence-graph COMMAND --help` for command-specific arguments."]
    return "\n".join(rows)


def _invoke(main_fn: Main, program: str, args: list[str]) -> int:
    previous = sys.argv
    sys.argv = [program, *args]
    try:
        return int(main_fn())
    finally:
        sys.argv = previous


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        print(_usage())
        return 0

    command, rest = args[0], args[1:]

    if command == "analyze":
        if not rest:
            print("project-evidence-graph analyze: GRAPH is required", file=sys.stderr)
            return 2
        return _invoke(evidence_graph.main, "project-evidence-graph analyze", [rest[0], "analyze", *rest[1:]])

    if command == "path":
        if len(rest) < 3:
            print("project-evidence-graph path: GRAPH FROM_ID TO_ID are required", file=sys.stderr)
            return 2
        return _invoke(evidence_graph.main, "project-evidence-graph path", [rest[0], "path", rest[1], rest[2], *rest[3:]])

    if command == "impact":
        if len(rest) < 2:
            print("project-evidence-graph impact: GRAPH NODE_ID are required", file=sys.stderr)
            return 2
        return _invoke(evidence_graph.main, "project-evidence-graph impact", [rest[0], "impact", rest[1], *rest[2:]])

    target = COMMANDS.get(command)
    if target is None:
        print(f"Unknown command: {command}\n", file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return 2

    main_fn, _ = target
    return _invoke(main_fn, f"project-evidence-graph {command}", rest)


if __name__ == "__main__":
    raise SystemExit(main())
