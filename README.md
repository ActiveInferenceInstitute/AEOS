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

## Quick start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/aeos validate
.venv/bin/aeos build
.venv/bin/pytest
.venv/bin/ruff check src tests scripts
```

The core commands are local and deterministic:

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
derived graph for downstream search and visualization.

## Contributing

Edit `data/aeos.yaml`, run the validation and test commands, review the JSON
diff, and document any release-level change in `releases.json`. See
[`docs/forking.md`](docs/forking.md), [`docs/data-contract.md`](docs/data-contract.md),
and [`docs/contributing.md`](docs/contributing.md).

## License and attribution

Repository content is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Please preserve the Active Inference Institute attribution, the ontology version,
and the source publication when redistributing or adapting AEOS.
