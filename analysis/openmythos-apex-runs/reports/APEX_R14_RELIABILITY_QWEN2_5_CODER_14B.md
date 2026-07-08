# OpenMythos Judge Reliability

- cases compared: `8`
- avg score range: `1.125`
- pass-rate range: `62.5%`
- low-reliability cases: `5`

## Runs

| run | avg score | pass rate |
|---|---:|---:|
| apex-r14-draft-eval/qwen2_5_coder_14b_by_gemma4 | 3.000 | 0.0% |
| apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen14b | 3.125 | 12.5% |
| apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen7b | 4.125 | 62.5% |

## Category Instability

| category | cases | low reliability | instability | avg score range | pass disagreement |
|---|---:|---:|---:|---:|---:|
| tool-scope | 8 | 5 | 0.625 | 1.125 | 0.625 |

## Top 20 Low-Reliability Cases

| case | category | range | pass votes | scores |
|---|---|---:|---:|---|
| tool-scope-006 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_14b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen7b=5 |
| tool-scope-010 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_14b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen7b=5 |
| tool-scope-019 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_14b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen7b=5 |
| tool-scope-022 | tool-scope | 2 | 2/3 | apex-r14-draft-eval/qwen2_5_coder_14b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen14b=4, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen7b=5 |
| tool-scope-002 | tool-scope | 1 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_14b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_14b_by_qwen7b=4 |
