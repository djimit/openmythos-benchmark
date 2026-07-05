# Apex R1 qwen2.5 14B judged

- trace: `traces/apex-r1/judged_qwen2_5_14b.jsonl`
- model: `qwen2.5:14b-instruct-q4_K_M`
- backend: `ollama`
- cases: 21
- errors: 0
- avg latency: 4533.8 ms
- avg tokens: 215.7
- judged cases: 21
- avg judge score: 3.81/5
- pass rate: 76.2%

## Categories

| category | cases | avg score | pass rate | avg ms | errors |
|---|---:|---:|---:|---:|---:|
| calibration | 3 | 3.33 | 66.7% | 4853.7 | 0 |
| canary | 3 | 3.67 | 66.7% | 4709.7 | 0 |
| hierarchy | 3 | 4.33 | 100.0% | 9757.7 | 0 |
| injection | 3 | 2.00 | 33.3% | 2358.9 | 0 |
| overthinking | 3 | 5.00 | 100.0% | 389.5 | 0 |
| temporal-reasoning | 3 | 3.67 | 66.7% | 3240.3 | 0 |
| value-alignment | 3 | 4.67 | 100.0% | 6427.1 | 0 |
