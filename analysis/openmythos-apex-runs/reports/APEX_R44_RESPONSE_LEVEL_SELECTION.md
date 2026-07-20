# OpenMythos R44 Response-Level Selection

Decision: `negative_result` — the deterministic JudgeService cannot select
among same-case candidate responses; category routing (R43) remains the best
practical method.

## Question

R43 showed category-level routing reaches 55.1% against a measured union
ceiling of 71.8%. Can an oracle-BLIND selector close the gap by picking
per-case among the three local models' responses?

## Configuration

- Harness: DjimFlo `OpenMythosEvalService.runEval` per model (production
  path), then per-case selection via `JudgeService.evaluate` (the in-process
  deterministic judge), argmax with ties breaking toward the cheaper model.
- Cases: the 78 oracle-anchored cases; subjects at temperature 0, seed 0.
- Executed 2026-07-15/16, isolated in-memory DB.

## Results

| metric | value |
|---|---|
| llama3.1:8b single | 33/78 = 42.3% |
| qwen2.5:14b single | 34/78 = 43.6% |
| qwen2.5:32b single | 37/78 = 47.4% |
| union ceiling (any model solves) | **56/78 = 71.8%** (exactly as predicted 2026-07-15) |
| category routing (R43-A, reference) | 43/78 = 55.1% |
| **judge-selected** | **33/78 = 42.3%** |

Selection distribution: **llama3.1:8b chosen 78/78 times** — the judge's
scores never exceeded the first candidate's, so the cheaper-model tie-break
decided every case.

## Findings

1. **The heuristic judge has zero discriminative power across same-case
   candidates.** Its scoring dimensions (evidence, sources, consistency,
   uncertainty) are dominated by metadata that is identical across the three
   candidates; response content differences do not move the score. Judge
   selection therefore degenerates to "always pick the first model" and lands
   exactly on that model's baseline.
2. **This is the R10 judge-reliability problem seen from the selection
   angle.** R10 showed LLM judges disagree wildly across runs; R44 shows the
   deterministic replacement judge doesn't disagree enough — it cannot rank.
   Between unreliable discrimination and no discrimination, oracle anchors
   remain the only trusted signal.
3. **Practical consequence.** The 16.7-point gap between R43 routing (55.1%)
   and the ceiling (71.8%) is NOT reachable with current in-process judging.
   Candidate paths: (a) a calibrated LLM judge with per-case reliability
   gating (expensive, R10 risk), (b) oracle-informed per-case routing learned
   from historical flips (leaks benchmark knowledge — fine for production
   routing, invalid for benchmark claims), or (c) content-aware fast
   discriminators (e.g. refusal/format detectors per category).
4. **Determinism, fourth and fifth reproductions.** Per-model baselines
   reproduced again (33/34/37; qwen14b on its known ±1 flip variant), and the
   measured union ceiling matched the 2026-07-15 prediction exactly.

## Artifacts

`r44-evidence/apex-r44-selection-results.json` — per-case judge scores,
chosen model, oracle outcomes; runs persisted under agents `R44:<model>`.
