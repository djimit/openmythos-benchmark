# OpenMythos Apex R18 Local Canonical Leaderboard

## Decision

- decision: `r18_full_local_canonical_oracle_leaderboard`
- canonical corpus outputs: `351` cases per model
- target models: `qwen2.5-coder:latest`, `qwen2.5-coder:14b`, `gpt-oss:20b`
- total model outputs: `1053`
- output errors: `0`
- scoring surface: deterministic oracle on mechanically checkable cases
- oracle common cases: `96`
- oracle coverage: `288/1053`
- oracle coverage rate: `0.274`

## Oracle Leaderboard

| rank | model | oracle avg | oracle pass rate | oracle cases | avg ms | avg tokens |
|---:|---|---:|---:|---:|---:|---:|
| 1 | qwen2.5-coder:latest | 3.042 | 0.510 | 96 | 1743.0 | 47.5 |
| 2 | qwen2.5-coder:14b | 2.958 | 0.490 | 96 | 2378.1 | 37.6 |
| 3 | gpt-oss:20b | 2.625 | 0.406 | 96 | 1850.1 | 63.7 |

## Full-Corpus Operational Gates

| model | result | cases | errors | avg ms | max ms | avg tokens | max tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen2.5-coder:latest | pass | 351 | 0 | 2255.8 | 9571.8 | 71.8 | 256 |
| qwen2.5-coder:14b | pass | 351 | 0 | 2906.4 | 10374.1 | 47.8 | 96 |
| gpt-oss:20b | pass | 351 | 0 | 1864.0 | 7251.9 | 63.9 | 64 |

## Benchmark Shape

- discrimination: `0.417`
- dead-case rate: `0.594`
- avg case spread: `1.625`

## Weakest Oracle Categories

| category | cases | avg score | avg spread | dead rate | all-fail rate | weakness |
|---|---:|---:|---:|---:|---:|---:|
| contradiction | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 4.500 |
| cross-lingual | 6 | 1.000 | 0.000 | 1.000 | 1.000 | 4.500 |
| temporal-reasoning | 2 | 1.000 | 0.000 | 1.000 | 1.000 | 4.500 |
| hallucination | 11 | 1.485 | 1.091 | 0.727 | 0.727 | 2.591 |
| canary | 37 | 4.207 | 1.405 | 0.649 | 0.000 | 2.041 |
| overthinking | 24 | 2.000 | 1.667 | 0.583 | 0.500 | 1.750 |
| tool-scope | 14 | 3.286 | 3.714 | 0.071 | 0.071 | 0.214 |

## Interpretation

R18 confirms that the full canonical corpus can be run locally across three
available models with zero runtime errors. The oracle-scored slice ranks
`qwen2.5-coder:latest` slightly ahead of `qwen2.5-coder:14b`, with `gpt-oss:20b`
behind on deterministic exactness and tool-scope checks.

The important engineering signal is not the ranking alone. `tool-scope` is now
the strongest oracle category by spread and low dead-rate after R16/R17, while
exact-output and hallucination-style cases are the next obvious weakness.

## Boundary

This is not a full LLM-as-judge leaderboard. R18 deliberately uses deterministic
oracle scoring for mechanically checkable rows and records the coverage. Raw
traces are under ignored `traces/apex-r18-local-canonical/`; commit-safe
evidence is in `analysis/openmythos-apex-runs/reports/`.

## Next

R19 should target exact-output and hallucination deterministic failures:
cross-lingual, contradiction, temporal-reasoning, legal authority, metrics, and
strict scalar/JSON/CSV output.
