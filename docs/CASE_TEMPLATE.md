# Case Template

Use this template when contributing new cases to the benchmark.

```json
{
  "id": "category-XXX",
  "category": "category-name",
  "subcategory": "specific_variant",
  "difficulty": 3,
  "prompt": "The test prompt (20-2000 chars)",
  "expected_behavior": "What a well-governed model should output",
  "failure_mode": "short_label_for_failure",
  "rationale": "Why this case matters — minimum 30 chars with academic grounding",
  "real_world_analog": "A real incident or documented scenario this maps to",
  "references": [
    {
      "title": "Paper or framework title",
      "url_or_doi": "https://doi.org/... or https://arxiv.org/abs/...",
      "year": 2024
    }
  ],
  "loop_sensitive": true,
  "validation_status": "draft",
  "author": "Your Name",
  "version": "1.0"
}
```

## Field Guidelines

| Field | Guidance |
|-------|----------|
| `id` | Format: `{category}-{seq:03d}`. Use next available number. |
| `category` | Must be one of the 11 defined categories |
| `subcategory` | Specific variant — snake_case, max 60 chars |
| `difficulty` | 1=trivial, 2=simple, 3=moderate, 4=hard, 5=PhD-level |
| `prompt` | Clear, self-contained, 20-2000 chars |
| `expected_behavior` | Specific, verifiable — what correct looks like |
| `failure_mode` | Short snake_case label for the failure being tested |
| `rationale` | Academic grounding — why this case exists |
| `real_world_analog` | Documented incident or realistic scenario |
| `references` | Min 1, max 10. Prefer peer-reviewed sources |
| `loop_sensitive` | true if deeper reasoning should change outcome |
| `validation_status` | Start with "draft", move to "reviewed" after peer review |
| `author` | Person who created the case |
| `version` | Semantic version of the case definition |

## Difficulty Calibration Guide

| Level | Description | Example |
|-------|-------------|---------|
| 1 | Trivial — any model should pass | "What is 1+1?" |
| 2 | Simple — requires basic knowledge | "Translate 'data controller' to Dutch" |
| 3 | Moderate — requires domain reasoning | "Navigate conflicting executive directives" |
| 4 | Hard — requires nuanced judgment | "Calibrate confidence near knowledge boundary" |
| 5 | PhD-level — requires philosophical depth | "Resolve incommensurable value conflict" |

## Review Checklist

Before submitting a new case, verify:

- [ ] Prompt is self-contained (no external context needed)
- [ ] Expected behavior is verifiable (not subjective)
- [ ] At least 1 academic reference provided
- [ ] Real-world analog documented
- [ ] Difficulty level justified
- [ ] Case doesn't duplicate existing case
- [ ] `loop_sensitive` flag is correct
