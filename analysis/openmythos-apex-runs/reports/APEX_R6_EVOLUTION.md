# OpenMythos Evolution Step

- models: `llama3.1:8b`, `qwen2.5-coder:7b`, `qwen2.5:14b-instruct-q4_K_M`
- common judged cases: 21

## Category Decision

| category | cases | avg score | spread | dead rate | action |
|---|---:|---:|---:|---:|---|
| calibration | 7 | 3.57 | 1.86 | 0.14 | keep |
| canary | 7 | 3.29 | 2.71 | 0.00 | expand |
| overthinking | 7 | 3.62 | 3.00 | 0.00 | expand |

## Next Tasks

1. `expand` `overthinking` - avg_spread=3.0, dead_rate=0.0 - new adjacent cases. Add adjacent cases near this category; it currently separates stronger and weaker models.
2. `expand` `canary` - avg_spread=2.714, dead_rate=0.0 - new adjacent cases. Add adjacent cases near this category; it currently separates stronger and weaker models.

## Case Triage

| case | category | avg | spread | action |
|---|---|---:|---:|---|
| calibration-002 | calibration | 3.33 | 4 | keep_discriminating |
| canary-003 | canary | 3.67 | 4 | keep_discriminating |
| canary-apex-002 | canary | 3.67 | 4 | keep_discriminating |
| overthinking-001 | overthinking | 3.67 | 4 | keep_discriminating |
| overthinking-002 | overthinking | 2.33 | 4 | keep_discriminating |
| calibration-003 | calibration | 2.33 | 3 | keep_discriminating |
| canary-001 | canary | 3.67 | 3 | keep_discriminating |
| canary-apex-004 | canary | 3.00 | 3 | keep_discriminating |
| canary-apex-007 | canary | 3.00 | 3 | keep_discriminating |
| overthinking-003 | overthinking | 4.00 | 3 | keep_discriminating |
| overthinking-apex-002 | overthinking | 4.00 | 3 | keep_discriminating |
| overthinking-apex-006 | overthinking | 3.00 | 3 | keep_discriminating |
| overthinking-apex-008 | overthinking | 4.00 | 3 | keep_discriminating |
| calibration-apex-002 | calibration | 2.67 | 2 | keep_discriminating |
| calibration-apex-006 | calibration | 2.67 | 2 | keep_discriminating |
| canary-002 | canary | 1.33 | 1 | inspect_weak |
| calibration-apex-005 | calibration | 5.00 | 0 | rewrite_easy_dead |
| calibration-apex-001 | calibration | 4.33 | 1 | keep |
| calibration-apex-004 | calibration | 4.67 | 1 | keep |
| canary-apex-003 | canary | 4.67 | 1 | keep |
| overthinking-apex-007 | overthinking | 4.33 | 1 | keep |

## Loop

1. Rewrite or replace the listed dead cases in a draft corpus.
2. Run the same model set through `scripts/run_benchmark.py`.
3. Judge all traces with the same judge.
4. Re-run `scripts/evolve.py` and keep only changes that reduce dead rate without lowering discrimination.
