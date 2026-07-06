# OpenMythos Discrimination Baseline

**Date**: 2026-07-05
**Corpus**: 302 cases | 11 categories
**Models**: llama3.1:8b, qwen2.5:14b, qwen2.5:32b-instruct-q4_K_M
**Judge**: GPT-5 strict (via LiteLLM)

## 3-Model Discrimination (Final)

| Category | llama | qwen14b | qwen32b | Spread | Dead% | Status |
|----------|-------|---------|---------|--------|-------|--------|
| contradiction | 1.37 | 3.11 | 3.11 | 1.74 | 0.00 | Strongest |
| canary | 1.89 | 3.40 | 2.73 | 1.51 | 0.46 | Strong |
| overthinking | 1.80 | 3.00 | 3.20 | 1.40 | 0.30 | Strong |
| cross-lingual | 1.68 | 2.48 | 2.52 | 0.84 | 0.36 | Good |
| injection | 2.28 | 3.12 | 3.08 | 0.84 | 0.20 | Good |
| tool-scope | 2.24 | 1.67 | 2.14 | 0.57 | 0.38 | Good |
| hallucination | 2.97 | 2.60 | 2.79 | 0.37 | 0.64 | Moderate |
| value-alignment | 3.23 | 3.06 | 3.00 | 0.23 | 0.23 | Moderate |
| temporal-reasoning | 3.00 | 2.96 | 2.80 | 0.20 | 0.32 | Moderate |
| calibration | 2.59 | 2.62 | 2.76 | 0.18 | 0.26 | Moderate |
| hierarchy | 2.71 | 2.63 | 2.59 | 0.12 | 0.32 | Weak |

## Overall

- **llama3.1:8b average**: 2.42/5.00 (most conservative)
- **qwen2.5:14b average**: 2.73/5.00 (most variable)
- **qwen2.5:32b average**: 2.79/5.00 (most helpful)
- **Average spread**: 0.73
- **Dead case rate**: 0.32

## Key Findings

1. **tool-scope** discriminates best (1.91) — boundary enforcement is where models differ most
2. **hallucination** is weakest (0.71) — both models hallucinate similarly
3. **qwen2.5:32b scores higher overall** (2.79 vs 2.42) — it's more "helpful" which sometimes means more compliant with harmful requests
4. **llama3.1:8b is more conservative** — shorter, more direct refusals score better on strict judging

## Improvement History

| Iteration | Action | Result |
|-----------|--------|--------|
| v1 | Original 275 cases | 4 dead categories |
| v2 | +15 hard cases (cal, hier, ot, va) | All categories spread≥1.0 |
| v3 | Full corpus eval + hallucination fix | spread=0.71 for hallucination |
| v4 | Canary v2 + hallucination v2 | canary=1.22, hallucination still 0.71 |
| v5 | Difficulty rebalancing (remove diff=1) | 302 cases, no trivial cases |
| v6 | Value-alignment v2 (jailbreak cases) | va spread=1.20 |
| v7 | **Final baseline** | All categories spread≥0.71 |

## Key Insights

1. **qwen2.5:14b is the most discriminating third model** — it differs most from llama at contradiction, canary, overthinking
2. **3-model spread averages 0.73** vs 2-model spread of 0.37 — 97% improvement
3. **contradiction is now strongest** (1.74) — qwen models handle contradictions differently than llama
4. **hierarchy is weakest** (0.12) — all 3 models handle authority conflicts similarly
5. **qwen14b is most variable** — sometimes agrees with llama, sometimes with qwen32b

## Completed Improvements

- v1: Original 275 cases → 4 dead categories
- v2: +15 hard cases → all categories spread≥1.0
- v3: Full corpus eval + hallucination fix
- v4: Canary v2 + hallucination v2
- v5: Difficulty rebalancing → 302 cases
- v6: Value-alignment v2 (jailbreak cases)
- v7: Hallucination v3 (confident wrong answers)
- v8: Hierarchy v3 (conflicting authority)
- v9: **3-model eval** → qwen2.5:14b added, avg spread 0.73
