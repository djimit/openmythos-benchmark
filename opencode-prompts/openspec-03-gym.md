## Why

Skill evolution gym traint skills op functionaliteit, niet op governance. Deze change voegt een governance curriculum toe zodat skills certificering nodig hebben voordat ze gedeployed worden.

## What Changes

- `gym-governance-curriculum.ts` — 4-fasen curriculum (basic → expert)
- Gym evaluation type: `governance_benchmark`
- Evolution pipeline: governance certificering vereist
- Skills tabel: `governance_phase`, `governance_certified`, `governance_scores`
- Automatische re-test bij skill updates
- API routes: `GET /api/gym/governance/:skillId`, `POST /api/gym/governance/:skillId/run`

## Non-Goals

- Geen auto-retraining bij fail
- Geen multi-model judge
- Gym runs asynchonous (5-15 min acceptabel)

## Success Criteria

- Curriculum indeelt cases correct in fasen
- Skills promoveren alleen na governance certificering (≥ 3.5/5.0)
- Her-test bij updates werkt
- Tests + lint + type-check clean
