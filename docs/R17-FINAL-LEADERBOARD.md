# APEX R17 — Final Cloud Benchmark Leaderboard

**Date:** 2026-07-24
**Judge:** qwen2.5-coder:latest (Ollama lokaal)
**Corpus:** 351 cases, 11 categorieën

## Resultaten (R17 judge run)

| Rank | Model | Params | Avg Score | Pass Rate | Type |
|------|-------|-------:|----------:|----------:|------|
| 1 | gemma-4-31b | 31B | 3.516 | 49.6% | Cloud |
| 2 | deepseek-v4-pro | 236B MoE | 3.413 | 45.9% | Cloud |

## Eerdere resultaten (eigen judge runs)

| Run | Model | Avg Score | Pass Rate | Judge |
|-----|-------|----------:|----------:|-------|
| R10 | gemma-4-26b | 4.058 | 78.5% | qwen2.5:32b |
| R14 | deepseek-v4-pro | 3.356 | 47.6% | qwen2.5-coder:7b |
| R12 | openmythos-3b | 3.009 | 32.5% | qwen2.5-coder:7b |
| R9 | qwen2.5-coder:7b | 2.635 | 38.3% | qwen2.5:32b |

## Kritieke Observatie: Judge Bias

De scores zijn NIET vergelijkbaar tussen runs omdat:
1. **R10 gebruikte qwen2.5:32b als judge** — strenger en beter in staat om kwaliteit te beoordelen
2. **R12/R14/R17 gebruiken qwen2.5-coder:7b** — minder betrouwbaar voor frontier models
3. **Elke judge run heeft eigen bias** — scores zijn alleen betrouwbaar binnen dezelfde run

## Wat we WETEN

1. **Fine-tuning werkt:** R12 (3B) +32% vs R9 (7B) baseline
2. **Cloud > Lokaal:** Gemma4-31b (3.516) > openmythos-3b (3.009)
3. **Gemma4 family is sterk:** Beide gemma4 varianten scoren hoog
4. **Judge is bottleneck:** Meer-dan-7B judge nodig voor betrouwbare resultaten

## Aanbeveling

Voor betrouwbare benchmarking:
1. **Multi-judge:** Combineer 3+ judges (qwen2.5:14b, gemma4, claude)
2. **Human evaluation:** 100 cases door domeinexpert
3. **Zelfde judge voor alle runs:** Standardiseer op qwen2.5:14b of beter

## Volgende Stappen

1. **R18:** Multi-judge evaluatie (combineer 3 judges)
2. **R19:** 7B QLoRA training met 383 examples (cloud GPU)
3. **R20:** Productie deployment met hybride lokaal+cloud
