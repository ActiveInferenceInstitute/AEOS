#!/usr/bin/env bash
# AEOS gate entry point.
#
# Every arm below runs exactly one command. CI calls these same arms, so a
# command never exists in two places. Run `./run.sh help` for the list.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

PIN=".github/gnn-pin.json"
GNN_VENV=".venv-gnn"
GNN_PYTHON="${GNN_PYTHON:-3.12}"

# The project environment is the lockfile, not an ad-hoc install: `--frozen`
# fails when `uv.lock` is out of date with `pyproject.toml`.
run() {
  uv run --frozen --extra test "$@"
}

ensure_gnn_env() {
  local requirements
  requirements="$(python3 scripts/check_gnn.py --print-requirements)"
  uv venv --quiet --allow-existing --python "$GNN_PYTHON" "$GNN_VENV"
  printf '%s\n' "$requirements" | uv pip install --quiet --python "$GNN_VENV/bin/python" --requirements -
}

arm_setup()    { uv sync --frozen --extra test; }
arm_validate() { run aeos validate --format json; }
arm_build()    { run aeos build --check; }
arm_lint()     { run ruff check src tests scripts; }
arm_fast()     { run pytest -q --no-cov; }
arm_test()     { run pytest; }
arm_docs()     { run python scripts/check_docs.py; run python scripts/gate_metrics.py --check; }
arm_gnn()      { run python scripts/check_gnn.py; }
arm_release()  { run python scripts/check_release.py; }
arm_render()   { run python scripts/render_artifacts.py "$@"; }
arm_measure()  { run python scripts/gate_metrics.py --measure; }

arm_gnn_parser() {
  ensure_gnn_env
  "$GNN_VENV/bin/python" scripts/check_gnn.py --parser "$@"
}

arm_compat() { arm_validate; arm_build; arm_fast; }
arm_gate()   { arm_validate; arm_build; arm_lint; arm_test; arm_docs; arm_gnn; }
arm_ci()     { arm_gate; arm_release; }

ARMS="setup validate build lint fast test compat docs gnn gnn-parser release render measure gate ci"

arm_list() {
  for name in $ARMS; do printf '%s\n' "$name"; done
}

arm_help() {
  cat <<'TXT'
AEOS gate: ./run.sh <arm> [args]

Environment
  setup        Install the locked project environment (uv sync --frozen).
  measure      Time every arm on this host and refresh docs/_generated/gate-metrics.{json,md}.

Fast feedback
  lint         ruff check src tests scripts
  fast         pytest without the coverage gate
  docs         Relative-link and index check plus generated-metrics freshness.
  gnn          Offline GNN pin and conformance-document check.
  validate     aeos validate --format json
  build        aeos build --check

Full gates
  test         pytest with --cov=src --cov-fail-under=90
  compat       Python-version compatibility slice: validate, build, fast.
  gnn-parser   Pinned upstream GNN parser conformance in .venv-gnn.
  release      scripts/check_release.py (needs soffice, qpdf, poppler, pdftoppm).
  render       Render every maintained artifact to page images for review.
  gate         validate, build, lint, test, docs, gnn  (what CI's gate job runs)
  ci           gate plus release.

Selection
  list         Print the arm names, one per line.
  help         Print this text.
TXT
}

arm="${1:-gate}"
if [ "$#" -gt 0 ]; then shift; fi

case "$arm" in
  setup)      arm_setup "$@" ;;
  validate)   arm_validate "$@" ;;
  build)      arm_build "$@" ;;
  lint)       arm_lint "$@" ;;
  fast)       arm_fast "$@" ;;
  test)       arm_test "$@" ;;
  compat)     arm_compat "$@" ;;
  docs)       arm_docs "$@" ;;
  gnn)        arm_gnn "$@" ;;
  gnn-parser) arm_gnn_parser "$@" ;;
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
