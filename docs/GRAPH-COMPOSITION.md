# Graph Fragment Composition

Project Evidence Graph can combine independently generated graph fragments without coupling their producers.

Typical fragments include:

- local requirements/tests/decisions;
- `cross_repo.py` materialized Mapping/Interface/Process artifacts;
- `reconciliation_adapter.py` Reconciliation-as-Code run/check results;
- Jira/ALM/GitHub imports;
- later Cutover Graph evidence.

## Merge

```bash
python graph_merge.py \
  project.json \
  reconciliation.json \
  --bridges explicit-bridges.json \
  --output merged-project.json
```

## Node identity

Nodes merge only by their stable `id`.

- the same identical node in multiple fragments is collapsed;
- the same ID with different node content is a conflict and fails the merge;
- no semantic or fuzzy matching is performed.

This makes `eac://` artifact references especially useful: a logical external artifact can be safely recognized across fragments without relying on a source file path.

## Links

Identical links are deduplicated by `from + type + to` and identical payload. A duplicate link key with conflicting metadata/provenance is reported as a conflict rather than silently choosing one version.

## Bridge links

Cross-fragment relationships are supplied explicitly:

```json
{
  "links": [
    {
      "from": "TEST-COUNTRY",
      "to": "eac://dkharlanau/reconciliation-as-code/reconciliation/customer-country-post-load/run/production-load-01",
      "type": "verified_by_reconciliation"
    }
  ]
}
```

Both endpoints must already exist after fragment merge. An unresolved bridge fails composition.

## Diagnostics and provenance

`merge_diagnostics` records:

- fragment labels;
- fragment-level adapter/import metadata;
- identical duplicate nodes/links;
- conflicting nodes/links;
- invalid and unresolved bridges;
- overall merge validity.

Per-node and per-link source/provenance fields remain on the artifacts themselves.

## Why this matters

Each domain repository can continue producing its own narrow canonical model. Project Evidence Graph only consumes exported graph fragments plus explicit bridges. The project-level traceability graph therefore grows by composition rather than by reimplementing every domain model in one repository.
