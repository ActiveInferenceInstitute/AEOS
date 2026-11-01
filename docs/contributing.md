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
pytest                       # runs with --cov=src --cov-fail-under=90
ruff check src tests scripts
python scripts/render_artifacts.py
python scripts/check_release.py
```

## Release record

Each release records the ontology version, source file, generated export,
schema version, counts, date, provenance, and a short summary of additions or
changes. Generated files are rebuilt from source during release preparation.

The current release entry also records a `digests` block: the SHA-256 of every
file in its `sourceFiles` and `generatedFiles` lists, plus the date the digests
were taken. `python scripts/check_release.py` fails when a listed file is
missing, when its bytes no longer match the recorded digest, or when a listed
file has no digest. Edit or regenerate an artifact and re-record its digest in
the same change.

The CI workflow runs the same checks on pushes and pull requests. A release is
ready only when source validation, generated-file freshness, artifact checks,
and document rendering all pass.

Cross-repository references (GNN, the Active Inference Ontology, ATLAS) are
documented in [ecosystem.md](ecosystem.md). They are cross-references, not
identifier mappings; do not add a mapping without the reviewed-input and
resolution process described there.
