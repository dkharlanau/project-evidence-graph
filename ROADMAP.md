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
- consolidated Markdown/HTML project assurance review
- one explicit review decision across supplied quality/freshness/risk policy gates
- compact bounded project context for agents
- deterministic `context_id` for reproducible context slices
- reusable zero-build browser graph explorer
- realistic traceability/freshness/risk/external-work-item/cross-repository examples
- unit tests and GitHub Actions CI

## Now — evidence packs and domain integration

1. Generate release and cutover evidence packs from bounded graph slices.
2. Import Reconciliation as Code results as evidence/control artifacts.
3. Ingest Cutover Graph tasks/checkpoints/evidence by stable refs.
4. Emit stable `eac://` refs from more domain repos so project packs need less manual linking.

## Next — historical assurance

- graph snapshot comparison and rationale drift
- assurance trend between releases
- changed requirement -> changed implementation -> required retest analysis
- explicit supersedes/replaces relationships for evidence and decisions

## Later — operational assurance

- signed or hashed evidence references
- project-level assurance cases and audit exports
- cross-project policy packs
- external evidence stores and verification adapters

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, what is upstream/downstream of it, where is it implemented across repositories, how was it tested, is the evidence current enough to trust now, are the remaining assurance gaps acceptable for the requirement's business risk, can that state be reviewed in one reproducible release artifact, and can an agent receive a bounded context package that identifies exactly which project state it consumed?
