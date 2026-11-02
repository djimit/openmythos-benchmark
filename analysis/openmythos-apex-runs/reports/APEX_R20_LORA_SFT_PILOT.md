# OpenMythos Apex R20 LoRA SFT Pilot

## Decision

- decision: `r20_lora_sft_pilot`
- training status: `trained`
- SFT rows: `29`
- DPO rows: `47`
- holdout rows: `30`
- train/holdout case overlap: `0`
- schema valid: `yes`

## Runtime

| dependency | available |
|---|---:|
| torch | yes |
| transformers | yes |
| datasets | yes |
| peft | yes |
| trl | yes |
| accelerate | yes |

## Blockers

- none

## Next Command

Do not promote this adapter unless `promotion status` is `eligible_for_review`.

## Paired Holdout Evidence

- device: `mps`
- baseline oracle pass rate: `0.367`
- post-training oracle pass rate: `0.333`
- baseline over-refusal: `0`
- post-training over-refusal: `0`
- numerically stable: `yes`
- improved cases: `0`
- regressed cases: `1`
- promotion status: `rejected`
