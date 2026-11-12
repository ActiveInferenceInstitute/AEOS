#!/usr/bin/env bash
# AEOS gate entry point.
#
# Each command has one implementation below; composites and CI reuse it.
# Run `./run.sh help` for the list. With no argument, run the fast tests.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

GNN_VENV=".venv-gnn"
GNN_PYTHON="${GNN_PYTHON:-3.12}"
GNN_PIN=".github/gnn-pin.json"
GNN_WORKFLOW=".github/workflows/aeos.yml"
GNN_JOB="gnn-conformance"

# The project environment is the lockfile, not an ad-hoc install: `--locked`
# refuses to run when `uv.lock` is out of date with `pyproject.toml`, and the
# `lock` arm checks the same condition without building an environment.
run() {
  uv run --locked --extra test "$@"
}

# Materialize the revision the pin names. Reading the pin here is the install
# step, not a second reader: `gnn.importers` owns every decision about the pin,
# the pointer and the specifications, and the arm runs it from this environment.
pinned_source() {
  python3 - "$GNN_PIN" <<'PY'
import json
import sys

pin = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"git+https://github.com/{pin['repository']}.git@{pin['revision']}")
PY
}

ensure_gnn_env() {
  local source
  source="$(pinned_source)"
  uv venv --quiet --allow-existing --python "$GNN_PYTHON" "$GNN_VENV"
  uv pip install --quiet --python "$GNN_VENV/bin/python" "$source"
}

arm_lock()     { uv lock --check; }
arm_setup()    { uv sync --locked --extra test; }
arm_validate() { run aeos validate --format json; }
arm_build()    { run aeos build --check; }
arm_lint()     { run ruff check src tests scripts; }
arm_fast()     { run pytest -q --no-cov; }
arm_test()     { run pytest; }
arm_docs()     { run python scripts/check_docs.py; run python scripts/gate_metrics.py --check; }
arm_gnn() {
  ensure_gnn_env
  "$GNN_VENV/bin/python" -m gnn.importers check --repo . --require-pointer \
    --workflow "$GNN_WORKFLOW" --job "$GNN_JOB" "$@"
}
arm_release()  { run python scripts/check_release.py; }
arm_render()   { run python scripts/render_artifacts.py "$@"; }
arm_measure()  { run python scripts/gate_metrics.py --measure "$@"; }

# The compatibility slice gets its own environment so that running it never
# leaves the shared `.venv` on the older interpreter.
arm_compat() (
  export UV_PROJECT_ENVIRONMENT=.venv-compat UV_PYTHON="${COMPAT_PYTHON:-3.11}"
  arm_lock
  arm_validate
  arm_build
  arm_fast
)
arm_gate()   { arm_lock; arm_validate; arm_build; arm_lint; arm_test; arm_docs; arm_gnn; }
arm_ci()     { arm_gate; arm_release; }

ARMS="setup lock validate build lint fast test compat docs gnn release render measure gate ci"

arm_list() {
  for name in $ARMS; do printf '%s\n' "$name"; done
}

arm_help() {
  cat <<'TXT'
AEOS gate: ./run.sh [arm] [args]  (default: fast)

Environment
  setup        Install the locked project environment (uv sync --locked).
  lock         uv lock --check: refuse a lockfile that is out of date.
  measure      Time every arm on this host and refresh docs/_generated/gate-metrics.{json,md}.

Fast feedback
  lint         ruff check src tests scripts
  fast         pytest without the coverage gate
  docs         Relative-link and index check plus generated-metrics freshness.
  gnn          Pin, pointer and specification check by the pinned GNN reader.
  validate     aeos validate --format json
  build        aeos build --check

Full gates
  test         pytest with --cov=src --cov-fail-under=90
  compat       Compatibility slice in .venv-compat: lock, validate, build, fast.
  release      scripts/check_release.py (needs soffice, qpdf, poppler, pdftoppm).
  render       Render every maintained artifact to page images for review.
  gate         lock, validate, build, lint, test, docs, gnn
  ci           gate plus release.

Selection
  list         Print the arm names, one per line.
  help         Print this text.
TXT
}

arm="${1:-fast}"
if [ "$#" -gt 0 ]; then shift; fi

case "$arm" in
  setup)      arm_setup "$@" ;;
  lock)       arm_lock "$@" ;;
  validate)   arm_validate "$@" ;;
  build)      arm_build "$@" ;;
  lint)       arm_lint "$@" ;;
  fast)       arm_fast "$@" ;;
  test)       arm_test "$@" ;;
  compat)     arm_compat "$@" ;;
  docs)       arm_docs "$@" ;;
  gnn)        arm_gnn "$@" ;;
  release)    arm_release "$@" ;;
  render)     arm_render "$@" ;;
  measure)    arm_measure "$@" ;;
  gate)       arm_gate "$@" ;;
  ci)         arm_ci "$@" ;;
  list)       arm_list ;;
  help|-h|--help) arm_help ;;
  *)
    printf 'unknown arm: %s\n\n' "$arm" >&2
    arm_help >&2
    exit 2
    ;;
esac
