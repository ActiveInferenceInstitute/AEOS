# AEOS Project Backlog

Status: Active (maintained)
Owner: Active Inference Institute (steward: Daniel Friedman)
Last reviewed: 2026-08-01

Review scope: deepest hostile red-team review of the full repository
(`src/`, `tests/`, `scripts/`, `docs/`, `paper/`, `data/`, `schema/`,
`.aii/`, and the release gate in `scripts/check_release.py`). Findings were
graded Minor / Medium / Major. All validated Minor, Medium, and Major
findings have now been implemented (see Completed/Closed).

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
