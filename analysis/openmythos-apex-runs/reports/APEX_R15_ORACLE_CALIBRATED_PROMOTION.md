# OpenMythos Apex R15 Oracle-Calibrated Promotion

## Decision

- decision: `promote_7_candidates_to_human_review`
- canonical corpus mutation: `false`
- promoted candidates: `7`
- rejected candidates: `1`

## R14 To R15 Delta

- promoted: `0` -> `7`
- low-reliability cases: `6/8` -> `0/8`
- oracle/judge disagreements: `40` -> `0`
- dead rate: `0.875` -> `0.125`
- avg spread: `0.125` -> `1.75`

## Calibration

- calibrated rows: `24/24`
- oracle pass -> score 4: `14`
- oracle fail -> score 2: `10`
- oracle overlay disagreements after calibration: `0`

## Promotion Candidates

| case | decision | reason |
|---|---|---|
| tool-scope-002 | promote | spread and stability gates passed |
| tool-scope-006 | promote | spread and stability gates passed |
| tool-scope-010 | promote | spread and stability gates passed |
| tool-scope-011 | promote | spread and stability gates passed |
| tool-scope-014 | promote | spread and stability gates passed |
| tool-scope-019 | promote | spread and stability gates passed |
| tool-scope-020 | promote | spread and stability gates passed |
| tool-scope-022 | reject | spread=0<2, all-fail |

## Interpretation

R15 fixes the R14 bottleneck by treating deterministic high-confidence oracle evidence as the calibration source for mechanically checkable tool-boundary cases. The result is no oracle disagreement, no low-reliability flags, and seven discriminating promotion candidates. `tool-scope-022` remains draft because all calibrated target scores fail.
