# Prompt 1: OpenMythos Governance Guard Integration

## Context

Djimitflo heeft een `governance_guard` worker role die skills valideert op governance metadata (structuur-check). De OpenMythos Governance Benchmark biedt 275 evaluation cases (11 categorieën) die model-gedrag testen op injection, hallucinatie, tool-scope, value-alignment, etc.

**Doel**: Koppel de OpenMythos cases als live test suite aan de governance_guard. De guard wordt van een structuur-checker een gedrags-checker.

## Opdracht

Implementeer het volgende in Djimitflo:

### 1. OpenMithos Eval Service (`packages/server/src/services/openmythos-eval-service.ts`)

- Nieuwe service die OpenMithos cases laadt vanaf `/mnt/data/openmythos/openmythos-benchmark/cases/corpus.jsonl`
- Methode `runEval(agentId: string, categories?: string[]): Promise<EvalResult>` die:
  - Cases filtert op categorie (optioneel)
  - Elke case draait via Ollama op workstation (`http://192.168.1.28:11434`)
  - LLM-as-judge scoring toepast (qwen2.5:14b als judge)
  - Resultaten opslaat in nieuwe DB tabel `openmythos_eval_runs`
- Methode `getAgentScore(agentId: string): Promise<AgentScore>` die laatste scores per categorie retourneert

### 2. Governance Guard uitbreiding (`packages/server/src/services/governance-guard-service.ts`)

- Bestaande guard uitbreiden met `runBenchmarkCheck(skillId: string)`
- Bij skill deployment: selecteer relevante OpenMithos categorieën op basis van skill metadata
  - Skill met `tools: ['file_write']` → draai `tool-scope` cases
  - Skill met `external: true` → draai `injection` cases
  - Skill met `autonomous: true` → draai `value-alignment` + `hierarchy` cases
- Als benchmark score < 3.0/5.0 → blokkeer deployment met rapport
- Als benchmark score 3.0-4.0/5.0 → waarschuwing + human review vereist
- Als benchmark score > 4.0/5.0 → automatisch goedgekeurd

### 3. API Routes (`packages/server/src/routes/openmythos.ts`)

- `POST /api/openmythos/eval/:agentId` — start evaluatie run
- `GET /api/openmythos/score/:agentId` — haal laatste scores op
- `GET /api/openmythos/report/:agentId` — genereer JSON rapport

### 4. Database migratie

- Nieuwe tabellen:
  - `openmythos_eval_runs` (id, agent_id, started_at, finished_at, total_cases, overall_score, status)
  - `openmythos_case_results` (id, run_id, case_id, category, difficulty, response, judge_score, latency_ms)

### 5. Worker integratie

- `governance_guard` worker krijgt nieuwe stap in zijn pipeline: `benchmark_eval`
- Worker leest skill metadata, bepaalt relevante categorieën, draait cases, slaat resultaat op
- Resultaat wordt toegevoegd aan het deployment approval flow

## Constraints

- Geen nieuwe npm dependencies — gebruik alleen bestaande (better-sqlite3, node fetch)
- Ollama calls gaan via workstation (`http://192.168.1.28:11434`) — geen lokale modellen
- Judge model is `qwen2.5:14b-instruct-q4_K_M` (al op workstation aanwezig)
- Respecteer bestaande Djimitflo architectuur (services pattern, routes pattern)
- TypeScript strict mode, ESM modules
- Schrijf vitest tests voor de service layer

## Acceptatie Criteria

- [ ] `openmythos-eval-service.ts` laadt cases en draait evaluaties
- [ ] `governance-guard-service.ts` blokkeert deployment bij score < 3.0
- [ ] API routes zijn bereikbaar en retourneren correcte responses
- [ ] Database migratie werkt (up + down)
- [ ] Worker pipeline bevat `benchmark_eval` stap
- [ ] Tests passen (`npm run test`)
- [ ] Lint clean (`npm run lint`)
- [ ] Type-check clean (`npm run type-check`)

## Referentie bestanden

- `packages/server/src/services/agent-assurance-service.ts` — bestaand eval patroon
- `packages/server/src/services/loop-service.ts` — governance_guard role definitie
- `packages/server/src/routes/agents.ts` — route patroon
- `/Users/dlandman/OpenMythos/openmythos-benchmark/scripts/judge.py` — judge logica
- `/Users/dlandman/OpenMythos/openmythos-benchmark/cases/corpus.jsonl` — 275 cases
