# OpenMythos Apex R1 Next Steps

## Run

- corpus: `analysis/openmythos-apex-runs/focused-corpus/apex-r1-21.jsonl`
- cases: 21, balanced as 3 cases each across 7 categories
- models: `llama3.1:8b`, `qwen2.5-coder:7b`, `qwen2.5:14b-instruct-q4_K_M`
- judge: `qwen2.5:32b-instruct-q4_K_M`
- orchestrator validation: Djimitflo `GoalBatchService.preview`

## Model Results

| model | avg score | pass rate |
|---|---:|---:|
| `qwen2.5:14b-instruct-q4_K_M` | 3.81 | 76.2% |
| `qwen2.5-coder:7b` | 3.33 | 52.4% |
| `llama3.1:8b` | 2.67 | 38.1% |

## Corpus Signal

- discrimination: 1.143
- dead-case rate: 0.286

| category | avg spread | dead rate | decision |
|---|---:|---:|---|
| `canary` | 4.00 | 0.00 | expand |
| `value-alignment` | 3.00 | 0.00 | expand |
| `injection` | 2.33 | 0.00 | expand |
| `hierarchy` | 0.67 | 0.67 | rewrite |
| `overthinking` | 1.33 | 0.67 | rewrite |
| `calibration` | 1.33 | 0.33 | keep for now |
| `temporal-reasoning` | 2.33 | 0.33 | keep for now |

## Apex R2 Goals

1. Rewrite `hierarchy-002` and `hierarchy-003`.
2. Rewrite `overthinking-002` and `overthinking-003`.
3. Expand `canary` with adjacent leak/suppression cases.
4. Expand `value-alignment` with proxy-harm and manipulation cases.
5. Expand `injection` with multi-turn and role-conflict cases.

## Promotion Rule

Do not promote R2 changes until the same model set is rerun and:

- dead-case rate drops below 0.286;
- discrimination stays at or above 1.143;
- `scripts/validate.py` passes;
- Djimitflo preview remains `valid=total`, `blocked=0`, `writes=0`.

## Artifacts

- OpenMythos evolution report: `analysis/openmythos-apex-runs/reports/APEX_R1_EVOLUTION.md`
- Djimitflo batch: `analysis/openmythos-apex-runs/reports/apex-r1-goal-batch.json`
- Djimitflo preview proof: `analysis/openmythos-apex-runs/reports/djimitflo-preview.json`
- judged traces: `traces/apex-r1/judged_*.jsonl`
