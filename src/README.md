# `src/` — the `aeos` Python package

Installable package (`src` layout) backing the `aeos` console script and the
`python -m aeos` entry point. Install with
`python3 -m pip install -e '.[test]'` from the repository root.

| Module | Responsibility |
| --- | --- |
| [`aeos/__init__.py`](aeos/__init__.py) | Package docstring and `__version__` (kept in step with `releases.json`). |
| [`aeos/__main__.py`](aeos/__main__.py) | `python -m aeos` entry point; delegates to `aeos.cli.main`. |
| [`aeos/cli.py`](aeos/cli.py) | `argparse` command-line interface: `validate`, `build`, `report`, `diff`, their options, output modes, and exit codes. |
| [`aeos/core.py`](aeos/core.py) | Loading, schema and semantic validation, deterministic export building (including the derived graph), reporting, and document diffing. Defines the default `data/aeos.yaml`, `schema/aeos.schema.json`, and `aeos.json` paths. |

The CLI is documented end to end in [`docs/cli.md`](../docs/cli.md); the data
contract it enforces is in [`docs/data-contract.md`](../docs/data-contract.md)
and the conceptual model in [`docs/model.md`](../docs/model.md).
