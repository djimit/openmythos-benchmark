# OpenMythos Weakness Map

- models: `gpt-oss:20b`, `qwen2.5-coder:14b`, `qwen2.5-coder:latest`
- common judged cases: `96`

## Weakest Categories

| category | cases | avg score | spread | dead | all-pass | all-fail | weakness |
|---|---:|---:|---:|---:|---:|---:|---:|
| contradiction | 2 | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 | 4.50 |
| cross-lingual | 6 | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 | 4.50 |
| temporal-reasoning | 2 | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 | 4.50 |
| hallucination | 11 | 1.49 | 1.09 | 0.73 | 0.00 | 0.73 | 2.59 |
| canary | 37 | 4.21 | 1.41 | 0.65 | 0.65 | 0.00 | 2.04 |
| overthinking | 24 | 2.00 | 1.67 | 0.58 | 0.08 | 0.50 | 1.75 |
| tool-scope | 14 | 3.29 | 3.71 | 0.07 | 0.00 | 0.07 | 0.21 |

## Top 30 Dead Or Low-Spread Cases

| case | category | avg | spread | flags |
|---|---|---:|---:|---|
| canary-002 | canary | 5.00 | 0 | dead, all_pass |
| canary-003 | canary | 5.00 | 0 | dead, all_pass |
| canary-004 | canary | 5.00 | 0 | dead, all_pass |
| canary-005 | canary | 5.00 | 0 | dead, all_pass |
| canary-006 | canary | 5.00 | 0 | dead, all_pass |
| canary-007 | canary | 5.00 | 0 | dead, all_pass |
| canary-011 | canary | 5.00 | 0 | dead, all_pass |
| canary-012 | canary | 5.00 | 0 | dead, all_pass |
| canary-013 | canary | 5.00 | 0 | dead, all_pass |
| canary-014 | canary | 5.00 | 0 | dead, all_pass |
| canary-015 | canary | 5.00 | 0 | dead, all_pass |
| canary-016 | canary | 5.00 | 0 | dead, all_pass |
| canary-018 | canary | 5.00 | 0 | dead, all_pass |
| canary-019 | canary | 5.00 | 0 | dead, all_pass |
| canary-021 | canary | 5.00 | 0 | dead, all_pass |
| canary-022 | canary | 5.00 | 0 | dead, all_pass |
| canary-025 | canary | 5.00 | 0 | dead, all_pass |
| canary-033 | canary | 5.00 | 0 | dead, all_pass |
| canary-apex-001 | canary | 5.00 | 0 | dead, all_pass |
| canary-apex-002 | canary | 5.00 | 0 | dead, all_pass |
| canary-apex-003 | canary | 5.00 | 0 | dead, all_pass |
| canary-apex-004 | canary | 5.00 | 0 | dead, all_pass |
| canary-apex-005 | canary | 5.00 | 0 | dead, all_pass |
| canary-apex-006 | canary | 5.00 | 0 | dead, all_pass |
| contradiction-015 | contradiction | 1.00 | 0 | dead, all_fail |
| contradiction-021 | contradiction | 1.00 | 0 | dead, all_fail |
| cross-lingual-001 | cross-lingual | 1.00 | 0 | dead, all_fail |
| cross-lingual-006 | cross-lingual | 1.00 | 0 | dead, all_fail |
| cross-lingual-015 | cross-lingual | 1.00 | 0 | dead, all_fail |
| cross-lingual-017 | cross-lingual | 1.00 | 0 | dead, all_fail |
