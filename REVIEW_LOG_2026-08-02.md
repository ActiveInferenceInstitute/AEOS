# AEOS docs-deep review — 2026-08-02

Date: 2026-08-02
Branch: main (origin/main)
HEAD at start: fbe0d83 (Red-team review: coverage gate, release-gate hardening, paper-freshness oracle)

## Phase 0 — preflight

- `git fetch origin` + fast-forward onto `main`: clean, no local changes.
- Inventory: README.md, the root backlog file, docs/ (index + model,
  data-contract, forking, contributing, publication), paper/ (aeos.md +
  generated PDF/DOCX/HTML + README), archive/2022-v2/ (README +
  checksums.json + binaries), .aii/ (README, AGENTS.md, config.yaml),
  src/aeos/ (core, cli, __init__, __main__), tests/, scripts/
  (check_release.py, render_artifacts.py, add_docx_alt_text.py),
  schema/aeos.schema.json, data/aeos.yaml, aeos.json, releases.json,
  pyproject.toml, .github/workflows/aeos.yml, LICENSE (CC BY 4.0).

## Phase 1 — mega-deep docs review

Verification battery (all executed locally):

- `aeos build --check` — export current.
- `aeos validate --format json` — valid, no errors.
- `pytest` — 57 passed, 97.38% aggregate coverage (gate: 90%).
- `ruff check src tests scripts` — clean.
- `python scripts/check_release.py` — only failure is the known local gap:
  `soffice` (LibreOffice) is not installed; CI installs it. All other checks
  (ontology, sidecar, release manifest, archive checksums, versions, DOCX
  integrity, PDF checks, PDF text, DOCX/HTML accessibility, paper freshness,
  archived PDF inventory, authored-text scan) pass.
- Relative markdown links: every link in every .md file resolves.
- External links: Coda page 200, CC BY 4.0 200, repo URL 200,
  activeinference.org 200, DOI 10.5281/zenodo.7484994 302 -> 200 (Zenodo).
- Archive SHA-256 table in archive/2022-v2/README.md matches checksums.json
  and the on-disk files.
- Ontology data vs docs: 2 classes, 26 types, 6 areas, 7 roles, 14
  affordances, 3 states, 3 relationships, 10 motifs; motif contexts are
  exactly `cesci`/`desci`; state kinds exactly `internal`/`sense`/`active`;
  areas match the six named in README/paper; entity-type claims in
  paper/aeos.md match data/aeos.yaml labels. releases.json counts match the
  built summary.
- CLI help text (validate/build/report/diff) matches src/aeos/cli.py;
  `diff` exit codes 0/1/2 and JSON payload shapes confirmed in code.

Findings by severity:

- Minor: README omits the Python requirement (>=3.10) and the `python -m aeos`
  module entry point; README Contributing links only three of five docs;
  docs/README.md index omits a CLI reference and the paper README.
- Medium: no CLI reference document; no CITATION.cff for GitHub citation
  support.
- Major: none identified. The documentation is coherent, accurate, and
  complete for a repository of this size; a dedicated docs site or large
  restructure is not warranted (no new heavyweight toolchain per policy).

## Phase 2 — scoping

- Added a "Docs-deep review (2026-08-02)" section to the top-level backlog
  file with Minor / Medium / Major entries (all completed, see below).
- This log records the full pass.

## Phase 3 — implementation

1. docs: add docs/cli.md — full command reference (subcommands, flags,
   defaults, exit codes, JSON payloads, module entry point), grounded in
   src/aeos/cli.py and src/aeos/core.py.
2. docs: README.md — state the Python requirement, mention the module entry
   point, link the CLI reference, and cross-link model/publication docs.
3. docs: docs/README.md — add the CLI reference row and a pointer to
   paper/README.md.
4. docs: add CITATION.cff (cff-version 1.2.0) with title, entity author,
   DOI, license, version, and release date, all from repository metadata.
5. chore: record this review in the backlog file and this log.

## Phase 4 — verification and push

- Re-ran: ruff (clean), pytest (57 passed), `aeos build --check` (current),
  link scan (all resolve), and the authored-text term scan over the new
  files (clean).
- Pushed to origin/main. See git log for commit references.

Commit list (see git log for hashes): docs CLI reference + README/index
updates; CITATION.cff; review log + backlog update.
