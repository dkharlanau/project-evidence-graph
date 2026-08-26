# Project Evidence Pack

`evidence_pack.py` creates a bounded, integrity-verifiable hand-off directory from a Project Evidence Graph.

## Build

```bash
python evidence_pack.py build merged-project.json release-evidence/ \
  --focus REQ-COUNTRY \
  --depth 5 \
  --quality-policy examples/quality-policy.json \
  --freshness-policy examples/freshness-policy.json \
  --risk-policy examples/risk-policy.json
```

The directory contains:

```text
release-evidence/
├── graph.json
├── context.json
├── review.md
├── review.html
└── manifest.json
```

## Contents

### `graph.json`

Full-fidelity bounded graph slice. Unlike the compact agent context, this retains complete node/link metadata such as reconciliation summary, fingerprints, external source metadata, and merge diagnostics.

### `context.json`

Compact reproducible agent/tool context with deterministic `context_id`.

### `review.md` / `review.html`

Human review surfaces generated from the bounded graph itself. Raw coverage, freshness, and risk-weighted assurance remain distinct signals.

### `manifest.json`

Records:

- evidence-pack format version;
- deterministic `pack_id`;
- focus/depth scope;
- PASS/FAIL review decision;
- optional source graph file SHA-256;
- semantic SHA-256 fingerprints of supplied policy documents;
- bounded node/link counts and context ID;
- SHA-256 and byte size for every generated pack file except the manifest itself.

## Deterministic pack identity

`pack_id` is derived from:

- bounded graph nodes and links;
- focus + depth;
- quality/freshness/risk policy fingerprints.

It does not depend on the current clock. The same semantic slice/scope/policies therefore produces the same pack ID.

The source file SHA may still differ if equivalent graph JSON is reformatted; that is kept separately as physical-input provenance.

## Failed assurance still produces a pack

A `FAIL` review is not an evidence-pack build error. The pack is produced with `decision: FAIL` so the failed review and exact graph/policies can be handed off or audited.

## Verify

```bash
python evidence_pack.py verify release-evidence/
```

Verification detects:

- missing generated files;
- content/size changes relative to the manifest;
- semantic `pack_id` mismatch between `graph.json` and the recorded focus/depth/policy fingerprints.

This protects generated hand-off integrity. It is not a cryptographic signature or external trust service; signed attestations remain a later integration boundary.

## Intended workflow

A practical release/cutover sequence can be:

1. materialize external `eac://` artifacts;
2. import reconciliation evidence;
3. merge fragments with explicit bridge links;
4. run assurance review/context;
5. build one bounded evidence pack;
6. attach or archive that pack for go/no-go, release, handover, or audit review.
