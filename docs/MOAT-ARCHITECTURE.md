# Moat Architecture: Governance + Evidence + Feedback

## Positionering

OpenMythos is geen modelplatform en geen orchestratieframework. Het is een **governed intelligence orchestration layer** waar modellen verwisselbare execution engines zijn.

De moat ligt in:
1. **Governance** — policy-versies, compliance-frameworks, audit trails
2. **Evidence** — historische besluiten, causale koppelingen, reproduceerbare chains
3. **Feedback** — gevalideerde correcties van domeinexperts, evaluatie-verbetering

## Bestaande Componenten (hergebruik)

| ADR | Bestaande code | Status |
|-----|---------------|--------|
| Model Registry | `corpus-schema.json` + `hybrid_inference_router.py` ROUTING_TABLE | Uitbreiden met governance metadata |
| Risk-aware Router | `hybrid_inference_router.py` | Uitbreiden met data sensitivity + assurance levels |
| Promotion Gates | `promotion_gate.py`, `regression_gate.py`, `operational_gate.py` | Bestaand — ADR-005 documenteert het |
| Outcome Ledger | Ontbreekt | Nieuw te bouwen |
| Evaluation Sets | `cases/corpus.jsonl` + `cases/nl-governance-drafts.jsonl` | Bestaand — golden sets |

## Nieuwe Componenten

1. `scripts/model_registry.py` — Model Capability Registry (YAML-backed)
2. `scripts/outcome_ledger.py` — Outcome recording + feedback loop
3. `policies/model-lifecycle.yaml` — Promotion gate policies declaratief

## Architectuurprincipes

1. **Model-agnostic by design** — elke component werkt met elk model
2. **Policy-bound by default** — geen AI-output zonder policy-versie
3. **Evidence-grounded by construction** — reproduceerbare evidence-chain per besluit
4. **Evaluated before promotion** — gates voorkomen regressie
5. **Human-accountable at material decisions** — menselijke accordering bij juridische gevolgen
