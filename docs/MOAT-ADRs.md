# Architecture Decision Records — Moat: Governance + Evidence + Feedback

## ADR-001: Governance as Primary Moat

**Status:** Accepted

### Context

Model commoditisering is reëel. Generieke inferentie wordt goedkoop. Orchestratie alleen is geen defensible moat — het wordt ook gecommoditiserd (LangChain, LlamaIndex, framework-agnostische tooling). Modelleveranciers absorberen orchestratie in hun SDKs.

### Decision

Positioneer OpenMythos niet als modelplatform of orchestratieframework, maar als **governed intelligence orchestration layer**. De moat ligt in:

1. **Governance** — policy-versies, compliance-frameworks, audit trails
2. **Evidence** — historische besluiten, causale koppelingen, reproduceerbare chains
3. **Feedback** — gevalideerde correcties van domeinexperts, evaluatie-verbetering

### Consequences

- Modellen zijn verwisselbare execution engines
- IP zit in data/feedback/regels, niet in code
- Governance-overhead per besluit (niet per token)
- Organisatiemoed vereist: mensen moeten correcties leveren

---

## ADR-002: Model Capability Registry

**Status:** Accepted — extends `hybrid_inference_router.py`

### Context

`hybrid_inference_router.py` bevat al een ROUTING_TABLE met modelcapaciteiten (cost, context, quality). Maar governance metadata ontbreekt: licentie, dataclass-toegang, security status, lifecycle state, geopolitiek.

### Decision

`model_registry.py` wordt de governance-extensie van de router. De router blijft cost/quality-optimalisatie doen. De registry beperkt welke modellen mogen draaien op welke data onder welke policies.

```
Router: "Welk model is goedkoopst voor deze taak?"
Registry: "Van die modellen, welke mogen op deze data onder het huidige beleid?"
```

### Integration

```python
from model_registry import eligible_models
from hybrid_inference_router import ROUTING_TABLE

# Filter router results through governance
candidates = ROUTING_TABLE[task_type]["tiers"]
allowed = eligible_models(registry, data_class="confidential")
final = [c for c in candidates if c["model"] in allowed]
```

---

## ADR-003: Risk-Aware Router Extension

**Status:** Proposed — extends `hybrid_inference_router.py`

### Context

Huidige router optimaliseert op cost en kwaliteit. Governance-eisen (datagevoeligheid, assurance level, geopolitiek) worden niet meegenomen.

### Decision

Router besluit op basis van:

```
route = f(
  task_criticality,      # low | medium | high | critical
  data_sensitivity,      # public | internal | confidential | restricted
  required_assurance,    # best_effort | validated | audited | certified
  model_trust_level,     # uit registry.security_status
  latency_budget_ms,
  cost_ceiling,
)
```

Een taak met `data_sensitivity=confidential` en `required_assurance=audited` kan alleen naar een model met:
- `security_status: scanned` in registry
- `confidential` in `allowed_data_classes`
- `lifecycle_state: production`

### Integration

Nieuwe functie `route_governed()` in `hybrid_inference_router.py` die bestaande `route()` aanroept en filtert op registry-constraints.

---

## ADR-004: Outcome Ledger

**Status:** Accepted — new component

### Context

Tokenvolume is consumptie, geen waarde. Bestaande traces (`traces/*.jsonl`) registreren modeloutput maar niet wat er mee gebeurde. Zonder outcome-registratie is er geen feedbackloop en geen audit-trail.

### Decision

`outcome_ledger.py` registreert per AI-output:
- Welke actie volgde (accepted/corrected/rejected/escalated)
- Welke correctie een mens aanbracht
- Causale koppeling naar business outcome
- Feedback-loop naar evaluatie-sets

Bron van waarde: `cost_per_accepted_outcome`, niet `cost_per_token`.

### Storage

Append-only JSONL in `outcomes/ledger.jsonl`. Privacy-first: geen volledige prompts, alleen hashes + metadata.

---

## ADR-005: Model Promotion Gates

**Status:** Accepted — documents existing gates

### Context

Er bestaan al drie gate-scripts:
- `promotion_gate.py` — case promotie op spread/discriminatie
- `regression_gate.py` — baseline vergelijking per category
- `operational_gate.py` — latency/error/token budgetten

Ontbreekt: integratie tot één end-to-end pipeline + declaratieve policy.

### Decision

`policies/model-lifecycle.yaml` is de declaratieve bron. De drie gate-scripts worden aangeroepen in volgorde:

```
1. operational_gate.py  (SLO check)
2. regression_gate.py   (no degradation vs baseline)
3. promotion_gate.py    (spread + discrimination)
```

Nieuwe modellen/prompts/workflows alleen productie na alle drie gates + formele approval.

### States

```
quarantined → evaluated → validated → staged → production → deprecated
```

Auto-quarantine bij: security incident, regressie, licensschending, geopolitieke sanctie.

---

## ADR-006: Geopolitical Risk Management

**Status:** Proposed

### Context

AI-markt fragmenteert in drie pools (US Closed, US/EU Open, CN Open). Exportcontroles, provenance-risico's en data residency worden strategische vragen.

### Decision

Registry krijgt `geopolitical_pool` veld per model:
- `tier_1_trusted` — EU/US allied, standard provenance
- `tier_2_verified` — global, enhanced provenance
- `tier_3_quarantine` — sanctioned, blocked

Router weigert modellen uit tier_3. Multi-pool diversificatie is verplicht: minstens één model per pool in registry.

### Sovereign Fallback

Als externe APIs onbereikbaar zijn (geopolitiek, outage), schakel over naar lokaal hostbare modellen uit tier_1 of tier_2.

---

## ADR-007: Middleware-Trap Mitigation

**Status:** Accepted

### Context

Orchestratielagen commoditiseren. Modelleveranciers absorberen orchestratie. "Good enough" tool use, RAG, agents komen in model-SDKs.

### Decision

OpenMythos bouwt geen orchestratieframework dat concurreert met LangChain/CrewAI. In plaats daarvan:

1. **Orchestratie is feature, geen product** — verwisselbaar, niet differentiator
2. **Governance is differentiator** — compliance, audit, policy-management wordt NIET geabsorbeerd door modelleveranciers
3. **Feedback is accumulatieve moat** — elke correctie, elke evaluatie maakt het systeem beter
4. **Integreer met frameworks, niet tegen** — werk bovenop bestaande orchestratie als governance-laag

De klant koopt niet model-agnosticisme (gratis), maar **audit-ability** (duur te bouwen).
