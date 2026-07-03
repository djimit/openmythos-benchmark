## Why

Djimitflo's governance layer valideert momenteel alleen structuur (metadata aanwezig?), niet gedrag. De OpenMythos Governance Benchmark biedt 275 cases die model-gedrag testen. Deze change koppelt OpenMythos als live test suite aan de governance_guard worker.

## What Changes

- Nieuwe `openmythos-eval-service.ts` — laadt cases, draait via Ollama op workstation, judge scoring
- `governance-guard-service.ts` uitbreiden met `runBenchmarkCheck(skillId)`
- API routes: `POST /api/openmythos/eval/:agentId`, `GET /api/openmythos/score/:agentId`
- Database migratie: `openmythos_eval_runs`, `openmythos_case_results`
- Worker pipeline: `benchmark_eval` stap in governance_guard

## Non-Goals

- Geen benchmark logica in Djimitflo — calls naar workstation:80
- Geen real-time monitoring
- Geen auto-retry bij fail

## Success Criteria

- Skill deployment triggert relevante OpenMithos cases
- Guard blokkeert bij score < 3.0/5.0
- API routes bereikbaar
- Tests + lint + type-check clean
