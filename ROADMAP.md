# Roadmap

## Done — usable MVP

- canonical project artifact/link model
- validation for duplicates, broken links, and artifact types
- directed path tracing
- upstream/downstream impact analysis
- requirement-to-test and requirement-to-evidence coverage
- fresh-evidence requirement coverage
- stale/future/missing-timestamp evidence diagnostics
- policy-based evidence freshness gates
- generated traceability-matrix data
- policy-based quality gates for CI
- generic CSV import with file/row provenance
- GitHub Issues/PR JSON import with explicit-reference traceability and unresolved-reference diagnostics
- reusable zero-build browser graph explorer
- realistic traceability/freshness-gap examples
- unit tests and GitHub Actions CI

## Now — strengthen assurance and reporting

1. Add Jira/ALM export profiles on top of the generic importer.
2. Add risk-weighted coverage and assurance policy profiles.
3. Generate Markdown/HTML traceability and audit reports.

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

> Why does this exist, what is upstream/downstream of it, where is it implemented, how was it tested, and is the evidence current enough to trust now?
