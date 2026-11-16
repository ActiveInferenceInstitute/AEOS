# Gate and CI run guide

`./run.sh` is the single entry point. With no argument it runs `fast`, the
existing full test selection without coverage instrumentation. `gate` explicitly
runs the coverage-enforced development gate; `ci` adds the release checks.
Commands are implemented once in the runner, including the compatibility slice.
There is no configured static type checker, so there is no types arm.

The project environment comes from `uv.lock`. Project commands use
`uv run --locked --extra test`; a stale lock fails instead of silently resolving
a new environment. After changing dependencies, refresh with `uv lock` in the
same change. `lock` checks freshness without installing packages.

```bash
./run.sh setup         # install the locked project environment
./run.sh               # default: fast tests, no coverage instrumentation
./run.sh ci-project    # hosted validate: shared project checks plus release, no duplicate GNN
./run.sh compat        # supported Python floor in a separate environment
./run.sh gnn           # pin, pointer and specs via the pinned reader; network required
./run.sh list          # all runnable arms
```

## Prerequisites

| Tool | Needed by | Notes |
| --- | --- | --- |
| `uv` (0.13 or newer) | every arm | The workflow installs it through the pinned setup action. |
| Python 3.11 or newer | project arms | `requires-python = ">=3.11"`; local measurements record the actual version. |
| Python 3.12 by default | `gnn` | The upstream parser requires `>=3.11,<3.15`; `GNN_PYTHON` selects its separate `.venv-gnn` interpreter. |
| Network access | initial setup, `gnn` | Project arms are offline after setup; `.venv-gnn` is provisioned from the revision the pin names, which needs network. |
| `soffice` (LibreOffice), `qpdf`, `pdftotext`, `pdfinfo`, `pdftoppm` | `release`, `render` | Missing commands are errors, not successful skipped rendering. |

## Arms

| Arm | Command or composition | Notes |
| --- | --- | --- |
| `setup` | `uv sync --locked --extra test` | Reuses an existing environment. |
| `lock` | `uv lock --check` | Refuses a stale project/lock pair without rewriting the lock. |
| `validate` | `aeos validate --format json` | Schema and semantic validation. |
| `build` | `aeos build --check` | Deterministic export freshness; does not rewrite the export. |
| `lint` | `ruff check src tests scripts` | One lint implementation. |
| `fast` | `pytest -q --no-cov` | Default; same test selection as `test`, without coverage. |
| `test` | `pytest` | Coverage instrumentation and the configured coverage threshold. |
| `docs` | `python scripts/check_docs.py`, then `python scripts/gate_metrics.py --check` | Relative links, anchors, flat-index completeness and generated-metrics consistency. |
| `gnn` | `python -m gnn.importers check --repo . --require-pointer --workflow .github/workflows/aeos.yml --job gnn-conformance` in `.venv-gnn` | Provisions the pinned parser revision first, then runs the reader that revision ships; see [GNN conformance](gnn-conformance.md). |
| `release` | `python scripts/check_release.py` | Release, ontology, digest, archive, accessibility, freshness and rendering checks. |
| `render` | `python scripts/render_artifacts.py` | Page images under ignored `qa/rendered/`; does not regenerate publication binaries. |
| `compat` | `lock`, `validate`, `build`, `fast` | Calls the same arm functions with `.venv-compat` and Python 3.11 (`COMPAT_PYTHON` overrides). |
| `gate` | Shared project gate plus `gnn` | Full local development gate retains GNN. |
| `ci` | Full local gate plus `release` | Full local qualification retains GNN. |
| `ci-project` | Shared project checks plus `release`, excluding GNN | Hosted `validate`; dedicated `gnn-conformance` alone owns hosted GNN. |
| `measure` | `python scripts/gate_metrics.py --measure` | Single sample of every substantive arm and the default invocation; not recursively itself. |

`help` and `list` are discovery commands, not gates. The measurement producer
accepts `--baseline PATH` to retain an earlier JSON snapshot and `--output-dir
PATH` to write evidence outside the source tree. `--record PATH` renders an
already measured snapshot without rerunning its arms. All commands above are
owned by `run.sh`, not repeated in workflow shell blocks.

## CI jobs

Each job uses
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`.

| Job key | Display name | Arm | Interpreter |
| --- | --- | --- | --- |
| `validate` | `validate` | `./run.sh ci-project` | 3.14 |
| `compat` | `compat` | `./run.sh compat` | 3.11 |
| `gnn-conformance` | `gnn conformance (pinned)` | `./run.sh gnn` | 3.12 |

The former separate `release-checks` job is folded into `validate`. Its artifact
validators (`libreoffice`, `poppler-utils`, `qpdf`) are installed there, and gate
and release reuse the same interpreter, lock and project environment. The other
jobs intentionally exercise different interpreter/package contracts; no job
repeats lint or the coverage-enforced suite. The standalone release arm retains
its own ontology integrity checks so it remains independently runnable.

GitHub Actions is organization billing-locked for this estate pass. Local runs
are the acceptance gate; neither this guide nor a PR claims hosted CI passed.

## Measured wall times

Generated v3 metrics separate current evidence from complete retained v2 observations. Content, membership, command/environment identity and runner implementation bind current observations; HEAD is descriptive, host Python names the measurement driver, and generated outputs do not fingerprint themselves.

`--record PATH --historical --output-dir PATH` preserves old observations without executing or promoting them. `ci-project` can be explicitly null/unmeasured. Actual current measurements require final source/docs plus all admitted tools/network/runtime; missing evidence and failures are not speedups. See [the generated evidence contract](_generated/README.md).
