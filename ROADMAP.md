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
- reusable zero-build browser graph explorer
- realistic traceability/freshness/risk/external-work-item examples
- unit tests and GitHub Actions CI

## Now — build the cross-repository project spine

1. Consume stable `eac://` artifact references from domain repositories.
2. Link Mapping as Code, Interface as Code, Process as Code, Cutover Graph, and Reconciliation as Code artifacts without copying their full models.
3. Generate Markdown/HTML traceability and audit reports.

## Next — project context and evidence packs

- generate release and cutover evidence packs
- expose a compact machine-readable project context for agents
- combine raw, fresh, and risk-weighted assurance into one release decision view
- export bounded subgraphs for downstream agents/tools

## Later — operational assurance

- signed or hashed evidence references
- historical graph snapshots and rationale drift
- project-level assurance cases and audit exports
- cross-project policy packs

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, what is upstream/downstream of it, where is it implemented, how was it tested, is the evidence current enough to trust now, and are the remaining assurance gaps acceptable for the requirement's business risk?
