# Project Evidence Graph

Connect requirements, decisions, mappings, interfaces, tests, defects, changes, and evidence into one traceable project graph.

## Why this exists

Project rationale disappears because requirements, mappings, tests, defects, changes, decisions, and evidence live in separate systems. A spreadsheet traceability matrix helps for a moment, but it is usually manual, stale, and hard to query.

Project Evidence Graph models traceability as data first. A matrix, quality gate, impact report, evidence pack, or visual explorer becomes a generated view of the graph rather than the source of truth.

## Current capabilities

- import ordinary CSV requirements/tests/links through a manifest
- import saved GitHub Issues/PR JSON exports with stable canonical IDs
- import saved Jira JSON exports with a built-in profile
- import ALM/other work-item JSON through profile-driven dot-path mapping
- preserve source IDs, status, risk, timestamps, URLs, and provenance
- create tracker/GitHub traceability only from explicit references
- report unresolved external references instead of inventing links
- validate artifact nodes and links
- detect duplicate nodes/links, broken references, and invalid artifact types
- trace directed paths between artifacts
- calculate requirement-to-test and requirement-to-evidence coverage
- calculate requirement coverage by **fresh** evidence, not merely any evidence
- classify evidence as fresh, stale, future-dated, or missing a trusted timestamp
- calculate **risk-weighted** test/evidence coverage and uncovered risk score
- generate traceability-matrix data per requirement
- run upstream/downstream impact analysis for any artifact
- enforce machine-readable quality, freshness, and risk-assurance policies in CI
- browse evidence, relationship, and cutover graphs in a reusable zero-build HTML explorer

This repository absorbs the useful core of three previously separate ideas:

- `traceability-matrix` -> generated from the evidence graph
- `quality-gate-as-code` -> quality/freshness/risk policy modules
- `github-pages-explorer` -> `docs/index.html`

## Quick start

```bash
python evidence_graph.py examples/customer-change.json analyze
python evidence_graph.py examples/customer-change.json path REQ-001 EVID-001
python evidence_graph.py examples/customer-change.json impact TEST-001
python quality_gate.py examples/customer-change.json examples/quality-policy.json
python evidence_freshness.py examples/evidence-freshness.json examples/freshness-policy.json
python risk_assurance.py examples/risk-assurance.json examples/risk-policy.json
```

CSV import:

```bash
python csv_adapter.py examples/csv/manifest.json --output project-evidence.json
python evidence_graph.py project-evidence.json analyze
```

GitHub import:

```bash
python github_adapter.py examples/github/export.json \
  --config examples/github/config.json \
  --output github-evidence.json
```

Jira import:

```bash
python workitem_adapter.py examples/workitems/jira-export.json \
  --profile jira \
  --output jira-evidence.json
```

Generic ALM/work-item import:

```bash
python workitem_adapter.py examples/workitems/alm-export.json \
  --profile examples/workitems/alm-profile.json \
  --output alm-evidence.json
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Risk-weighted assurance

Raw coverage treats every requirement equally. That is often the wrong business signal: one untested critical requirement can matter more than many low-risk gaps.

`risk_assurance.py` assigns explicit weights and calculates weighted coverage:

```json
{
  "risk_field": "risk",
  "risk_weights": {
    "low": 1,
    "medium": 2,
    "high": 5,
    "critical": 10
  },
  "default_weight": 1,
  "require_known_risk": true,
  "min_weighted_test_coverage": 0.9,
  "min_weighted_evidence_coverage": 0.9,
  "max_uncovered_test_risk_score": 3,
  "max_uncovered_evidence_risk_score": 3
}
```

The report includes per-requirement risk/weight/coverage state, weighted test/evidence coverage, uncovered risk scores, and unknown-risk diagnostics. The existing unweighted traceability calculation remains unchanged.

## Work-item import profiles

`workitem_adapter.py` keeps vendor-specific JSON at the import boundary. The built-in `jira` profile understands the common `issues[].fields.*` export shape, including explicit Jira issue links.

For another tracker or an exported SAP Cloud ALM-style work-item list, use a profile:

```json
{
  "source": "cloud-alm",
  "project_name": "CUSTOMER-TRANSFORMATION",
  "items_path": "work_items",
  "id": "id",
  "tracker_type": "type",
  "title": "title",
  "status": "status",
  "risk": "risk",
  "updated_at": "updated_at",
  "url": "url",
  "type_map": {
    "requirement": "requirement",
    "test": "test",
    "defect": "defect",
    "change": "change"
  },
  "default_artifact_type": "change",
  "links": {
    "path": "links",
    "target": "target",
    "type": "relation",
    "direction": "outward"
  }
}
```

Unknown tracker item types use the explicitly configured default. Unresolved linked IDs remain diagnostics and do not create invented artifacts.

## Evidence freshness

A requirement should not be considered operationally assured merely because some evidence node is reachable. `evidence_freshness.py` evaluates evidence against an explicit point in time and policy.

```json
{
  "as_of": "2026-08-26T12:00:00Z",
  "max_age_days": 30,
  "timestamp_fields": ["observed_at", "updated_at", "created_at"],
  "missing_timestamp": "fail",
  "fail_on_stale": false,
  "fail_on_future": true,
  "min_fresh_evidence_coverage": 0.5
}
```

The report distinguishes fresh, stale, future-dated, and missing-timestamp evidence and identifies requirements with evidence but no **fresh** evidence.

## GitHub import semantics

GitHub objects receive stable IDs such as:

```text
GH:acme/customer-platform:ISSUE:12
GH:acme/customer-platform:PR:31
```

References are not guessed from semantic similarity: only explicit references in PR text or `linked_issues` create edges.

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

Open `docs/index.html` directly in a browser. No build step or external JavaScript dependency is required. It accepts Project Evidence Graph (`nodes` + `links`), Data Relationship Map (`nodes` + `relationships`), and Cutover Graph (`tasks` + `depends_on`).

## Canonical model

```json
{
  "nodes": [
    {"id": "REQ-001", "type": "requirement", "risk": "high"},
    {"id": "DEC-001", "type": "decision"},
    {"id": "TEST-001", "type": "test"},
    {"id": "EVID-001", "type": "evidence", "observed_at": "2026-08-20T10:00:00Z"}
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

1. Stable `eac://` cross-repository references to Mapping as Code, Interface as Code, Process as Code, Reconciliation as Code, Cutover Graph, and other domain tools.
2. Generated Markdown/HTML release and audit reports.
3. Compact machine-readable project context for agents.
4. Release/cutover evidence packs generated from the graph.
5. Historical assurance/rationale drift across graph snapshots.

## Design principles

- traceability as graph data, not a manually maintained matrix
- deterministic coverage and policy logic
- explicit references over guessed traceability
- provenance-preserving imports
- freshness-aware and risk-aware evidence assurance
- vendor-neutral core with vendor adapters at the boundary
- versionable and portable state
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

**MVP / active development.** CSV, GitHub, Jira and profile-driven work-item ingestion; provenance; validation; traceability; impact; raw/fresh/risk-weighted coverage; policy gates; reusable graph exploration; examples; tests; and CI are implemented.
