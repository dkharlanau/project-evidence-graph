# Golden quickstart — v0.2.0

This walkthrough analyzes the synthetic customer-change graph, exposes its known evidence gap, and creates a verifiable evidence pack.

Requirements: Git and Python 3.10+.

```bash
git clone --branch v0.2.0 --depth 1 \
  https://github.com/dkharlanau/project-evidence-graph.git
cd project-evidence-graph
python -m venv .venv
. .venv/bin/activate
python -m pip install .

project-evidence-graph analyze examples/customer-change.json \
  > /tmp/peg-v0.2.0-analysis.json
```

Verify the deterministic analysis:

```bash
python - <<'PY'
from hashlib import sha256
from pathlib import Path

path = Path('/tmp/peg-v0.2.0-analysis.json')
actual = sha256(path.read_bytes()).hexdigest()
expected = 'f76c6ef76e6e9454c51db2d480c31c58840a03c02aff34dc24c74408912ac371'
assert actual == expected, (actual, expected)
print(f'verified {actual}')
PY
```

Generate reviewable assurance and freeze it into a pack:

```bash
project-evidence-graph review examples/customer-change.json \
  --quality-policy examples/quality-policy.json \
  --freshness-policy examples/freshness-policy.json \
  --risk-policy examples/risk-policy.json \
  --lifecycle \
  --markdown /tmp/peg-v0.2.0-review.md \
  --html /tmp/peg-v0.2.0-review.html

project-evidence-graph pack build examples/customer-change.json \
  /tmp/peg-v0.2.0-pack \
  --quality-policy examples/quality-policy.json \
  --freshness-policy examples/freshness-policy.json \
  --risk-policy examples/risk-policy.json \
  --lifecycle
project-evidence-graph pack verify /tmp/peg-v0.2.0-pack
```

The example intentionally contains an uncovered requirement. Verification proves pack integrity, not that the project is ready for release.
