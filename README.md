# Active Entity Ontology for Science (AEOS)

AEOS is a portable ontology for modeling active and informational entities,
their roles, affordances, states, and interaction motifs in scientific
ecosystems. The repository is designed to be forked, edited, validated, and
consumed without access to an external application.

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
  [integration guides](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/tree/8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1/docs/gnn/integration)
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

## Quick start

Requires Python 3.11 or newer.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/aeos validate
.venv/bin/aeos build
.venv/bin/pytest
.venv/bin/ruff check src tests scripts
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
The full local gate is `python scripts/check_release.py`; see
[`docs/contributing.md`](docs/contributing.md) for the complete command list.

## License and attribution

Repository content is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Please preserve the Active Inference Institute attribution, the ontology version,
and the source publication when redistributing or adapting AEOS.
