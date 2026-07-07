# OpenMythos Leaderboard

- common cases: `342`
- discrimination: `0.526`
- dead-case rate: `0.313`
- avg case spread: `1.661`

| rank | model | avg score | pass rate | cases | errors | avg ms | avg tokens |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | qwen2.5:14b-instruct-q4_K_M | 3.143 | 0.547 | 342 | 0 | 3578.2 | 156.0 |
| 2 | qwen2.5-coder:7b | 2.635 | 0.383 | 342 | 0 | 1733.3 | 126.5 |
| 3 | llama3.1:8b | 2.617 | 0.392 | 342 | 0 | 2519.9 | 139.2 |

## Regression Delta

| model | avg score delta | pass rate delta |
|---|---:|---:|
| llama3.1:8b | +0.257 | +0.057 |

- benchmark delta skipped: baseline and current model sets differ
