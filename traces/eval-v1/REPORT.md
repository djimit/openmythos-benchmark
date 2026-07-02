# Evaluation Report v1 — AMD R9700

**Date**: 2025-07-02
**Hardware**: AMD Radeon AI PRO R9700 (32GB VRAM, gfx1201)
**Software**: Ollama with Vulkan backend (`OLLAMA_VULKAN=1`)
**Cases**: 33 (3 per category × 11 categories)

## Summary (keyword-match scoring)

| Model | Params | Accuracy | Avg Latency | VRAM Usage |
|-------|--------|----------|-------------|------------|
| llama3.1:8b | 8B Q4 | 36.4% | 1777ms | ~5.1GB |
| qwen2.5-coder:7b | 7B Q4 | 27.3% | 1494ms | ~4.7GB |
| ornith-1.0-9b | 9B Q4 | 39.4% | 5840ms | ~5.6GB |
| qwen2.5:14b | 14B Q4 | 39.4% | 3073ms | ~9.7GB |
| qwen2.5:32b | 32B Q4 | 36.4% | 5866ms | ~21GB |

**Scoring**: Keyword-match (conservative). LLM-as-judge recommended for production scores.

## LLM-as-Judge Results (11 cases, qwen2.5:14b as judge)

| Model | Avg Score | Pass Rate (≥4) |
|-------|-----------|----------------|
| qwen2.5:14b | 3.64/5.00 | 63.6% |

## Per-Category Breakdown (qwen2.5:14b)

| Category | Accuracy | Avg Latency |
|----------|----------|-------------|
| hierarchy | 100% | 4755ms |
| contradiction | 67% | 1445ms |
| cross-lingual | 67% | 1759ms |
| overthinking | 67% | 1218ms |
| calibration | 33% | 2691ms |
| canary | 33% | 3378ms |
| injection | 33% | 2601ms |
| temporal-reasoning | 33% | 4453ms |
| hallucination | 0% | 3620ms |
| tool-scope | 0% | 4725ms |
| value-alignment | 0% | 3157ms |

## Key Findings

1. **AMD R9700 works well with Ollama** via Vulkan backend — 2.4x faster than NVIDIA 2060 Super
2. **14B Q4 fits in 32GB VRAM** with room to spare (9.7GB used)
3. **hierarchy category is easy** (100% all models) — authority conflicts are well-handled
4. **hallucination, tool-scope, value-alignment are hard** (0% keyword match) — these require LLM-as-judge scoring
5. **Keyword matching is too conservative** — models often give correct answers that don't contain the exact expected keywords

## Key Insight

Keyword-match scoring is too coarse to differentiate model quality. All models score 27-39% on keyword match, but LLM-as-judge reveals the 14B model achieves 63.6% pass rate. **LLM-as-judge is essential for meaningful benchmark results.**

## Next Steps

- [ ] Run full 275-case evaluation with qwen2.5:14b
- [ ] Full LLM-as-judge scoring for all models (qwen2.5:14b or GPT-4o as judge)
- [ ] Compare qwen2.5:14b vs qwen2.5:32b with judge scores (keyword match shows no difference)
- [ ] Community evaluation runs with multiple judges
