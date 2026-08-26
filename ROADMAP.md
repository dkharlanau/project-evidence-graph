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
- Reconciliation-as-Code evidence v1 import with pass->evidence / fail->defect semantics
- stable reconciliation run/check `eac://` references and preserved fingerprints
- stable `eac://` cross-repository artifact materialization
- explicit local<->external and external<->external traceability links
- deterministic graph-fragment merge with explicit bridge links
- cross-repository invalid/duplicate/conflict/unresolved diagnostics
- consolidated Markdown/HTML project assurance review
- one explicit review decision across supplied quality/freshness/risk policy gates
- compact bounded project context for agents
- deterministic `context_id` for reproducible context slices
- integrity-verifiable bounded release/cutover evidence packs
- deterministic `pack_id`, per-file SHA-256 manifest, and pack verification
- reusable zero-build browser graph explorer
- realistic traceability/freshness/risk/external-work-item/reconciliation/cross-repository examples
- unit tests and GitHub Actions CI

## Now — cutover and domain emitters

1. Ingest Cutover Graph tasks/checkpoints/evidence by stable refs.
2. Emit stable `eac://` refs directly from Cutover Graph and Data Relationship Map.
3. Connect Reconciliation-as-Code evidence refs into Cutover Graph checkpoints without duplicating evidence content.

## Next — historical assurance

- graph snapshot comparison and rationale drift
- assurance trend between releases
- changed requirement -> changed implementation -> required retest analysis
- explicit supersedes/replaces relationships for evidence and decisions
- compare evidence packs/release decisions across rehearsals and production

## Later — operational assurance

- signed or externally attested evidence-pack manifests
- project-level assurance cases and audit exports
- cross-project policy packs
- external evidence stores and verification adapters

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, what is upstream/downstream of it, where is it implemented across repositories, how was it tested and reconciled, is the evidence current enough to trust now, are the remaining assurance gaps acceptable for the requirement's business risk, can that state be reviewed and integrity-checked in one bounded release pack, and can an agent receive a reproducible context package that identifies exactly which project state it consumed?
