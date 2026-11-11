# InstituteOS integration — AEOS

## Identity

| Field | Value |
| --- | --- |
| Repository | `ActiveInferenceInstitute/AEOS` |
| Affiliation | `institute` |
| Category | `ontology` |
| Status | `active` |
| Maturity | `released` |
| Steward | Active Inference Institute |
| Default branch | `main` |
| Current release | v1.0.0 |
| License | `CC-BY-4.0` |
| Citation | Active Inference Institute — AEOS, version 1.0.0. |

## Federation

| Setting | Value |
| --- | --- |
| Dashboard mode | `repos` |
| Analytics | `true` |
| Dashboard | `true` |
| Sync policy | `pull` |
| Registries | — |
| Tags | aeos, entity, ontology, science |

## Ecosystem relations

| Repository | Relation | Note |
| --- | --- | --- |
| `ActiveInferenceInstitute/InstituteOS` | `referenced-by` | Federated via the InstituteOS .aii manifest. |
| `ActiveInferenceInstitute/Active_Inference_Ontology` | `references` | Related controlled vocabulary; verified 2026-11-01 that 2 of 71 AEOS labels match release v5 terms by normalized label only (state-internal, state-sense) and no identifiers are shared. See docs/ecosystem.md. |

## Key artifacts

| Path | Kind | Description |
| --- | --- | --- |
| `README.md` | `doc` | Repository overview. |
| `data/aeos.yaml` | `source` | Canonical human-editable AEOS source. |
| `aeos.json` | `export` | Deterministic machine-readable AEOS export. |
| `schema/aeos.schema.json` | `model` | JSON Schema and structural data contract. |
| `releases.json` | `doc` | Release and provenance manifest. |
| `docs/` | `doc` | Model, integration, fork, curation, and publication documentation. |
| `paper/` | `doc` | Maintained publication source and artifact notes. |
| `paper/aeos.md` | `source` | Maintained editable publication source. |
| `paper/aeos-local.pdf` | `export` | Reproducible local PDF generated from the maintained source. |
| `paper/aeos-local.docx` | `export` | Editable DOCX generated from the maintained source. |
| `paper/aeos-local.html` | `export` | Accessible browser-readable export generated from the maintained source. |
| `paper/aeos-2022-v2.pdf` | `export` | Warning-free normalized PDF of the preserved 2022/v2 paper. |
| `paper/aeos-2022-v2.docx` | `export` | Editable copy of the preserved 2022/v2 paper. |
| `archive/2022-v2/` | `doc` | Preserved 2022/v2 publication snapshot. |
| `archive/2022-v2/checksums.json` | `other` | Machine-readable checksums for the preserved historical binaries. |
| `LICENSE` | `doc` | License. |

## Portable tasks

| Task | Command | Working directory | Description |
| --- | --- | --- | --- |
| `validate` | `python -m aeos validate --format json` | `.` | Validate the canonical AEOS source. |
| `build` | `python -m aeos build` | `.` | Build the deterministic JSON export. |
| `check` | `python -m aeos build --check` | `.` | Verify that the generated JSON export is current. |
| `report` | `python -m aeos report --format json` | `.` | Produce a machine-readable validation report. |
| `test` | `python -m pytest` | `.` | Run the ontology and CLI test suite. |
| `lint` | `ruff check src tests scripts` | `.` | Run the repository Python lint gate. |
| `release-check` | `python scripts/check_release.py` | `.` | Run ontology, sidecar, archive, document, and rendering release gates. |
| `render` | `python scripts/render_artifacts.py` | `.` | Render every maintained PDF and DOCX page to PNG for inspection. |

## Validation

```bash
python -m aii_platform.aii_sidecar.validate <repo> --completeness
python -m aii_platform.aii_sidecar docs <repo> --overwrite
python -m aii_platform.aii_sidecar.run <repo> --list
```

The sidecar is valid when `validate` prints `OK` and reports no missing artifact,
manifest, link, or declared-doc path. Completeness is a curation target, not a
runtime requirement.

## Data boundary

This sidecar carries metadata only. It does not grant execution permission, does not
replace the repository's own documentation, and must not be used to move private
content into a public repository. Task execution is limited to trusted checkouts.
