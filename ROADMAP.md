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
- risk-weighted test/evidence coverage and uncovered risk scoring
- policy-based risk-assurance gates
- generated traceability-matrix data
- policy-based quality gates for CI
- generic CSV import with file/row provenance
- GitHub Issues/PR JSON import with explicit-reference traceability and unresolved-reference diagnostics
- built-in Jira work-item import profile
- profile-driven ALM/other tracker import with explicit links only
- stable `eac://` cross-repository artifact materialization
- explicit local<->external and external<->external traceability links
- cross-repository invalid/duplicate/unresolved reference diagnostics
- reusable zero-build browser graph explorer
- realistic traceability/freshness/risk/external-work-item/cross-repository examples
- unit tests and GitHub Actions CI

## Now — turn the graph into a review product

1. Generate Markdown/HTML traceability, assurance, and audit reports.
2. Combine raw, fresh, and risk-weighted assurance into one release decision view.
3. Expose a compact machine-readable project context for agents.
4. Emit stable `eac://` refs from more domain repos so project packs need less manual linking.

## Next — project evidence packs

- generate release and cutover evidence packs
- import Reconciliation as Code results as evidence/control artifacts
- ingest Cutover Graph tasks/checkpoints/evidence by stable refs
- export bounded subgraphs for downstream agents/tools
- add historical graph snapshot comparison and rationale drift

## Later — operational assurance

- signed or hashed evidence references
- project-level assurance cases and audit exports
- cross-project policy packs
- external evidence stores and verification adapters

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, what is upstream/downstream of it, where is it implemented across repositories, how was it tested, is the evidence current enough to trust now, and are the remaining assurance gaps acceptable for the requirement's business risk?
