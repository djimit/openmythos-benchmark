# Related Work

## Foundational Papers

| Paper | Relevance |
|-------|-----------|
| Bender et al. (2021) — On the Dangers of Stochastic Parrots | Foundational framework for LLM risk taxonomy |
| Bommasani et al. (2021) — Opportunities and Risks of Foundation Models | Comprehensive foundation model risk survey |
| Wei et al. (2023) — Chain-of-Thought Prompting Elicits Reasoning | Loop sensitivity methodology |
| Wei et al. (2024) — Jailbroken: How Does LLM Safety Training Fail? | Injection category foundation |
| Perez & Gontijo-Lopes (2022) — Red Teaming with Language Models | Canary case methodology |
| Park et al. (2023) — AI Deception: A Survey | Hallucination category grounding |

## Benchmarks

| Benchmark | Scope | Relation |
|-----------|-------|----------|
| TruthfulQA (Lin et al. 2022) | Factual accuracy | Subset of our hallucination category |
| MMLU (Hendrycks et al. 2021) | Multitask understanding | Complementary — we test governance, not knowledge |
| HELM (Liang et al. 2023) | Holistic evaluation | Broader scope, less governance focus |
| AgentBench (Liu et al. 2023) | Agent capabilities | Overlaps with tool-scope category |
| DecodingTrust (Wang et al. 2024) | Trustworthiness | Closest analog — complements our governance focus |

## Frameworks

| Framework | Application |
|-----------|------------|
| NIST AI RMF (2023) | Category selection rationale |
| EU AI Act (2024) | Regulatory grounding for hierarchy cases |
| OWASP LLM Top 10 (2025) | Injection and tool-scope taxonomy |

## Key Distinctions

OpenMythos differs from existing benchmarks by:
1. **Governance-first**: Focus on organizational/regulatory compliance, not just capability
2. **Loop sensitivity**: Explicitly tests reasoning depth effects
3. **Real-world grounding**: Every case maps to documented incident
4. **Academic references**: Required for every case, not optional
5. **Difficulty calibration**: 5-level scale with community validation plan
