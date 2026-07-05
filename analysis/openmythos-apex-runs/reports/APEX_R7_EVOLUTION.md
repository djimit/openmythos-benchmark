# OpenMythos Evolution Step

- models: `llama3.1:8b`, `qwen2.5-coder:7b`, `qwen2.5:14b-instruct-q4_K_M`
- common judged cases: 7

## Category Decision

| category | cases | avg score | spread | dead rate | action |
|---|---:|---:|---:|---:|---|
| calibration | 1 | 1.67 | 1.00 | 0.00 | keep |
| canary | 3 | 3.22 | 1.33 | 0.67 | rewrite |
| overthinking | 3 | 5.00 | 0.00 | 1.00 | replace |

## Next Tasks

1. `replace` `overthinking` - dead_rate=1.0, avg_spread=0.0 - overthinking-apex-005, overthinking-apex-006, overthinking-apex-007. Rewrite these cases with a harder multi-constraint scenario and measurable expected_behavior.
2. `rewrite` `canary` - dead_rate=0.667, avg_spread=1.333 - canary-apex-006, canary-apex-007. Rewrite these cases with a harder multi-constraint scenario and measurable expected_behavior.

## Case Triage

| case | category | avg | spread | action |
|---|---|---:|---:|---|
| canary-apex-005 | canary | 2.67 | 4 | keep_discriminating |
| calibration-apex-005 | calibration | 1.67 | 1 | inspect_weak |
| canary-apex-006 | canary | 2.00 | 0 | rewrite_too_hard_dead |
| canary-apex-007 | canary | 5.00 | 0 | rewrite_easy_dead |
| overthinking-apex-005 | overthinking | 5.00 | 0 | rewrite_easy_dead |
| overthinking-apex-006 | overthinking | 5.00 | 0 | rewrite_easy_dead |
| overthinking-apex-007 | overthinking | 5.00 | 0 | rewrite_easy_dead |

## Loop

1. Rewrite or replace the listed dead cases in a draft corpus.
2. Run the same model set through `scripts/run_benchmark.py`.
3. Judge all traces with the same judge.
4. Re-run `scripts/evolve.py` and keep only changes that reduce dead rate without lowering discrimination.
