# Data Documentation

## Format

The corpus is stored as JSON Lines (`corpus.jsonl`) — one JSON object per line.
Each object conforms to the schema defined in `corpus-schema.json`.

## Files

| File | Description |
|------|-------------|
| `cases/corpus.jsonl` | Full 275-case corpus |
| `cases/corpus-schema.json` | JSON Schema (Draft 2020-12) for validation |

## Schema Validation

```bash
python3 scripts/validate.py
```

Validates:
- All required fields present
- Correct types and formats
- Unique, sequential IDs per category
- Minimum 25 cases per category
- All 11 categories present
- At least 1 reference per case

## Provenance

- **v1.0** (2025-07): Initial release — 275 cases across 11 categories
  - 150 cases enriched from OpenMythos internal red-team corpus
  - 125 new cases across 5 new categories (hallucination, calibration, value-alignment, temporal-reasoning, cross-lingual)
  - All cases include academic references and real-world analogs

## Statistics

```
Total cases:    275
Categories:     11
References:     825 (avg 3.0/case)
Loop-sensitive: 155 (56%)
```

Run `python3 scripts/stats.py` for full breakdown.

## Usage Notes

- Cases are designed for both zero-shot and few-shot evaluation
- `loop_sensitive: true` cases should be tested at multiple reasoning depths
- Difficulty levels are calibrated for current-generation frontier models
- Cross-lingual cases focus on Dutch/French/German GDPR terminology
