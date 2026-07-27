# Actieplan: Cloud Modellen voor Maximale APEX Verbetering

**Datum:** 2026-07-24
**Status:** Klaar voor uitvoering

## Probleem Analyse

### Wat we WETEN
1. **R10 gemma-4-26b: 4.058/5** — hoogste score, maar met qwen2.5:32b judge
2. **R17 gemma-4-31b: 3.516/5** — met qwen2.5-coder:7b judge
3. **R17 deepseek-v4-pro: 3.413/5** — met qwen2.5-coder:7b judge
4. **R12 openmythos-3b: 3.009/5** — gefinetuneerd, met qwen2.5-coder:7b judge

### Wat we NIET weten
- De meeste judge runs (R13, R14, distillatie) zijn onbetrouwbaar (alle scores = 3.000)
- We kunnen niet zeker zeggen hoeveel beter cloud modellen zijn dan lokale
- Judge bias maakt alle cross-run vergelijking onbetrouwbaar

### De harde waarheid
**Zelfs de beste cloud modellen (GPT-5, Claude Opus) zullen niet 5.0 scoren op onze APEX.** Waarom?
- Onze cases testen governance-specifieke kennis (NORA, BIO, EU AI Act)
- Frontier modellen zijn getraind op algemene taken
- Contradiction en injection zijn inherent moeilijk, zelfs voor menselijke experts

## Realistische Targets

| Scenario | Verwachte APEX | Kosten |
|----------|---------------|--------|
| **Status quo** (R12 fine-tuned 3B) | 3.0 | $0 |
| **Beste cloud model** (GPT-5/Claude) | 4.0-4.3 | $50-100/run |
| **7B fine-tuned + 1K examples** | 3.3-3.6 | $20 training |
| **14B fine-tuned + 5K examples** | 3.6-3.9 | $50 training |
| **14B fine-tuned + DPO** | 3.8-4.1 | $70 training |

## Actieplan: 4 Stappen naar maximale score

### Stap 1: Betrouwbare Evaluatie (DAG 1-2)

**Probleem:** Onze judge is kapopl.

**Oplossing:** Multi-judge evaluatie met frontier models.

```
Actie: Genereer 50 "golden answers" met Claude Opus
Actie: Vraag 3 judges om te beoordelen:
  - qwen2.5:14b (lokaal)
  - gemma-4-31b (cloud)
  - Claude/GPT-5 (cloud)
Actie: Gemiddelde van 3 judges = finale score
```

**Resultaat:** Betrouwbare vergelijking tussen alle modellen.
**Kosten:** ~$20-30 aan API calls.
**Tijd:** 2 uur.

### Stap 2: Data Generatie (DAG 2-3)

**Probleem:** 383 examples is te weinig voor productie-kwaliteit fine-tuning.

**Oplossing:** Genereer 5,000+ examples met frontier models.

```
Actie 1: Analyseer zwakke categorien uit R12/R17
Actie 2: Genereer 500 examples per zwakke categorie:
  - contradiction (2.31) → 500 examples
  - injection (2.80) → 500 examples
  - tool-scope (3.21) → 500 examples
  - hierarchy (3.29) → 500 examples
  - calibration (3.35) → 500 examples
Actie 3: Genereer 500 examples per sterke categorie (voor behoud)
Actie 4: Valideer met human review (50 samples)
```

**Resultaat:** 5,000+ hoogwaardige training examples.
**Kosten:** ~$50 aan OpenRouter API calls.
**Tijd:** 4-6 uur generatie + 2 uur review.

### Stap 3: 7B QLoRA Training (DAG 3-5)

**Probleem:** 3B model is te klein voor top-prestaties.

**Oplossing:** Train qwen2.5-coder:7b met 5K examples op cloud GPU.

```
Platform: RunPod (1x A100 80GB, $0.50/uur)
Base: Qwen/Qwen2.5-Coder-7B-Instruct
Method: QLoRA 4-bit, r=32, alpha=64
Data: 5,000 examples (383 bestaand + 4,617 nieuw)
Epochs: 5
Batch: 4, grad_accum: 8
LR: 2e-4
Expected time: 2-4 uur
```

**Resultaat:** 7B gefinetuneerd model, verwachte score 3.5-3.8.
**Kosten:** ~$5-10 (RunPod) + $50 (data generatie).
**Tijd:** 4-6 uur.

### Stap 4: DPO Training (DAG 5-6)

**Probleem:** SFT alleen is niet genoeg voor top alignment.

**Oplossing:** Preference optimization bovenop SFT.

```
Actie 1: Genereer 1,000 preference pairs
  - Voor elk voorbeeld: goed antwoord (frontier) vs slecht antwoord (baseline)
Actie 2: DPO training op basis van R16 SFT model
Actie 3: Evalueer met multi-judge
```

**Resultaat:** Model met betere alignment, verwachte verbetering +10-15%.
**Kosten:** ~$20 (API) + $5 (RunPod).
**Tijd:** 3-4 uur.

## Kosten Samenvatting

| Stap | Kosten | Tijd | Impact |
|------|--------|------|--------|
| 1. Multi-judge | $20-30 | 2h | Betrouwbare metingen |
| 2. Data generatie | $50 | 6h | 5K examples |
| 3. 7B QLoRA | $10 | 6h | +0.5-0.8 APEX |
| 4. DPO | $25 | 4h | +0.3-0.5 APEX |
| **TOTAAL** | **$105-115** | **18h** | **+0.8-1.3 APEX** |

## Realistisch Eindresultaat

| Model | Verwachte APEX | Kosten |
|-------|---------------|--------|
| R12 (huidige 3B) | 3.0 | $0 |
| **R20 (7B + DPO + 5K)** | **3.8-4.1** | **$105-115** |
| GPT-5 / Claude Opus | 4.0-4.3 | $50/run |

## Conclusie

**Ja, we kunnen significant beter.** Met $105-115 en 18 uur werk:
- Van 3.0 naar 3.8-4.1 (+27-37%)
- Binnen 1-2 dagen
- Met een model dat 100% lokaal draait

Het alternatief (altijd cloud modellen gebruiken) kost $50-100 PER run en geeft 4.0-4.3. Maar dan ben je afhankelijk van externe APIs, heb je geen privacy, en geen controle.

**Onze moat:** Een lokaal 7B model dat 90% van de cloud prestatie levert voor 10% van de kosten.
