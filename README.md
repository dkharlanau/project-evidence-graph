# Project Evidence Graph

Connect requirements, decisions, mappings, interfaces, tests, defects, changes, and evidence into one traceable project graph.

## Why this exists

Project rationale disappears because requirements, mappings, tests, defects, changes, decisions, and evidence live in separate systems. A spreadsheet traceability matrix helps for a moment, but it is usually manual, stale, and hard to query.

Project Evidence Graph models traceability as data first. A matrix, quality gate, evidence pack, or visual explorer becomes a generated view of the graph rather than the source of truth.

## Current MVP

The repository now includes a zero-dependency Python engine that can:

- validate project artifact nodes and links
- detect duplicate nodes and links
- detect broken references
- trace directed paths from one artifact to another
- calculate requirement-to-test coverage
- calculate requirement-to-evidence coverage
- generate traceability-matrix data per requirement
- enforce machine-readable quality policies in CI
- browse evidence, relationship, and cutover graphs in a reusable zero-build HTML explorer

This absorbs the useful core of three previously separate product ideas:

- `traceability-matrix` -> generated from the evidence graph
- `quality-gate-as-code` -> implemented as `quality_gate.py`
- `github-pages-explorer` -> implemented as `docs/index.html`

Keeping these capabilities together avoids three thin repositories while the interfaces are still evolving.

## Quick start

```bash
python evidence_graph.py examples/customer-change.json analyze
python evidence_graph.py examples/customer-change.json path REQ-001 EVID-001
python quality_gate.py examples/customer-change.json examples/quality-policy.json
python -m unittest discover -s tests -v
```

The bundled example deliberately contains a second requirement without tests or evidence. The report therefore exposes a real traceability gap instead of only demonstrating a perfect graph.

## Quality policy

```json
{
  "require_valid_graph": true,
  "min_test_coverage": 0.5,
  "min_evidence_coverage": 0.5,
  "max_requirements_without_tests": 1,
  "max_requirements_without_evidence": 1
}
```

The command exits non-zero when the policy fails, so the same rule set can become a GitHub Actions quality gate.

## Reusable graph explorer

Open `docs/index.html` directly in a browser. No build step or external JavaScript dependency is required.

The explorer accepts three canonical shapes:

- Project Evidence Graph: `nodes` + `links`
- Data Relationship Map: `nodes` + `relationships`
- Cutover Graph: `tasks` + `depends_on`

It supports local JSON loading, filtering, grouped SVG visualization, and node/connection inspection. This makes it reusable across the repository family without coupling the projects to a frontend framework.

## Canonical model

```json
{
  "nodes": [
    {"id": "REQ-001", "type": "requirement"},
    {"id": "DEC-001", "type": "decision"},
    {"id": "TEST-001", "type": "test"},
    {"id": "EVID-001", "type": "evidence"}
  ],
  "links": [
    {"from": "REQ-001", "to": "DEC-001", "type": "resolved_by"},
    {"from": "DEC-001", "to": "TEST-001", "type": "verified_by"},
    {"from": "TEST-001", "to": "EVID-001", "type": "produced"}
  ]
}
```

Supported first-class artifact types are `requirement`, `decision`, `mapping`, `interface`, `test`, `defect`, `change`, and `evidence`.

## Product direction

1. Import adapters for GitHub Issues, Jira/CSV exports, ALM exports, and mapping repositories.
2. Bidirectional impact analysis: “what changes if this requirement/interface changes?”
3. Evidence freshness and provenance.
4. Generated Markdown/HTML release and audit reports.
5. Cross-repository references to Mapping as Code, Interface as Code, Process as Code, and Cutover Graph.
6. Machine-readable project context for AI agents.
7. Release/cutover evidence packs generated from the graph.

## Design principles

- versionable
- portable
- machine-readable
- deterministic-first
- visual where useful
- Git-friendly
- vendor-neutral where practical
- interoperable with enterprise tools

## Related projects

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code)
- [Transformation Graph](https://github.com/dkharlanau/transformation-graph)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph)
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code)
- [Data Relationship Map](https://github.com/dkharlanau/data-relationship-map)
- [Cutover Graph](https://github.com/dkharlanau/cutover-graph)

## Status

**MVP / active development.** Validation, directed traceability, coverage metrics, quality gates, reusable graph exploration, examples, tests, and CI are implemented.
