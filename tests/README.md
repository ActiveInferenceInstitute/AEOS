# `tests/` — offline test suite

The suite runs entirely offline with `pytest` (configured in
[`pyproject.toml`](../pyproject.toml) with `--cov=src --cov-fail-under=90`, so
it must stay at 90% coverage or higher). Install the locked environment once
with `./run.sh setup`, then run `./run.sh test` from the repository root;
`./run.sh fast` runs the same selection without the coverage gate.

| Test module | Covers |
| --- | --- |
| [`test_core.py`](test_core.py) | Source loading, schema and semantic validation branches, deterministic build, export freshness (`build --check`), reporting, and document diffing. |
| [`test_cli.py`](test_cli.py) | The `validate`, `build`, `report`, and `diff` commands in text and JSON modes, their error paths, and the `python -m aeos` / `python -m aeos.cli` entry points. |
| [`test_release_checks.py`](test_release_checks.py) | Regression coverage for [`scripts/check_release.py`](../scripts/check_release.py): release digest and manifest verification, and the paper-freshness oracle. |
| [`test_gate.py`](test_gate.py) | A fresh lock passes; changed dependencies refuse without modifying the lock, independent of uv's diagnostic wording or registry cache. |

No test needs a network service, Coda, GitHub, Zenodo, or an external
application. The release-checks tests exercise the non-rendering checks; the
rendering path additionally needs the external tools listed in
[`scripts/README.md`](../scripts/README.md).
