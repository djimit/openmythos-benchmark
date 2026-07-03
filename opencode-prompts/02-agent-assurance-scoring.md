# Prompt 2: Agent Assurance Governance Scoring

## Context

Djimitflo's `agent-assurance-service.ts` heeft al `EvalRunRecord` met interne evaluatie scores. Die scores komen nu uit zelf-evaluatie door de agent. De OpenMythos Governance Benchmark biedt een externe, objectieve meetlat voor governance-kwaliteit.

**Doel**: Voeg een externe governance benchmark score toe aan de agent assurance layer. Agents krijgen naast hun interne eval score ook een objectieve governance score gebaseerd op gestandaardiseerde cases.

## Opdracht

Implementeer het volgende in Djimitflo:

### 1. Assurance Service uitbreiding (`packages/server/src/services/agent-assurance-service.ts`)

- Voeg `governance_score` en `governance_eval_id` toe aan `AgentAssuranceRecord`
- Nieuwe methode `runGovernanceEval(agentId: string): Promise<GovernanceEvalResult>`:
  - Roept OpenMithos eval service uit (Prompt 1) voor alle 11 categorieën
  - Slaat resultaat op als `EvalRunRecord` met `span_type: 'eval'`
  - Update `AgentAssuranceRecord.governance_score` met overall judge score
- Nieuwe methode `getGovernanceTrend(agentId: string, limit: number = 10)`:
  - Retourneert historische governance scores over tijd
  - Toont verbetering/verslechtering per categorie

### 2. Assurance Dashboard data (`packages/server/src/routes/assurance.ts`)

- Bestaande `/api/assurance/:agentId` endpoint uitbreiden met:
  - `governance_score` (overall 0-5)
  - `governance_categories` (per-categorie scores)
  - `governance_trend` (laatste 5 runs)
  - `governance_status` | 'pass' | 'warn' | 'fail' (gebaseerd op threshold)

### 3. Eval Run Record uitbreiding

- Voeg `source` veld toe aan `EvalRunRecord`: `'internal'` | `'openmythos_benchmark'`
- Voeg `benchmark_version` veld toe (bijv. `'1.0'`)
- Voeg `judge_model` veld toe (bijv. `'qwen2.5:14b-instruct-q4_K_M'`)

### 4. Notificatie bij degradatie

- Als governance score daalt met > 0.5 tussen opeenvolgende runs → trigger alert
- Alert wordt opgeslagen in `agent_evidence` tabel met type: `'governance_degradation'`
- Optioneel: webhook notificatie (bestaand notificatie patroon volgen)

### 5. Rapportage

- Nieuwe methode `generateGovernanceReport(agentId: string): Promise<GovernanceReport>`:
  - Samenvatting met overall score, per-categorie breakdown, trend
  - Aanbevelingen per zwakke categorie (bijf "injection: 2.1/5 — overweeg prompt-hardening")
  - Exporteerbaar als JSON voor klant rapporten

## Constraints

- Bouw voort op Prompt 1 (openmythos-eval-service moet bestaan)
- Geen nieuwe npm dependencies
- Respecteer bestaande assurance service architectuur
- TypeScript strict mode, ESM modules
- Schrijf vitest tests voor nieuwe methoden

## Acceptatie Criteria

- [ ] `AgentAssuranceRecord` bevat `governance_score` en `governance_eval_id`
- [ ] `runGovernanceEval` draait OpenMithos cases en slaat resultaten op
- [ ] `getGovernanceTrend` retourneert historische data
- [ ] Assurance endpoint retourneert governance data
- [ ] Degradatie-alert werkt bij score-daling > 0.5
- [ ] Governance rapport genereert correcte aanbevelingen
- [ ] Tests passen
- [ ] Lint + type-check clean

## Referentie bestanden

- `packages/server/src/services/agent-assurance-service.ts` — bestaande assurance logic
- `packages/server/src/routes/assurance.ts` — bestaande assurance routes
- `packages/server/src/services/openmythos-eval-service.ts` — uit Prompt 1
