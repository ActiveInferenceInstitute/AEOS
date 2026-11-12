# Gate and CI run guide

`./run.sh` is the single gate entry point. Each arm runs exactly one command,
CI calls these same arms, and no command is written down twice. The project
environment is `uv.lock`; every arm runs through `uv run --locked`, so an
out-of-date lockfile fails the arm instead of resolving a different set of
packages. `--frozen` would skip that check, which is why no arm uses it.
After changing a dependency in `pyproject.toml`, refresh the lock with
`uv lock` in the same change; `./run.sh lock` and the first step of `gate`
refuse a stale pair before any build runs.

```bash
./run.sh help          # arms and what they run
./run.sh list          # arm names, one per line
./run.sh gate          # the local gate CI's `validate` job runs
```

## Prerequisites

| Tool | Needed by | Notes |
| --- | --- | --- |
| `uv` (0.13 or newer) | every arm | Syncs and runs the locked environment. The workflow installs it through a pinned action, not a floating tag. |
| Python 3.11 or newer | every arm | The lock declares `requires-python = ">=3.11"`. |
| Python 3.14 or older for the parser arm | `gnn-parser` | The pinned upstream package declares `>=3.11,<3.15`, so this arm provisions its own interpreter (3.12 by default) in `.venv-gnn`. |
| Network access | `gnn-parser` | Installs the pinned parser and, when the repository has no sketch, downloads the pinned exemplar. |
| `soffice` (LibreOffice), `qpdf`, `pdftotext`, `pdfinfo`, `pdftoppm` | `release`, `render` | These arms name the exact missing command and fail; the rest of the gate still runs. |

## Arms

| Arm | Command it runs | Notes |
| --- | --- | --- |
| `setup` | `uv sync --locked --extra test` | Idempotent; arms sync on first use anyway. |
| `lock` | `uv lock --check` | Refuses a lockfile that is out of date; runs first in `gate` and `compat`. |
| `validate` | `aeos validate --format json` | Schema and semantic validation of `data/aeos.yaml`. |
| `build` | `aeos build --check` | Generated export freshness. |
| `lint` | `ruff check src tests scripts` | The lint gate. |
| `fast` | `pytest -q --no-cov` | Same selection as the full arm without coverage instrumentation; use it while editing. |
| `test` | `pytest` | Full arm; `addopts` carries `--cov=src --cov-fail-under=90`. |
| `docs` | `scripts/check_docs.py`, then `scripts/gate_metrics.py --check` | Relative links and anchors, index completeness, generated metrics freshness. |
| `gnn` | `scripts/check_gnn.py` | Offline: pin schema, revision, workflow job, and every document that restates them. |
| `gnn-parser` | `scripts/check_gnn.py --parser` in `.venv-gnn` | Pinned parser conformance; see [gnn-conformance.md](gnn-conformance.md). |
| `release` | `scripts/check_release.py` | Ontology, sidecar, archive, digest, artifact, freshness, and rendering checks. |
| `render` | `scripts/render_artifacts.py` | Renders every maintained PDF and DOCX page to `qa/rendered/` for review. |
| `measure` | `scripts/gate_metrics.py --measure` | Times every arm and rewrites [`_generated/gate-metrics.md`](_generated/gate-metrics.md). |
| `compat` | `lock`, `validate`, `build`, `fast` | The compatibility slice; runs in its own `.venv-compat` on Python 3.11 (`COMPAT_PYTHON` overrides), so it never moves the shared `.venv`. |
| `gate` | `lock`, `validate`, `build`, `lint`, `test`, `docs`, `gnn` | What CI's `validate` job runs. |
| `ci` | `gate`, `release` | Full local reproduction of every CI job except the parser arm. |

`test` and `fast` are the only placement of the suite, `lint` the only
placement of ruff, and `validate`/`build` the only placement of the ontology
commands; every composite arm and every CI job calls them rather than repeating
them.

## CI jobs

Every job checks out the repository, installs uv and one interpreter with
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`,
then runs one arm. The first arm syncs the lock; later steps reuse it.

| Job key | Display name | Arm | Interpreter |
| --- | --- | --- | --- |
| `validate` | `validate` | `./run.sh gate` | 3.14 |
| `compat` | `compat` | `./run.sh compat` | 3.11 |
| `release-checks` | `release-checks` | `./run.sh release` | 3.14 |
| `gnn-conformance` | `gnn conformance (pinned)` | `./run.sh gnn-parser` | 3.12 (provisioned by the arm) |

The `release-checks` job installs `libreoffice`, `poppler-utils`, and `qpdf`
with `apt-get` before running its arm; it needs `validate` to pass first.
`compat` exists so the 3.11 floor is still exercised without running the whole
gate twice on every push.

## Measured wall times

Baseline measured once on this host on 2026-11-12, before `run.sh` existed:
macOS arm64, Python 3.15.2, a fresh `python3 -m venv` plus
`pip install -e '.[test]'`, then each command run once.

| Step | Before (s) |
| --- | --- |
| Create the environment (`venv` + `pip install`) | 31.15 |
| `aeos validate --format json` | 0.52 |
| `aeos build --check` | 0.47 |
| `pytest` (67 tests, 97.13% coverage) | 5.65 |
| `ruff check src tests scripts` | 0.28 |
| `scripts/check_release.py` | 35.05 (failed: `soffice` absent) |
| Documentation arm | none existed |
| GNN conformance | inline workflow logic only; no local command |

Current arm wall times, collected tests, and coverage live in
[`_generated/gate-metrics.md`](_generated/gate-metrics.md), which
`./run.sh measure` rewrites; do not copy those numbers into prose.
