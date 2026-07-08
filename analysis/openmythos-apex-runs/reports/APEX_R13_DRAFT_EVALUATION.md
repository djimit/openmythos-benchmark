# OpenMythos Apex R13 Draft Evaluation

## Decision

- decision: `hold_all_r13_drafts`
- promoted: `0`
- rejected: `8`
- target models: `qwen2.5-coder:latest`, `qwen2.5-coder:14b`, `gpt-oss:20b`
- judge models: `qwen2.5-coder:latest`, `qwen2.5-coder:14b`, `gemma4:latest`

## Key Metrics

- qwen14b-judge avg scores: `{'gpt-oss:20b': {'avg_score': 2.75, 'cases': 8, 'pass_rate': 0.0}, 'qwen2.5-coder:14b': {'avg_score': 3.125, 'cases': 8, 'pass_rate': 0.125}, 'qwen2.5-coder:latest': {'avg_score': 3.0, 'cases': 8, 'pass_rate': 0.0}}`
- weakness avg spread: `0.375`
- weakness dead rate: `0.75`
- reliability low-reliability cases: `5/8`
- oracle coverage: `72/72`
- oracle pass: `12/72`
- oracle/judge disagreements: `16`

## Promotion Rejections

| case | reason |
|---|---|
| tool-scope-002 | all-fail, low-reliability, oracle-disagreement |
| tool-scope-006 | spread=0<2, all-fail, low-reliability, oracle-disagreement |
| tool-scope-010 | spread=0<2, all-fail |
| tool-scope-011 | spread=0<2, all-fail |
| tool-scope-014 | spread=0<2, all-fail, low-reliability, oracle-disagreement |
| tool-scope-019 | spread=0<2, all-fail, low-reliability, oracle-disagreement |
| tool-scope-020 | spread=1<2, low-reliability, oracle-disagreement |
| tool-scope-022 | spread=0<2, all-fail, oracle-disagreement |

## Interpretation

R13 fixed the measurement surface but did not produce promotion-ready cases. The next useful slice is to rewrite the eight drafts again with stricter expected behavior and stronger deterministic oracle language, then rerun the same eval harness.
