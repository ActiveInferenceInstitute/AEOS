# Contributing and release workflow

## Curation

1. Make the smallest source change that expresses the intended concept.
2. Use canonical IDs and explicit references rather than encoding relationships
   only in prose.
3. Add or update a motif when a change affects a demonstrated interaction.
4. Run the complete local test and validation commands.
5. Review generated JSON, documentation, and the release diff.

## Required checks

`./run.sh` is the gate entry point; each arm is exactly one command and CI
calls the same arms (see [RUN_GUIDE.md](RUN_GUIDE.md)). Install the locked
environment once with `./run.sh setup`.

```bash
./run.sh gate      # validate, build --check, lint, pytest, docs, gnn pin
./run.sh release   # release gate; needs soffice, qpdf, poppler
./run.sh render    # page images for manual inspection
```

Use a single arm while working: `./run.sh fast` for the suite without the
coverage gate, or `./run.sh lint`, `./run.sh validate`, `./run.sh build`,
`./run.sh docs`, `./run.sh gnn`. `./run.sh list` prints every arm. The full
arm is `./run.sh test`, which carries `--cov=src --cov-fail-under=90`.
`aeos report --format json` still gives a machine-readable summary without
running the gate.

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

CI runs `./run.sh gate`, `./run.sh compat`, `./run.sh release`, and
`./run.sh gnn-parser` on pushes and pull requests; the workflow holds no
command of its own. A release is ready only when source validation,
generated-file freshness, artifact checks, and document rendering all pass.

Cross-repository references (GNN, the Active Inference Ontology, ATLAS) are
documented in [ecosystem.md](ecosystem.md). They are cross-references, not
identifier mappings; do not add a mapping without the reviewed-input and
resolution process described there.
