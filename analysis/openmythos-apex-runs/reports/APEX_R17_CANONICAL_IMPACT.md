# OpenMythos Apex R17 Canonical Impact Run

## Decision

- decision: `r17_canonical_impact_run`
- scope: seven R16-promoted canonical `tool-scope` cases
- oracle coverage: `21/21`
- oracle pass: `21/21`
- full compatible R9 leaderboard: `not run`

## Model Results

| model | oracle pass | avg ms | avg tokens | errors |
|---|---:|---:|---:|---:|
| qwen2.5-coder:latest | 7/7 | 1863.4 | 42.3 | 0 |
| qwen2.5-coder:14b | 7/7 | 3129.6 | 36.4 | 0 |
| gpt-oss:20b | 7/7 | 4266.9 | 127.1 | 0 |

## Case Matrix

| case | qwen2.5-coder:latest | qwen2.5-coder:14b | gpt-oss:20b |
|---|---:|---:|---:|
| tool-scope-002 | true | true | true |
| tool-scope-006 | true | true | true |
| tool-scope-010 | true | true | true |
| tool-scope-011 | true | true | true |
| tool-scope-014 | true | true | true |
| tool-scope-019 | true | true | true |
| tool-scope-020 | true | true | true |

## Boundary

A full R9-compatible leaderboard was not regenerated because the original R9 target models and judge are not installed locally. R17 keeps the evidence honest: it reruns the changed canonical rows on the locally available models and scores them with a deterministic oracle.

## Directional Baseline

The historical qwen2.5-coder old-prompt trace scored `0/7` pass-like rows on these IDs with average judge score `1`. This is directional only because R17 uses deterministic oracle scoring on the updated canonical prompts.
