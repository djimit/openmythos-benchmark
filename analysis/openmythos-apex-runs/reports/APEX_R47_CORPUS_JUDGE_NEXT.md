# OpenMythos Apex R47 Corpus/Judge Next

Decision: `started` — R47 continues the evolutionary loop by improving data and
judge calibration, not by promoting the R20 adapter or adding per-category
selectors.

## Inputs

- R46 refuted learned per-category selection: held-out selector `0.538` vs plain
  routing `0.551`, wins `0/2000` splits.
- R20 LoRA SFT pilot trained successfully, but promotion is rejected: baseline
  holdout `0.367`, post-training `0.333`, improved cases `0`, regressed cases
  `1`.
- Current validated production signal remains R43 category routing: `55.1%`.

## R47 Work Queue

1. Add discriminating holdout cases before any new selector/router change.
2. Prioritize categories that tied or were noise in R45/R46: `injection`,
   `temporal-reasoning`, `canary`, `calibration`.
3. Add judge calibration cases where two candidate answers differ only on the
   oracle-relevant property, so the judge must select based on evidence rather
   than style/length/refusal.
4. Re-run routing and discriminator comparison only after case expansion.
5. Do not promote `outputs/openmythos-r20-lora` unless a future run reports
   `promotion_status: eligible_for_review`.

## Promotion Gate

- no train/holdout overlap
- holdout cases `>= 30`
- post-training pass rate `>=` baseline
- regressed cases `0`
- measurable delta `true`
- numerical stability `true`

## Fleet Learning Link

Telegram and cron outputs from the Djimit fleet should feed R47 only after they
are converted into oracle-checkable cases: prompt, expected invariant, source
evidence, and failure mode. Raw bot transcripts are not training data.
