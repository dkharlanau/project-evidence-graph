# Roadmap

## Done — project assurance MVP

- canonical project artifact/link model
- validation for duplicates, broken links, and artifact types
- directed path tracing and upstream/downstream impact analysis
- requirement-to-test and requirement-to-evidence coverage
- fresh-evidence requirement coverage and stale/future/missing-timestamp diagnostics
- policy-based quality, freshness and risk-assurance gates
- risk-weighted test/evidence coverage and uncovered-risk scoring
- generated traceability-matrix data
- CSV, GitHub, Jira and profile-driven ALM/work-item imports with provenance
- explicit-reference-only tracker traceability and unresolved-reference diagnostics
- Reconciliation-as-Code evidence import with stable run/check `eac://` references and retained fingerprints
- Cutover Graph artifact-index import with stable task/checkpoint/contingency references
- Data Relationship Map import for producer-owned objects, relationships and findings
- explicit observation-time propagation from Data Relationship Map into freshness-aware project evidence
- relationship-policy findings materialized as project `defect` artifacts without copying relationship semantic ownership
- explicit project bridges from requirements/changes to relationship findings; no semantic-similarity linking
- explicit checkpoint -> reconciliation evidence bridge resolution
- stable cross-repository artifact materialization and deterministic graph-fragment merge
- consolidated Markdown/HTML project assurance review
- one explicit review decision across supplied quality/freshness/risk policies
- compact bounded project context with deterministic `context_id`
- integrity-verifiable evidence packs with deterministic `pack_id` and per-file SHA-256 manifest
- reusable zero-build graph explorer
- installable Python package and unified `project-evidence-graph` command
- unit tests, installed-CLI smoke tests and GitHub Actions CI

## Done — historical assurance

- compare project graph snapshots and explain node/link traceability drift
- classify rationale and implementation drift
- compare assurance decisions and coverage between states
- detect changed implementation beneath a requirement
- derive deterministic retest/evidence-refresh candidates with current tests and evidence
- render historical assurance comparison as JSON or Markdown

## Now — evidence lifecycle

1. Add explicit `supersedes` / `replaces` lifecycle semantics for evidence and decisions.
2. Detect **stale-by-change** evidence: implementation changed after the observation the evidence is meant to support.
3. Compare bounded evidence packs between rehearsal, release and production rather than comparing only whole graphs.
4. Define resolution semantics for externally owned findings without rewriting producer history.

## Next — assurance trends and review workflow

- release-to-release assurance trend with explicit metric definitions
- resolved/open lifecycle for assurance gaps
- review annotations that preserve who accepted a gap, why, and for which exact graph/policy fingerprint
- generated release/audit summary from current review + historical delta + retained evidence pack
- project-level consumption contract for Enterprise Change Graph and Cutover Graph

## Later — operational assurance

- signed or externally attested evidence-pack manifests
- project-level assurance cases and audit exports
- cross-project policy packs
- external evidence stores and verification adapters

## Product test

For any important requirement or production change, the graph should answer:

> Why does this exist, what is upstream/downstream of it, where is it implemented across repositories, how was it tested and reconciled, which cutover checkpoint accepted it, what observed relationship evidence challenges it, is the evidence current enough to trust now, what changed since the previous trusted state, which implementation change requires retest or evidence refresh, are the remaining assurance gaps acceptable for the requirement's business risk, and can that state be reviewed and integrity-checked in one bounded release pack?
