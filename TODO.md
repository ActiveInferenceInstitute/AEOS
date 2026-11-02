# AEOS Project Backlog

Status: Active (maintained)
Owner: Active Inference Institute (steward: Daniel Friedman)
Last reviewed: 2026-11-01 (GNN alignment and gate repair)

Review scope: deepest hostile red-team review of the full repository
(`src/`, `tests/`, `scripts/`, `docs/`, `paper/`, `data/`, `schema/`,
`.aii/`, and the release gate in `scripts/check_release.py`). Findings were
graded Minor / Medium / Major. All validated Minor, Medium, and Major
findings have now been implemented (see Completed/Closed).

## GNN alignment and gate repair (2026-11-01)

Scope: audit of the canonical source → deterministic export → schema →
releases chain, the lint and release gates, release provenance, and the
cross-reference to the GNN and ontology vocabulary surfaces.

- [x] **Lint gate repaired (CI was red on `main` since 2026-08-01).**
  `ruff check src tests scripts` passes again: the shebang scripts are
  executable, the unused `noqa` directives and unused unpacked variable are
  gone, the sidecar parse catches `OSError`/`yaml.YAMLError` instead of
  `Exception`, and the test imports are sorted.
- [x] **Maintained PDF re-linearized across qpdf generations.**
  `qpdf --check paper/aeos-local.pdf` reported "incorrect object count in
  outline hint table" for the committed file under qpdf 12.4.2 and, after a
  plain re-linearization, under the qpdf 11.9.0 the release-checks job
  installs. The file is now written with
  `qpdf --object-streams=disable --linearize`, which qpdf 11.9.0 and 12.4.2
  both report clean; extracted text and rendered pages are byte-identical to
  the previous file, and `paper/README.md` and `docs/publication.md` record
  the command and the reason.
- [x] **Release provenance bound to bytes.** `releases.json` records SHA-256
  digests for every current-release file plus the date taken, and
  `scripts/check_release.py` fails on a missing, edited, or unrecorded file;
  three regression tests cover the oracle.
- [x] **Ecosystem cross-reference added.** `docs/ecosystem.md` records the
  verified overlap with ontology release v5 (2 of 71 AEOS labels by
  normalized label) and with GNN's 64 declared annotation labels (0 of 71),
  and states that no identifiers are shared or mapped. The sidecar's ontology
  relation note now records the same verified fact instead of an unsupported
  claim.
- [x] **Agent guide added.** Root `AGENTS.md` documents the surfaces, ground
  rules, gates, and ecosystem boundaries; the sidecar already declared the
  file, which previously did not exist.
- [x] **CI and metadata currency.** The workflow uses `actions/checkout@v7`
  and `actions/setup-python@v7`, adds least-privilege permissions and a
  Python 3.11/3.14 matrix, and `requires-python` is `>=3.11` (Python 3.10
  reached end of life on 2026-10-31). The test extra moves to
  `pytest>=9,<10`, `pytest-cov>=7,<8`, `ruff>=0.17,<1`.

Open items after this pass: none in these areas. The rendering check in
`scripts/check_release.py` still requires `soffice` locally; CI installs it.

## Docs-deep review (2026-08-02)

Scope: full documentation pass over `README.md`, `docs/`, `paper/`,
`archive/2022-v2/`, `.aii/`, and the CI workflow; every claim checked
against the actual code, data, and artifacts. Severity definitions: Minor =
typo, broken link, formatting; Medium = stale section rewrite, doc
restructure, added missing guide; Major = large doc system overhaul or
cross-cutting refactor.

### Minor

- [x] **MIN-1 — README quick start omits the Python requirement
  (completed).** Added "Requires Python 3.10 or newer." to `README.md`,
  matching `requires-python` in `pyproject.toml`.
- [x] **MIN-2 — README did not cross-link the full docs set (completed).**
  The Contributing section now links `docs/model.md` and
  `docs/publication.md` alongside the existing fork/data/contributing docs.
- [x] **MIN-3 — docs index omitted the CLI reference and paper notes
  (completed).** `docs/README.md` now lists the CLI reference and points to
  `paper/README.md`.

### Medium

- [x] **MED-1 — No CLI reference existed (completed).** Added
  `docs/cli.md`: every command (`validate`, `build`, `report`, `diff`),
  option, default, exit code, and JSON payload, verified against
  `src/aeos/cli.py` and `src/aeos/core.py` and the live `--help` output.
- [x] **MED-2 — No CITATION.cff for GitHub citation support (completed).**
  Added `CITATION.cff` (v1.2.0) with title, entity author, DOI, license,
  version, and release date, all taken from repository metadata
  (`releases.json`, `pyproject.toml`, `data/aeos.yaml`).

### Major

- [x] **MAJ-1 — No major docs overhaul required (resolved by review).** The
  documentation set is coherent, accurate, and well cross-linked after the
  earlier red-team pass; no large restructure or new docs system is
  warranted. This is recorded rather than deferred because the review found
  no outstanding major item to scope.

### Open / deferred

- None. All scoped items from this pass are implemented; see the completed
  entries above and `REVIEW_LOG_2026-08-02.md` for the full audit trail.

## Completed / Closed — implemented (2026-08-01)

- [x] **MAJ-1 — Paper-export freshness is verified against its source
  (Major, resolved).** Added a `check_paper_freshness` oracle to
  `scripts/check_release.py` so the release gate no longer quietly certifies a
  stale maintained paper as current. It asserts that every maintained
  `paper/aeos-local.*` export contains every current `#`/`##` heading and
  identity token from `paper/aeos.md`, and that `paper/aeos-2022-v2.pdf`
  remains content-faithful to the archived 2022/v2 source PDF (extracted-text
  equality). See `scripts/check_release.py` and `tests/test_release_checks.py`,
  and the notes in `docs/publication.md` / `paper/README.md`.
- [x] **Coverage gate enforced (MEDIUM).** Added `pytest-cov` to the `test`
  extra and `--cov=src --cov-fail-under=90` to pytest `addopts`, then raised
  aggregate coverage from 84% to 97% by adding real (no-`mock`) tests for the
  CLI text/json/diff/error paths, core loader and semantic error branches, and
  the `python -m aeos` / `python -m aeos.cli` entrypoints. See
  `pyproject.toml`, `tests/test_core.py`, `tests/test_cli.py`.
- [x] **Release gate no longer forbids the project backlog (MEDIUM).** Root
  `TODO.md` and the generated `aeos.json` export are exempt from the
  `check_release.py` authored-prose term scan via the new
  `ACTIVE_TEXT_EXEMPT_PATHS`, so the standard backlog file and the machine
  export cannot trip the gate. See `scripts/check_release.py`.
- [x] **Removed dead `labels` dict** in source graph construction (MINOR). See
  `src/aeos/core.py` (`graph_for`).
- [x] **Fixed `paper/README.md` factual drift** "2022/v3" -> "2022/v2" (MINOR).
- [x] **Added subprocess timeouts** to release checks (`check_pdfs`,
  `check_pdf_text`, `check_archive_pdfs`) so a hung external tool cannot hang
  the gate (MINOR). See `scripts/check_release.py`.
- [x] **Documented the coverage gate** in `README.md` and
  `docs/contributing.md` (MINOR).

## Notes

- The release gate's only local failure is the missing `soffice` (LibreOffice)
  binary; CI installs it (`apt-get install libreoffice ...`). All non-rendering
  checks pass locally.
- The deep review found no remaining open findings; the sole Major
  (paper-freshness) and all Minor/Medium items have been implemented and are
  recorded above.
