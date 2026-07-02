# Methodology

## Design Principles

1. **Grounded in real incidents**: Every case maps to a documented real-world failure or governance challenge
2. **Academic references**: Each case cites peer-reviewed literature or established frameworks
3. **Difficulty calibration**: 5-level scale from trivial (L1) to PhD-level nuance (L5)
4. **Loop sensitivity**: Cases marked `loop_sensitive` test whether deeper reasoning changes outcomes
5. **Category coverage**: 11 orthogonal dimensions of AI governance

## Category Selection Rationale

The 11 categories were selected to cover the full spectrum of LLM governance risks identified in:

- NIST AI Risk Management Framework (2023)
- EU AI Act risk taxonomy (2024)
- OWASP Top 10 for LLM Applications (2025)
- Academic literature on AI alignment (see RELATED_WORK.md)

### Original 6 categories (v0.1 → v1.0 enriched)
- **hierarchy**: Authority/privilege escalation — core to organizational governance
- **injection**: Prompt injection — the most documented attack vector
- **tool-scope**: Tool boundary violations — critical for agentic systems
- **contradiction**: Logical paradoxes — tests reasoning integrity
- **canary**: Information leakage — measures context contamination
- **overthinking**: Unnecessary elaboration — measures efficiency and directness

### New 5 categories (v1.0)
- **hallucination**: Factual fabrication — the most pervasive LLM failure mode
- **calibration**: Confidence calibration — essential for trustworthy deployment
- **value-alignment**: Ethical reasoning — tests normative judgment under uncertainty
- **temporal-reasoning**: Date/time reasoning — critical for legal/compliance applications
- **cross-lingual**: Multilingual legal terminology — essential for EU governance

## Case Construction Process

1. **Identify failure mode**: Select a specific, documented failure pattern
2. **Ground in literature**: Find academic reference(s) describing the phenomenon
3. **Map to real incident**: Identify a real-world analog
4. **Write prompt**: Craft a prompt that elicits the failure mode
5. **Define expected behavior**: Specify what a well-governed model should do
6. **Set difficulty**: Calibrate based on required reasoning depth
7. **Peer review**: Minimum 2 reviewers per case

## Evaluation Protocol

See [docs/EVALUATION_PROTOCOL.md](docs/EVALUATION_PROTOCOL.md) for detailed evaluation procedures.

## Limitations

See [LIMITATIONS.md](LIMITATIONS.md) for known limitations and caveats.
