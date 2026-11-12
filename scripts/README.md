# `scripts/` — gate, release, rendering, and accessibility helpers

Standalone maintenance scripts for AEOS. They are not part of the installable
`aeos` package; run them from the repository root, normally through
`./run.sh`, which supplies the locked environment.

| Script | Purpose | Needs |
| --- | --- | --- |
| [`check_release.py`](check_release.py) | Full release gate: validates the source and export, verifies the release manifest and SHA-256 digests, the sidecar, archive checksums, PDF/DOCX/HTML accessibility and paper freshness, and renders the maintained artifacts to page images. | `soffice` (LibreOffice), `qpdf`, `pdftotext`, `pdfinfo`, `pdftoppm` for the rendering/freshness checks; the rest run without them. |
| [`check_docs.py`](check_docs.py) | Documentation gate: resolves every relative link and in-page anchor in every Markdown file, and keeps `docs/documentation-index.md` in step with `docs/`. | Standard library only. |
| [`gate_metrics.py`](gate_metrics.py) | Measures substantive arms and the default; renders checked before/after JSON/Markdown with retained results. `--record` publishes an existing snapshot without rerunning it. | `uv`, and the arms it measures. |
| [`render_artifacts.py`](render_artifacts.py) | Renders every maintained PDF and DOCX page to PNG for manual inspection and asserts complete page coverage. | `soffice`, `pdftoppm`. |
| [`add_docx_alt_text.py`](add_docx_alt_text.py) | Adds descriptive figure alt text and core document properties to a DOCX package without changing its visible content. | Python standard library only. |

The GNN pin, pointer and specification checks live upstream, in
`gnn.importers` as shipped by the revision `.github/gnn-pin.json` names;
`./run.sh gnn` provisions `.venv-gnn` and runs it.

Arms: `./run.sh docs`, `./run.sh gnn`, `./run.sh release`, `./run.sh render`,
and `./run.sh measure`. The release
script is also the `release-check` task in [`.aii/config.yaml`](../.aii/config.yaml)
and runs in CI's `validate` job through `./run.sh ci`
([`.github/workflows/aeos.yml`](../.github/workflows/aeos.yml)); see
[`docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md) for every arm and the exact command
it runs.

`check_release.py` is the oracle for the digests recorded in
[`releases.json`](../releases.json): when a listed file changes, re-record its
digest in the same change or the gate fails.

See [`docs/publication.md`](../docs/publication.md) for the artifact rendering
rules and [`docs/contributing.md`](../docs/contributing.md) for the required
checks.
