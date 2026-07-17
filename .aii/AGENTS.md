# Agent guide for `.aii/`

- Keep `config.yaml` valid as a standalone `aii-sidecar/v1` document.
- Update `meta.updated` and `meta.sidecar_version` when sidecar structure changes.
- Keep artifact paths aligned with files that actually exist.
- Do not duplicate dynamic GitHub facts such as stars, size, or language.
- Keep the repository license, ontology license, and provenance fields aligned.
- Keep `releases.json` synchronized with the current ontology export.
- Run `python -m aeos validate`, `python -m aeos build --check`, and
  `python -m pytest` before completing a substantive change.
