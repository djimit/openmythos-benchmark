# OpenMythos Apex R20 LoRA SFT Pilot

## Decision

- decision: `r20_lora_sft_pilot`
- training status: `blocked`
- SFT rows: `29`
- DPO rows: `47`
- holdout rows: `30`
- train/holdout case overlap: `0`
- schema valid: `yes`

## Runtime

| dependency | available |
|---|---:|
| torch | no |
| transformers | no |
| datasets | no |
| peft | no |
| trl | no |
| accelerate | no |

## Blockers

- `missing-local-ml-dependencies`

## Next Command

`python3 scripts/r20_lora_sft_pilot.py --train`
