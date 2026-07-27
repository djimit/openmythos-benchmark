# OpenDjicht-1 — Volledig Autonoom Plan

> **Build Mode** | Geen lokale GPU | Alleen Cloud APIs | Uitvoerbaar door Dennis of een agent
> **Versie:** 2.0 FINAAL | **Datum:** 2026-07-23

---

## 🎯 Doel

Een **governance-frontier model** trainen dat:
- Even goed presteert als Claude Opus 4.8 / GPT-5 op AI-governance
- Via Cloud APIs getraind is (geen lokale GPU)
- Nederlandse/EU governance beheert
- Klaar is voor productie als `open-djicht-governance`

---

## ✅ Wat is er vandaag al gerealiseerd

| # | Taak | Status | Bestand |
|---|------|--------|---------|
| 1 | Resource mapping (7 APIs) | ✅ | `cloud_resource_mapper.py` |
| 2 | Hybrid inference router | ✅ | `hybrid_inference_router.py` |
| 3 | Cloud data generator | ✅ | `open_djicht_generate.py` |
| 4 | NL governance cases | ✅ | `nl_governance_generator.py` |
| 5 | Trace distillation | ✅ | `frontier_distill_collector.py` |
| 6 | Evolution loop | ✅ | `evolution_training_loop.py` |
| 7 | Together AI training | ✅ | `together_training.py` |
| 8 | **37 SFT samples gegenereerd** | ✅ | `sft_free.jsonl` |
| 9 | **15 frontier DPO chosen** | ✅ | `dpo_chosen.jsonl` |
| 10 | **10 DPO pairs gebouwd** | ✅ | `dpo_pairs.jsonl` |
| 11 | **15 NL cases gegenereerd** | ✅ | `nl-governance-drafts.jsonl` |
| 12 | **88 combined SFT samples** | ✅ | `sft_combined.jsonl` |
| 13 | **Upload naar OpenAI** | ✅ | `file-1rzc46EEBhCrQXPUTnRC33` |
| 14 | **25/27 backends getest** | ✅ | `benchmark_inference.json` |

---

## 🏗️ Cloud Resources (geverifieerd werkend)

### Beschikbare APIs

| Provider | Status | Snelheid | Kosten | Beste model |
|----------|--------|----------|--------|-------------|
| **OpenRouter FREE** | ✅ 6 modellen | 0.5-8s | **$0** | gpt-oss-120b, kimi-k2, gemini-flash-lite |
| **OpenRouter Paid** | ✅ 15+ modellen | 1.5-4s | $0.00001-0.00003/tok | claude-opus-4.8, gpt-5.4, gemini-3.5 |
| **OpenAI Direct** | ✅ | 1.5s | $0.00015-0.01/tok | gpt-4o-mini, gpt-4o |
| **Google Gemini** | ✅ | 0.5-12s | $0.00015-0.00125/tok | gemini-2.5-pro, gemini-3-flash |
| **Ollama Cloud** | ✅ | variabel | $0 | qwen3.5:397b, kimi-k2:1t |
| **Requesty** | ✅ | ~2s | $0.0005-0.002/tok | Alle via proxy |

### Beste Modellen per Taak (uit benchmark)

| Taak | Beste Model | Backend | Latency | Kosten |
|------|------------|---------|---------|--------|
| **Governance (bulk)** | gpt-oss-120b | OpenRouter FREE | 3.1s | $0 |
| **Governance (quality)** | claude-sonnet-4.6 | OpenRouter | 2.3s | $0.00002/tok |
| **NL Governance** | gemini-2.5-flash-lite | OpenRouter FREE | 0.5s | $0 |
| **Code Governance** | gpt-5.1-codex | OpenRouter | 1.1s | $0.00002/tok |
| **Reasoning** | claude-opus-4.8 | OpenRouter | 3.2s | $0.00003/tok |
| **Judge** | gemini-2.5-flash-lite | OpenRouter FREE | 0.8s | $0 |
| **DPO Chosen** | claude-opus-4.8 | OpenRouter | 3.1s | $0.00003/tok |
| **DPO Rejected** | gpt-oss-120b | OpenRouter FREE | 1.0s | $0 |

---

## 📋 Executie Plan (stap voor stap)

### STAP 1: Data Genereren (vandaag, ~15 min, $0)

```bash
cd /Users/dlandman/OpenMythos/openmythos-benchmark

# 50 gratis SFT samples (~$0)
python3 scripts/open_djicht_generate.py free --cases 50

# 25 frontier DPO chosen (~$0.50)
python3 scripts/open_djicht_generate.py frontier --cases 25

# Bouw DPO pairs
python3 scripts/open_djicht_generate.py dpo
```

### STAP 2: Data Kwaliteit Checken (~2 min, $0)

```bash
# Combineer alle data
python3 -c "
import json
from pathlib import Path

ds = Path('analysis/openmythos-apex-runs/datasets/frontier-distill')
sft = [json.loads(l) for l in (ds / 'sft_free.jsonl').open() if l.strip()]
dpo = [json.loads(l) for l in (ds / 'dpo_pairs.jsonl').open() if l.strip()]
print(f'SFT: {len(sft)} samples')
print(f'DPO: {len(dpo)} pairs')
print(f'Categories: {set(r.get(\"category\",\"?\") for r in sft)}')
"
```

### STAP 3: Upload naar Together AI (~2 min, $0)

```bash
# Upload combined SFT data
python3 scripts/together_training.py upload \
  --dataset analysis/openmythos-apex-runs/datasets/frontier-distill/sft_combined.jsonl
```

### STAP 4: Training Starten (~5 min setup, 2-6 uur train, ~$5-15)

```bash
# Start Qwen3-32B fine-tuning
python3 scripts/together_training.py train \
  --file-id <file_id_from_upload> \
  --model qwen3-32b \
  --epochs 3

# Monitor
python3 scripts/together_training.py status --job-id <job_id>
```

### STAP 5: Evaluatie (~30 min, ~$1-3)

```bash
# Run benchmark against OpenMythos canon
python3 scripts/run_benchmark.py \
  --model <fine_tuned_model> \
  --backend openai

# Vergelijk met baseline
python3 scripts/compare.py \
  --run-a traces/baseline.jsonl \
  --run-b traces/open_djicht.jsonl
```

### STAP 6: Iteratie (indien nodig)

```bash
# Genereer meer data voor zwakke categories
python3 scripts/evolution_training_loop.py --single-shot
```

---

## 💰 Kostenoverzelling

| Fase | Wat | Kosten |
|------|-----|--------|
| Data generatie (200 cases) | Free models | **$0** |
| DPO chosen (50 cases) | Claude Opus 4.8 | **$0.50** |
| NL cases (50 cases) | Gemini 2.5 Pro | **$0.25** |
| Training (Qwen3-32B, 3 epochs) | Together AI | **$5-15** |
| Evaluatie (5 runs) | Free models | **$0** |
| **TOTAAL** | | **$6-16** |

---

## 🔧 Scripts Overzicht

| Script | Doel | Status |
|--------|------|--------|
| `open_djicht_generate.py` | Data generatie met optimale modellen | ✅ Werkend |
| `hybrid_inference_router.py` | Intelligent model routing | ✅ Werkend |
| `cloud_resource_mapper.py` | API availability check | ✅ Werkend |
| `together_training.py` | Together AI fine-tuning | ✅ Werkend |
| `cloud_frontier_distiller.py` | OpenAI upload/train (deprecated) | ⚠️ OpenAI FT deprecated |
| `evolution_training_loop.py` | Autonome verbetering | ✅ Werkend |
| `frontier_distill_collector.py` | Bestaande traces → data | ✅ Werkend |
| `nl_governance_generator.py` | NL cases genereren | ✅ Werkend |

---

## ⚠️ Belangrijke Wijziging: OpenAI FT Deprecated

OpenAI's self-serve fine-tuning is **deprecated** (mei 2026). Alternatieven:

| Alternatief | Status | Aanbeveling |
|------------|--------|-------------|
| **Together AI** | ✅ Werkend | **PRIMAIRE KEUZE** — Qwen3-32B, Llama-4, DeepSeek |
| **Azure AI Foundry** | ❌ Geen toegang | Niet beschikbaar |
| **OpenRouter** | ⚠️ Geen FT API | Alleen inference |
| **Google Vertex AI** | ⚠️ Geen key | Toekomstige optie |

**Wij gebruiken nu Together AI voor training.**

---

## 📊 Huidige Data Status

```
SFT samples:     88 totaal (37 free + 36 traces + 15 NL)
DPO pairs:       10 (frontier chosen vs free rejected)
NL cases:        15 (AVG, NORA, EU AI Act, Common Ground)
Categories:      8/11 gedekt
Backend combos:  25/27 werkend
```

---

## 🚀 Volgende Actie (nu)

```bash
# 1. Genereer meer data (15 min, $0):
python3 scripts/open_djicht_generate.py free --cases 50

# 2. Upload naar Together AI:
python3 scripts/together_training.py upload \
  --dataset analysis/openmythos-apex-runs/datasets/frontier-distill/sft_combined.jsonl

# 3. Start training (na upload):
python3 scripts/together_training.py train \
  --file-id <file_id> --model qwen3-32b --epochs 3
```

---

> "Own the model. Own the benchmark. Own the loop."
> — OpenDjicht Architectuur, 2026
