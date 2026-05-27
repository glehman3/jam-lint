# jam-lint

[![CI](https://github.com/glehman3/jam-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/glehman3/jam-lint/actions/workflows/ci.yml)

Structural validator for **test jam CSV** files — catches column misalignment, missing required headers, bullet-vs-numbered-list violations, and formula-injection risks before Excel or Jira import breaks.

## Quick start

```bash
pip install .
jam-lint check examples/
jam-lint check examples/valid.csv --format json
```

## Checks

- Row width matches header (unquoted comma / newline detection)
- Required core columns including `Type` in column 5
- Duplicate header names
- Execution tracking columns empty in generated files (warning)
- Cells starting with `=`, `+`, `-`, `@` without escape quote
- Numbered lists only in Pre-conditions, Test Steps, Expected Results

## Scope

Validates structure only — not test content quality. Derived from patterns in [qe-skill](https://github.com/glehman3/qe-skill); see [ATTRIBUTION.md](ATTRIBUTION.md).

## License

MIT
