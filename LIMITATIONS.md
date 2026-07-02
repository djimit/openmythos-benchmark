# Limitations

## Known Constraints

### 1. English-Centric Prompts
All 275 cases are in English. The cross-lingual category tests translation of
terminology but does not evaluate non-English reasoning quality. Non-English
prompt injection, cultural context, and locale-specific governance are out of scope.

### 2. Static Corpus
This is a static benchmark. It does not capture:
- Emerging attack vectors (new jailbreak techniques post-release)
- Model-specific behaviors (each model has unique failure modes)
- Multi-turn adversarial strategies (all cases are single-turn)

### 3. Simplified Evaluation
The built-in `compare.py` uses keyword matching. For production evaluation:
- Use LLM-as-judge with calibrated scoring rubrics
- Include human expert review for difficulty ≥4 cases
- Run multiple seeds and aggregate

### 4. Difficulty Calibration
Difficulty levels are expert-estimated, not empirically calibrated. Actual model
performance may not correlate with assigned difficulty. Post-release community
data will enable IRT-based recalibration.

### 5. Western Legal Bias
Legal references are primarily EU/US-centric (GDPR, NIST, FCPA). Other jurisdictions
(China PIPL, Brazil LGPD, India DPDP) are underrepresented.

### 6. No Multimodal Cases
All cases are text-only. Image, audio, and video governance failures are out of scope.

### 7. Single-Agent Focus
Cases test individual model responses. Multi-agent coordination failures,
emergent behaviors in agent swarms, and tool-chain attacks are not covered.

## Planned for v2.0

- [ ] Multi-turn adversarial cases
- [ ] Non-English prompt sets (DE, FR, NL, ZH)
- [ ] Multimodal governance cases
- [ ] Agent-chain failure modes
- [ ] Empirically calibrated difficulty (IRT)
- [ ] Expanded legal jurisdiction coverage
