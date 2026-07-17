# Contributing and release workflow

## Curation

1. Make the smallest source change that expresses the intended concept.
2. Use canonical IDs and explicit references rather than encoding relationships
   only in prose.
3. Add or update a motif when a change affects a demonstrated interaction.
4. Run the complete local test and validation commands.
5. Review generated JSON, documentation, and the release diff.

## Required checks

```bash
aeos validate --format json
aeos build
aeos build --check
aeos report --format json
pytest
ruff check src tests scripts
python scripts/render_artifacts.py
python scripts/check_release.py
```

## Release record

Each release records the ontology version, source file, generated export,
schema version, counts, date, provenance, and a short summary of additions or
changes. Generated files are rebuilt from source during release preparation.

The CI workflow runs the same checks on pushes and pull requests. A release is
ready only when source validation, generated-file freshness, artifact checks,
and document rendering all pass.
