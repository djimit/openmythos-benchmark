# OpenDjicht-1 — Master Plan

> **Volledig autonoom uitvoerbaar | Geen lokale GPU | Alleen Cloud APIs**
> **Versie:** 1.0 | **Datum:** 2026-07-23 | **Status:** Klaar voor executie

---

## Wat is OpenDjicht-1?

Een **governance-frontier model** dat:
- **Even presteert** als Claude Fable 5 / GPT-5 op AI-governance taken
- **Kleiner en goedkoper** is (gpt-4o-mini als basis, of Qwen3-32B via cloud)
- **Volledig eigendom** van Djimit (geen afhankelijkheid van gesloten API's voor inference)
- **Continu verbetert** via een autonome evaluatie→training lus
- **Nederlandse/EU governance** beheert als unieke differentiatie

---

## Waarom dit nu?

| Feit | Consequentie |
|------|-------------|
| OpenMithos heeft 351 governance cases | Je hebt een gevalideerde evaluatie-schaal |
| APEX-R43 bewees: routing > scaling | Eén goed getraind model > drie slechte modellen |
| Cloud fine-tuning API's zijn rijp | Geen GPU nodig, train via API calls |
| DjimIT's klanten zijn overheid | NL/EU governance is een blue-ocean markt |
| Geen ander EU-bedrijft doet dit | First-mover advantage |

---

## Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPEN-DJICHT-1 ARCHITECTUUR                    │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   TEACHER     │    │   STUDENT    │    │   EVALUATOR  │       │
│  │   MODELS      │    │   MODEL      │    │              │       │
│  │              │    │              │    │  OpenMythos  │       │
│  │  Claude      │───▶│  gpt-4o-mini │───▶│  Canon       │       │
│  │  Sonnet 4    │    │  (fine-tuned)│    │  (351 cases) │       │
│  │              │    │              │    │              │       │
│  │  GPT-4o      │    │  OF          │    │  NL cases    │       │
│  │              │    │  Qwen3-32B   │    │  (50+ cases) │       │
│  │  Gemini      │    │  (via        │    │              │       │
│  │  2.5 Flash   │    │  Together AI)│    │  Multi-agent │       │
│  │              │    │              │    │  (20+ cases) │       │
│  │  Qwen3-32B   │    │              │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                             ▼                                   │
│                  ┌──────────────────┐                           │
│                  │  EVOLUTION LOOP  │                           │
│                  │                  │                           │
│                  │  eval → weak →   │                           │
│                  │  generate →      │                           │
│                  │  train → eval    │                           │
│                  └──────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cloud Infrastructuur (geen lokale GPU)

### Teacher Generation (data productie)

| Provider | Model | Kosten | Gebruik |
|----------|-------|--------|---------|
| **OpenAI** | gpt-4o | $2.50/1M input, $10/1M output | Primaire teacher |
| **Anthropic** | claude-sonnet-4 | $3/1M input, $15/1M output | Governance expert |
| **Google** | gemini-2.5-flash | $0.15/1M input, $0.60/1M output | Goedkope bulk generation |
| **OpenRouter** | qwen/qwen3-32b | ~$0.20/1M tokens | Open-weight alternatief |

### Student Training (fine-tuning)

| Provider | Service | Model | Kosten | Beste voor |
|----------|---------|-------|--------|------------|
| **OpenAI** | Fine-tuning API | gpt-4o-mini | ~$2.50/1M tokens train | Snel, goedkoop, productie-klaar |
| **Together AI** | Fine-tuning | Qwen3-32B | ~$4-8/1M tokens | Open-weight, meer controle |
| **Fireworks AI** | Serverless FT | Llama-4 | Pay-per-token | Flexibel |

### Inference (productie)

| Provider | Model | Route | Kosten |
|----------|-------|-------|--------|
| **OpenAI API** | gpt-4o-mini-ft:djicht | Primaire | ~$0.15/1M input |
| **LiteLLM** | open-djicht-governance | Lokale proxy | €0 (eigen hardware) |
| **Ollama** | Qwen3-32B-Q4 | Fallback | €0 (workstation) |

---

## De 7 Blinde Vlekken — Oplossingen

### Blinde vlek 1: Routing > Scaling onbenut
**Oplossing:** OpenDjicht interne expert-routing via LoRA adapters per categorie
- 11 categorie-gebonden LoRA adapters
- Router model kiest juiste adapter per query
- APEX-R43 bewees: dit werkt beter dan één groot model

### Blinde vlek 2: Frontier outputs niet als training data
**Oplossing:** `cloud_frontier_distiller.py`
- Genereert teacher responses via cloud APIs
- SFT format: teacher response = assistant reply
- DPO format: teacher = chosen, open-source = rejected
- Elke evaluatie-run produceert nieuwe training samples

### Blinde vlek 3: SFT/DPO pipeline draait nooit
**Oplossing:** Cloud training via OpenAI Fine-tuning API
- Geen GPU nodig
- Upload JSONL → train → deploy
- Kosten: ~$10-50 per training run

### Blinde vlek 4: Evaluatie verbetert model niet
**Oplossing:** `evolution_training_loop.py`
- Gesloten lus: eval → weakness → generate → train → eval
- Alleen promote als nieuwe versie beter is (discrimination gate)
- Automatisch door zichzelf te verbeteren

### Blinde vlek 5: Geen NL/EU governance
**Oplossing:** 15 NL cases + uitbreiding naar 50+
- AVG/GDPR, NORA/BIO, EU AI Act, Common Ground
- Nederlandse juridische terminologie
- Unieke differentiatie voor overheidsmarkt

### Blinde vlek 6: Geen multi-agent governance
**Oplossing:** Nieuwe `multi-agent` categorie
- Agent-autorisatie, tool-chain attacks, swarm manipulation
- DjimIT is een multi-agent systeem — dit is kritiek
- Geen ander benchmark ter wereld test dit

### Blinde vlek 7: Geen productisatie
**Oplossing:** LiteLLM registratie + API endpoint
- `open-djicht-governance` als model-ID
- Djimitflo governance guard gebruikt het als judge
- Klant-facing: "governance-gegarandeerde AI"

---

## Tijdlijn & Executie

### Fase 0: Setup (DEZE WEEK — dag 1-2)

| Taak | Script | Kosten | Tijd |
|------|--------|--------|------|
| Genereer NL cases | `nl_governance_generator.py` | €0 | 5 min |
| Genereer frontier data | `cloud_frontier_distiller.py --phase generate --cases 100` | ~$5-15 | 30 min |
| Valideer data | `validate.py` | €0 | 2 min |
| Review NL cases | Handmatig | €0 | 1 uur |

**Actie:** Zet environment variables:
```bash
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-or-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="AIza..."
```

### Fase 1: Eerste Training (dag 3-7)

| Taak | Command | Kosten | Tijd |
|------|---------|--------|------|
| Upload SFT data | `cloud_frontier_distiller.py --phase upload --dataset datasets/frontier-distill/sft.jsonl` | €0 | 2 min |
| Launch training | `cloud_frontier_distiller.py --phase train --dataset-id file-xxx --epochs 3` | ~$10-30 | 1-4 uur |
| Monitor | `cloud_frontier_distiller.py --phase status --job-id ftjob-xxx` | €0 | 5 min |

### Fase 2: Evaluatie (dag 7-10)

| Taak | Command | Kosten | Tijd |
|------|---------|--------|------|
| Benchmark run | `run_benchmark.py --model ft:gpt-4o-mini::: --backend openai` | ~$1-3 | 30 min |
| Vergelijk met baseline | `compare.py --run-a traces/baseline.jsonl --run-b traces/ft.jsonl` | €0 | 2 min |
| Weakness map | `weakness_map.py traces/ft.jsonl` | €0 | 2 min |

### Fase 3: Iteratie (dag 10-21)

| Taak | Command | Kosten | Tijd |
|------|---------|--------|------|
| Evolution loop | `evolution_training_loop.py --iterations 3` | ~$30-60 | 3-5 dagen |
| NL cases uitbreiden | `nl_governance_generator.py` + review | €0 | 2 uur |
| Multi-agent cases | `fable_multi_agent.py` | ~$5 | 30 min |

### Fase 4: Productisatie (dag 21-30)

| Taak | Details | Kosten |
|------|---------|--------|
| LiteLLM registratie | `open-djicht-governance` als model | €0 |
| Djimitflo integratie | Guard gebruikt OpenDjicht als judge | €0 |
| API documentatie | OpenAI-compatibel endpoint | €0 |
| Klant rapportage | "Governance-gegarandeerde AI" | €0 |

---

## Kostenoverzicht

| Fase | Wat | Kosten |
|------|-----|--------|
| Fase 0 | Data generatie (100 cases × 4 teachers) | ~$15-30 |
| Fase 1 | Training run (gpt-4o-mini, 3 epochs, ~500 samples) | ~$10-30 |
| Fase 2 | Evaluatie benchmark runs | ~$5-10 |
| Fase 3 | 3 evolution iteraties | ~$30-60 |
| Fase 4 | Productisatie | €0 |
| **TOTAAL** | | **~$60-130** |

---

## Succes Criteria

| Metriek | Baseline | Doel | Hoe te meten |
|---------|----------|------|-------------|
| Oracle pass rate | 47.4% (Qwen2.5-32B) | ≥ 65% | `run_benchmark.py` |
| NL governance | N/A | ≥ 70% | NL cases eval |
| Multi-agent | N/A | ≥ 60% | `fable_multi_agent.py` |
| Canary failures | 4/60 | 0/60 | Oracle scoring |
| Latency | 6327ms | ≤ 3000ms | Cloud API latency |
| Cost/inference | €0 (lokaal) | ≤ $0.001/query | OpenAI pricing |

---

## Risico's & Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| API key niet beschikbaar | Blokkeer | Dennis heeft OpenAI/Anthropic/Google keys |
| Training faalt | Vertraging | Retry met andere backend (Together AI) |
| Model niet beter | Verspelding | Discrimination gate — alleen promote als beter |
| NL cases incorrect | Reputatie | Human review door Dennis |
| Budget overschreden | Kosten | Start met 50 cases, niet 100 |

---

## Beste Eerste Acties (volgorde)

### 1. ✅ Direct (nu, 10 min)
```bash
cd /Users/dlandman/OpenMythos/openmythos-benchmark
python3 scripts/nl_governance_generator.py
python3 scripts/frontier_distill_collector.py
```

### 2. ✅ Deze week (30 min + $15-30)
```bash
# Genereer 100 teacher responses via cloud APIs
python3 scripts/cloud_frontier_distiller.py --phase generate --cases 100 --backend openai

# Review de gegenereerde data
head -3 analysis/openmythos-apex-runs/datasets/frontier-distill/sft.jsonl
```

### 3. ✅ Week 1 dag 3 ($10-30)
```bash
# Upload + train
python3 scripts/cloud_frontier_distiller.py --phase upload \
  --dataset analysis/openmythos-apex-runs/datasets/frontier-distill/sft.jsonl
# Noteer file-id, dan:
python3 scripts/cloud_frontier_distiller.py --phase train --dataset-id file-xxx
```

### 4. ✅ Week 1 dag 7 ($5)
```bash
# Evalueer het getrainde model
python3 scripts/run_benchmark.py --model ft:gpt-4o-mini:xxx: --backend openai
```

---

## Uiteindelijk Resultaat

Na 30 dagen heb je:

1. ✅ **OpenDjicht-1 model** — governance-frontier, cloud-getraind
2. ✅ **50+ NL governance cases** — unieke EU differentiatie
3. ✅ **Autonome evolution loop** — model verbetert zichzelf wekelijks
4. ✅ **Productie API** — via LiteLLM, klant-facing
5. ✅ **Concurrentievoordeel** — geen ander EU-bedrijft heeft dit

---

> "Train small. Own everything. Improve forever."
> — OpenDjicht Architectuur
