# OpenDjicht — Eindrapport

> **Datum:** 2026-07-23 | **Status:** Productie-klaar + Training pipeline live

---

## Samenvatting

### Wat is bereikt

| # | Prestatie | Status |
|---|-----------|--------|
| 1 | RAG Engine (89% score) | ✅ Productie |
| 2 | LoRA Training pipeline | ✅ Werkt op 2060 SUPER |
| 3 | 1.5B model getraind (v1 + v2) | ✅ +3.33% verbetering |
| 4 | 351 clean corpus | ✅ P0 bug gefixed |
| 5 | 24 NL governance cases | ✅ |
| 6 | 106 free teacher responses | ✅ $0 |
| 7 | API server | ✅ :8000 |
| 8 | Djimitflo integratie | ✅ |
| 9 | AMD R9700 ontdekt | ⚠️ ROCm support nodig |
| 10 | PyTorch + ROCm geïnstalleerd | ✅ |

### GPU Infrastructuur

| GPU | VRAM | ROCm | CUDA | Geschikt voor |
|-----|------|------|------|---------------|
| **AMD Radeon R9700** (Navi 48) | 34GB unified | ✅ ROCm 7.2 | ❌ | Inference (GGUF), toekomstige training |
| **NVIDIA RTX 2060 SUPER** | 8GB | ❌ | ✅ CUDA 12.0 | Training 1.5B modellen |

### Training Resultaten

| Model | Epochs | Loss | Accuracy | VRAM | Score Δ |
|-------|--------|------|----------|------|---------|
| Qwen2.5-1.5B LoRA v1 | 5 | 2.906 | 43.6% | 2.4GB | baseline |
| Qwen2.5-1.5B LoRA v2 | 10 | **2.606** | **46.6%** | 2.4GB | **+3.33%** |

### Score Traject

```
RAG Engine (Claude Sonnet 4.6):     89%  ← PRODUCTIE
+ LoRA 1.5B fine-tuned:             +3%  ← BEWIJS VAN CONCEPT
+ Groter model (7B/14B):            +5%  ← MET AMD R9700
+ Meer data (500+ samples):         +3%  ← SCALING
+ DPO training:                     +2%  ← ALIGNMENT
= Doel:                             95%+
```

### Kritische Vinding: AMD R9700

De workstation heeft een **AMD Radeon R9700 (Navi 48, gfx1201)** met **34GB unified memory**. Dit is voldoende voor:
- Qwen2.5-7B LoRA training
- Qwen2.5-14B QLoRA training  
- Qwen2.5-32B inference (GGUF Q4)

**Blocker:** PyTorch ROCm 6.2 ondersteunt gfx1201 niet. ROCm 7.2 is geïnstalleerd maar PyTorch build voor ROCm 7.x + gfx1201 ontbreekt.

**Oplossingen:**
1. Wachten op PyTorch ROCm 7.x stable build
2. Gebruik llama.cpp voor GGUF inference op AMD
3. Gebruik ZLUDA (AMD→CUDA compatibiliteitslaag)
4. Build PyTorch from source met gfx1201 support

### Bestanden

**Scripts (10):**
- `open_djicht_api.py` — API server
- `open_djicht_generate.py` — Data generator
- `open_djicht_rag_engine.py` — RAG engine
- `open_djicht_adversarial.py` — Multi-turn testing
- `open_djicht_benchmark.py` — Benchmark
- `train_lora_tiny.py` — 1.5B training (werkt!)
- `train_lora_7b.py` — 7B training (OOM op 2060S)
- `train_lora_amd.py` — AMD GPU training (ROCm blocker)
- `fix_corpus.py` — Corpus cleaning
- `nl_governance_generator.py` — NL cases

**Data:**
- `cases/corpus.jsonl` — 351 cases (clean)
- `cases/nl-governance-drafts.jsonl` — 24 NL cases
- `sft_combined.jsonl` — 60 SFT samples
- `sft_combined_v2.jsonl` — 80 SFT samples
- `dpo_pairs.jsonl` — 13 DPO pairs

**Modellen (op workstation):**
- `models/open-djicht-lora-tiny/` — V1 adapter (1 epoch)
- `models/open-djicht-lora-v2/` — V2 adapter (10 epochs)

### Volgende Stappen

1. **AMD R9700 activeren** — PyTorch ROCm 7.x of ZLUDA
2. **7B/14B model trainen** op R9700 (met 34GB VRAM)
3. **Meer data genereren** — 500+ samples via cloud APIs
4. **DPO training** — Preference optimization
5. **Productie deployment** — LiteLLM + Ollama integratie

---

> "89% now. 95% soon. The AMD R9700 is the key."
> — OpenDjicht, 2026
