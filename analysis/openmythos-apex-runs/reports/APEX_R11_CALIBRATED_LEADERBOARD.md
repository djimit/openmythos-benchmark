# OpenMythos Calibrated Leaderboard

- gold anchors: `30`
- common cases: `351`
- weighted discrimination: `0.506`
- avg case weight: `0.988`

## Leaderboard

| rank | model | weighted avg | raw avg | weighted pass | raw pass | ci95 | effective cases | discounted |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | qwen2.5:14b-instruct-q4_K_M | 3.127 | 3.140 | 0.541 | 0.547 | 0.155 | 347.4 | 5 |
| 2 | qwen2.5-coder:7b | 2.626 | 2.615 | 0.381 | 0.379 | 0.164 | 347.4 | 5 |
| 3 | llama3.1:8b | 2.621 | 2.621 | 0.390 | 0.390 | 0.158 | 347.4 | 5 |

## Judge Calibration

| judge | anchors | agreement | false pass | false fail | bias | weight |
|---|---:|---:|---:|---:|---:|---:|
| ornith-1.0-9b:latest | 10 | 0.600 | 0.000 | 0.400 | -0.400 | 0.600 |
| qwen2.5:14b-instruct-q4_K_M | 10 | 0.800 | 0.100 | 0.100 | +0.000 | 0.800 |
| qwen2.5:32b-instruct-q4_K_M | 10 | 0.800 | 0.100 | 0.100 | +0.000 | 0.800 |
