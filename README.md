# Project Evidence Graph

Connect requirements, decisions, mappings, interfaces, tests, defects, changes, and evidence into one traceable project graph.

## Why this exists

Project rationale disappears because requirements, mappings, tests, defects, changes, decisions, and evidence live in separate systems. A spreadsheet traceability matrix helps for a moment, but it is usually manual, stale, and hard to query.

Project Evidence Graph models traceability as data first. A matrix, quality gate, impact report, evidence pack, or visual explorer becomes a generated view of the graph rather than the source of truth.

## Current capabilities

- import ordinary CSV requirements/tests/links through a manifest
- preserve source file + row provenance
- validate artifact nodes and links
- detect duplicate nodes/links, broken references, and invalid artifact types
- trace directed paths between artifacts
- calculate requirement-to-test and requirement-to-evidence coverage
- generate traceability-matrix data per requirement
- run upstream/downstream impact analysis for any artifact
- enforce machine-readable quality policies in CI
- browse evidence, relationship, and cutover graphs in a reusable zero-build HTML explorer

This repository absorbs the useful core of three previously separate ideas:

- `traceability-matrix` -> generated from the evidence graph
- `quality-gate-as-code` -> `quality_gate.py`
- `github-pages-explorer` -> `docs/index.html`

Keeping these capabilities together avoids thin repositories while the shared contracts are still evolving.

## Quick start

Analyze the bundled graph:

```bash
python evidence_graph.py examples/customer-change.json analyze
python evidence_graph.py examples/customer-change.json path REQ-001 EVID-001
python evidence_graph.py examples/customer-change.json impact TEST-001
python quality_gate.py examples/customer-change.json examples/quality-policy.json
```

Build a graph from CSV exports:

```bash
python csv_adapter.py examples/csv/manifest.json --output project-evidence.json
python evidence_graph.py project-evidence.json analyze
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

The bundled examples intentionally contain traceability gaps so reports demonstrate missing coverage instead of only a perfect graph.

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

The quality command exits non-zero when policy fails, so the same rules become a GitHub Actions gate.

## CSV import manifest

```json
{
  "artifact_sources": [
    {
      "file": "requirements.csv",
      "id": "{REQ_ID}",
      "type": "requirement",
      "title": "{TITLE}",
      "fields": {"risk": "{RISK}"}
    }
  ],
  "link_sources": [
    {
      "file": "links.csv",
      "from": "{FROM_ID}",
      "to": "{TO_ID}",
      "type": "{RELATION}"
    }
  ]
}
```

## Reusable graph explorer

Open `docs/index.html` directly in a browser. No build step or external JavaScript dependency is required.

It accepts:

- Project Evidence Graph: `nodes` + `links`
- Data Relationship Map: `nodes` + `relationships`
- Cutover Graph: `tasks` + `depends_on`

The explorer supports local JSON loading, filtering, grouped SVG visualization, and node/connection inspection.

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

1. GitHub Issues/PR and Jira/ALM export adapters.
2. Evidence freshness and stale-evidence detection.
3. Risk-weighted coverage and policy profiles.
4. Generated Markdown/HTML release and audit reports.
5. Stable cross-repository references to Mapping as Code, Interface as Code, Process as Code, Reconciliation as Code, and Cutover Graph.
6. Compact machine-readable project context for agents.
7. Release/cutover evidence packs generated from the graph.

## Design principles

- traceability as graph data, not a manually maintained matrix
- deterministic coverage and policy logic
- provenance-preserving imports
- versionable and portable state
- vendor-neutral core
- Git-friendly outputs
- synthetic examples safe to publish

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

**MVP / active development.** CSV ingestion, provenance, validation, traceability, impact analysis, coverage metrics, policy gates, reusable graph exploration, examples, tests, and CI are implemented.
