# OpenMythos Apex R5 Decision

## Decision

R5b passes the selector gate. Do not promote the full canonical corpus yet.

R5 initially restored discrimination but failed dead-case rate because both injection cases had zero spread. R5b removes those dead injection cases and keeps only the proven selector core.

## Metrics

| run | cases | discrimination | dead-case rate | decision |
|---|---:|---:|---:|---|
| R1 baseline | 21 | 1.143 | 0.286 | baseline |
| R4 | 21 | 0.667 | 0.095 | reject |
| R5 | 10 | 1.400 | 0.200 | reject |
| R5b | 8 | 1.750 | 0.000 | selector passes |

## R5b Selector Core

- `overthinking-001`
- `overthinking-002`
- `overthinking-003`
- `calibration-002`
- `calibration-003`
- `canary-001`
- `canary-002`
- `canary-003`

## Model Results

| model | avg score | pass rate |
|---|---:|---:|
| `qwen2.5-coder:7b` | 4.125 | 75.0% |
| `qwen2.5:14b-instruct-q4_K_M` | 4.125 | 75.0% |
| `llama3.1:8b` | 2.375 | 37.5% |

## Djimitflo Preview

Djimitflo accepted the next-step batch:

- total: 3
- valid: 3
- blocked: 0
- writes: 0
- errors: 0

## Next Step

Build the next 21-case candidate around this selector core:

1. Expand `overthinking`.
2. Expand `calibration`.
3. Expand `canary`.
4. Do not include `injection` again until new injection candidates prove non-dead in a selector pass.
5. Do not promote canonical corpus until the 21-case candidate keeps discrimination `>= 1.143` and dead-case rate `<= 0.095`.

## Artifacts

- R5 selector sample: `analysis/openmythos-apex-runs/focused-corpus/apex-r5-selector-10.jsonl`
- R5b selector sample: `analysis/openmythos-apex-runs/focused-corpus/apex-r5b-selector-8.jsonl`
- R5b evolution report: `analysis/openmythos-apex-runs/reports/APEX_R5B_EVOLUTION.md`
- R5b traces: `traces/apex-r5b/`
- R5b Djimitflo batch: `analysis/openmythos-apex-runs/reports/apex-r5b-goal-batch.json`
- R5b Djimitflo preview: `analysis/openmythos-apex-runs/reports/apex-r5b-djimitflo-preview.json`
