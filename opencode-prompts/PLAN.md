## Why

Djimitflo's governance layer valideert momenteel alleen structuur (metadata aanwezig?), niet gedrag (gedraagt een agent zich correct onder druk?). De OpenMythos Governance Benchmark biedt 275 gestandaardiseerde cases die precies dit testen — injection, hallucinatie, tool-scope, value-alignment, en meer.

Door OpenMythos te integreren als governance-test-infra veranderen we Djimitflo van een platform dat aangeeft "je agent heeft de juiste velden" naar een platform dat kan zeggen "je agent weigert correct bij injection pogingen en scoort 4.2/5 op governance".

Dit maakt governance meetbaar, trainbaar, en auditief bewijsbaar — precies wat klanten nodig hebben voor compliance.

## What Changes

### Change 1: Governance Guard als benchmark-target
- Nieuwe `openmythos-eval-service.ts` die cases draait via workstation Ollama
- `governance-guard-service.ts` uitbreiden met deployment-blokkage bij lage scores
- API routes voor evaluatie, scoring, en rapportage
- Database migratie voor `openmythos_eval_runs` en `openmythos_case_results`

### Change 2: Agent Assurance governance scoring
- `agent-assurance-service.ts` uitbreiden met externe governance score
- Assurance dashboard data verrijken met governance trend
- Degradatie-alerts bij score-daling
- Rapportage voor klant-facing governance rapporten

### Change 3: Skill Evolution Gym met governance curriculum
- `gym-governance-curriculum.ts` — cases indeelen in 4 trainingsfasen
- Gym evaluation uitbreiden met governance benchmark type
- Evolution pipeline: skills moeten governance certificering halen
- Automatische re-test bij skill updates

## Non-Goals

- Geen OpenMythos benchmark logica in Djimitflo zelf — calls gaan naar workstation
- Geen real-time governance monitoring (alleen bij deployment/training)
- Geen automatische skill-hertraining bij governance fail (human-in-the-loop)
- Geen multi-model judge consensus (single judge: qwen2.5:14b)
- Geen productie-deploy van de benchmark zelf (blijft in OpenMythos repo)

## Success Criteria

- Een skill deployment triggert automatisch relevante OpenMithos cases
- Governance guard blokkeert deployment bij score < 3.0/5.0
- Agent assurance dashboard toont governance trend over tijd
- Gym skills promoveren alleen na governance certificering
- Alle integraties hebben vitest coverage
- Geen nieuwe npm dependencies nodig

## Implementation Order

1. **Change 1** (foundation) — OpenMithos eval service + guard integratie
2. **Change 2** (verrijking) — Assurance scoring bouwt voort op Change 1
3. **Change 3** (gym) — Skill gym bouwt voort op Change 1 + 2

Elke change is een aparte OpenCode sessie met eigen scope.
