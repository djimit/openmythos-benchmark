# OpenMythos Apex R3 Decision

## Decision

R2 is rejected. R3 is the next valid direction, but not yet promoted into the canonical corpus.

Reason:

- R1 baseline: discrimination `1.143`, dead-case rate `0.286`.
- R2 result: discrimination `0.429`, dead-case rate `0.429`.
- R3 result: discrimination `0.429`, dead-case rate `0.190`.

R3 fixed the dead-case problem but did not restore R1-level global discrimination. Promote only after the next run keeps R3's lower dead-case rate and recovers stronger global separation.

## What Improved

| category | R3 spread | R3 dead rate | decision |
|---|---:|---:|---|
| `canary` | 3.67 | 0.00 | keep expanding |
| `overthinking` | 3.67 | 0.00 | R3 candidates are useful |
| `temporal-reasoning` | 3.00 | 0.00 | R3 candidates are useful |

## What Still Blocks Promotion

Global discrimination dropped below the R1 baseline:

- required: `>= 1.143`
- R3: `0.429`

The next run should keep the R3 overthinking and temporal candidates, then add or select stronger canary/injection/value-alignment cases to recover global model separation.

## Djimitflo Preview

Djimitflo accepted the R3 next-step batch:

- total: 3
- valid: 3
- blocked: 0
- writes: 0
- errors: 0

## Next Batch

1. Expand `canary`.
2. Expand `overthinking`.
3. Expand `temporal-reasoning`.

The next run should remain draft-only until both gates pass:

- dead-case rate <= `0.190`;
- discrimination >= `1.143`.

## Artifacts

- R2 rejected evidence: `analysis/openmythos-apex-runs/reports/APEX_R2_EVOLUTION.md`
- R3 evolution report: `analysis/openmythos-apex-runs/reports/APEX_R3_EVOLUTION.md`
- R3 sample: `analysis/openmythos-apex-runs/focused-corpus/apex-r3-21.jsonl`
- R3 traces: `traces/apex-r3/`
- R3 Djimitflo batch: `analysis/openmythos-apex-runs/reports/apex-r3-goal-batch.json`
- R3 Djimitflo preview: `analysis/openmythos-apex-runs/reports/apex-r3-djimitflo-preview.json`
