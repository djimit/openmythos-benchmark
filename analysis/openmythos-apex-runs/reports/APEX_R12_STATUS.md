# APEX R12 — Status & Plan

## Doel

Fine-tune lokaal model op governance SFT data om te meten of domein-specifieke training de governance-scores verbetert.

## Status: ⏳ Geblokkeerd door hardware

### Poging 1: QLoRA 7B op MacBook (MPS)
- **Probleem:** 25GB RAM te weinig voor 7B model loading
- **Result:** Process hangt bij weight loading (OOM risk)

### Poging 2: LoRA 3B op MacBook (MPS)
- **Probleem:** Ook geblokkeert — PyTorch MPS + memory pressure tijdens loading
- **Result:** CPU op 198% maar geen vooruitgang na 10+ minuten

### Root Cause
- Qwen2.5-Coder-3B in fp16 = ~6GB model weights
- LoRA init + optimizer state = +2-3GB overhead
- macOS memory management onder druk met 8GB vrij

## Alternatieven voor R12

### Optie A: Cloud Fine-Tuning (aanbevolen)
- **Platform:** Replicate, Together AI, of Fireworks
- **Model:** Qwen2.5-Coder-7B-Instruct
- **Data:** 112 SFT entries (klaar in `r12-openai-ft.jsonl`)
- **Kost:** ~$5-15
- **Tijd:** ~30-60 min

### Optie B: Upgrade Hardware
- **AMD 9700 AI Turbo** (zoals eerder besproken): 128GB unified RAM
- Kan 70B+ modellen draaien
- Kost: ~$800-1200

### Optie C: Unsloth Optimized Training
- Unsloth biedt 2x memory reduction voor LoRA training
- Kan 7B draaien op 16GB RAM
- Install: `pip install unsloth`

### Optie D: Wacht op R13
- Gebruik R10/R11 resultaten als baseline
- Plan training voor Q1 2027 met cloud credits of hardware upgrade

## Wat er WEL klaar is

| Asset | Locatie | Status |
|-------|---------|--------|
| SFT data (112 entries) | `datasets/apex-r10-sft-gemma4.jsonl` | ✅ |
| Holdout (23 entries) | `datasets/apex-r10-holdout-gemma4.jsonl` | ✅ |
| OpenAI FT format | `datasets/r12-openai-ft.jsonl` | ✅ |
| QLoRA script (7B) | `scripts/train_qlora_r12.py` | ✅ |
| MPS script (3B) | `scripts/train_r12_mps.py` | ✅ |
| R12 Goal | `goals/openmythos-apex-r12/GOAL.md` | ✅ |

## Aanbeveling

Gebruik **Optie A (Cloud)** voor R12 als je snel resultaten wilt. Gebruik **Optie C (Unsloth)** als je lokaal wilt blijven zonder hardware upgrade.

Voor nu: R12 is "data-ready, execution-blocked". De SFT data is gevalideerd en klaar voor training zodra resources beschikbaar zijn.
