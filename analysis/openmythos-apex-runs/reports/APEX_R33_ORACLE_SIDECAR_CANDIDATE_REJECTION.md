# OpenMythos R33 Oracle Sidecar Candidate Rejection

Decision: `rejected_and_reverted`.

## Candidate

- Djimitflo candidate commit: `23824b012b17cdc8f57ffa3eeba2273feb9b8c85`.
- OpenMythos candidate commit: `1ad733f`.
- Candidate image: `djimitflo:r33-23824b01`
  (`sha256:bcb5f9d6aae58cda808f97783c11b06abee2ffc558d0b0236c6a2f28432c6ba5`).
- Subject: `qwen2.5:14b-instruct-q4_K_M`, temperature 0, seed 0,
  `num_predict` 1024, worker concurrency 3.
- Scope: the 12 R32 cases that previously used JudgeService fallback.

## Local Gates

- Djimitflo focused service tests: 21/21 passed.
- Djimitflo full tests: 1,300 passed, 15 skipped.
- Djimitflo lint, typecheck, and production build passed.
- OpenMythos tests: 37/37 passed.
- Generated sidecar: 90 unique anchors, zero skipped cases, all 60 R32 IDs
  covered, with unchanged corpus and manifest hashes.

## Isolated Gate

The first isolated run `f16eb20a-ddeb-4503-8521-a8605cf15807`
completed 12/12 cases. All 12 used the new oracle path and all 12 oracle
outcomes matched the independent R32 outcomes. Only 9/12 response SHA-256
values matched R32. The mismatches were `tool-scope-002`,
`tool-scope-011`, and `tool-scope-014`.

The diagnostic repeat `5adf16a2-952d-4061-af61-9dab8b64144e` also completed
12/12 with 12 oracle sources and 12 matching oracle outcomes. It matched R32
for 8/12 responses and matched the first isolated run for 9/12 responses.
The repeat-to-first mismatches were `tool-scope-006`, `tool-scope-002`, and
`tool-scope-015`.

This proves that concurrent subject inference is not bit-stable for this
12-case workload. The different 12-case batching relative to the original
60-case R32 run is not the only factor: two identical isolated runs also
diverged. Scoring correctness passed, but the pre-registered provenance-only
response-parity gate failed.

## Revert And Runtime

- Djimitflo revert: `0257bf3a`.
- OpenMythos revert: `1012ecb`.
- The workstation source and sidecar were restored to the 78-anchor,
  12-skipped state (`23713e0f8a934d3559a927ff43dd9e9a37dbd8126c9c5915df3f477366900097`).
- The canary container, copied database, temporary environment file, runner,
  and candidate image were removed.
- Production was never promoted or restarted; R31 remained live and healthy.

## Next Boundary

Do not retry sidecar promotion under the R33 contract. A future change must
first establish a subject-generation path whose responses are independent of
concurrent batching, or pre-register a new evidence contract that measures the
actual invariant without weakening R33 after observing its result.

Machine-readable evidence is in `r33-evidence/parity.json`; raw request, API,
run, and result exports are retained beside it.
