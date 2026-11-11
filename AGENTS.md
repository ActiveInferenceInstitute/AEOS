# AGENTS.md — working in the AEOS repository

AEOS (Active Entity Ontology for Science) is a public repository of the Active
Inference Institute. It holds a portable ontology of active and informational
entities, roles, affordances, states, and interaction motifs, plus the local
tooling that validates, exports, and publishes it.

## Canonical surfaces

| Path | Role |
| --- | --- |
| `data/aeos.yaml` | Canonical human-editable source. Edit this, not the export. |
| `aeos.json` | Deterministic export; regenerate with `aeos build`. |
| `schema/aeos.schema.json` | Structural contract for the source. |
| `releases.json` | Release manifest with counts and SHA-256 digests for the current release. |
| `scripts/check_release.py` | Full release gate (see below). |
| `docs/` | Model, data contract, CLI, forking, contributing, publication, ecosystem. |
| `paper/` | Maintained publication source and rendered artifacts. |
| `archive/2022-v2/` | Preserved 2022/v2 snapshot with its checksum manifest. |

Each code folder carries its own guide: [`scripts/README.md`](scripts/README.md),
[`src/README.md`](src/README.md), and [`tests/README.md`](tests/README.md). The
documentation index is [`docs/README.md`](docs/README.md).

## Ground rules

- Every command is local and deterministic; no command calls a network service.
- IDs are kebab-case and globally unique, and references must resolve.
- Edit `data/aeos.yaml` and regenerate `aeos.json`; never hand-edit the export.
- When a file listed in `releases.json` changes, re-record its digest in the
  same change; the release gate fails on a stale digest.
- Docs must match the code and data; verify claims against the pinned sources.
- The repository license is CC BY 4.0; preserve attribution and the DOI.

## Gates

Install once:
`python3 -m venv .venv && .venv/bin/python -m pip install -e '.[test]'`.

```bash
.venv/bin/aeos validate --format json      # schema and semantic validation
.venv/bin/aeos build --check               # deterministic export freshness
.venv/bin/pytest                           # suite with the 90% coverage gate
.venv/bin/ruff check src tests scripts     # lint
.venv/bin/python scripts/check_release.py  # release gate
```

`check_release.py` also verifies the release manifest and digests, the
sidecar, archive checksums, PDF/DOCX/HTML accessibility and freshness, and
renders the maintained publication artifacts to page images. Rendering needs
`soffice` (LibreOffice), `qpdf`, `pdftotext`, `pdfinfo`, and `pdftoppm`; CI
installs them. The gate's other checks run without them.

Sidecar conventions for `.aii/` are in [`.aii/AGENTS.md`](.aii/AGENTS.md).

## Ecosystem

`docs/ecosystem.md` records the verified cross-reference to GNN (v5.0.3,
commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`), the Active Inference
Ontology release v5 bridge, and ATLAS. These are cross-references, not
identifier mappings: do not equate AEOS identifiers with another vocabulary,
and do not add a mapping without the reviewed-input and resolution process the
ontology bridge uses.
