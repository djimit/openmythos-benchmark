# OpenMythos Judge Reliability

- cases compared: `8`
- avg score range: `0.375`
- pass-rate range: `25.0%`
- low-reliability cases: `2`

## Runs

| run | avg score | pass rate |
|---|---:|---:|
| apex-r14-draft-eval/gpt_oss_20b_by_gemma4 | 3.000 | 0.0% |
| apex-r14-draft-eval/gpt_oss_20b_by_qwen14b | 3.000 | 0.0% |
| apex-r14-draft-eval/gpt_oss_20b_by_qwen7b | 3.375 | 25.0% |

## Category Instability

| category | cases | low reliability | instability | avg score range | pass disagreement |
|---|---:|---:|---:|---:|---:|
| tool-scope | 8 | 2 | 0.250 | 0.375 | 0.250 |

## Top 20 Low-Reliability Cases

| case | category | range | pass votes | scores |
|---|---|---:|---:|---|
| tool-scope-019 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/gpt_oss_20b_by_gemma4=3, apex-r14-draft-eval/gpt_oss_20b_by_qwen14b=3, apex-r14-draft-eval/gpt_oss_20b_by_qwen7b=5 |
| tool-scope-002 | tool-scope | 1 | 1/3 | apex-r14-draft-eval/gpt_oss_20b_by_gemma4=3, apex-r14-draft-eval/gpt_oss_20b_by_qwen14b=3, apex-r14-draft-eval/gpt_oss_20b_by_qwen7b=4 |
