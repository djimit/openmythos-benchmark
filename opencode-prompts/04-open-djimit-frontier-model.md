# Prompt 4: OpenDjimit Frontier Model — Strategie & Realisatie

## Samenvatting van bevindingen uit volledige context-analyse

Deze analyse combineert:
- OpenMythos benchmark (351 cases, 11 categorieën, APEX R1-R46)
- OpenFable adversary pipeline (generate.py, fable.py, learning_data_factory.py)
- Djimitflo governance guard & assurance scoring
- Frontier model context (Claude Fable 5, GPT-5, Gemini 2.5, GLM-5.5, Qwen3)
- Bestaande SFT/DPO pipeline (r20_lora_sft_pilot.py, learning_data_factory.py)

---

## Blinde vlekken & gemiste opportunities

### 1. **Routing > Scaling, maar je blijft bij bestaande modellen**

APEX-R43 bewezen: twee kleine modellen (8B + 14B) met category-routing verslaan 32B single-model. Dit is een **fundamentele insight** die onbenut blijft — je bouwt geen model dat deze routing *intern* uitvoert.

**Opportunity:** Eén model trainen dat *alle* governance-categories beheert, met interne routing (MoE-achtige architectuur). In plaats van 3 modellen orchestreren, één model met gespecialiseerde experts.

### 2. **Frontier output is gratis lesmateriaal — je verzamelt het niet systematisch**

`generate.py` en `fable.py` produceren frontier-model outputs, maar die worden alleen gebruikt als draft cases. De **responses zelf** — hoe Claude Fable 5 een injection-afwerring formuleert, hoe GPT-5 een tool-scope boundary hanteert — worden nooit systematisch verzameld als trainingsdata.

**Opportunity:** Elke frontier-model call in de pipeline moet output loggen in SFT-formaat. Je hebt al duizenden frontier responses — die liggen in traces, niet in datasets.

### 3. **De SFT/DPO pipeline is er, maar doet niets**

`learning_data_factory.py` (R19) en `r20_lora_sft_pilot.py` bestaan. Ze zijn gevalideerd. Maar er is **nooit een echte training gedraaid** — geen GPU toegang, geen base model selection, geen experimentele validatie.

**Opportunity:** De code is klaar. Het enige wat mist is een trainingsrun op workstation (met Qwen3-32B base + LoRA op A100 of via cloud API).

### 4. **Governance is je USP, maar je benchmark is alleen evaluatie**

OpenMithos is een *meetschaal*. Het zegt of een model goed is. Het maakt geen model beter. Er is een **gat tussen evaluatie en training** — je herkent zwaktes (weakness_map.py) maar lost ze niet op door het model te verbeteren.

**Opportunity:** Sluit de evaluatie→training lus. Elke weakness_map output moet automatisch nieuwe SFT samples genereren.

### 5. **Nederlands/EU governance is onderbelicht**

LIMITATIONS.md geeft toe: alle cases zijn Engels, EU/US-centric. Voor DjimIT's overheidsklanten is Nederlandse governance (AVG, NORA, BIO, Common Ground) essentieel.

**Opportunity:** 50-100 Nederlandse cases genereren voor governance-categories specifiek voor de Nederlandse overheidscontext. Dit is een **unique selling point** dat geen enkel andere benchmark ter wereld heeft.

### 6. **Multi-agent governance is onbestaande**

LIMITATIONS.md punt 7: multi-agent coordinatie, agent swarms, tool-chain attacks zijn out of scope. Maar DjimIT **is** een multi-agent systeem. Je test individuele model-governance, maar niet of een swarm van ge-governancede agents veilig samenwerkt.

**Opportunity:** Multi-agent governance cases — een agent die een andere agent manipuleert, tool-chain waarin output van agent A input is voor agent B met injection in de keten.

### 7. **Geen productisatie als model-as-a-service**

OpenMythos blijft een benchmark. Er is geen plan om het model dat je traint te exposeren als API, te integreren met LiteLLM routing, of aan te bieden aan klanten als "Djimit Governance-Guaranteed AI".

**Opportunity:** Het OpenDjicht model hosten op workstation, registreren in LiteLLM als `open-djimit-governance`, en aanbieden als premium governance-gegarandeerde inference voor klanten.

---

## Strategisch advies: De beste oplossing voor Djimit

### Visie: **OpenDjicht-1** — Het eerste governance-frontier model voor de EU

Een 14B-32B model dat op alle OpenMythos-governance categorieen frontier-niveau presteert, Nederlandse/EU governance beheert, en draait op eigen hardware.

### Waarom dit de beste oplossing is

1. **Je hebt al het materiaal** — benchmark, adversary, SFT pipeline, evaluatie framework
2. **Je hebt een gevalideerde metriek** — calibrated leaderboard, oracle scoring, discrimination
3. **Je hebt een markt** — overheidsklanten die governance-garanties eisen
4. **Je hebt differentiatie** — geen ander EU-bedrijft traint een model specifiek op AI-governance
5. **Je hebt een lus** → model traint → benchmark evalueert → weaknesses → nieuwe training → beter model

### Architectuur

```
┌─────────────────────────────────────────────────────────┐
│                    OpenDjicht-1 Model                     │
│                                                          │
│  Base: Qwen3-32B (Apache 2.0)                           │
│  Fine-tuned via QLoRA op:                               │
│    - 1000+ SFT samples (frontier distillation)          │
│    - 500+ DPO pairs (frontier vs open-source)           │
│    - 200+ NL governance cases (EU-specific)             │
│    - 100+ multi-agent governance cases                  │
│                                                          │
│  Inference: Ollama op workstation (192.168.1.28)        │
│  LiteLLM registration: open-djicht-governance           │
│  Evaluatie: OpenMithos canon + NL extension             │
└─────────────────────────────────────────────────────────┘
```

### Fasering

#### Fase 0: Data verzamelen (NU — 1 week, €0)

Dit is de **snelste winst** — geen training nodig, alleen frontier outputs verzamelen:

1. **Log alle frontier-model calls** in `generate.py` en `fable.py` naar `datasets/frontier-distill/`
2. **Voeg toe aan `learning_data_factory.py`**: elke trace run automatisch omzetten naar SFT/DPO formaat
3. **Genereer 200 NL governance cases** met `generate.py` (category injection, hierarchy, tool-scope in Nederlandse context)
4. **Voeg multi-agent cases toe** aan de corpus (nieuwe categorie: `multi-agent`)

**Output:** 1500+ SFT samples, 600+ DPO pairs, 50 NL cases, 20 multi-agent cases

#### Fase 1: Distillatie training (week 2-4, €50-200 GPU)

1. **Base model**: Qwen3-32B-Q4_K_M (draait op workstation)
2. **QLoRA training** met `r20_lora_sft_pilot.py` uitgebreid met:
   - Frontier distillation data (Fase 0)
   - Bestaande R19 SFT/DPO data
3. **Validatie**: `run_benchmark.py` tegen OpenMythos canon
4. **Doel**: ≥ 60% oracle pass rate (vs huidige 47% voor 32B)

#### Fase 2: Iteratie + NL governance (week 4-8)

1. **Weakness map** → identificeer categories waar model faalt
2. **Gerichte frontier distillation** voor zwakke categories
3. **NL governance validatie** — Nederlandse cases draaien, scoren, itereren
4. **Multi-agent testen** — fable.py uitgebreid met multi-agent scenarios

#### Fase 3: Productisatie (week 8-12)

1. **LiteLLM registratie** als `open-djicht-governance`
2. **API endpoint** op workstation
3. **Djimitflo integratie** — governance guard gebruikt OpenDjicht als judge
4. **Klant-facing**: "Governance-gegarandeerde AI" als premium tier

---

## Concrete eerste stap (wat je deze week doet)

### Script: `scripts/frontier_distill_collector.py`

Dit script bestaat nog niet. Het moet:

1. Doorlopen: alle bestaande traces in `traces/apex-r*-*/` 
2. Voor elke trace: als een frontier model (claude-fable-5, gpt-5, gemini-2.5-pro) als attacker/target/judge draaide → response extraheren
3. Omzetten naar SFT formaat: `{messages: [{role: "user", content: case_prompt}, {role: "assistant", content: frontier_response}]}`
4. Omzetten naar DPO formaat: `{prompt: case_prompt, chosen: frontier_response, rejected: open_source_response}`
5. Schrijven naar `datasets/frontier-distill/sft.jsonl` en `datasets/frontier-distill/dpo.jsonl`

### Script: `scripts/nl_governance_generator.py`

1. Neem OpenMithos case template
2. Genereer Nederlandse varianten met specifieke EU/NL referenties:
   - AVG/GDPR in plaats van generic privacy
   - NORA/BIO in plaats van generic IT governance
   - Common Ground in plaats van generic government data
   - Nederlandse juridische terminologie
3. Output: `cases/nl-governance-drafts.jsonl`

### Uitbreiding: `scripts/fable_multi_agent.py`

1. Twee-agent setup: attacker agent + target agent
2. Attacker probeert target te manipuleren via tool-chain
3. Judge evalueert of target governance hield over hele keten
4. Output: multi-agent governance cases voor corpus

---

## Success criteria

| Metriek | Huidige baseline | OpenDjicht-1 doel |
|---------|------------------|-------------------|
| Oracle pass rate (78 cases) | 47.4% (Qwen2.5-32B) | ≥ 65% |
| NL governance score | N/A (geen NL cases) | ≥ 70% |
| Multi-agent governance | N/A | ≥ 60% |
| Canary failures | 4/60 | 0/60 |
| Latency (p50) | 6327ms | ≤ 8000ms |
| Model size | 32B | 32B (QLoRA) |

---

## Risico's & mitigatie

| Risico | Mitigatie |
|--------|-----------|
| GPU geen toegang | QLoRA op 1x A100 (cloud, ~$1/uur) of Apple MLX op M4 Max |
| Frontier model weigert (safety) | Fallback naar Opus 4.8, log refusals als signal |
| Te weinig trainingsdata | Active evolution loop: zwakke categories → meer generatie |
| NL cases te laag kwaliteit | Human review door Dennis + Nederlandse consultants |
| Overfitting op benchmark | Holdout set (R21), discriminatie-check |

---

## Waarom dit next-level is

1. **Geen ander EU-bedrijf** traint een model op AI-governance — je wordt de eerste
2. **Benchmark + training = lus** — elke iteratie maakt het model beter én de benchmark strenger
3. **Nederlandse governance** is een blue-ocean markt — geen concurrentie
4. **Multi-agent governance** is het volgende frontier — je bent voorloper
5. **Klantencase**: "Onze AI is getest op 351 governance scenarios en scoort 65% — uw huidige provider scoort 30%" is een verkoopargument
