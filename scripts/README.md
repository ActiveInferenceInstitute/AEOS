# `scripts/` — release, rendering, and accessibility helpers

Standalone maintenance scripts for AEOS. They are not part of the installable
`aeos` package; run them from the repository root with `python scripts/<name>.py`.
They import the package from `src/`, so install it first
(`python3 -m pip install -e '.[test]'`).

| Script | Purpose | Needs |
| --- | --- | --- |
| [`check_release.py`](check_release.py) | Full release gate: validates the source and export, verifies the release manifest and SHA-256 digests, the sidecar, archive checksums, PDF/DOCX/HTML accessibility and paper freshness, and renders the maintained artifacts to page images. | `soffice` (LibreOffice), `qpdf`, `pdftotext`, `pdfinfo`, `pdftoppm` for the rendering/freshness checks; the rest run without them. |
| [`render_artifacts.py`](render_artifacts.py) | Renders every maintained PDF and DOCX page to PNG for manual inspection and asserts complete page coverage. | `soffice`, `pdftoppm`. |
| [`add_docx_alt_text.py`](add_docx_alt_text.py) | Adds descriptive figure alt text and core document properties to a DOCX package without changing its visible content. | Python standard library only. |

`check_release.py` is the script referenced by the `release-check` task in
[`.aii/config.yaml`](../.aii/config.yaml) and by CI
([`.github/workflows/aeos.yml`](../.github/workflows/aeos.yml)). It is the
oracle for the digests recorded in [`releases.json`](../releases.json): when a
listed file changes, re-record its digest in the same change or the gate fails.

See [`docs/publication.md`](../docs/publication.md) for the artifact
rendering rules and [`docs/contributing.md`](../docs/contributing.md) for the
full check list.
