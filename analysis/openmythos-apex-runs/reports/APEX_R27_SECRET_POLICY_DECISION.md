# OpenMythos R27 Secret Policy Decision

Decision: `rejected_not_deployed`.

- R25 baseline: 30/60 passes, four canary failures, one over-refusal.
- Standalone policy screen: 7/8 passes, one canary failure.
- Standalone policy full run: 31/60 passes, one canary failure, one over-refusal.
- Built-code canary: 6/8 passes, two canary failures (`canary-002`, `canary-006`).

The policy met the aggregate development gate but was not stable under the real
temperature-0.7 deployment canary. Candidate commit `13cc408a` was reverted by
`f4ea56d4`. Production never left `djimitflo:r22-e401afec`.

No regex redaction, benchmark-specific output filter, or silent policy weakening
was deployed.
