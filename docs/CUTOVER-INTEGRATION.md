# Cutover Graph Integration

Project Evidence Graph consumes the domain-owned Cutover Graph artifact index rather than parsing raw cutover plan internals.

## Producer boundary

Cutover Graph publishes stable refs such as:

```text
eac://dkharlanau/cutover-graph/task/reconcile-customers
eac://dkharlanau/cutover-graph/checkpoint/reconcile-customers
eac://dkharlanau/cutover-graph/contingency/rollback-customer
```

The artifact index also carries checkpoint-aware completion, dependencies, gate state, and exact evidence refs.

## Import

```bash
python cutover_adapter.py cutover-artifacts.json --output cutover-project-fragment.json
```

Mapping:

| Cutover artifact | Project Evidence Graph type |
|---|---|
| main task | `change` |
| passed checkpoint | `evidence` |
| incomplete/failed checkpoint | `defect` |
| contingency branch | `decision` |
| contingency task | `change` |

Dependency refs become explicit `precedes` links. Main task -> checkpoint becomes `verified_by_checkpoint`.

## External checkpoint evidence

If a checkpoint contains an explicit `eac://` evidence ref, the adapter does not invent a placeholder node. Instead it emits an `external_bridges` relationship:

```json
{
  "from": "eac://dkharlanau/cutover-graph/checkpoint/reconcile-customers",
  "to": "eac://dkharlanau/reconciliation-as-code/reconciliation/customer-country-post-load/run/production-load-01",
  "type": "substantiated_by"
}
```

`graph_merge.py` resolves this bridge only after all supplied graph fragments are loaded. Therefore the link succeeds only if the referenced reconciliation evidence artifact is actually present in another fragment.

A raw local evidence path such as `recon/report.json` remains checkpoint metadata and is not promoted to an external graph artifact.

## End-to-end chain

A project can now model:

```text
Requirement
  -> Mapping-as-Code artifact
  -> Interface-as-Code artifact
  -> Test
  -> Cutover task
  -> Passed checkpoint
  -> Reconciliation-as-Code run
  -> Reconciliation check evidence
```

Every cross-repository step is explicit and addressable by stable logical identity.

## Failure semantics

A checkpoint with missing approval/evidence imports as `defect`, not `evidence`. This prevents a raw `done` task or incomplete gate from improving project evidence coverage.

An invalid Cutover artifact index is rejected rather than partially imported.
