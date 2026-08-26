# Roadmap

## Done — usable MVP

- canonical project artifact/link model
- validation for duplicates, broken links, and artifact types
- directed path tracing
- upstream/downstream impact analysis
- requirement-to-test and requirement-to-evidence coverage
- generated traceability-matrix data
- policy-based quality gates for CI
- generic CSV import with file/row provenance
- reusable zero-build browser graph explorer
- realistic traceability-gap examples
- unit tests and GitHub Actions CI

## Now — ingest richer project evidence

1. Add GitHub Issues/PR export adapter.
2. Add Jira/ALM export profiles on top of the generic importer.
3. Add evidence freshness and stale-evidence detection.
4. Add risk-weighted coverage and quality policy profiles.
5. Generate Markdown/HTML traceability and audit reports.

## Next — cross-repository project spine

- link Mapping as Code artifacts by stable IDs
- link Interface as Code contracts
- link Process as Code steps and controls
- link Cutover Graph tasks/checkpoints/evidence
- ingest Reconciliation as Code results
- generate release and cutover evidence packs
- expose a compact machine-readable project context for agents

## Later — operational assurance

- signed or hashed evidence references
- historical graph snapshots and rationale drift
- project-level assurance cases and audit exports
- cross-project policy packs

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, what is upstream/downstream of it, where is it implemented, how was it tested, and what evidence proves the current state?
