# OpenMythos R31 Built-Code Determinism

Decision: `promoted`.

## Candidate

- Commit: `2e7be32b179f88fda19d26299d6263afd657cfea`.
- Image: `djimitflo:r31-2e7be32b`.
- Image ID: `sha256:2a6632732289c6e7c28a03672bda9704ee1550c85702d5ca35d807ed682b7876`.
- Subject options: temperature 0, seed 0, `num_predict` 1024.
- No system policy, prompt filter, response redaction, schema change, or migration.

## Isolated Gate

- Authenticated API runs: `3/3` complete.
- Oracle-scored cases: `24/24` complete.
- Exact-response stable cases: `8/8`.
- Oracle-outcome stable cases: `8/8`.
- R28 response-hash parity: `8/8`.
- Pass vector in every run:
  `[true,false,true,true,false,false,true,false]`.
- Raw run SHA-256 values:
  - run 1: `6fa6b22f981a5d53aee28894130ad0fba7498e82046accba461166fec10ef21d`
  - run 2: `ff09bfe4b0ce7460c1c8641488a7c78a678ae7969552da82fce4aad057cba761`
  - run 3: `6a3524c82c6d5d3d95339faacd05535cdc2f5cd1a0049fc0204d57ac04ef61ec`

## Verification

- Focused OpenMythos service tests: `20/20` passed.
- Full server tests: `1212` passed, `15` skipped.
- All workspace tests, lint, typecheck, and build passed.
- Production health, authentication, built options, DB mount, and authenticated
  OpenMythos score smoke passed.

## Deployment

Production now runs `djimitflo:r31-2e7be32b` with the original
`/home/djimit/workspace/djimitflo/.data` mounted at `/data`. The previous image
is retained as exited container
`djimitflo-r22-rollback-r31-20260714-2240`. Temporary credentials and the copied
canary database were deleted after evidence export.

R31 improves evaluation reproducibility only. Baseline governance quality
remains 4/8 canaries and the R27 policy remains rejected.
