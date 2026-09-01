# Release and compatibility policy

Project Evidence Graph uses Semantic Versioning for the installed CLI, Python modules, graph semantics, and retained evidence-pack formats.

- Patch releases preserve the v0.2 graph and CLI contracts while fixing defects.
- Minor releases may add optional node/link fields, adapters, analyses, or pack members. During `0.x`, consumers must review release notes.
- Major releases may change identity, reachability, policy, or pack semantics and require migration guidance.

## Supported release surface

The v0.2 release covers Python 3.10–3.12, the installed CLI, vendor-neutral graph model, synthetic examples, public adapters, consolidated reviews, and evidence-pack build/verify behavior.

GitHub Releases attach a reproducible wheel, a deterministic `git archive` source snapshot, and `SHA256SUMS` from the proven tagged commit. The wheel is built twice with `SOURCE_DATE_EPOCH` set to the commit time and must match byte for byte before publication.

## Compatibility boundaries

- Cross-repository references are explicit links, not automatic semantic inference.
- Source adapters retain provenance but cannot prove the source system was complete or authoritative.
- Pack verification checks recorded file integrity; it does not establish business acceptance, retention compliance, or production truth.
- The browser explorer is a generated view, not the canonical graph editor.

See the [golden quickstart](GOLDEN_QUICKSTART.md) and [v0.2.0 release notes](../release/v0.2.0.md).
