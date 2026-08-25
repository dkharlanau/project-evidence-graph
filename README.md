# Project Evidence Graph

Connect requirements, decisions, mappings, tests, defects, changes, and evidence into a traceable project graph.

## Problem

Project rationale disappears because requirements, mappings, tests, defects, changes, decisions, and evidence live in separate systems.

## Core idea

Link requirements, decisions, mappings, interfaces, tests, defects, changes, and evidence into one traceable, versionable project graph.

## Example

```text
Requirement
  -> Decision
  -> Mapping
  -> Interface
  -> Test
  -> Defect
  -> Change
  -> Evidence
```

## Initial scope

- structured project entities
- links between artifacts
- orphan detection
- traceability gaps
- visual graph
- requirement-to-test traceability
- decision-to-change traceability
- evidence coverage

## Long-term direction

A lightweight project knowledge/evidence layer that sits across GitHub, Jira, SAP ALM, documentation, and spreadsheets.

## Design principles

- versionable
- portable
- machine-readable
- deterministic-first
- visual where useful
- Git-friendly
- vendor-neutral where practical
- interoperable with enterprise tools

## Status

Planning.
