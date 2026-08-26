#!/usr/bin/env python3
"""Generate consolidated Markdown/HTML assurance reviews from Project Evidence Graph."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from evidence_freshness import evaluate as evaluate_freshness
from evidence_freshness import load_policy as load_freshness_policy
from evidence_graph import build_report, load_graph
from quality_gate import evaluate as evaluate_quality
from quality_gate import load_policy as load_quality_policy
from risk_assurance import evaluate as evaluate_risk
from risk_assurance import load_policy as load_risk_policy


def build_summary(
    graph: dict[str, Any],
    quality_policy: dict[str, Any] | None = None,
    freshness_policy: dict[str, Any] | None = None,
    risk_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = build_report(graph)
    quality = evaluate_quality(base, quality_policy) if quality_policy is not None else None
    freshness = evaluate_freshness(graph, freshness_policy) if freshness_policy is not None else None
    risk = evaluate_risk(graph, risk_policy) if risk_policy is not None else None

    gate_results = [base["validation"]["valid"]]
    for section in (quality, freshness, risk):
        if section is not None:
            gate_results.append(bool(section["passed"]))

    trace = base["traceability"]
    return {
        "passed": all(gate_results),
        "decision": "PASS" if all(gate_results) else "FAIL",
        "validation": base["validation"],
        "raw_coverage": {
            "test_coverage": trace["test_coverage"],
            "evidence_coverage": trace["evidence_coverage"],
            "requirements_without_tests": trace["requirements_without_tests"],
            "requirements_without_evidence": trace["requirements_without_evidence"],
        },
        "quality_policy": quality,
        "freshness_policy": freshness,
        "risk_policy": risk,
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _items(values: list[Any]) -> str:
    return ", ".join(str(value) for value in values) if values else "none"


def render_markdown(summary: dict[str, Any], title: str = "Project Assurance Review") -> str:
    raw = summary["raw_coverage"]
    freshness = summary.get("freshness_policy")
    risk = summary.get("risk_policy")
    quality = summary.get("quality_policy")

    lines = [
        f"# {title}",
        "",
        f"**Decision: {summary['decision']}**",
        "",
        "## Scorecard",
        "",
        "| Signal | Result |",
        "|---|---:|",
        f"| Graph valid | {'yes' if summary['validation']['valid'] else 'no'} |",
        f"| Raw test coverage | {_pct(raw['test_coverage'])} |",
        f"| Raw evidence coverage | {_pct(raw['evidence_coverage'])} |",
    ]
    if freshness is not None:
        lines.append(f"| Fresh evidence coverage | {_pct(freshness['fresh_evidence_coverage'])} |")
    if risk is not None:
        lines.append(f"| Risk-weighted test coverage | {_pct(risk['weighted_test_coverage'])} |")
        lines.append(f"| Risk-weighted evidence coverage | {_pct(risk['weighted_evidence_coverage'])} |")
        lines.append(f"| Uncovered test risk score | {risk['uncovered_test_risk_score']:.2f} |")
        lines.append(f"| Uncovered evidence risk score | {risk['uncovered_evidence_risk_score']:.2f} |")

    lines += [
        "",
        "## Assurance gaps",
        "",
        f"- Requirements without tests: {_items(raw['requirements_without_tests'])}",
        f"- Requirements without evidence: {_items(raw['requirements_without_evidence'])}",
    ]
    if freshness is not None:
        lines.append(f"- Requirements without fresh evidence: {_items(freshness['requirements_without_fresh_evidence'])}")
        lines.append(f"- Stale evidence: {_items([item['evidence'] for item in freshness['stale']])}")
        lines.append(f"- Missing evidence timestamp: {_items([item['evidence'] for item in freshness['missing_timestamp']])}")
    if risk is not None:
        uncovered_test = [row["requirement"] for row in risk["requirements"] if not row["test_covered"]]
        uncovered_evidence = [row["requirement"] for row in risk["requirements"] if not row["evidence_covered"]]
        lines.append(f"- Risk-weighted test gaps: {_items(uncovered_test)}")
        lines.append(f"- Risk-weighted evidence gaps: {_items(uncovered_evidence)}")
        lines.append(f"- Unknown requirement risk: {_items([item['requirement'] for item in risk['unknown_risks']])}")

    lines += ["", "## Policy gates", ""]
    if quality is None and freshness is None and risk is None:
        lines.append("No optional policy files were supplied; the decision reflects graph validity only.")
    else:
        for name, result in (("Quality", quality), ("Freshness", freshness), ("Risk", risk)):
            if result is None:
                continue
            lines.append(f"### {name}")
            lines.append("")
            lines.append(f"Result: **{'PASS' if result['passed'] else 'FAIL'}**")
            failed = result.get("failed_checks", [])
            lines.append(f"Failed checks: {_items(failed)}")
            lines.append("")

    lines += [
        "## Machine summary",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
        "",
    ]
    return "\n".join(lines)


def render_html(summary: dict[str, Any], title: str = "Project Assurance Review") -> str:
    raw = summary["raw_coverage"]
    freshness = summary.get("freshness_policy")
    risk = summary.get("risk_policy")
    rows = [
        ("Graph valid", "yes" if summary["validation"]["valid"] else "no"),
        ("Raw test coverage", _pct(raw["test_coverage"])),
        ("Raw evidence coverage", _pct(raw["evidence_coverage"])),
    ]
    if freshness is not None:
        rows.append(("Fresh evidence coverage", _pct(freshness["fresh_evidence_coverage"])))
    if risk is not None:
        rows += [
            ("Risk-weighted test coverage", _pct(risk["weighted_test_coverage"])),
            ("Risk-weighted evidence coverage", _pct(risk["weighted_evidence_coverage"])),
            ("Uncovered test risk", f"{risk['uncovered_test_risk_score']:.2f}"),
            ("Uncovered evidence risk", f"{risk['uncovered_evidence_risk_score']:.2f}"),
        ]
    score_rows = "".join(f"<tr><td>{html.escape(label)}</td><td>{html.escape(str(value))}</td></tr>" for label, value in rows)

    gaps = [
        f"Requirements without tests: {_items(raw['requirements_without_tests'])}",
        f"Requirements without evidence: {_items(raw['requirements_without_evidence'])}",
    ]
    if freshness is not None:
        gaps.append(f"Requirements without fresh evidence: {_items(freshness['requirements_without_fresh_evidence'])}")
        gaps.append(f"Stale evidence: {_items([item['evidence'] for item in freshness['stale']])}")
    if risk is not None:
        gaps.append(f"Unknown requirement risk: {_items([item['requirement'] for item in risk['unknown_risks']])}")
    gap_html = "".join(f"<li>{html.escape(item)}</li>" for item in gaps)
    machine = html.escape(json.dumps(summary, indent=2, sort_keys=True))

    decision_class = "pass" if summary["passed"] else "fail"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>{html.escape(title)}</title>
<style>
body{{font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#171717;background:#fafafa}}
header{{display:flex;align-items:end;justify-content:space-between;gap:24px;border-bottom:1px solid #ddd;padding-bottom:18px}}
h1{{font-size:32px;margin:0}} .decision{{font-size:18px;font-weight:700;padding:8px 14px;border:1px solid #aaa;border-radius:999px}}
.decision.pass{{background:#f1f8f3}} .decision.fail{{background:#fff2f2}}
section{{margin-top:32px}} table{{width:100%;border-collapse:collapse;background:white}} td{{padding:12px;border-bottom:1px solid #eee}} td:last-child{{text-align:right;font-variant-numeric:tabular-nums}}
pre{{white-space:pre-wrap;word-break:break-word;background:#111;color:#eee;padding:18px;border-radius:8px;font-size:12px}} li{{margin:8px 0}}
</style>
</head>
<body>
<header><h1>{html.escape(title)}</h1><div class=\"decision {decision_class}\">{summary['decision']}</div></header>
<section><h2>Scorecard</h2><table>{score_rows}</table></section>
<section><h2>Assurance gaps</h2><ul>{gap_html}</ul></section>
<section><h2>Machine summary</h2><pre>{machine}</pre></section>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate consolidated project assurance review")
    parser.add_argument("graph")
    parser.add_argument("--quality-policy")
    parser.add_argument("--freshness-policy")
    parser.add_argument("--risk-policy")
    parser.add_argument("--markdown")
    parser.add_argument("--html")
    parser.add_argument("--title", default="Project Assurance Review")
    args = parser.parse_args()

    graph = load_graph(args.graph)
    summary = build_summary(
        graph,
        load_quality_policy(args.quality_policy) if args.quality_policy else None,
        load_freshness_policy(args.freshness_policy) if args.freshness_policy else None,
        load_risk_policy(args.risk_policy) if args.risk_policy else None,
    )
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(summary, args.title), encoding="utf-8")
    if args.html:
        Path(args.html).write_text(render_html(summary, args.title), encoding="utf-8")
    if not args.markdown and not args.html:
        print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
