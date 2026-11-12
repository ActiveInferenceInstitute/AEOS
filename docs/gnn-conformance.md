# GNN conformance

The repository pins one upstream revision of Generalized Notation Notation and
validates its pin, its pointer and its specifications with the reader that
revision ships. AEOS keeps no copy of that logic.

## The pin

| Field | Value |
| --- | --- |
| Pin file | `.github/gnn-pin.json` |
| Schema | `gnn-importer-pin/v1` |
| Repository | `ActiveInferenceInstitute/Generalized_Notation_Notation` |
| Tag | `v5.1.0` |
| Revision | `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf` |
| Recorded | `2026-11-12` |

`.github/GNN.md` is the pointer: it names the pin file, the revision, the
conformance workflow and the job key. The reader checks that those four facts
appear in it, so the pointer cannot drift from the pin it describes.

Changing the parser means editing the pin, then refreshing `.github/GNN.md`,
this page, and [`ecosystem.md`](ecosystem.md) where they restate the revision.

## The arm

| Arm | What it does | Needs |
| --- | --- | --- |
| `./run.sh gnn` | Provisions `.venv-gnn` with Python 3.12 from the revision the pin names, then runs the reader from that environment: `python -m gnn.importers check --repo . --require-pointer --workflow .github/workflows/aeos.yml --job gnn-conformance`. The reader validates the pin shape and revision, requires the pointer to name the pin, the revision, the workflow and the job, and parses every declared or discovered `*.gnn.md` specification with the pinned parser. | Network access for provisioning; nothing beyond the project environment otherwise. |

The precedence list the reader searches (`PIN_CANDIDATES`) finds
`.github/gnn-pin.json` first, so the pin path is also the conventional one. This
repository carries no `*.gnn.md` specification, so the reader reports
`spec-absent` as a **warning**: the pin and the pointer pass, and the arm makes
no claim that AEOS ships a GNN model. Adding a model under the same pin means
the reader validates it in this arm, with no second gate.

The provisioning step reads only the pin's `repository` and `revision` to build
the git URL it installs. Every decision about the pin's shape, the pointer and
the specifications belongs to `gnn.importers` in the pinned revision.

## The workflow

The `gnn-conformance` job, display name `gnn conformance (pinned)`, runs
`./run.sh gnn` on Python 3.12 and uses the pinned setup action
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`.
GitHub Actions is billing-locked during this estate pass, so a local run of the
arm — not a hosted job — is the available conformance evidence.

## Migration from the interim reader

The [GNN–FEP workflow contract](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/workflows/gnn-fep.md)
stages adoption by the pin, because `gnn.importers` ships in a revision rather
than a version name: it was added in `e6a9d3917`, after `v5.0.3`.

The interim state, recorded at `v5.0.3` (`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`),
was a local reader in `scripts/check_gnn.py`: it read the pin, validated the
pointer and the documents that restated it, and ran the pinned parser
conformance under `--parser`. The contract's own command failed there —
`No module named gnn.importers` — because that revision predates the module.

The cutover, in this change:

- `scripts/check_gnn.py` is deleted; AEOS no longer carries a pin reader, a
  pointer check or a specification validator of its own.
- The pin advances from `v5.0.3` (`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`) to
  `v5.1.0` (`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`), the release that ships
  `src/gnn/importers.py`.
- `./run.sh gnn` calls that reader from `.venv-gnn`, and the separate
  `gnn-parser` arm is gone: parsing specifications is what the reader does.
- `.github/GNN.md`, this page, [`ecosystem.md`](ecosystem.md),
  [`RUN_GUIDE.md`](RUN_GUIDE.md), and the workflow record the new revision.

The previous page recorded an upstream `GNNTypeChecker` warning sentinel
(`2` returned for warning-only results) as a pinned-revision behavior. That
caveat belonged to the deleted `--parser` path and does not apply to the
reader.
