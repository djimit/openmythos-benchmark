# OpenMythos Strategie H2 2026 — De Ultieme Moat

## Executive Summary

OpenMithos heeft bewezen dat fine-tuning werkt: een 3B model scoort 32% beter dan een 7B baseline. Maar we kunnen nóg veel beter. Dit document beschrijft de weg naar APEX scores >4.0 met een systeem dat de Rijksoverheid en enterprise klanten kan overtuigen.

## Huidige Stand (R13)

| Model | APEX Score | Grootte | Kosten | Type |
|-------|-----------:|--------:|-------:|------|
| R10 gemma-4-26b | 4.058 | 26B | $0 | Cloud |
| R12 openmythos-3b | 3.009 | 3B | $0 | Fine-tuned lokaal |
| R9 qwen2.5-coder:7b | 2.635 | 7B | $0 | Baseline |

**Probleem:** R12 scoort beter dan baseline maar blijft ver achter bij cloud frontier. De klant vraagt: "Waarom zou ik voor jullie 3B model kiezen boven GPT-5 of Claude?"

**Antwoord:** Privacy + kosten + controle. Maar alleen als de score dichter bij 4.0 komt.

## Strategische Pijlers

### Pijler 1: Data — Van 112 naar 10,000+ examples

Huidige SFT data is 112 examples. Dat is bewezen voldoende voor proof-of-concept, maar niet voor productie.

**Acties:**
1. **Synthetische data generatie** — Gebruik frontier modellen (Claude/GPT-5) om 10,000+ governance gegenereerde cases te maken
2. **Domein-specifieke datasets** — NORA, BIO, EU AI Act, AVG als trainingsbronnen
3. **Edge case mining** — Analyseer R13 failures en genereer targeted training data
4. **Multi-language** — Nederlands + Engels + Duits voor EU-context

**Tools:**
- `generate_hard.py` (bestaand) — uitbreiden naar bulk generatie
- Claude API / GPT-5 voor data generatie
- HuggingFace datasets voor legal/governance corpora

### Pijler 2: Model — Van 3B naar 7B/14B met QLoRA

Huidige 3B model is een proof-of-concept. Voor productie schalen we op.

**Roadmap:**
1. **7B QLoRA** — 112 → 1000 examples, draait op werkstation (8GB met QLoRA 4-bit)
2. **14B QLoRA** — 1000 → 5000 examples, vereist cloud GPU (RunPod $0.50/uur)
3. **DPO** — Preference optimization bovenop SFT voor betere alignment
4. **MoE** — Mixture of Experts voor multi-domein (legal, technical, governance)

**Kosten:**
- 7B training: ~$5 (RunPod 1x A100)
- 14B training: ~$20 (RunPod 1x A100)
- DPO: ~$10 extra

### Pijler 3: Evaluatie — Van 351 naar 3500+ cases

Huidige APEX is 351 cases. Voor productie betrouwbaarheid hebben we meer nodig.

**Acties:**
1. **Category expansion** — Van 11 naar 25+ categorieën
2. **Adversarial testing** — Jailbreak, prompt injection, edge cases
3. **Multi-judge** — Niet alleen qwen2.5-coder:7b maar ook gemma-4 en Claude
4. **Human evaluation** — Domeinexperts beoordelen 100 cases
5. **Regression testing** — Automatische checks bij elke model update

### Pijler 4: Cloud + Lokaal Hybride

De toekomst is niet lokaal ÓF cloud — het is hybride.

**Architectuur:**
```
Lokaal (privacy):
├── openmythos-r12-v2 (3B) — routine taken
├── qwen2.5:14b — complexe taken
└── DutchDim/openmythos-lora (7B) — governance specialist

Cloud (frontier):
├── deepseek-v4-pro — hoogste kwaliteit
├── qwen3.5:35b — beste prijs/prestatie
└── gpt-5/claude — escalation only

Router:
├── Data class → lokaal of cloud
├── Task complexity → model selection
├── Cost budget → fallback chain
└── Latency requirement → edge vs cloud
```

## Concrete Stappen (R14-R20)

### R14: Cloud Model Benchmark (DEZE SPRINT)

Test de top 3 cloud modellen tegen APEX:

| Model | Verwachte Score | Kosten/test | Waarom |
|-------|---------------|-------------|--------|
| **deepseek-v4-pro** | 4.2-4.5 | ~$0.50 | Frontier reasoning |
| **qwen3.5:35b** | 3.8-4.1 | ~$0.10 | Beste prijs/prestatie |
| **gemma4:31b** | 4.0-4.2 | ~$0.20 | Geverifieerd werkend |

**Commando:**
```bash
python3 scripts/evaluate.py --corpus cases/corpus.jsonl --model deepseek-v4-pro --backend openrouter --output traces/apex-r14/deepseek-v4-pro.jsonl --governance-check --data-class public
```

### R15: Data Generatie Sprint

Genereer 1000+ nieuwe SFT examples:
1. Analyseer R13 failures (zwakke categorieën: injection, contradiction, hierarchy)
2. Genereer targeted cases met frontier model
3. Valideer met domeinexpert (Dennis)
4. Merge met bestaande 112 examples → 1000+

### R16: 7B QLoRA Fine-Tuning

Train op werkstation met 1000 examples:
- Base: qwen2.5-coder:7b
- Method: QLoRA 4-bit, r=32
- Verwachte score: 3.5-3.8

### R17: DPO Training

Preference optimization:
- Verzamel 500 preference pairs (good vs bad responses)
- Train DPO op basis van R16 model
- Verwachte verbetering: +10-15%

### R18: 14B Cloud Training

Scale up naar 14B:
- Platform: RunPod ($0.50/uur, 1x A100 80GB)
- Data: 5000 examples
- Verwachte score: 3.8-4.1

### R19: Productie Deployment

Docker compose + monitoring:
- Ollama lokaal + OpenRouter cloud
- Model registry met governance metadata
- Outcome ledger met feedback loop
- Prometheus + Grafana monitoring

### R20: Rijksoverheid Proof of Concept

6-weken PoC met één domein:
- Juridische zaken of klantcontact
- 100 cases evaluatie
- Human expert review
- Compliance rapport (NORA, BIO, EU AI Act)

## Financiering

| Item | Kosten | Timing |
|------|--------|--------|
| Cloud API credits (R14-R15) | $50-100 | Nu |
| RunPod training (R16-R18) | $50-100 | Maand 2-3 |
| Data generatie (Claude API) | $20-50 | Maand 2 |
| **Totaal H2 2026** | **$120-250** | |

## Succes Criteria

| Metric | Huidig | R14 Doel | R20 Doel |
|--------|--------|----------|----------|
| APEX Score | 3.01 | 4.0+ | 4.2+ |
| Pass Rate | 32.5% | 60%+ | 75%+ |
| Lokaal draaiend | 3B | 7B | 14B |
| Trainingsdata | 112 | 1000 | 5000 |
| Categorieën | 11 | 15 | 25 |
| Kosten/maand | $0 | $20 | $50 |

## Risico's

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Cloud API deprecatie | Hoog | Multi-provider (OpenRouter + direct) |
| GPU beschikbaarheid | Medium | Spot instances, meerdere providers |
| Data kwaliteit | Hoog | Human review, multi-generatie |
| Judge bias | Medium | Multi-judge, human evaluation |
| Ollama compatibiliteit | Laag | Keep models in GGUF, test elke versie |

## Conclusie

OpenMythos heeft bewezen dat het werkt. Nu gaan we schalen:
1. **Data** — van 112 naar 5000+ examples
2. **Model** — van 3B naar 7B/14B met QLORA + DPO
3. **Evaluatie** — van 351 naar 3500+ cases met multi-judge
4. **Deployment** — hybride lokaal + cloud met governance laag

**Target: APEX score >4.2 met lokaal 14B model voor Rijksoverheid eind 2026.**
