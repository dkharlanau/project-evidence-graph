# Project Evidence Graph

Connect requirements, decisions, mappings, interfaces, tests, defects, changes, and evidence into one traceable project graph.

## Why this exists

Project rationale disappears because requirements, mappings, tests, defects, changes, decisions, and evidence live in separate systems. A spreadsheet traceability matrix helps for a moment, but it is usually manual, stale, and hard to query.

Project Evidence Graph models traceability as data first. A matrix becomes one generated view of the graph rather than the source of truth.

## Current MVP

The repository now includes a zero-dependency Python engine that can:

- validate project artifact nodes and links
- detect duplicate nodes and links
- detect broken references
- trace directed paths from one artifact to another
- calculate requirement-to-test coverage
- calculate requirement-to-evidence coverage
- generate a traceability matrix per requirement
- run validation automatically in GitHub Actions

This absorbs the core `traceability-matrix` idea, so a separate repository is unnecessary unless the matrix later becomes an independent UI/product.

## Quick start

```bash
python evidence_graph.py examples/customer-change.json analyze
python evidence_graph.py examples/customer-change.json path REQ-001 EVID-001
python -m unittest discover -s tests -v
```

The bundled example deliberately contains a second requirement without tests or evidence. The report therefore exposes a real traceability gap instead of only demonstrating a perfect graph.

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
3. Policy gates such as “every high-risk requirement requires tests and evidence.”
4. Evidence freshness and provenance.
5. Generated Markdown/HTML traceability reports.
6. Interactive GitHub Pages graph explorer.
7. Cross-repository references to Mapping as Code, Interface as Code, Process as Code, and Cutover Graph.
8. Machine-readable project context for AI agents.
9. Release/cutover evidence packs generated from the graph.

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

**MVP / active development.** Validation, directed traceability, coverage metrics, generated matrix data, examples, tests, and CI are implemented.
