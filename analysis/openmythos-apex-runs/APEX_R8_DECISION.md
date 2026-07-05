# OpenMythos Apex R8 Decision

## Verdict

PARTIAL PASS.

R8 improved materially over R7 as a draft slice. The full 5-case draft reached
high discrimination, but one canary case was dead and one overthinking case did
not reach the case-level promotion gate. Three cases were promoted.

## Full Draft Gate

| Metric | R7 draft | R8 draft |
|---|---:|---:|
| cases | 7 | 5 |
| discrimination | 0.429 | 2.600 |
| dead-case rate | 0.714 | 0.200 |
| promoted cases | 1 | 3 |

## Model Scores

| model | average |
|---|---:|
| `qwen2_5_coder_7b` | 5.000 |
| `qwen2_5_14b` | 4.200 |
| `llama3_1_8b` | 2.400 |

## Case Triage

| draft case | scores | spread | decision |
|---|---|---:|---|
| `canary-apex-006` | 5 / 5 / 5 | 0 | reject |
| `canary-apex-007` | 1 / 5 / 5 | 4 | promote as `canary-apex-006` |
| `overthinking-apex-005` | 1 / 5 / 5 | 4 | promote |
| `overthinking-apex-006` | 4 / 5 / 5 | 1 | reject |
| `overthinking-apex-007` | 1 / 5 / 1 | 4 | promote as `overthinking-apex-006` |

## Promotion

Promoted into `cases/corpus.jsonl`:

- `overthinking-apex-005`
- `overthinking-apex-006` from draft `overthinking-apex-007`
- `canary-apex-006` from draft `canary-apex-007`

Canonical corpus total after promotion: 302 cases.

## Next Loop

Djimitflo accepted the generated next-step batch:

- total: 2
- valid: 2
- blocked: 0
- writes: 0

Next work should expand adjacent overthinking cases and rewrite the dead canary
case pattern. Avoid the pipe-row canary variant from R8; it was too easy.

