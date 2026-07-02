# Changelog

## [1.0.0] - 2025-07-02

### Added
- 275 cases across 11 categories (25 per category)
- 6 original categories enriched with PhD-level fields:
  - hierarchy, injection, tool-scope, contradiction, canary, overthinking
- 5 new categories (125 cases):
  - hallucination, calibration, value-alignment, temporal-reasoning, cross-lingual
- JSON Schema validation (corpus-schema.json)
- Evaluation scripts: validate.py, evaluate.py, stats.py, compare.py
- Docker support
- GitHub Actions CI (validate + release)
- Full documentation suite (9 files)
- CITATION.cff for academic citation

### Schema
- 14 required fields per case
- Academic references mandatory
- Real-world analog required
- 5-level difficulty scale
- Loop sensitivity flag
