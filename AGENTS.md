# Agent Development Contract

## Product objective

Create a project evidence spine that can reconstruct why a requirement/change exists, where it is implemented, how it was tested, and what evidence supports the current state.

## Work loop

1. Pick the highest-value unfinished item in `ROADMAP.md`.
2. Implement the smallest end-to-end traceability capability.
3. Add a synthetic example with at least one real gap/failure condition.
4. Add tests for validation, coverage, and policy impact.
5. Run graph analysis and the quality gate.
6. Keep the browser explorer generic across supported graph formats.
7. Update documentation only after executable behavior exists.

## Commands

```bash
python -m unittest discover -s tests -v
python evidence_graph.py examples/customer-change.json analyze
python evidence_graph.py examples/customer-change.json path REQ-001 EVID-001
python quality_gate.py examples/customer-change.json examples/quality-policy.json
```

## Invariants

- traceability is stored as graph data; matrices/reports are generated views
- broken references are validation failures
- coverage is computed deterministically from directed reachability
- policy thresholds live in policy files, not hidden constants
- provenance should be preserved when importing external artifacts
- the canonical model stays vendor-neutral
- examples must be synthetic and safe to publish

## Definition of done

A change is complete when graph semantics, policy behavior, tests, examples, and documentation agree.
