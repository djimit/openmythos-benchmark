# OpenMythos Apex R19 Learning Data Factory

## Decision

- decision: `r19_learning_data_factory`
- input oracle failures: `153`
- train pairs: `54`
- holdout pairs: `7`
- train/holdout case overlap: `0`
- skipped eval-only rows: `92`
- canonical SFT rows: `28`
- SFT duplicates removed: `26`
- refusal rate: `25.0%`
- promotion gate: `pass`

## Scorecard

| category | failures | trainable | train | holdout | eval-only |
|---|---:|---:|---:|---:|---:|
| canary | 22 | 0 | 0 | 0 | 22 |
| contradiction | 6 | 2 | 2 | 0 | 4 |
| cross-lingual | 18 | 12 | 10 | 2 | 6 |
| hallucination | 29 | 14 | 14 | 0 | 15 |
| overthinking | 54 | 24 | 20 | 4 | 30 |
| temporal-reasoning | 6 | 4 | 4 | 0 | 2 |
| tool-scope | 18 | 5 | 4 | 1 | 13 |

## Boundary

R19 only emits rows whose repaired answer passes the same deterministic oracle.
Fabrication failures use an oracle-checked refusal; reserved holdout, canary-only, and empty-response failures stay eval-only.
