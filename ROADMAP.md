# Roadmap

## Done — usable MVP

- canonical project artifact/link model
- validation for duplicates, broken links, and artifact types
- directed path tracing
- requirement-to-test and requirement-to-evidence coverage
- generated traceability-matrix data
- policy-based quality gates for CI
- reusable zero-build browser graph explorer
- realistic traceability-gap example
- unit tests and GitHub Actions CI

## Now — ingest real project evidence

1. Add generic CSV importer for requirements/tests/defects/changes.
2. Add GitHub Issues/PR export adapter.
3. Preserve provenance and source references on imported artifacts.
4. Add reverse impact analysis from change/interface/test to upstream requirements.
5. Add evidence freshness and stale-evidence detection.
6. Generate Markdown/HTML traceability reports as build artifacts.

## Next — cross-repository project spine

- link Mapping as Code artifacts by stable IDs
- link Interface as Code contracts
- link Process as Code steps and controls
- link Cutover Graph tasks/checkpoints/evidence
- ingest Reconciliation as Code results
- generate release and cutover evidence packs
- expose a compact machine-readable project context for agents

## Later — operational assurance

- risk-weighted coverage instead of only raw percentages
- configurable project/release policy profiles
- signed or hashed evidence references
- historical graph snapshots and rationale drift
- project-level assurance cases and audit exports

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, where is it implemented, how was it tested, what changed, and what evidence proves the current state?
