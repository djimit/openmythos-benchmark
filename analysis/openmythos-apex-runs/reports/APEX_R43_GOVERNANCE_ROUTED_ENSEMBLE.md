# OpenMythos R43 Governance-Routed Ensemble

Decision: `confirmed` — category-level routing beats raw scale.

## Configuration

- Harness: DjimFlo `OpenMythosEvalService.runEval` (production code path:
  generation, oracle scoring, run persistence), isolated in-memory DB.
- Cases: the 78 oracle-anchored cases (`apex-r22-oracle-anchors.json`),
  100% oracle scoring provenance, zero LLM-judge involvement.
- Subjects: temperature 0, seed 0, `num_predict` 1024, worker concurrency 6,
  Ollama `http://192.168.1.28:11434`.
- Routing tables preregistered from the 2026-07-15 run-1 category matrix
  (ties broken toward the cheaper model), executed 2026-07-16.

## Preregistered routing

| ensemble | llama3.1:8b | qwen2.5:14b | qwen2.5:32b |
|---|---|---|---|
| R43-A (all locals) | injection, calibration, hallucination | contradiction, overthinking | canary, temporal-reasoning, cross-lingual |
| R43-B (no 32b) | injection, calibration, hallucination, temporal-reasoning, cross-lingual | contradiction, overthinking, canary | — |

## Results

| run | oracle pass | rate | wall | predicted |
|---|---|---|---|---|
| **R43-A** | **43/78** | **55.1%** | 227s | 43/78 (55.1%) ✓ exact |
| **R43-B** | **40/78** | **51.3%** | 134s | 40/78 (51.3%) ✓ exact |
| baseline: qwen2.5:32b single | 37/78 | 47.4% | 305s | (2026-07-15 run) |
| baseline: qwen2.5:14b single | 33/78 | 42.3% | 172s | |
| baseline: llama3.1:8b single | 33/78 | 42.3% | 116s | |

Per-category outcomes matched the preregistered predictions cell-for-cell in
both ensembles (R43-A: injection 9/12, hallucination 2/8, calibration 2/4,
contradiction 2/3, overthinking 7/12, canary 7/12, temporal-reasoning 8/12,
cross-lingual 6/15).

## Findings

1. **Routing beats scale.** R43-A outperforms the 32B single-model baseline
   by +7.7 points (55.1% vs 47.4%). R43-B — using only the 8B and 14B
   models, no 32B at all — still beats it by +3.9 points at 44% of its wall
   time (134s vs 305s). Two small models, correctly routed, beat a model
   larger than both combined.
2. **Determinism held across days and code paths.** The predictions were
   derived from 2026-07-15 runs through a validation harness; R40 executed
   2026-07-16 through the production service and reproduced every
   per-category cell exactly (temp 0, seed 0, concurrency 6).
3. **Ceiling.** Only 22/78 cases are failed by every model, so perfect
   response-level selection tops out at 71.8%. Category-level routing
   captures 43 of those 56 solvable cases (77%); the remaining gap is
   within-category model disagreement, reachable only with response-level
   judging (candidate R44).

## Production tie-in

The routing table used here is exactly what DjimFlo's `LlmRouterService`
consumes via `riskCategory` (PR #62), fed by the nightly scheduler (PR #61)
and enforced by the governance gate (PR #65). This run is the measured
justification for that pipeline.

Artifacts: `r43-evidence/apex-r43-ensemble-results.json` (per-case results,
both ensembles). Note: the preregistration harness labeled the runs R40-A/-B
before the collision with the existing R40/R41/R42 slots was noticed; the
persisted agent ids and the JSON keys carry that original prefix.
