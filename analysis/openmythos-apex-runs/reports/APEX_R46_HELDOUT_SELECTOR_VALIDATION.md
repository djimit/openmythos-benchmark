# OpenMythos R46 Held-Out Selector Validation

Decision: `refuted` — the per-category content-discriminator choice does not
generalize; learning it hurts out of sample. R45's 57.7% selective hybrid was
overfit, as R45 itself warned.

## Question

R45 measured a 57.7% "selective hybrid" (apply the content discriminator only
in categories where it helped) but flagged it as overfit — winners were picked
on the same 78 cases they were scored on. R46 tests whether that per-category
choice survives a held-out split.

## Method

Pure re-analysis of R45 data (no new generation). Each anchored case carries
its outcome under BOTH policies: content discriminator (`disc`) and R43
category routing (`route`). Repeated random 50/50 splits, stratified by
category (2000 splits):

1. TRAIN half: per category, pick whichever policy has the higher pass rate
   (ties → route, conservative).
2. TEST half: apply that learned per-category choice; score on held-out cases.
3. Compare to always-route and always-disc scored on the same test halves.

## Results

| policy (held-out, mean of 2000 splits) | pass rate |
|---|---|
| learned per-category selector | **0.538** |
| always-route (R43) | 0.551 |
| always-disc (R45 uniform) | 0.551 |
| splits where learned > route | **0/2000 (0.0%)** |

Full-data per-category preference (the signal the learner chases):
injection `disc 10/12 > route 9/12`, temporal `disc 9/12 > route 8/12`,
canary `route 7/12 > disc 6/12`, calibration `route 2/4 > disc 1/4`, four
categories tied.

## Findings

1. **The selective hybrid does not generalize — it is refuted.** Learning
   which categories prefer the discriminator scores 53.8% out of sample,
   BELOW the 55.1% you get by ignoring the per-category signal entirely, and
   loses to always-route in every one of 2000 splits. With ~12 cases per
   category (6 train / 6 test), a ±1 advantage is within sampling noise and
   the learner reliably chases noise.
2. **The R45 injection/temporal signals are noise, not signal.** R45's
   "candidate router refinement for injection (+1/12)" is withdrawn: it does
   not survive a held-out test. No router change is warranted.
3. **This is the reconciliation discipline applied to our own research.** R45
   hinted at a win; R46 held-out validation killed it; no product code shipped
   on the hint. A benchmark of ~12 discriminating cases per category cannot
   support per-category policy learning — the corpus would need to grow
   before category-level selection is testable.

## Standing conclusion across R43–R46

- R43: category routing beats single-model scale — **55.1% vs 47.4%, real.**
- R44: heuristic judge cannot rank responses — chose model 0 for all 78.
- R45: answer-agnostic content discriminator ties routing (55.1%) uniformly.
- R46: the selective hybrid over-fits; **category routing (R43) remains the
  best validated method.** The path to the 71.8% ceiling is more
  discriminating cases and/or a calibrated judge, not per-category selectors
  learned on the current 78.

## Artifacts

`r46-evidence/apex-r46-crossval.py` (repeatable) reads `r45-evidence/
apex-r45-results.json`. No Ollama generation in this round.
