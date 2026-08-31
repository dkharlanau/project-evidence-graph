# Project Assurance Review

`project_review.py` consolidates several deterministic signals into one review artifact while keeping their meanings separate.

## Inputs

- Project Evidence Graph JSON
- optional quality policy
- optional evidence freshness policy
- optional risk-weighted assurance policy
- optional evidence lifecycle and stale-by-change gate, enabled with the default policy or a JSON policy

## Example

```bash
python project_review.py project-graph.json \
  --quality-policy examples/quality-policy.json \
  --freshness-policy examples/freshness-policy.json \
  --risk-policy examples/risk-policy.json \
  --lifecycle \
  --markdown project-review.md \
  --html project-review.html
```

## Decision semantics

The overall decision is `PASS` only when:

1. the graph is structurally valid; and
2. every supplied policy and enabled lifecycle gate passes.

Policies are optional. `--lifecycle` enables lifecycle assurance with deterministic defaults; `--lifecycle-policy policy.json` enables it with overrides. If no optional gate is enabled, the review decision reflects graph validity only.

The report intentionally does not collapse all assurance into one opaque percentage. It shows separately:

- raw requirement-to-test coverage;
- raw requirement-to-evidence coverage;
- fresh-evidence coverage at the policy `as_of` point;
- risk-weighted test coverage;
- risk-weighted evidence coverage;
- uncovered test/evidence risk score;
- stale/missing-timestamp evidence;
- failed policy checks.
- lifecycle contract errors;
- active evidence that predates a reachable upstream implementation change;
- unknown evidence age after an upstream change;
- requirements without current active evidence.

## Outputs

### Markdown

Human-readable Git-native review suitable for a PR, release pack, handover, or audit folder.

### HTML

Self-contained static report with a decision, scorecard, assurance gaps, and embedded machine summary. It has no external JavaScript or service dependency.

### Machine summary

The same JSON summary is embedded in both outputs so an agent or downstream script can consume the exact state that produced the human-facing decision.

## Bounded-review boundary

When the review is generated inside an evidence pack, lifecycle is evaluated only over the bounded graph slice retained in that pack. Choose a depth that includes the requirement, relevant implementation, test and evidence path. The tool does not claim that a slice proves assurance for artifacts outside it.

## Intended use

The report is a review surface, not a replacement for the graph. Source truth remains structured evidence/traceability data plus explicit policies. A reviewer can inspect why a gate failed rather than trusting a generated narrative.
