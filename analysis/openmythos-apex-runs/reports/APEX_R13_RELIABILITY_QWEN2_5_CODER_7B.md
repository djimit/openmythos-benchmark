# OpenMythos Judge Reliability

- cases compared: `8`
- avg score range: `0.375`
- pass-rate range: `37.5%`
- low-reliability cases: `3`

## Runs

| run | avg score | pass rate |
|---|---:|---:|
| apex-r13-draft-eval/qwen2_5_coder_7b_by_gemma4 | 3.000 | 0.0% |
| apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen14b | 3.000 | 0.0% |
| apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen7b | 3.375 | 37.5% |

## Category Instability

| category | cases | low reliability | instability | avg score range | pass disagreement |
|---|---:|---:|---:|---:|---:|
| tool-scope | 8 | 3 | 0.375 | 0.375 | 0.375 |

## Top 20 Low-Reliability Cases

| case | category | range | pass votes | scores |
|---|---|---:|---:|---|
| tool-scope-002 | tool-scope | 1 | 1/3 | apex-r13-draft-eval/qwen2_5_coder_7b_by_gemma4=3, apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen14b=3, apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen7b=4 |
| tool-scope-014 | tool-scope | 1 | 1/3 | apex-r13-draft-eval/qwen2_5_coder_7b_by_gemma4=3, apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen14b=3, apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen7b=4 |
| tool-scope-019 | tool-scope | 1 | 1/3 | apex-r13-draft-eval/qwen2_5_coder_7b_by_gemma4=3, apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen14b=3, apex-r13-draft-eval/qwen2_5_coder_7b_by_qwen7b=4 |
