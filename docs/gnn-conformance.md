# GNN conformance

The repository pins one upstream parser and proves it still parses and
type-checks the repository's sketches, or the pinned exemplar when the
repository has none.

## The pin

| Field | Value |
| --- | --- |
| Pin file | `.github/gnn-pin.json` |
| Schema | `gnn-importer-pin/v1` |
| Repository | `ActiveInferenceInstitute/Generalized_Notation_Notation` |
| Tag | `v5.0.3` |
| Revision | `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1` |
| Recorded | `2026-11-12` |

`.github/GNN.md` is the pointer: it records what the conformance job parses and
that a pinned-exemplar result is a pipeline and pin baseline, not a claim that
this repository ships a model.

Changing the parser means editing the pin, then refreshing `.github/GNN.md`,
this page, and [`ecosystem.md`](ecosystem.md) where they restate the revision.
`./run.sh gnn` fails on any of those going stale.

## The two arms

| Arm | What it does | Needs |
| --- | --- | --- |
| `./run.sh gnn` | Reads the pin, requires the `gnn-importer-pin/v1` schema, a 40-character revision and a `vX.Y.Z` tag, then checks that the workflow still defines the `gnn-conformance` job named `gnn conformance (pinned)`, still calls `./run.sh gnn-parser`, and holds no copy of the parser logic. It also checks that `.github/GNN.md`, [`RUN_GUIDE.md`](RUN_GUIDE.md), and this page record the same pin, job, and setup action. | Nothing beyond the project environment. |
| `./run.sh gnn-parser` | Provisions `.venv-gnn` with Python 3.12 (the pinned upstream declares `>=3.11,<3.15`), installs the pinned parser, then imports it to confirm `gnn.__version__` equals the pinned tag. It parses and syntax-checks every `*.gnn.md` sketch in the repository and type-checks them; with no sketch present it downloads the pinned `input/gnn_files/basics/static_perception.md` exemplar and runs the same three steps on it. | Network access. |

`scripts/check_gnn.py` is the only implementation of those steps. The workflow
job with key `gnn-conformance` and display name `gnn conformance (pinned)`
installs the pinned setup action and calls `./run.sh gnn-parser`, so the parser
logic cannot drift between CI and a local run.

## Known caveat

`GNNTypeChecker().validate_gnn_files(...)` returns the integer `2` for a
warning-only result, and `2` is truthy, so the current `if not result` check
cannot separate warnings from a clean pass. The clean result observed from the
pinned revision is the boolean `True`, and `True != 0` is also true, so a
`!= 0` comparison would not separate them either. This is upstream behavior at
the pinned revision; it is recorded rather than worked around, and the pin
stays where it is.
