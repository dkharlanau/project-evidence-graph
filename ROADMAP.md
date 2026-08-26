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
- Cutover Graph artifact-index import with stable task/checkpoint/contingency refs
- passed checkpoint -> evidence / incomplete checkpoint -> defect semantics
- automatic checkpoint -> Reconciliation-as-Code bridge resolution through explicit `eac://` evidence refs
- stable `eac://` cross-repository artifact materialization
- explicit local<->external and external<->external traceability links
- deterministic graph-fragment merge with explicit and fragment-emitted bridge links
- cross-repository invalid/duplicate/conflict/unresolved diagnostics
- consolidated Markdown/HTML project assurance review
- one explicit review decision across supplied quality/freshness/risk policy gates
- compact bounded project context for agents
- deterministic `context_id` for reproducible context slices
- integrity-verifiable bounded release/cutover evidence packs
- deterministic `pack_id`, per-file SHA-256 manifest, and pack verification
- reusable zero-build browser graph explorer
- realistic traceability/freshness/risk/external-work-item/reconciliation/cutover/cross-repository examples
- unit tests and GitHub Actions CI

## Now — historical assurance and broader domain emitters

1. Compare project graph snapshots and explain traceability/rationale drift.
2. Compare assurance/evidence-pack decisions between rehearsal, release, and production states.
3. Detect changed requirement -> changed implementation -> required retest/evidence refresh.
4. Consume stable `eac://` refs from Data Relationship Map and additional domain repositories.

## Next — evidence lifecycle

- explicit supersedes/replaces relationships for evidence and decisions
- stale-by-change detection: evidence becomes suspect when implementation changed after observation
- release-to-release assurance trend
- bounded evidence-pack comparison reports

## Later — operational assurance

- signed or externally attested evidence-pack manifests
- project-level assurance cases and audit exports
- cross-project policy packs
- external evidence stores and verification adapters

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, what is upstream/downstream of it, where is it implemented across repositories, how was it tested and reconciled, which cutover checkpoint accepted it, is the evidence current enough to trust now, are the remaining assurance gaps acceptable for the requirement's business risk, can that state be reviewed and integrity-checked in one bounded release pack, and how did that assurance state change from rehearsal to production?
