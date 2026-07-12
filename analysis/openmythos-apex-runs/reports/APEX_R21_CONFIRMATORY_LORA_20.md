# OpenMythos Apex R20 LoRA SFT Pilot

## Decision

- decision: `r20_lora_sft_pilot`
- training status: `trained`
- SFT rows: `28`
- DPO rows: `50`
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

`python3 scripts/r20_lora_sft_pilot.py --train`

## Paired Holdout Evidence

- device: `cuda`
- baseline oracle pass rate: `0.433`
- post-training oracle pass rate: `0.467`
- baseline over-refusal: `2`
- post-training over-refusal: `1`
- numerically stable: `yes`
- improved cases: `1`
- regressed cases: `0`
- promotion status: `eligible_for_review`
