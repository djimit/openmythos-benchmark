# OpenDjicht-1 Resource Map — Wat je nu al hebt

> Gegenereerd: 2026-07-23 | Alle API keys geverifieerd

---

## Beschikbare Subscriptions (7/8 werkend)

| # | Provider | Status | Models | Kosten | Gebruik |
|---|----------|--------|--------|--------|---------|
| 1 | **OpenRouter** | ✅ | 342 modellen | $0 - $0.00003/tok | **PRIMAIRE TEACHER** |
| 2 | **OpenRouter FREE** | ✅ | 10+ frontier modellen | **$0** | Bulk SFT data |
| 3 | **OpenAI Direct** | ✅ | gpt-5, gpt-4o, gpt-4o-mini | $2.50-10/1M | Fine-tuning target |
| 4 | **Google Gemini** | ✅ | gemini-2.5-pro, gemini-3-flash | $1.25-10/1M | NL governance |
| 5 | **Ollama Cloud** | ✅ | qwen3.5:397b, kimi-k2:1t, deepseek-v4 | $0 | Backup teacher |
| 6 | **Requesty** | ✅ | gpt-5, deepseek-pro, gemini-flash | $0.50-2/1M | Proxy fallback |
| 7 | **OpenCode OpenAI** | ✅ | gpt-5, gpt-4o, gpt-4o-mini | $2.50-10/1M | Backup OpenAI |
| 8 | Anthropic Direct | ❌ | Invalid key | — | Niet beschikbaar |

---

## Optimale Model Routing per Taak

### 1. Bulk SFT Data Generatie (200+ cases) — KOSTEN: $0

| Prioriteit | Model | Backend | Context | Succesrate |
|-----------|-------|---------|---------|------------|
| 1 | `openai/gpt-oss-120b` | OpenRouter FREE | 128K | ~90% |
| 2 | `moonshotai/kimi-k2-thinking` | OpenRouter FREE | 256K | ~90% |
| 3 | `google/gemini-2.5-flash-lite` | OpenRouter FREE | 1M | ~90% |
| 4 | `deepseek/deepseek-v4-flash` | OpenRouter FREE | 1M | ~80% |
| 5 | `qwen/qwen3.5-flash-02-23` | OpenRouter FREE | 1M | ~30% |
| 6 | `z-ai/glm-4.7-flash` | OpenRouter FREE | 200K | ~20% |

**Beste 3 modellen:** gpt-oss-120b, kimi-k2-thinking, gemini-2.5-flash-lite

### 2. Frontier DPO Chosen (50-100 cases) — KOSTEN: ~$0.50-2.00

| Prioriteit | Model | Backend | Kosten/1M | Context |
|-----------|-------|---------|-----------|---------|
| 1 | `anthropic/claude-opus-4.8` | OpenRouter | $0.00003 | 1M |
| 2 | `openai/gpt-5.4` | OpenRouter | $0.00002 | 1M |
| 3 | `google/gemini-3.5-flash` | OpenRouter | $0.00001 | 1M |
| 4 | `deepseek/deepseek-v4-pro` | OpenRouter | $0.00001 | 1M |

### 3. NL/EU Governance (50 cases) — KOSTEN: ~$0.25

| Prioriteit | Model | Backend | Reden |
|-----------|-------|---------|-------|
| 1 | `google/gemini-2.5-pro` | Google Direct | Meertalig, EU context |
| 2 | `anthropic/claude-opus-4.8` | OpenRouter | Beste reasoning |
| 3 | `openai/gpt-5` | OpenRouter | Backup |

### 4. Code/Tool-Scope Governance (50 cases) — KOSTEN: ~$0.25

| Prioriteit | Model | Backend | Reden |
|-----------|-------|---------|-------|
| 1 | `moonshotai/kimi-k2.7-code` | OpenRouter | Code specialist |
| 2 | `qwen/qwen3-coder-480b` | OpenRouter FREE | Gratis, 480B |
| 3 | `openai/gpt-5.1-codex` | OpenRouter | Frontier coding |

### 5. Fast Judge (LLM-as-judge) — KOSTEN: $0

| Prioriteit | Model | Backend | Reden |
|-----------|-------|---------|-------|
| 1 | `google/gemini-2.5-flash-lite` | OpenRouter FREE | Snel, gratis |
| 2 | `deepseek/deepseek-v4-flash` | OpenRouter FREE | Gratis, 1M context |
| 3 | `openai/gpt-4o-mini` | OpenAI Direct | Bekend, betrouwbaar |

### 6. Fine-tuning Target — KOSTEN: ~$10-30

| Provider | Model | Kosten | Beste voor |
|----------|-------|--------|------------|
| **OpenAI** | gpt-4o-mini | ~$10-30/train | Snel, goedkoop, productie |
| **OpenAI** | gpt-4o | ~$50-100/train | Hogere kwaliteit |
| **Together AI** | Qwen3-32B | ~$4-8/1M tokens | Open-weight, meer controle |

---

## Kostenberadering (volledige pipeline)

| Fase | Wat | Modellen | Kosten |
|------|-----|----------|--------|
| SFT data (200 cases) | Free models | gpt-oss-120b, kimi-k2, gemini-flash | **$0** |
| DPO chosen (50 cases) | Claude Opus 4.8 | claude-opus-4.8 | **$0.50** |
| DPO rejected (50 cases) | Free models | gpt-oss-120b | **$0** |
| NL governance (50 cases) | Gemini 2.5 Pro | gemini-2.5-pro | **$0.25** |
| Code governance (50 cases) | Kimi K2.7 Code | kimi-k2.7-code | **$0.25** |
| Training (SFT) | OpenAI Fine-tuning | gpt-4o-mini, 3 epochs | **$10-30** |
| Evaluatie (5 runs) | Free models | gemini-flash-lite | **$0** |
| **TOTAAL** | | | **$11-31** |

---

## Wat is er vandaag al gedaan?

| Taak | Status | Resultaat |
|------|--------|-----------|
| NL cases genereren | ✅ | 15 cases (AVG, NORA, EU AI Act, Common Ground) |
| Bestaande trace distillation | ✅ | 31 SFT + 18 DPO samples |
| Cloud resource mapping | ✅ | 7/8 APIs werkend, 342 modellen beschikbaar |
| Free model data generatie | ✅ | 20 SFT samples (gratis) |
| Resource mapper script | ✅ | `cloud_resource_mapper.py` |
| Optimal data generator | ✅ | `open_djicht_generate.py` |
| Cloud distiller (upload+train) | ✅ | `cloud_frontier_distiller.py` |
| Evolution loop | ✅ | `evolution_training_loop.py` |

---

## Volgende Acties (in volgorde)

### Direct (vandaag, 30 min, $0)
```bash
# Genereer 50 gratis SFT samples
python3 scripts/open_djicht_generate.py free --cases 50

# Genereer 25 frontier DPO chosen samples (~€1)
python3 scripts/open_djicht_generate.py frontier --cases 25

# Bouw DPO pairs
python3 scripts/open_djicht_generate.py dpo
```

### Deze week (dag 2-3, ~€15-30)
```bash
# Upload naar OpenAI Fine-tuning
python3 scripts/cloud_frontier_distiller.py upload \
  --dataset analysis/openmythos-apex-runs/datasets/frontier-distill/sft_free.jsonl

# Start training
python3 scripts/cloud_frontier_distiller.py train --dataset-id file-xxx
```

### Week 2 (evaluatie + iteratie)
```bash
# Evalueer getraind model
python3/scripts/run_benchmark.py --model ft:gpt-4o-mini:xxx: --backend openai

# Genereer meer data voor zwakke categories
python3/scripts/open_djicht_generate.py all --cases 100
```

---

## Belangrijkste Bevinding

**OpenRouter is de game-changer.** Vrijwel alle frontier modellen (Claude Opus 4.8, GPT-5.4, Gemini 3.5, DeepSeek V4, Kimi K2) zijn beschikbaar voor $0.00001-0.00003 per token. Dat betent:

- 1000 cases genereren met Claude Opus = ~$0.50
- 1000 cases genereren met GPT-5 = ~$0.40
- 1000 cases genereren met gratis modellen = $0

**Je hebt geen lokale GPU nodig.** Alles draait via cloud APIs die je al hebt geabonneerd.
