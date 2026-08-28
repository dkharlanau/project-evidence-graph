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

For checkpoints backed by external `eac://` evidence, use a Cutover export produced with its verification registry. Presence of an external URI is not sufficient assurance.

## Import

```bash
python cutover_adapter.py verified-cutover-artifacts.json --output cutover-project-fragment.json
```

Mapping:

| Cutover artifact | Project Evidence Graph type |
|---|---|
| main task | `change` |
| local passed checkpoint | `evidence` |
| externally backed, registry-verified passed checkpoint | `evidence` |
| incomplete/failed checkpoint | `defect` |
| externally backed checkpoint without verification metadata | `defect` with `status: unverified` |
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

The checkpoint itself becomes positive `evidence` only when all of these are true for an external-evidence checkpoint:

- Cutover exported `passed: true`;
- `verification_mode` is `external_registry`;
- `external_evidence_passed` is `true`.

The adapter retains the Cutover verification records, including evidence status and document/configuration hashes where supplied. A legacy or third-party index that only says `passed: true` while carrying an external URI is treated as unverified, not trusted.

A raw local evidence path such as `recon/report.json` remains checkpoint metadata and is not promoted to an external graph artifact. Local-only checkpoints retain normal Cutover native gate semantics.

## End-to-end chain

The reference assurance path is:

```text
Mapping as Code artifact
  -> Reconciliation as Code run + evidence identity
  -> Cutover external evidence registry
  -> verified Cutover checkpoint
  -> verified Cutover artifact index
  -> Project Evidence Graph checkpoint evidence node
  -> external bridge back to the exact RAC run
```

A wider project can connect requirements, mappings, interfaces and tests around that path, but those links remain explicit rather than inferred.

## Failure semantics

A checkpoint with missing approval/evidence imports as `defect`, not `evidence`.

A checkpoint whose external evidence is missing, failed, or not accompanied by verification metadata also imports as `defect`; if Cutover declared it passed but verification metadata is absent, its status is `unverified` and `cutover_import_diagnostics.assurance_complete` becomes false.

External bridges are still retained in the unverified case so the missing assurance boundary remains inspectable instead of disappearing.

An invalid Cutover artifact index is rejected rather than partially imported.

## Moving-main drift evidence and reproducibility

The `Portfolio assurance contract` workflow deliberately checks out the current `main` of Mapping as Code, Reconciliation as Code and Cutover Graph. That makes the scheduled run a **drift detector**: it answers whether the current repository heads still interoperate under the documented assurance semantics.

A moving-main green check is not a pinned release-compatibility claim. To make each run auditable, the workflow retains a finite-lived synthetic `portfolio-assurance-*` Actions artifact containing:

- the exact checked-out commit SHA for all four repositories;
- the linked Mapping and generated RAC contracts;
- RAC evidence and Cutover evidence registry;
- verified and deliberately unverified Cutover artifact indexes;
- the corresponding Project Evidence fragments;
- a `receipt.json` with SHA-256 and byte size for every retained artifact;
- explicit `verified_path_passed` and `unverified_path_failed_closed` assertions;
- GitHub workflow run ID, attempt and event.

The bundle contains only the synthetic reference scenario. It is retained for 90 days and is intended for regression/audit reproduction, not as a central artifact registry or long-term enterprise evidence store.

For a release or customer assurance claim, pin the actual product versions/commits separately and retain the relevant evidence according to that delivery's governance and privacy requirements. A scheduled current-main receipt demonstrates tested interoperability for the recorded commits only.
