# Reconciliation-as-Code Integration

Project Evidence Graph consumes the canonical Reconciliation-as-Code `evidence.json` schema v1.0 directly.

## Why this contract

Reconciliation-as-Code already produces a deterministic evidence document containing:

- reconciliation name and status;
- run ID/timestamps/duration;
- engine/spec/evidence schema versions;
- configuration SHA-256;
- source/target/specification fingerprints;
- summary counts;
- check-level type, severity, status, metrics, and prepared details.

The project graph therefore does not define a second reconciliation result format.

## Import

```bash
python reconciliation_adapter.py rac-evidence.json --output project-reconciliation.json
python evidence_graph.py project-reconciliation.json analyze
```

## Semantic mapping

| Reconciliation result | Project Evidence Graph type |
|---|---|
| passed run | `evidence` |
| failed run | `defect` |
| passed check | `evidence` |
| failed check | `defect` |

This distinction is deliberate. A failed reconciliation must not improve requirement-to-evidence coverage merely because a result document exists.

Each run/check receives a stable logical reference under:

```text
eac://dkharlanau/reconciliation-as-code/reconciliation/<name>/run/<run-id>
eac://dkharlanau/reconciliation-as-code/reconciliation/<name>/run/<run-id>/check/<check-id>
```

`generated_at` is mapped to `observed_at`, so existing freshness policy can decide whether the reconciliation result is still current enough to use as evidence.

## Provenance

The run node retains:

- `configuration_sha256`;
- source/target/specification `path` + `sha256` records;
- engine/schema/spec versions;
- run metadata;
- reconciliation summary.

Check nodes retain type/severity/metrics and truncation state. Sensitive values remain governed by the Reconciliation-as-Code evidence-preparation layer; this importer does not reconstruct raw source values.

## Composition

The adapter emits an ordinary `nodes` + `links` Project Evidence Graph fragment. It can therefore be merged or referenced into a larger release/cutover graph without changing `traceability`, `impact`, `freshness`, review, or context tooling.
