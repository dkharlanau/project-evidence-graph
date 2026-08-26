# Cross-Repository Traceability

Project Evidence Graph consumes the shared Enterprise-as-Code logical reference contract without copying complete domain models into this repository.

## Input

A cross-repository project pack has ordinary local `nodes`, explicit `external_artifacts`, and links that may use `from_ref` or `to_ref`.

```json
{
  "nodes": [
    {"id": "REQ-COUNTRY", "type": "requirement"},
    {"id": "TEST-COUNTRY", "type": "test"},
    {"id": "EVID-COUNTRY", "type": "evidence"}
  ],
  "external_artifacts": [
    {
      "ref": "eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3",
      "type": "mapping",
      "source": {
        "repository": "dkharlanau/mapping-as-code",
        "path": "examples/customer-country.yaml",
        "revision": "abc123"
      }
    }
  ],
  "links": [
    {
      "from": "REQ-COUNTRY",
      "to_ref": "eac://dkharlanau/mapping-as-code/mapping/customer/country?version=v3",
      "type": "implemented_by"
    }
  ]
}
```

## Materialization

```bash
python cross_repo.py examples/cross-repo-pack.json --output project-graph.json
python evidence_graph.py project-graph.json analyze
```

`cross_repo.py` canonicalizes the `eac://` URI and materializes each external artifact as a normal evidence-graph node whose `id` and `artifact_ref` are the logical reference.

The `source` object remains metadata. Moving a file or changing a Git commit does not change the logical artifact identity.

## Diagnostics

The materializer reports and fails on:

- invalid `eac://` references;
- duplicate logical references;
- invalid refs used by links;
- explicit references that are not present in local nodes or `external_artifacts`.

It does **not** fetch another repository and does not invent missing artifacts from names or semantic similarity.

## Why materialize

After materialization, existing Project Evidence Graph tools need no cross-repository special cases. The same graph can be passed to:

- `evidence_graph.py` for path/traceability/impact;
- `quality_gate.py`;
- `evidence_freshness.py`;
- `risk_assurance.py`;
- `docs/index.html`.

This keeps cross-repository integration as a thin identity/linking layer rather than a new monolithic platform.
