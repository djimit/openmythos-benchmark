# OpenMythos R45 Answer-Agnostic Content Discriminator

Decision: `tie_with_mechanism` — a uniform answer-agnostic discriminator
matches category routing (55.1%); the value is category-specific, and the
selective hybrid that beats it is currently overfit and unproven.

## Question

R44 showed the JudgeService cannot rank same-case responses. Can a small set
of ANSWER-AGNOSTIC content features — computed from prompt+response without
the per-case oracle rule — select per-case better than R43's whole-category
routing (55.1%)?

## Method

- Harness: DjimFlo `OpenMythosEvalService.runEval` per model (production
  path), 78 oracle-anchored cases, temperature 0 / seed 0, isolated DB.
- Selection is blind to the oracle; the oracle is read only to score the
  choice afterward.
- Per-category selectors (honesty boundary: category is known to any router;
  the expected answer is not):
  - overthinking / temporal-reasoning / calibration → shortest response
  - canary / injection → prefer a refusing response (generic refusal regex)
  - else → R43 category-routing choice

## Results

| method | oracle pass | rate |
|---|---|---|
| llama3.1:8b / qwen14b / qwen32b single | 33 / 34 / 37 | 42–47% |
| R43 category routing | 43/78 | 55.1% |
| **R45 uniform discriminator** | **43/78** | **55.1%** (tie) |
| R45 selective hybrid (**overfit**, see caveat) | 45/78 | 57.7% |
| union ceiling | 56/78 | 71.8% |

Per-category delta (R45 − R43): injection **+1** (refusal picker), temporal
**+1** (shortest picker), canary **−1**, calibration **−1**, others 0.

## Findings

1. **Answer-agnostic features have real but category-specific value.** They
   help where the feature aligns with the oracle (injection rewards refusal;
   temporal/scalar oracles reward terse answers) and hurt where it misaligns
   (canary refusal picks false-positive refusals; "shortest" is wrong for some
   calibration cases). Applied uniformly the effects cancel — a clean tie.
2. **The 57.7% hybrid is overfit and must not be quoted as a win.** It was
   built by keeping the discriminator only in the two categories where it
   helped ON THESE 78 CASES — winner selection on the evaluation set itself.
   It is an upper-bound hypothesis, not a measurement. A defensible number
   needs a train/test split (choose per-category selectors on one half,
   report on the held-out half) — candidate R46.
3. **Contrast with R44.** The heuristic judge had zero discrimination (chose
   model 0 for all 78). Hand-built content features do discriminate — just
   not net-positively when applied blind across all categories.
4. **Determinism, sixth reproduction.** Per-model baselines 33/34/37 again;
   union ceiling 56 again.

## Production implication

Do NOT wire a global content discriminator into the router on this evidence —
it's a wash. The validated, shippable signal is narrower: for `injection`
tasks, preferring a refusing local response is worth +1/12 over routing
alone, and it's answer-agnostic. That was a candidate refinement to the
governance router's `injection` path, pending R46 held-out confirmation.

**UPDATE (R46): REFUTED.** Held-out cross-validation (2000 splits) shows the
per-category selector scores 53.8% out of sample vs 55.1% for plain routing,
winning 0/2000 splits. The injection +1 is sampling noise. No router change.

## Artifacts

`r45-evidence/apex-r45-results.json` — per-case chosen model, chosen oracle
outcome, and the R43-routing counterfactual; runs persisted under `R45:<model>`.
