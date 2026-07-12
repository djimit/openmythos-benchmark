# OpenMythos Apex R19 Learning Data Factory

## Decision

- decision: `r19_learning_data_factory`
- input oracle failures: `153`
- train pairs: `52`
- holdout pairs: `10`
- train/holdout case overlap: `0`
- skipped eval-only rows: `91`
- canonical SFT rows: `29`
- SFT duplicates removed: `23`
- refusal rate: `10.3%`
- promotion gate: `pass`

## Scorecard

| category | failures | trainable | train | holdout | eval-only |
|---|---:|---:|---:|---:|---:|
| canary | 22 | 0 | 0 | 0 | 22 |
| contradiction | 6 | 4 | 2 | 2 | 2 |
| cross-lingual | 18 | 12 | 12 | 0 | 6 |
| hallucination | 29 | 5 | 5 | 0 | 24 |
| overthinking | 54 | 32 | 24 | 8 | 22 |
| temporal-reasoning | 6 | 4 | 4 | 0 | 2 |
| tool-scope | 18 | 5 | 5 | 0 | 13 |

## Boundary

R19 only emits rows whose repaired answer passes the same deterministic oracle.
Fabrication, canary-only, and empty-response failures stay eval-only when no useful deterministic repair exists.
