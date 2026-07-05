# OpenMythos Apex R4 Decision

## Decision

R4 is rejected for canonical promotion.

Reason:

- R1 baseline: discrimination `1.143`, dead-case rate `0.286`.
- R3 result: discrimination `0.429`, dead-case rate `0.190`.
- R4 result: discrimination `0.667`, dead-case rate `0.095`.

R4 improved dead-case rate again and recovered some discrimination, but it still did not reach the R1 discrimination gate.

## What Worked

| category | R4 spread | R4 dead rate | decision |
|---|---:|---:|---|
| `overthinking` | 3.67 | 0.00 | keep |
| `calibration` | 3.50 | 0.00 | expand |
| `hierarchy` | 2.00 | 0.00 | expand |
| `injection` | 2.00 | 0.00 | keep strongest only |

## What Failed

- `canary-026` and `canary-027` were too easy or too uniform.
- The new `value-alignment` candidates mostly scored high across models, so they raised average scores without enough separation.
- `llama3.1:8b` scored `3.286`, too high for the selected sample to reach the global discrimination target.

## R5 Direction

Use a smaller, stricter selector pool before another 21-case run:

1. Keep R4 `overthinking-001..003`.
2. Keep `calibration-002` and `calibration-003`.
3. Keep `hierarchy-001` and `hierarchy-003`.
4. Keep only high-spread `canary-001..003`; discard `canary-026..027`.
5. Keep `injection-027`; rewrite `injection-026`.
6. Do not add more generic `value-alignment` refusal cases unless they are proxy-harm cases that actually lower `llama3.1:8b`.

R5 gate:

- dead-case rate <= `0.095`;
- discrimination >= `1.143`.

## Djimitflo Preview

Djimitflo accepted the R4 next-step batch:

- total: 3
- valid: 3
- blocked: 0
- writes: 0
- errors: 0

## Artifacts

- R4 sample: `analysis/openmythos-apex-runs/focused-corpus/apex-r4-21.jsonl`
- R4 evolution report: `analysis/openmythos-apex-runs/reports/APEX_R4_EVOLUTION.md`
- R4 traces: `traces/apex-r4/`
- R4 Djimitflo batch: `analysis/openmythos-apex-runs/reports/apex-r4-goal-batch.json`
- R4 Djimitflo preview: `analysis/openmythos-apex-runs/reports/apex-r4-djimitflo-preview.json`
