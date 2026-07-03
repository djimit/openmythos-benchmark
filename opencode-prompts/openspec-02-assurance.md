## Why

Agent assurance scores zijn nu intern (zelf-evaluatie). Deze change voegt externe governance scores toe gebaseerd op OpenMythos benchmark, zodat agents een objectieve, reproduceerbare governance score krijgen.

## What Changes

- `agent-assurance-service.ts` — `runGovernanceEval()`, `getGovernanceTrend()`
- Assurance routes uitbreiden met governance data
- Degradatie-alerts bij score-daling > 0.5
- `generateGovernanceReport()` voor klant rapporten
- `EvalRunRecord` uitbreiden met `source`, `benchmark_version`, `judge_model`

## Non-Goals

- Geen nieuwe notificatie infrastructure — reuse bestaande evidence tabel
- Geen PDF export (alleen JSON)

## Success Criteria

- Assurance endpoint retourneert governance scores
- Degradatie-alerts werken
- Rapport genereert per-categorie aanbevelingen
- Tests + lint + type-check clean
