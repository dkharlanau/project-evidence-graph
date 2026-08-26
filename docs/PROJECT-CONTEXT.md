# Bounded Project Context

`project_context.py` creates a compact machine-readable context package for an agent or downstream tool.

The goal is not to summarize the entire project. It is to provide a reproducible bounded slice around a focus artifact while retaining the identifiers and provenance needed to verify claims.

## Example

```bash
python project_context.py project-graph.json \
  --focus REQ-COUNTRY \
  --depth 2 \
  --quality-policy examples/quality-policy.json \
  --freshness-policy examples/freshness-policy.json \
  --risk-policy examples/risk-policy.json \
  --output project-context.json
```

## Scope semantics

Traversal is bidirectional for context selection. At each depth step, both immediate upstream and downstream linked artifacts are included. This differs from impact analysis: the purpose here is to give an agent enough surrounding context to understand the selected artifact.

Only links whose two endpoints are inside the selected node set are included.

## Preserved fields

The compact node representation keeps high-value machine context including:

- `id`, `type`, `title`;
- `risk`, `status`;
- `artifact_ref` (`eac://...`);
- source/provenance metadata;
- evidence timestamps;
- external tracker IDs/source metadata.

Arbitrary large fields are intentionally omitted.

## Stable context ID

`context_id` is a deterministic SHA-256-derived ID over the focus, depth, selected nodes, and links. The same graph slice and scope produce the same ID. A material change to the selected context changes the ID.

This allows prompts, agent runs, decisions, or review results to record exactly which project context they consumed.

## Optional assurance

If quality/freshness/risk policies are supplied, the output embeds the same consolidated assurance summary used by `project_review.py`. The assurance calculation still evaluates the project graph; the bounded slice controls what contextual artifacts are delivered to the agent.

## Safety boundary

The context builder does not infer missing links, fetch remote repositories, or execute project actions. It packages already explicit project knowledge into a smaller deterministic envelope.
