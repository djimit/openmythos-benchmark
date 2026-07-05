# OpenMythos Apex R6 Decision

## Verdict

PASS as a 21-case apex selector candidate.

R6 improves the last accepted 21-case baseline by preserving the 21-case shape,
reducing dead cases, and increasing measured model separation.

After final human approval, the 13 selected R6 cases that were not already in
the canonical corpus were appended to `cases/corpus.jsonl`. The existing corpus
was preserved, producing a 298-case canonical corpus. This includes 10
OpenFable rows that were already present in the working corpus mutation.
The canonical promoted rows were renumbered where needed to satisfy the
existing sequential ID validator.

## Gate Result

| Gate | Required | R6 |
|---|---:|---:|
| cases | 21 | 21 |
| discrimination | >= 1.143 | 1.667 |
| dead-case rate | <= 0.095 | 0.048 |
| category balance | no hard gate | 7 / 7 / 7 |
| Djimitflo preview | valid=total, blocked=0, writes=0 | valid=2/2, blocked=0, writes=0 |
| canonical promotion | preserve existing corpus | 13 R6 rows plus existing OpenFable rows |

## Selected Corpus

`analysis/openmythos-apex-runs/focused-corpus/apex-r6-selected-21.jsonl`

Selected IDs:

- `overthinking-001`
- `overthinking-002`
- `overthinking-003`
- `calibration-002`
- `calibration-003`
- `canary-001`
- `canary-002`
- `canary-003`
- `overthinking-apex-002`
- `overthinking-apex-006`
- `overthinking-apex-007`
- `overthinking-apex-008`
- `calibration-apex-001`
- `calibration-apex-002`
- `calibration-apex-004`
- `calibration-apex-005`
- `calibration-apex-006`
- `canary-apex-002`
- `canary-apex-003`
- `canary-apex-004`
- `canary-apex-007`

## Model Scores

| model | average |
|---|---:|
| `qwen2_5_14b` | 4.190 |
| `qwen2_5_coder_7b` | 3.762 |
| `llama3_1_8b` | 2.524 |

## Evolution Signal

Keep calibration in the selected candidate, but rewrite the one dead selected
case, `calibration-apex-005`, in the next draft pass.

Expand the categories that prove useful:

- `overthinking`: spread 3.00, dead rate 0.00
- `canary`: spread 2.71, dead rate 0.00

## Promotion

Promoted ID mapping:

- `overthinking-apex-002` -> `overthinking-apex-001`
- `overthinking-apex-006` -> `overthinking-apex-002`
- `overthinking-apex-007` -> `overthinking-apex-003`
- `overthinking-apex-008` -> `overthinking-apex-004`
- `calibration-apex-001` -> `calibration-apex-001`
- `calibration-apex-002` -> `calibration-apex-002`
- `calibration-apex-004` -> `calibration-apex-003`
- `calibration-apex-005` -> `calibration-apex-004`
- `calibration-apex-006` -> `calibration-apex-005`
- `canary-apex-002` -> `canary-apex-001`
- `canary-apex-003` -> `canary-apex-002`
- `canary-apex-004` -> `canary-apex-003`
- `canary-apex-007` -> `canary-apex-004`
