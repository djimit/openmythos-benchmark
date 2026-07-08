# OpenMythos Apex R12 Active Evolution Queue

## Evidence Summary

- common calibrated cases: `351`
- weighted discrimination: `0.506`
- gold anchors: `30`
- R10 unstable cases: `8`
- R10 promoted cases: `0`
- R10 rejected cases: `16`

## Category Priority

| rank | category | priority | drivers | weakness | instability | anchors | oracle gap | calibration gap |
|---:|---|---:|---|---:|---:|---:|---:|---:|
| 1 | tool-scope | 6.822 | judge-instability, weak-category, calibration-gap | 1.536 | 1.000 | 9 | 0.000 | 0.750 |
| 2 | contradiction | 6.433 | judge-instability, oracle-gap, weak-category, dead-or-nondiscriminating-cases, calibration-gap | 1.154 | 0.500 | 0 | 1.000 | 1.000 |
| 3 | temporal-reasoning | 4.876 | oracle-gap, weak-category, dead-or-nondiscriminating-cases, calibration-gap | 1.179 | 0.000 | 0 | 1.000 | 1.000 |
| 4 | value-alignment | 4.757 | oracle-gap, weak-category, dead-or-nondiscriminating-cases, calibration-gap | 1.157 | 0.000 | 0 | 1.000 | 1.000 |
| 5 | overthinking | 4.490 | oracle-gap, weak-category, dead-or-nondiscriminating-cases, calibration-gap | 1.000 | 0.000 | 0 | 1.000 | 1.000 |
| 6 | hallucination | 4.008 | judge-instability, weak-category, dead-or-nondiscriminating-cases | 1.119 | 0.500 | 9 | 0.000 | 0.083 |
| 7 | calibration | 3.872 | oracle-gap, calibration-gap | 0.730 | 0.000 | 0 | 1.000 | 1.000 |
| 8 | hierarchy | 3.799 | oracle-gap, calibration-gap | 0.683 | 0.000 | 0 | 1.000 | 1.000 |
| 9 | injection | 3.760 | oracle-gap, calibration-gap | 0.680 | 0.000 | 0 | 1.000 | 1.000 |
| 10 | cross-lingual | 3.570 | oracle-gap, calibration-gap | 0.600 | 0.000 | 0 | 1.000 | 1.000 |
| 11 | canary | 2.650 | weak-category, dead-or-nondiscriminating-cases | 1.231 | 0.000 | 12 | 0.000 | 0.000 |

## Djimitflo Goal Batch

- change: `openmythos-apex-r12-djimitflo-active-evolution`
- ordered goals: `5`
- preview expectation: `writes=0`

| order | goal | risk | target |
|---:|---|---|---|
| 1 | om-r12-01-stabilize-low-reliability-categories | medium | openmythos-benchmark/scripts/reliability_gate.py |
| 2 | om-r12-02-expand-oracle-anchor-coverage | medium | openmythos-benchmark/scripts/oracle_score.py |
| 3 | om-r12-03-rewrite-dead-or-nondiscriminating-cases | medium | openmythos-benchmark/cases/corpus.jsonl |
| 4 | om-r12-04-close-calibration-bias-loop | medium | openmythos-benchmark/scripts/calibrated_leaderboard.py |
| 5 | om-r12-05-promotion-firewall | low | openmythos-benchmark/scripts/promotion_gate.py |

## Human Interactions At End

- Approve Djimitflo goal-batch apply after preview remains valid and blocked=0.
- Approve canonical case promotion only after R10, R11, and R12 evidence stays green.
