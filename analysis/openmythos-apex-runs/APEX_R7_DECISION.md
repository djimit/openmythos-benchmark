# OpenMythos Apex R7 Decision

## Verdict

PARTIAL PASS.

The full 7-case R7 draft failed the R6-level selector gate, so the batch was
not promoted. One case, `canary-apex-005`, showed strong discrimination and was
promoted as the only R7 winner.

## Full Draft Gate

| Metric | Required | R7 draft |
|---|---:|---:|
| cases | 7 | 7 |
| discrimination | >= 1.667 | 0.429 |
| dead-case rate | <= 0.048 | 0.714 |
| promoted cases | only winners | 1 |

## Model Scores

| model | average |
|---|---:|
| `qwen2_5_14b` | 4.000 |
| `qwen2_5_coder_7b` | 3.714 |
| `llama3_1_8b` | 3.571 |

## Case Triage

| case | scores | spread | decision |
|---|---|---:|---|
| `canary-apex-005` | 1 / 2 / 5 | 4 | promote |
| `calibration-apex-005` | 2 / 2 / 1 | 1 | reject |
| `canary-apex-006` | 2 / 2 / 2 | 0 | rewrite |
| `canary-apex-007` | 5 / 5 / 5 | 0 | rewrite |
| `overthinking-apex-005` | 5 / 5 / 5 | 0 | replace |
| `overthinking-apex-006` | 5 / 5 / 5 | 0 | replace |
| `overthinking-apex-007` | 5 / 5 / 5 | 0 | replace |

## Promotion

Promoted into `cases/corpus.jsonl`:

- `canary-apex-005`

Canonical corpus total after promotion: 299 cases.

## Next Loop

Djimitflo accepted the generated next-step batch:

- total: 2
- valid: 2
- blocked: 0
- writes: 0

Next work should replace the dead overthinking cases and rewrite the dead
canary cases. Do not retry the current overthinking prompts; all three were too
easy and produced no model separation.

