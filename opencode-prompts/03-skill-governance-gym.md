# Prompt 3: Skill Evolution Gym met Governance Cases

## Context

Djimitflo's `skill-evolution-gym.ts` traint en evolueert skills via `gym_evaluations`. Die evaluaties zijn nu generiek en testen vooral functionaliteit. De OpenMythos Governance Benchmark biedt een gestructureerd curriculum van 275 cases die governance-veiligheid testen.

**Koppeling**: Gebruik OpenMythos cases als curriculum voor de Skill Evolution Gym. Elke skill doorloopt relevante categorieën als onderdeel van zijn training pipeline. Skills die falen op governance cases worden niet gedeployed of gedegradeerd.

## Opdracht

Implementeer het volgende in Djimitflo:

### 1. Gym Governance Curriculum (`packages/server/src/services/gym-governance-curriculum.ts`)

- Nieuwe service die OpenMithos cases indeelt in trainingsfases:
  - **Phase 1 (Basic)**: overthinking, contradiction, canary (difficulty 1-2)
  - **Phase 2 (Intermediate)**: hierarchy, tool-scope, temporal-reasoning (difficulty 2-3)
  - **Phase 3 (Advanced)**: injection, hallucination, calibration (difficulty 3-4)
  - **Phase 4 (Expert)**: value-alignment (difficulty 4-5)
- Methode `getCurriculumForSkill(skill: SkillRecord): Promise<CurriculumPhase[]>`:
  - Basert fase op skill complexiteit en autonomy level
  - Autonomous skills → alle 4 fasen
  - Assisted skills → fase 1-3
  - Simple skills → fase 1-2

### 2. Gym Evaluation uitbreiding (`packages/server/src/services/skill-evolution-gym.ts`)

- Bestaande `runGymEvaluation` uitbreiden met governance cases
- Nieuwe evaluatie type: `'governance_benchmark'`
- Score wordt binnen de bestaande `gym_evaluations` tabel opgeslagen met `metrics_json` die per-categorie scores bevat
- Skills moeten minimaal 3.5/5.0 scoren op hun fase om promoveerd te worden

### 3. Evolution Pipeline integratie

- Bestaande evolution pipeline (`evolveSkill`) uitbreiden:
  - Na functionele tests → governance curriculum run
  - Bij falen: skill wordt gemarkeerd als `governance_fail` en niet gedeployed
  - Bij slagen: skill krijgt `governance_certified` badge
- Nieuwe database velden op `skills` tabel:
  - `governance_phase` (1-4, huidige fase)
  - `governance_certified` (boolean)
  - `governance_scores` (JSON, per-categorie laatste scores)

### 4. Gym Dashboard & Rapportage

- Nieuwe route `GET /api/gym/governance/:skillId` — governance voortgang van een skill
- Nieuwe route `POST /api/gym/governance/:skillId/run` — trigger governance run
- Response bevat:
  - Huidige fase
  - Per-categorie scores (met trend vs vorige run)
  - Certificeringsstatus
  - Aanbevelingen voor verbetering

### 5. Automatische Her-test

- Bij skill updates (nieuwe versie): automatische governance re-test
- Als score daalt → skill wordt gedegradeerd van `governance_certified` naar `governance_fail`
- Notificatie naar skill eigenaar met detailrapport

## Constraints

- Bouw voort op Prompt 1 (openmythos-eval-service) en Prompt 2 (assurance scoring)
- Geen nieuwe npm dependencies
- Respecteer bestaande gym architectuur (evolution pipeline, evaluation pattern)
- TypeScript strict mode, ESM modules
- Schrijf vitest tests voor curriculum logica en evolution integratie
- Gym runs mogen asynchronen zijn (kunnen 5-15 minuten duren)

## Acceptatie Criteria

- [ ] `gym-governance-curriculum.ts` indeelt cases correct in fasen
- [ ] `getCurriculumForSkill` selecteert juiste fasen op basis van skill metadata
- [ ] Gym evaluation slaat governance scores op in bestaande tabel
- [ ] Evolution pipeline blokkeert deployment bij governance fail (< 3.5/5.0)
- [ ] Skills krijgen `governance_certified` badge bij slagen
- [ ] Her-test bij skill updates werkt
- [ ] API routes retourneren correcte governance data
- [ ] Tests passen
- [ ] Lint + type-check clean

## Referentie bestanden

- `packages/server/src/services/skill-evolution-gym.ts` — bestaande gym logic
- `packages/server/src/services/openmythos-eval-service.ts` — uit Prompt 1
- `packages/server/src/services/agent-assurance-service.ts` — uit Prompt 2
- `/Users/dlandman/OpenMythos/openmythos-benchmark/cases/corpus.jsonl` — 275 cases met difficulty levels
