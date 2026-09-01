# Changelog

All notable public release changes are recorded here. Versions follow Semantic Versioning.

## [0.2.1] - 2026-09-01

### Documentation

- Added a copy-paste 30-second proof that analyzes the committed synthetic graph and creates an integrity-verifiable evidence pack.
- Made the fixture's expected failing assurance decision explicit while separating policy findings from successful pack-integrity verification.
- Linked the public generated review and product documentation.

### Compatibility

- The v0.2 graph model, CLI, modules, policies, adapters, analysis digest, and evidence-pack format are unchanged from v0.2.0.

## [0.2.0] - 2026-09-01

### Added

- Deterministic traceability, path, impact, and policy-aware coverage analysis.
- CSV, GitHub, Jira/generic work-item, reconciliation, cutover, and relationship-evidence adapters.
- Graph composition with explicit cross-repository references and conflict diagnostics.
- Consolidated assurance review across quality, freshness, risk, and evidence lifecycle.
- Integrity-verifiable bounded evidence packs and historical assurance comparison.
- Installed `project-evidence-graph` CLI and public browser explorer.

### Boundaries

- Imported artifacts do not create traceability unless links are explicit.
- A passing graph policy is evidence about the supplied state, not approval for release or production.
- External artifact meaning and retention remain owned by their producers and delivery governance.

[0.2.1]: https://github.com/dkharlanau/project-evidence-graph/releases/tag/v0.2.1
[0.2.0]: https://github.com/dkharlanau/project-evidence-graph/releases/tag/v0.2.0
