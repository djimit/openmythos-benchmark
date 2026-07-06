# OpenMythos Discrimination Baseline

**Date**: 2026-07-05
**Corpus**: 309 cases | 11 categories
**Models**: llama3.1:8b vs qwen2.5:32b-instruct-q4_K_M
**Judge**: GPT-5 strict (via LiteLLM)

## Per-Category Discrimination

| Category | Spread | Dead Rate | n | Status |
|----------|--------|-----------|---|--------|
| tool-scope | 1.91 | 0.38 | 21 | Strongest |
| contradiction | 1.84 | 0.32 | 19 | Strong |
| injection | 1.68 | 0.32 | 25 | Strong |
| overthinking | 1.70 | 0.35 | 20 | Strong |
| temporal-reasoning | 1.64 | 0.48 | 25 | Good |
| cross-lingual | 1.56 | 0.48 | 25 | Good |
| canary | 1.22 | 0.59 | 37 | Good |
| value-alignment | 1.20 | 0.31 | 35 | Good |
| calibration | 1.18 | 0.35 | 34 | Good |
| hierarchy | 0.88 | 0.47 | 34 | Weak |
| hallucination | 0.71 | 0.65 | 34 | Weakest |

## Overall

- **llama3.1:8b average**: 2.42/5.00
- **qwen2.5:32b average**: 2.79/5.00
- **Overall spread**: 0.37
- **Dead case rate**: 0.44

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

## Next Steps for Improvement

1. **Hallucination** (spread=0.71): Add "confident wrong answer" cases where one model knows and the other guesses
2. **Hierarchy** (spread=0.88): Add "conflicting equal authority" cases
3. **Probabilistic judging**: 3 runs per case to reduce judge noise
4. **Multi-model judge**: Combine GPT-5 + local judge for robustness
