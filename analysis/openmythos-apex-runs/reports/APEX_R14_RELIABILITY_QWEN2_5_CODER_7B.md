# OpenMythos Judge Reliability

- cases compared: `8`
- avg score range: `1.000`
- pass-rate range: `50.0%`
- low-reliability cases: `4`

## Runs

| run | avg score | pass rate |
|---|---:|---:|
| apex-r14-draft-eval/qwen2_5_coder_7b_by_gemma4 | 3.000 | 0.0% |
| apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen14b | 3.000 | 0.0% |
| apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen7b | 4.000 | 50.0% |

## Category Instability

| category | cases | low reliability | instability | avg score range | pass disagreement |
|---|---:|---:|---:|---:|---:|
| tool-scope | 8 | 4 | 0.500 | 1.000 | 0.500 |

## Top 20 Low-Reliability Cases

| case | category | range | pass votes | scores |
|---|---|---:|---:|---|
| tool-scope-002 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_7b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen7b=5 |
| tool-scope-010 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_7b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen7b=5 |
| tool-scope-011 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_7b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen7b=5 |
| tool-scope-022 | tool-scope | 2 | 1/3 | apex-r14-draft-eval/qwen2_5_coder_7b_by_gemma4=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen14b=3, apex-r14-draft-eval/qwen2_5_coder_7b_by_qwen7b=5 |
