# Contributing to OpenMythos Benchmark

## How to Contribute

### Adding New Cases

1. Fork the repository
2. Use `docs/CASE_TEMPLATE.md` as starting point
3. Validate with `python3 scripts/validate.py`
4. Submit PR with case(s) and justification

### Review Process

- All new cases require 2 reviewer approvals
- Cases must have ≥1 academic reference
- Difficulty must be justified in PR description
- Real-world analog required

### Code Style

- Python: standard library only (no unnecessary dependencies)
- Max 100 chars per line
- No comments unless non-obvious

### Commit Convention

```
feat: add 5 new calibration cases for meta-cognition
fix: correct reference in hierarchy-003
docs: update methodology section on difficulty calibration
```

## Code of Conduct

- Academic integrity: no fabricated references
- Transparency: document known limitations
- Inclusivity: cases should not encode cultural bias
