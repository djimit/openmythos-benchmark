# OpenMythos R21 Evidence-Closed CUDA Smoke

## Decision

- runtime: `workstation`
- GPU: `NVIDIA GeForce RTX 2060 SUPER`
- device: `cuda`
- model: `Qwen/Qwen2.5-0.5B-Instruct`
- training steps: `5`
- train loss: `4.182562637329101`
- numerically stable: `yes`
- adapter saved: `yes`
- baseline oracle pass: `0/10`
- post-training oracle pass: `0/10`
- over-refusal before/after: `0/0`
- promotion status: `smoke_only`

The smoke proves the CUDA training and paired-evaluation pipeline, but it does
not prove behavioral improvement. The adapter is not eligible for promotion.

## Evidence Hashes

- adapter: `daae62c61813718e16acbe3f33791e36108ebdddb10a0c2a4bb1d5c604fc95a2`
- SFT: `2f841360277dd26d7496196fa560c191bb761c9e13de2f2ec3f8d5488dee55b0`
- DPO: `f6c064d7e52c373af92d22c6b812661e5f38cfcbddb828ac31c460558fcef0c2`
- holdout: `774d1699a9660a106ba5b88a87d8df06d56d353c0357d55c84450829f7927706`

## Djimitflo Production Proof

- image revision: `85d46e8dce`
- health/deep health: `200/healthy`
- MCP servers running: `9`
- OpenMythos run: `04cc910f-391e-4559-9049-81d499a3803c`
- subject model: `qwen2.5:14b-instruct-q4_K_M`
- category: `overthinking`
- completed/persisted cases: `25/25`
- score: `1.96/5`
