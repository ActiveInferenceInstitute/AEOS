# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/aeos.yml`. The job reads `.github/gnn-pin.json`, whose
schema is `gnn-importer-pin/v1` and which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The job installs that parser and then calls `./run.sh gnn-parser`, so the
parsing and type-checking steps live in `scripts/check_gnn.py` and nowhere
else.

What it parses: every `*.gnn.md` sketch in the repository, and, when the
repository has none, the pinned upstream
`input/gnn_files/basics/static_perception.md` exemplar. In both cases it
requires a clean formal parse, clean syntax validation, and a passing type
check. The pinned-exemplar result is a pipeline and pin baseline, not a claim
that the repository already contains a model.

[`docs/gnn-conformance.md`](../docs/gnn-conformance.md) records the pin fields,
both arms, and the warning-sentinel caveat of the pinned checker.
