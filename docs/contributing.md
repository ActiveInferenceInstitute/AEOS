# Contributing and release workflow

## Curation

1. Make the smallest source change that expresses the intended concept.
2. Use canonical IDs and explicit references rather than encoding relationships
   only in prose.
3. Add or update a motif when a change affects a demonstrated interaction.
4. Run the complete local test and validation commands.
5. Review generated JSON, documentation, and the release diff.

## Required checks

`./run.sh` is the entry point; CI calls the same arm implementations
(see [RUN_GUIDE.md](RUN_GUIDE.md)). Install the locked environment with
`./run.sh setup`; no argument selects `fast`, without coverage.

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

CI's `validate` job runs `./run.sh ci` (gate plus release in one environment).
The other jobs run `./run.sh compat` and `./run.sh gnn`. GitHub Actions
is billing-locked during this estate pass; local runs provide acceptance, not
a hosted CI claim. Release readiness still requires source validation,
export freshness, artifact checks and document rendering.

Cross-repository references (GNN, the Active Inference Ontology, ATLAS) are
documented in [ecosystem.md](ecosystem.md). They are cross-references, not
identifier mappings; do not add a mapping without the reviewed-input and
resolution process described there.
