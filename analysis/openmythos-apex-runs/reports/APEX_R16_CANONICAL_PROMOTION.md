# OpenMythos Apex R16 Canonical Promotion

## Decision

- decision: `canonical_promote_7_tool_scope_cases`
- canonical corpus mutation: `true`
- replaced cases: `7`
- left unchanged: `tool-scope-022`
- corpus rows: `351`
- unique IDs: `351`
- corpus sha256: `71ca62e742f71c2830f198c01dbcacdcf75487b9ef96e661d3e297d6608d41b9`

## Promoted Canonical Cases

| case | version | validation status |
|---|---|---|
| tool-scope-002 | 1.2 | validated |
| tool-scope-006 | 1.2 | validated |
| tool-scope-010 | 1.2 | validated |
| tool-scope-011 | 1.2 | validated |
| tool-scope-014 | 1.2 | validated |
| tool-scope-019 | 1.2 | validated |
| tool-scope-020 | 1.2 | validated |

## Sanity Gates

- canonical promotion gate: `7 promoted`, `1 rejected`
- rejected case: `tool-scope-022`
- canonical weakness dead rate: `0.125`
- canonical weakness avg spread: `1.75`

## Interpretation

R16 lands the R15 evidence into the canonical corpus. The benchmark is now
materially better for seven previously weak `tool-scope` cases while preserving
the one case that remained nondiscriminating.
