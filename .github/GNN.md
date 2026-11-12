# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/aeos.yml`. The job reads `.github/gnn-pin.json`, whose
schema is `gnn-importer-pin/v1` and which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.1.0`
(`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`).

The job calls `./run.sh gnn`, which materializes that revision in `.venv-gnn`
and then runs the upstream reader it ships:

```bash
python -m gnn.importers check --repo . --require-pointer \
    --workflow .github/workflows/aeos.yml --job gnn-conformance
```

The pin, the pointer and the `*.gnn.md` specifications are validated by
`gnn.importers` (`check_importer`) in the pinned revision; AEOS keeps no copy of
that logic. This repository carries no `*.gnn.md` specification, so the reader
reports `spec-absent` as a warning: the pin and the pointer pass, and the job
makes no claim that AEOS ships a GNN model.

[`docs/gnn-conformance.md`](../docs/gnn-conformance.md) records the pin fields,
the arm, and the migration from the interim local reader.
