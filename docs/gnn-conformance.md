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

## GNN–FEP migration blocker

The [GNN–FEP workflow contract](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/b0da6caca954509894cdead55f52efcaa3aef981/docs/workflows/gnn-fep.md)
requires AEOS to replace its local pin reader, pointer checks and specification
validation with the upstream reader, called from the pinned environment:

```bash
.venv-gnn/bin/python -m gnn.importers check --repo . --require-pointer \
    --workflow .github/workflows/aeos.yml --job gnn-conformance
```

The current pin cannot supply that command. The installed distribution's
`direct_url.json` identifies the pinned revision above, but that distribution
has no `gnn.importers` module. The upstream file is also absent at that exact
revision. The contract was merged after the pinned release.

The migration is blocked, not complete. The existing implementation and pin
remain unchanged; a passing existing `gnn` arm does not prove adoption of the
shared reader. Unblocking requires a reviewed parser-pin update to an upstream
revision containing the contract's reader, with the corresponding environment
provisioning and pin references updated together. Do not copy the reader from
another checkout or run it through `PYTHONPATH`: that would no longer be the
reader supplied by this repository's pinned parser.

## The two arms

| Arm | What it does | Needs |
| --- | --- | --- |
| `./run.sh gnn` | Reads the pin, requires the `gnn-importer-pin/v1` schema, a 40-character revision and a `vX.Y.Z` tag, then checks that the workflow still defines the `gnn-conformance` job named `gnn conformance (pinned)`, still calls `./run.sh gnn-parser`, and holds no copy of the parser logic. It also checks that `.github/GNN.md`, [`RUN_GUIDE.md`](RUN_GUIDE.md), and this page record the same pin, job, and setup action. | Nothing beyond the project environment. |
| `./run.sh gnn-parser` | Provisions `.venv-gnn` with Python 3.12 (the pinned upstream declares `>=3.11,<3.15`), installs the pinned parser, then imports it to confirm `gnn.__version__` equals the pinned tag. It parses and syntax-checks every `*.gnn.md` sketch in the repository and type-checks them; with no sketch present it downloads the pinned `input/gnn_files/basics/static_perception.md` exemplar and runs the same three steps on it. | Network access. |

`scripts/check_gnn.py` is the only implementation of those steps. The workflow
job with key `gnn-conformance` and display name `gnn conformance (pinned)`
installs the pinned setup action and calls `./run.sh gnn-parser`, so the parser
logic cannot drift between CI and a local run.

The setup step uses
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`.
This separate interpreter is intentional: the parser's Python range differs
from the project gate. Actions is billing-locked during the estate pass;
local parser output, not a hosted run, is the available conformance evidence.

## Known caveat

`GNNTypeChecker().validate_gnn_files(...)` returns the integer `2` for a
warning-only result, and `2` is truthy, so the current `if not result` check
cannot separate warnings from a clean pass. The clean result observed from the
pinned revision is the boolean `True`, and `True != 0` is also true, so a
`!= 0` comparison would not separate them either. This is upstream behavior at
the pinned revision; it is recorded rather than worked around, and the pin
stays where it is.
