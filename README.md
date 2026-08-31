# Project Evidence Graph

**Evidence-backed project assurance across requirements, decisions, implementation, tests, cutover, defects, changes, relationships, and retained proof.**

Project Evidence Graph (`project-evidence-graph`) turns fragmented project artifacts into one deterministic traceability model. The graph is not the report: assurance reviews, coverage, impact, bounded context, historical drift and integrity-verifiable evidence packs are generated from the same versioned state.

The reference use case is enterprise/SAP transformation, but the core model is vendor-neutral and does not require SAP access.

## The question it answers

A project may have requirements in Jira, mappings in spreadsheets, tests in another tool, reconciliation evidence in a release folder, identity findings in exported data and cutover acceptance in a plan. A green traceability matrix can still hide stale evidence or a requirement whose implementation changed after it was tested.

Project Evidence Graph asks:

> **Why does this exist, where is it implemented, how was it tested, what evidence supports or challenges it, is that evidence still current, what changed since the previous trusted state, and what must be re-tested or re-evidenced now?**

## Try it

Requires Python 3.10+.

```bash
python -m pip install .

project-evidence-graph analyze examples/customer-change.json
project-evidence-graph path examples/customer-change.json REQ-001 EVID-001
project-evidence-graph impact examples/customer-change.json TEST-001
```

The console command is a thin dispatcher over the same deterministic modules used by the test suite. Existing `python evidence_graph.py ...` workflows remain supported.

## The assurance workflow

```text
project exports + domain evidence
          ↓
 explicit/provenance-preserving imports
          ↓
       evidence graph
          ↓
 validation + traceability + impact
          ↓
 quality + freshness + risk policies
          ↓
     assurance review
          ↓
 bounded context / evidence pack
          ↓
 historical assurance comparison
          ↓
 retest / evidence-refresh candidates
```

### 1. Review current assurance

```bash
project-evidence-graph review examples/customer-change.json \
  --quality-policy examples/quality-policy.json \
  --markdown build/project-review.md \
  --html build/project-review.html
```

The review produces one explicit decision from the supplied deterministic gates and surfaces the assurance gaps behind that decision.

### 2. Build bounded context

```bash
project-evidence-graph context examples/customer-change.json \
  --focus REQ-001 \
  --depth 3 \
  --output build/context.json
```

A bounded context keeps the focus artifact, nearby traceability, external references and assurance state together without handing an agent or reviewer the entire project graph.

### 3. Freeze an integrity-verifiable evidence pack

```bash
project-evidence-graph pack build examples/customer-change.json build/release-pack \
  --focus REQ-001 \
  --depth 3

project-evidence-graph pack verify build/release-pack
```

A pack has deterministic semantic identity, per-file SHA-256 integrity, bounded graph/context and review artifacts. It is intended to be retained with a release, rehearsal or cutover decision rather than rebuilt later from mutable sources.

### 4. Compare assurance over time

```bash
project-evidence-graph history before.json after.json \
  --json-output build/assurance-delta.json \
  --markdown build/assurance-delta.md
```

Historical assurance compares more than raw graph bytes. It identifies node/link drift, rationale drift, implementation drift, coverage changes, decision changes and requirements that need evidence refresh because their implementation changed.

### 5. Evaluate evidence lifecycle

```bash
project-evidence-graph lifecycle examples/evidence-lifecycle.json \
  --json-output build/evidence-lifecycle.json \
  --markdown build/evidence-lifecycle.md
```

Lifecycle links point from the current artifact to the retained artifact it `supersedes` or `replaces`. Only same-type evidence-to-evidence and decision-to-decision links are accepted. The evaluator also fails by default when active evidence predates a changed implementation that it is meant to support.

## What works today

### Traceability and analysis

- canonical project artifact/link model;
- duplicate, broken-link and invalid-artifact validation;
- directed path tracing;
- upstream/downstream impact analysis;
- requirement-to-test and requirement-to-evidence coverage;
- traceability-matrix data generated from the graph rather than maintained separately.

### Evidence assurance

- fresh/stale/future/missing-timestamp evidence classification;
- requirement coverage by **fresh** evidence, not merely reachable evidence;
- risk-weighted test/evidence coverage and uncovered-risk scoring;
- machine-readable quality, freshness and risk policies;
- consolidated JSON/Markdown/HTML project assurance review.

### Cross-repository composition

- stable `eac://` external artifact references;
- explicit local-to-external and external-to-external traceability;
- deterministic fragment merge with provenance;
- conflict, duplicate, invalid and unresolved-reference diagnostics;
- Reconciliation-as-Code evidence import with stable run/check references and fingerprints;
- Cutover Graph artifact-index import with task/checkpoint/contingency references;
- Data Relationship Map import for observed objects, relationships and policy findings;
- producer observation time propagated into relationship evidence so strict freshness policy remains meaningful;
- relationship findings represented as external `defect` nodes rather than copied/re-authored relationship rules;
- explicit project bridges from requirements or changes to producer-owned relationship findings;
- explicit checkpoint → reconciliation evidence bridge resolution.

### Review, agent context and retained evidence

- compact bounded context with deterministic `context_id`;
- integrity-verifiable evidence packs with deterministic `pack_id`;
- per-file SHA-256 manifest and independent pack verification;
- reusable zero-build browser graph explorer;
- installable `project-evidence-graph` command;
- CI coverage for both installed CLI and original module workflows.

### Historical assurance

- before/after graph comparison;
- rationale and implementation drift classification;
- assurance/coverage decision deltas;
- changed-implementation detection beneath requirements;
- deterministic retest/evidence-refresh candidates showing current tests and current evidence.

### Evidence lifecycle

- explicit `supersedes` and `replaces` semantics for evidence and decisions;
- retained but inactive historical evidence rather than deletion;
- replacement-cycle, ambiguous replacement and cross-type replacement validation;
- active-evidence stale-by-change detection using explicit timestamps;
- machine-readable and Markdown lifecycle decisions through the installed CLI.

## Import project evidence without inventing traceability

Adapters keep vendor-specific exports at the boundary. Links are created only from explicit references or explicit bridge contracts; semantic similarity is not treated as evidence that two artifacts are related.

### CSV

```bash
project-evidence-graph import-csv examples/csv/manifest.json \
  --output project-evidence.json
```

A manifest can map requirements, tests and links from ordinary project exports while retaining file/row provenance.

### GitHub

```bash
project-evidence-graph import-github examples/github/export.json \
  --config examples/github/config.json \
  --output github-evidence.json
```

GitHub Issues/PRs receive stable canonical IDs. Only explicit references create traceability; unresolved references remain diagnostics.

### Jira / generic ALM

```bash
project-evidence-graph import-workitems examples/workitems/jira-export.json \
  --profile jira \
  --output jira-evidence.json

project-evidence-graph import-workitems examples/workitems/alm-export.json \
  --profile examples/workitems/alm-profile.json \
  --output alm-evidence.json
```

The built-in Jira profile handles common saved JSON export shapes. Other trackers can be mapped through explicit dot-path profiles.

### Reconciliation, cutover and relationship evidence

```bash
project-evidence-graph import-reconciliation examples/reconciliation/evidence.json \
  --output reconciliation-evidence.json

project-evidence-graph import-cutover examples/cutover/artifact-index.json \
  --output cutover-evidence.json

project-evidence-graph import-relationship examples/relationship/artifact-index.json \
  --output relationship-evidence.json
```

For Data Relationship Map, `policy_passed: false` is not treated as a broken adapter contract: those findings are the evidence being imported. A malformed producer contract or invalid `eac://` reference fails loud. Missing observation time remains importable but will fail a strict freshness policy such as `missing_timestamp: fail`; a valid producer `observed_at` is preserved on imported evidence.

Domain products remain semantic owners of their artifacts. Project Evidence Graph materializes only the assurance facts and references it needs.

## Explicit bridges, not guessed traceability

Importing independently owned evidence does **not** automatically attach it to a project requirement. The project must state that relationship explicitly.

Example:

```json
{
  "from": "REQ-COUNTRY",
  "to": "eac://dkharlanau/data-relationship-map/finding/cardinality/mapped_to/outgoing/AFS:4711",
  "type": "challenged_by_relationship_finding",
  "provenance": {
    "kind": "explicit_project_bridge",
    "reason": "Country replication assurance assumes one governed MDG business partner; the observed 1:N identity relationship challenges that assumption"
  }
}
```

This keeps three facts separate: Data Relationship Map owns the observed relationship/finding, the project owns why that finding matters to `REQ-COUNTRY`, and Project Evidence Graph owns the assurance relationship between them.

## Risk-weighted assurance

Raw coverage treats every requirement equally. That is often the wrong release signal: one unsupported critical requirement can matter more than many low-risk gaps.

Example policy:

```json
{
  "risk_field": "risk",
  "risk_weights": {
    "low": 1,
    "medium": 2,
    "high": 5,
    "critical": 10
  },
  "default_weight": 1,
  "require_known_risk": true,
  "min_weighted_test_coverage": 0.9,
  "min_weighted_evidence_coverage": 0.9,
  "max_uncovered_test_risk_score": 3,
  "max_uncovered_evidence_risk_score": 3
}
```

The raw coverage calculation remains visible. Risk policy adds a decision layer; it does not rewrite or hide the underlying gaps.

## Evidence freshness

A requirement is not operationally assured merely because an old evidence node is reachable.

```json
{
  "as_of": "2026-08-26T12:00:00Z",
  "max_age_days": 30,
  "timestamp_fields": ["observed_at", "updated_at", "created_at"],
  "missing_timestamp": "fail",
  "fail_on_stale": false,
  "fail_on_future": true,
  "min_fresh_evidence_coverage": 0.5
}
```

Freshness is explicit and reproducible: the policy supplies the point in time instead of relying on a hidden system clock. Producer-owned observed evidence should carry its own explicit observation time for the same reason.

## Canonical model

```json
{
  "nodes": [
    {"id": "REQ-001", "type": "requirement", "risk": "high"},
    {"id": "DEC-001", "type": "decision"},
    {"id": "TEST-001", "type": "test"},
    {"id": "EVID-001", "type": "evidence", "observed_at": "2026-08-20T10:00:00Z"}
  ],
  "links": [
    {"from": "REQ-001", "to": "DEC-001", "type": "resolved_by"},
    {"from": "DEC-001", "to": "TEST-001", "type": "verified_by"},
    {"from": "TEST-001", "to": "EVID-001", "type": "produced"}
  ]
}
```

First-class artifact types are `requirement`, `decision`, `mapping`, `interface`, `test`, `defect`, `change`, and `evidence`.

## Reusable explorer

Open `docs/index.html` directly in a browser. No build step or external JavaScript dependency is required. The explorer accepts Project Evidence Graph (`nodes` + `links`), Data Relationship Map (`nodes` + `relationships`), and Cutover Graph (`tasks` + `depends_on`) shapes for local inspection.

## Ownership boundary

Project Evidence Graph owns **project assurance relationships and derived assurance views**. It does not become a second authoring system for process, mapping, interface, reconciliation, cutover or relationship semantics.

Prefer stable references and reproducible projections over copying the same business fact into several repositories.

Current next step: compare bounded evidence packs between rehearsal, release and production, integrate lifecycle state into the consolidated assurance review, and define resolution semantics for externally owned findings without rewriting producer history.

See [ROADMAP.md](ROADMAP.md) for the current sequence.

## Design principles

- traceability as graph data, not a manually maintained matrix;
- deterministic policy logic;
- explicit references over guessed traceability;
- provenance-preserving imports;
- freshness-aware and risk-aware evidence assurance;
- vendor-neutral core with adapters at the boundary;
- bounded, integrity-verifiable retained evidence;
- one semantic owner per maintained fact;
- versionable and portable state;
- synthetic examples safe to publish.

## Related projects

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Transformation Graph](https://github.com/dkharlanau/transformation-graph)
- [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph)
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code)
- [Data Relationship Map](https://github.com/dkharlanau/data-relationship-map)
- [Cutover Graph](https://github.com/dkharlanau/cutover-graph)

Portfolio map: https://dkharlanau.github.io/products/

## Status

**Executable MVP / active development, v0.2.0.** Imports, relationship-finding assurance, cross-repository composition, traceability/impact, quality/freshness/risk assurance, evidence lifecycle, project review, bounded context, evidence packs, historical assurance, installed CLI, examples, tests and CI are implemented. The next product gaps are bounded evidence-pack comparison, lifecycle-aware consolidated review, and externally owned finding resolution—not the core traceability engine.
