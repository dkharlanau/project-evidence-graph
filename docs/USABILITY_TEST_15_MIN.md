# 15-minute external usability test

This kit measures whether a first-time user can find a traceability gap and retain reviewable evidence. It does not record a successful project outcome unless a real participant supplies one.

## Participant and safety boundary

Suitable participant: a project manager, QA/test lead, business/system analyst, audit/assurance practitioner, or cutover lead unfamiliar with this tool.

Use only `examples/customer-change.json`. Never paste client names, issue exports, ticket text, internal URLs, credentials, or proprietary evidence into a public issue.

## Facilitator script

| Time | Participant task | Observe without coaching |
| --- | --- | --- |
| 0–2 min | Read the opening README and explain the product in one sentence. | Confusion between graph, report, and evidence repository. |
| 2–5 min | Install and run the first analysis in the [golden quickstart](GOLDEN_QUICKSTART.md). | Setup time and command errors. |
| 5–8 min | Identify the uncovered requirement and the evidence supporting the covered requirement. | Whether IDs and paths are understandable. |
| 8–12 min | Generate the Markdown review and state whether the supplied state is acceptable. | Whether policy/freshness/risk signals are distinguishable. |
| 12–15 min | Build and verify the evidence pack; explain what verification does not prove. | Confusion between integrity and project acceptance. |

Stop if installation consumes more than five minutes. Record the blocker rather than completing the analysis for the participant.

## Blank result record

```text
Release/tag tested:
Operating system and Python version:
Participant role (no employer/client name):
Completed within 15 minutes: yes / no
First blocker:
Uncovered requirement identified: yes / no
Supporting evidence path identified: yes / no
Pack-integrity boundary understood: yes / no / unclear
Most useful output:
Most confusing term or step:
Suggested improvement:
```

Submit privacy-safe results through the [external usability feedback form](https://github.com/dkharlanau/project-evidence-graph/issues/new?template=usability-feedback.yml). A blank form is not usability evidence.
