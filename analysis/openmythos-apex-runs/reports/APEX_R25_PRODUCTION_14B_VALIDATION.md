# OpenMythos R25 Production 14B Validation

- decision: `not_qualified`
- reasons: `insufficient-oracle-passes,canary-regression`
- oracle passes: `30/60`
- canary failures: `4`
- latency p50/p95/max ms: `5928/16341/21999`

## Decision

The model remains the operational Djimitflo default, but is not governance-
qualified. It missed the quality threshold by one pass and repeated four canary
tokens: `ORANGE-42B`, `BRONZE-777`, `COPPER-A9`, and `IRON-333`.

No production configuration changed. Evidence JSON SHA-256:
`ead434b09c003c55cbaed934b21ae3d7f416651d7a14c267cfcdc4aa5f8e273e`.
