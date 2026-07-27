# OpenDjicht-1 Master Plan — Next Level AI voor Djimit

> **Status:** Draft klaar voor review
> **Datum:** 2026-07-23
> **Auteur:** OpenMythos Architectuur

---

## Executive Summary

Djimit heeft alle bouwstenen voor een **frontier-level governance model** dat:
- Op eigen hardware draait (workstation, geen API-afhankelijkheid)
- Specifiek getraind op AI-governance (OpenMythos canon)
- Nederlandse/EU regulatory context beheert (unieke differentiatie)
- Multi-agent governance test (toekomstig differentiatie)
- Continue verbetert via evaluatie→training lus

**Investment:** ~€100-500 GPU-tijd, 4-8 weken ontwikkeling
**ROI:** Productdifferentiatie die geen ander EU-bedrijf heeft + directe klantwaarde voor overheid

---

## 7 Blinde Vlekken die nu worden opgelost

| # | Blinde vlek | Impact | Oplossing in dit plan |
|---|-------------|--------|----------------------|
| 1 | Routing > scaling onbenut | Je gebruikt 3 modellen waar 1 met interne routing beter is | OpenDjicht met MoE-achtige expert-routing |
| 2 | Frontier outputs niet als training data | Duizenden frontier responses liggen ongebruikt in traces | `frontier_distill_collector.py` — nu 31 SFT + 18 DPO samples |
| 3 | SFT/DPO pipeline draait nooit | Code is er, geer training | QLoRA training op workstation (deze week opstarten) |
| 4 | Evaluatie-Training gat | Benchmark meet maar verbetert niet | Gesloten lus: weakness → nieuwe data → training |
| 5 | Geen NL/EU governance | LIMITATIONS.md punt 5 — alles is Engels | 15 NL cases (AVG, NORA, EU AI Act, Common Ground) |
| 6 | Geen multi-agent governance | LIMITATIONS.md punt 7 — en DjimIT is multi-agent | Nieuwe `multi-agent` categorie + test cases |
| 7 | Geen productisatie | Benchmark blijft academisch | LiteLLM registratie + API endpoint + klant-facing |

---

## De 3 Pijlers van OpenDjicht-1

### Pijler 1: Frontier Distillatie

**Wat:** Claude Fable 5, GPT-5, Gemini outputs omzetten naar trainingsdata

**Hoe:** `scripts/frontier_distill_collector.py`
- Scan alle traces → extraheer frontier responses
- SFT: frontier response = assistant reply
- DPO: frontier = chosen, open-source = rejected
- Holdout split (80/20) om overfitting te voorkomen

**Huidige status:**
- 76 frontier responses gevonden (gpt-oss:20b als frontier)
- 9239 open-source responses (Qwen2.5, Llama3.1)
- → 31 SFT samples + 18 DPO pairs (eerste run)

**Volgende stap:** Meer frontier modellen toegen via `generate.py` en `fable.py` met Claude Fable 5, GPT-5, Gemini als attackers/targets. Doel: 500+ SFT, 200+ DPO.

### Pijler 2: NL/EU Governance

**Wat:** 15 Nederlandse cases die unieke governance-dekking bieden

**Hoe:** `scripts/nl_governance_generator.py`
- AVG/GDPR (5 cases): data-export, BSN, geautomatiseerde besluitvorming
- NORA/BIO (2 cases): beveiligingsinformatie, kwetsbaarheden
- EU AI Act (2 cases): high-risk systemen, transparantie
- Common Ground (2 cases): datadeling, federatieve architectuur
- Nederlands recht (3 cases): hallucinatie, termijnen, minimumloon
- Multi-agent (1 case): agent-autorisatie

**Volgende stap:** Uitbreiden naar 50+ NL cases, human review door Dennis + consultants

### Pijler 3: Gesloten Evaluatie-Training Lus

**Wat:** Elke benchmark-run genereert automatisch trainingsdata voor de volgende iteratie

**Hoe:** Uitbreiding van bestaande pipeline:
```
evaluate.py → weakness_map.py → frontier_distill_collector.py → training → evaluate.py
     ↑                                                              │
     └──────────────────────────────────────────────────────────────┘
```

**Nieuw script:** `scripts/evolution_training_loop.py` (nog te bouwen)
- Draait benchmark op huidige model
- Identificeert zwakke categories
- Genereert frontier-distill cases voor die categories
- Traint nieuwe LoRA adapter
- Valideert tegen holdout set
- Promoveert alleen als beter dan vorige versie

---

## Technische Architectuur

### Base Model Selectie

| Optie | Params | Licentie | Geschikt? | Aanbeveling |
|-------|--------|----------|-----------|-------------|
| **Qwen3-32B** | 32B dense | Apache 2.0 | ✅ Beste keuze | **Start hier** |
| Qwen3-235B-A22B | 235B/22B MoE | Apache 2.0 | ✅ Efficiënter | Iteratie 2 |
| GLM-5 | 744B/40B MoE | Open-weight | ⚠️ Nog niet beschikbaar | Wacht op release |
| Kimi K2 | 1T/32B MoE | MIT | ✅ Sterk | Alternatief |

### Training Stack

```
Base: Qwen3-32B-Q4_K_M
Method: QLoRA (4-bit quantized LoRA)
Hardware: 1x A100 80GB (cloud) of Apple M4 Max (MLX)
Framework: TRL (Transformer Reinforcement Learning)
Duration: 2-4 uur voor SFT, 4-8 uur voor DPO
Cost: ~€50-200 (cloud GPU)
```

### Inference Stack

```
Model: open-djicht-governance (GGUF Q4_K_M)
Runtime: Ollama op workstation (192.168.1.28:11434)
API: LiteLLM proxy (192.168.1.28:4000)
Endpoint: /v1/chat/completions
Model ID: open-djicht-governance
```

---

## Tijdlijn

### Week 1: Data & Setup (NU)
- [x] `frontier_distill_collector.py` — DONE
- [x] `nl_governance_generator.py` — DONE
- [ ] Draai collector → schijf SFT/DPO data
- [ ] Draai NL generator → 15 NL cases
- [ ] Review NL cases (Dennis)
- [ ] Setup training environment (MLX of cloud GPU)

### Week 2-3: Eerste Training
- [ ] SFT run op Qwen3-32B met frontier data
- [ ] DPO run met chosen/rejected paren
- [ ] Validatie tegen OpenMythos canon
- [ ] Vergelijking met baseline (Qwen2.5-32B single)

### Week 4-6: Iteratie & NL Governance
- [ ] Weakness-analyse → gerichte frontier distillatie
- [ ] NL cases uitbreiden naar 50+
- [ ] Multi-agent cases toegen (10+)
- [ ] Tweede training iteratie

### Week 8-12: Productisatie
- [ ] LiteLLM registratie
- [ ] Djimitflo integratie (governance guard)
- [ ] API documentatie
- [ ] Klant-facing governance rapportage

---

## Risico's

| Risico | Kans | Impact | Mitigatie |
|--------|------|--------|-----------|
| GPU onbeschikbaar | Laag | Hoog | Cloud A100 (~€1/uur) of MLX op M4 |
| Te weinig trainingsdata | Medium | Medium | Active loop: zwakke cat → meer generatie |
| Frontier model weigert | Medium | Laag | Fallback naar Opus 4.8 |
| NL cases te laag kwaliteit | Laag | Medium | Human review + consultant validatie |
| Overfitting op benchmark | Medium | Hoog | Holdout set + discriminatie-check |

---

## Succes Criteria

| Metriek | Baseline | Doel OpenDjicht-1 |
|---------|----------|-------------------|
| Oracle pass rate (78 cases) | 47.4% (Qwen2.5-32B) | ≥ 65% |
| NL governance score | N/A | ≥ 70% |
| Multi-agent governance | N/A | ≥ 60% |
| Canary failures | 4/60 | 0/60 |
| Latency p50 | 6327ms | ≤ 8000ms |
| Model size | 32B | 32B (QLoRA) |
| Cost per inference | €0 (eigen hardware) | €0 (eigen hardware) |

---

## Wat je deze week doet (actiepunten)

1. **Review** dit document + `04-open-djicht-frontier-model.md`
2. **Goedkeuring** NL cases door Dennis (juridische correctheid)
3. **Draai** `frontier_distill_collector.py` zonder `--dry-run` → data genereren
4. **Draai** `nl_governance_generator.py` zonder `--dry-run` → NL cases schrijven
5. **Bepaal** training hardware: cloud A100 of lokaal MLX?
6. **Plan** eerste training run (Week 2)

---

> "The best model is the one you own, that beats frontier models on your specific domain, and that improves every week."
> — OpenMythos Architectuur, 2026
