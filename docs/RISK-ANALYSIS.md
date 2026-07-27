# Risico-analyse: Geopolitiek en Middleware-Trap

## 1. Geopolitieke Risico's

### Drie Pools

| Pool | Vertegenwoordigers | Kenmerken | OpenMythos Response |
|------|-------------------|-----------|---------------------|
| US Closed | OpenAI, Anthropic, Google | Beste modellen, vendor lock-in, CLOUD Act | Frontier escalation tier |
| US/EU Open | Meta, Mistral, community | Flexibel, self-hosted, lagere kosten | Differentiated tier |
| CN Open | Alibaba (Qwen), DeepSeek, Baidu | Concurrend, provenance-risico | Registry tier_2_verified |

### Risico Register

| ID | Risico | Waarschijnlijkheid | Impact | Mitigatie | Component |
|----|--------|-------------------|--------|-----------|-----------|
| R1 | Exportcontroles beperken modelkeuze | Hoog | Hoog | Pool-diversificatie | Registry |
| R2 | Modelleveranciers absorberen orchestratie | Hoog | Medium | Focus op governance | ADR-007 |
| R3 | Geopolitieke escalatie | Medium | Hoog | Sovereign fallback | Registry + Router |
| R4 | Provenance-risico Chinese modellen | Medium | Hoog | Enhanced verification gate | Promotion gates |
| R5 | EU AI Act compliance complexity | Hoog | Medium | Policy-bound by design | ADR-001 |
| R6 | Framework-agnostische commoditisatie | Hoog | Laag | Orchestratie is feature | ADR-007 |
| R7 | Composability door frontierlabs | Hoog | Medium | Feedback als moat | ADR-004 |

### Concrete Mitigaties

**Registry velden:**
```yaml
geopolitical_pool: tier_2_verified
provenance:
  training_data_known: false
  export_control_status: "EAR99"
  data_residency: "EU"
```

**Router policy:**
- `tier_3_quarantine` modellen worden automatisch afgewezen
- Bij `data_residency=EU` requirement: alleen modellen met EU hosting of self-hosted
- Sovereign fallback: lokaal hostbaar model als extern APIs onbereikbaar

**Promotion gate addition:**
```python
# In promotion_gate.py — extra check
if model_registry[model_id]["geopolitical_pool"] == "tier_3_quarantine":
    reject(reason="geopolitical-quarantine")
```

## 2. Middleware-Trap

### Absorptie door Modelleveranciers

| Functie | Absorbeerd door | OpenMythos Response |
|---------|-----------------|---------------------|
| Tool use | OpenAI function calling, Anthropic tools | Geen eigen tool-use laag bouwen |
| RAG | OpenAI Assistants, Vertex RAG | Integreer met bestaande RAG |
| Memory | Thread-based memory in APIs | Eigen memory = governance + feedback, niet storage |
| Routing | Model-specific optimalisatie | Router = governance-filter, niet cost-optimalisator |

### Defensible Positionering

**Wat OpenMythis WEL bouwt (niet te absorberen):**
1. **Policy engine** — versies, approvals, compliance-frameworks
2. **Audit trail** — reproduceerbare evidence chains
3. **Feedback accumulation** — correcties → eval verbetering → betere outcomes
4. **Domain knowledge** — juridische regels, organisatorische verantwoordelijkheden

**Wat OpenMythos NIET bouwt (laat aan anderen):**
1. Tool-use frameworks
2. RAG implementaties
3. Chat interfaces
4. Model training pipelines

### Integratie, niet competitie

OpenMythos werkt bovenop:
- `hybrid_inference_router.py` — bestaande router als execution layer
- `open_djicht_api.py` — bestaande API als serving layer
- Externe orchestratie frameworks — als optionele integratie

## 3. Gecombineerd Impact op Architectuur

### Bestaande Componenten → Uitbreiding

| Component | Huidige Functie | Toevoeging voor Moat |
|-----------|----------------|---------------------|
| `promotion_gate.py` | Case spread/discriminatie | + geopolitical check, + provenance gate |
| `regression_gate.py` | Baseline vergelijking | + data residency check |
| `operational_gate.py` | SLO budgetten | + governance SLO (audit completeness) |
| `hybrid_inference_router.py` | Cost-optimalisatie | + governance filter (registry integration) |
| `corpus.jsonl` | Eval cases | + feedback-loop labeling |

### Nieuwe Componenten

| Component | Doel | Integratiepunt |
|-----------|------|----------------|
| `model_registry.py` | Governance metadata | Filter voor router |
| `outcome_ledger.py` | Outcome tracking | Input voor feedback loop |
| `policies/model-lifecycle.yaml` | Declaratief beleid | Config voor alle gates |

## 4. Actieplan

1. **Model Registry live** — `model_registry.py` + `registry.yaml` met alle actieve modellen
2. **Router integratie** — `hybrid_inference_router.py` koppelt aan registry voor governance-filter
3. **Ledger adoption** — Outcome recording bij elke productie-run
4. **Gate pipeline** — `operational → regression → promotion` als één command
5. **Geopolitical monitoring** — quarterly review van registry pool-diversificatie
