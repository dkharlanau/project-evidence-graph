# Contributing

Contributions should improve deterministic traceability, evidence assurance, explicit interoperability, or adoption evidence.

Read `AGENTS.md` and `ROADMAP.md` first. The canonical graph remains vendor-neutral, links must be explicit, and examples must be synthetic.

## Development checks

```bash
python -m unittest discover -s tests -v
python evidence_graph.py examples/customer-change.json analyze
python quality_gate.py examples/customer-change.json examples/quality-policy.json
```

Add a synthetic failure/gap fixture and tests for semantic changes. Document compatibility effects when changing IDs, graph relationships, policy behavior, or evidence-pack contents.

## Feedback paths

- Use the [15-minute usability kit](docs/USABILITY_TEST_15_MIN.md) for a first-use session.
- File a privacy-safe [usability report](https://github.com/dkharlanau/project-evidence-graph/issues/new?template=usability-feedback.yml).
- Use a normal GitHub issue for reproducible defects or bounded enhancements.

Do not publish client data, proprietary exports, internal identifiers, credentials, or evidence whose redistribution is not authorized.
