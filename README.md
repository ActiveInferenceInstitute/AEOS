# Active Entity Ontology for Science (AEOS)

AEOS is a portable ontology for modeling active and informational entities,
their roles, affordances, states, and interaction motifs in scientific
ecosystems. The repository is designed to be forked, edited, validated, and
consumed without access to an external application.

## Contents

- [Canonical surfaces](#canonical-surfaces)
- [Related surfaces](#related-surfaces)
- [Status](#status)
- [Quick start](#quick-start)
- [Contributing](#contributing)
- [License and attribution](#license-and-attribution)
- [InstituteOS sidecar](#instituteos-sidecar)

## Canonical surfaces

| Path | Purpose |
| --- | --- |
| [`data/aeos.yaml`](data/aeos.yaml) | Canonical human-editable ontology source. |
| [`aeos.json`](aeos.json) | Deterministic machine-readable export. |
| [`schema/aeos.schema.json`](schema/aeos.schema.json) | Structural data contract. |
| [`releases.json`](releases.json) | Release and provenance manifest. |
| [`docs/`](docs/) | Model, data, fork, curation, and publication guidance. |
| [`paper/`](paper/) | Maintained publication source and artifact notes. |
| [`archive/`](archive/) | Preserved 2022/v2 source artifacts. |

The interactive reference is [AEOS on Coda](https://coda.io/@active-inference-institute/active-entity-ontology-for-science-aeos).
The published paper is [An Active Inference Ontology for Decentralized Science](https://doi.org/10.5281/zenodo.7484994).

## Related surfaces

- [GNN](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation) —
  the Institute's notation and 25-step pipeline for specifying, validating,
  rendering, and executing active inference generative models; see its
  [integration guides](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/tree/75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf/docs/gnn/integration)
  and the [downstream adoption guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md)
  for repositories that consume the notation.
- [Active Inference Ontology](https://github.com/ActiveInferenceInstitute/Active_Inference_Ontology) —
  controlled vocabulary of active inference concepts with a generated GNN
  vocabulary bridge.
- [ATLAS](https://github.com/ActiveInferenceInstitute/ATLAS) — question-oriented
  discovery over entity, pattern, and typed-relationship graphs.
- [docs/ecosystem.md](docs/ecosystem.md) — the verified cross-reference: what
  overlaps with these surfaces, what does not, and what a real integration
  would require.

## Status

Active, released as v1.0.0. Everything in this repository runs locally and
offline: validation, the deterministic export, reporting, diffing, the test
suite, and the release gate. No ontology command calls Coda, GitHub, Zenodo, or
another network service. The release gate's artifact-freshness and page-image checks
need external tools (`soffice`, `qpdf`, `pdftotext`, `pdfinfo`, `pdftoppm`);
without them, those checks cannot run, but the ontology, manifest, and digest
checks still do. The GNN conformance pin is `.github/gnn-pin.json`; the arm
`./run.sh gnn` provisions the pinned parser revision in `.venv-gnn` and runs the
reader that revision ships, and is the only network step in the repository. The
pin, the pointer and the migration from the interim local reader are recorded in
[`docs/gnn-conformance.md`](docs/gnn-conformance.md).

## Quick start

Requires Python 3.11 or newer and [`uv`](https://docs.astral.sh/uv/).

```bash
./run.sh setup
./run.sh gate
```

`./run.sh` is the single gate entry point; with no argument it runs `fast`
(the suite without coverage instrumentation). CI's main job calls `./run.sh ci`
for the complete development and release gates in one environment.
`./run.sh list` prints every arm; [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md)
records their commands and CI mapping.

The environment comes from `uv.lock`. To call the CLI directly:

```bash
uv run aeos validate
uv run aeos build
uv run aeos report --format json
```

`pytest` runs with the coverage gate (`--cov=src --cov-fail-under=90`), so the
suite must stay at 90% or higher. The core commands are local and deterministic:

```bash
aeos validate --input data/aeos.yaml --schema schema/aeos.schema.json
aeos build --input data/aeos.yaml --output aeos.json
aeos build --check
aeos build --check --format json
aeos report --format json
aeos diff OLD.json NEW.json --format json
```

Use `--input`, `--output`, and `--schema` to work with a fork or a separate
ontology file. The validator checks structure, IDs, references, roles,
affordances, states, relationships, and motif steps. The export includes a
derived graph for downstream search and visualization. The same commands are
available as `python -m aeos ...`; see the [command-line
reference](docs/cli.md) for all options, defaults, and exit codes.

## Contributing

Edit `data/aeos.yaml`, run the validation and test commands, review the JSON
diff, and document any release-level change in `releases.json`. The current
release entry records SHA-256 digests of its source and generated files; the
release gate verifies them, so regenerate and re-record the digests whenever a
listed artifact changes. See
[`docs/forking.md`](docs/forking.md), [`docs/data-contract.md`](docs/data-contract.md),
[`docs/contributing.md`](docs/contributing.md), [`docs/model.md`](docs/model.md),
[`docs/ecosystem.md`](docs/ecosystem.md), and [`docs/publication.md`](docs/publication.md).
The complete local main-job gate is `./run.sh ci`; see
[`docs/contributing.md`](docs/contributing.md) for the required checks.

## License and attribution

Repository content is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Please preserve the Active Inference Institute attribution, the ontology version,
and the source publication when redistributing or adapting AEOS.

## InstituteOS sidecar

This repository carries a committed [`.aii/`](.aii/README.md) sidecar with curated
InstituteOS metadata (`aii-sidecar/v1`): category, maturity, ecosystem relations,
key artifacts, provenance, and portable tasks. It is read by
[InstituteOS](https://github.com/ActiveInferenceInstitute/InstituteOS) tooling and
does not affect the project's build or runtime.
