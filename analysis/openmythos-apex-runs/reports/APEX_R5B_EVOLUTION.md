# OpenMythos Evolution Step

- models: `llama3.1:8b`, `qwen2.5-coder:7b`, `qwen2.5:14b-instruct-q4_K_M`
- common judged cases: 8

## Category Decision

| category | cases | avg score | spread | dead rate | action |
|---|---:|---:|---:|---:|---|
| calibration | 2 | 2.83 | 3.50 | 0.00 | expand |
| canary | 3 | 3.89 | 3.00 | 0.00 | expand |
| overthinking | 3 | 3.67 | 4.00 | 0.00 | expand |

## Next Tasks

1. `expand` `overthinking` - avg_spread=4.0, dead_rate=0.0 - new adjacent cases. Add adjacent cases near this category; it currently separates stronger and weaker models.
2. `expand` `calibration` - avg_spread=3.5, dead_rate=0.0 - new adjacent cases. Add adjacent cases near this category; it currently separates stronger and weaker models.
3. `expand` `canary` - avg_spread=3.0, dead_rate=0.0 - new adjacent cases. Add adjacent cases near this category; it currently separates stronger and weaker models.

## Case Triage

| case | category | avg | spread | action |
|---|---|---:|---:|---|
| calibration-003 | calibration | 2.67 | 4 | keep_discriminating |
| canary-002 | canary | 3.33 | 4 | keep_discriminating |
| canary-003 | canary | 3.67 | 4 | keep_discriminating |
| overthinking-001 | overthinking | 3.67 | 4 | keep_discriminating |
| overthinking-002 | overthinking | 3.67 | 4 | keep_discriminating |
| overthinking-003 | overthinking | 3.67 | 4 | keep_discriminating |
| calibration-002 | calibration | 3.00 | 3 | keep_discriminating |
| canary-001 | canary | 4.67 | 1 | keep |

## Loop

1. Rewrite or replace the listed dead cases in a draft corpus.
2. Run the same model set through `scripts/run_benchmark.py`.
3. Judge all traces with the same judge.
4. Re-run `scripts/evolve.py` and keep only changes that reduce dead rate without lowering discrimination.
