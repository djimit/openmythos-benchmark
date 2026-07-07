# OpenMythos Leaderboard

- common cases: `351`
- discrimination: `0.524`
- dead-case rate: `0.305`
- avg case spread: `1.695`

| rank | model | avg score | pass rate | cases | errors | avg ms | avg tokens |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | qwen2.5:14b-instruct-q4_K_M | 3.140 | 0.547 | 351 | 0 | 3564.0 | 155.3 |
| 2 | llama3.1:8b | 2.621 | 0.390 | 351 | 0 | 2549.0 | 138.7 |
| 3 | qwen2.5-coder:7b | 2.615 | 0.379 | 351 | 0 | 1736.1 | 126.1 |

## Regression Delta

| model | avg score delta | pass rate delta |
|---|---:|---:|
| qwen2.5:14b-instruct-q4_K_M | -0.003 | +0.000 |
| llama3.1:8b | +0.004 | -0.002 |
| qwen2.5-coder:7b | -0.020 | -0.004 |

- discrimination delta: `-0.002`
- dead-case-rate delta: `-0.008`
