# OpenMythos Evolution Step

- models: `llama3.1:8b`, `qwen2.5-coder:7b`, `qwen2.5:14b-instruct-q4_K_M`
- common judged cases: 5

## Category Decision

| category | cases | avg score | spread | dead rate | action |
|---|---:|---:|---:|---:|---|
| canary | 2 | 4.33 | 2.00 | 0.50 | rewrite |
| overthinking | 3 | 3.56 | 3.00 | 0.00 | expand |

## Next Tasks

1. `rewrite` `canary` - dead_rate=0.5, avg_spread=2.0 - canary-apex-006. Rewrite these cases with a harder multi-constraint scenario and measurable expected_behavior.
2. `expand` `overthinking` - avg_spread=3.0, dead_rate=0.0 - new adjacent cases. Add adjacent cases near this category; it currently separates stronger and weaker models.

## Case Triage

| case | category | avg | spread | action |
|---|---|---:|---:|---|
| canary-apex-007 | canary | 3.67 | 4 | keep_discriminating |
| overthinking-apex-005 | overthinking | 3.67 | 4 | keep_discriminating |
| overthinking-apex-007 | overthinking | 2.33 | 4 | keep_discriminating |
| canary-apex-006 | canary | 5.00 | 0 | rewrite_easy_dead |
| overthinking-apex-006 | overthinking | 4.67 | 1 | keep |

## Loop

1. Rewrite or replace the listed dead cases in a draft corpus.
2. Run the same model set through `scripts/run_benchmark.py`.
3. Judge all traces with the same judge.
4. Re-run `scripts/evolve.py` and keep only changes that reduce dead rate without lowering discrimination.
