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
| `run.sh` | Single gate entry point; every arm and the CI jobs call it. |
| `uv.lock` | Locked environment that every arm runs through `uv run --frozen`. |
| `scripts/check_release.py` | Full release gate (see below). |
| `docs/` | Model, data contract, CLI, forking, contributing, publication, ecosystem, run guide, GNN conformance. |
| `paper/` | Maintained publication source and rendered artifacts. |
| `archive/2022-v2/` | Preserved 2022/v2 snapshot with its checksum manifest. |

Each code folder carries its own guide: [`scripts/README.md`](scripts/README.md),
[`src/README.md`](src/README.md), and [`tests/README.md`](tests/README.md). The
documentation hub is [`docs/README.md`](docs/README.md), its flat index is
[`docs/documentation-index.md`](docs/documentation-index.md), and measured
numbers live only in [`docs/_generated/`](docs/_generated/README.md).

## Ground rules

- Every ontology command is local and deterministic; none of them calls a
  network service. The only network step in the repository is the optional
  `./run.sh gnn-parser` arm, which installs the pinned parser and exemplar.
- IDs are kebab-case and globally unique, and references must resolve.
- Edit `data/aeos.yaml` and regenerate `aeos.json`; never hand-edit the export.
- When a file listed in `releases.json` changes, re-record its digest in the
  same change; the release gate fails on a stale digest.
- Docs must match the code and data; verify claims against the pinned sources.
- The repository license is CC BY 4.0; preserve attribution and the DOI.

## Gates

`./run.sh` is the only gate entry point; CI calls the same arms, so a command
is written down once. Setup once with `./run.sh setup`, then:

```bash
./run.sh gate       # validate, build --check, lint, pytest, docs, gnn pin
./run.sh fast       # pytest without the coverage gate, while editing
./run.sh release    # release gate (needs soffice, qpdf, poppler)
./run.sh render     # page images for manual inspection
./run.sh list       # every arm
```

The individual arms are `./run.sh validate`, `build`, `lint`, `test`, `docs`,
`gnn`, and `gnn-parser`; [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md) lists the
exact command behind each one and the CI job that calls it.

`check_release.py` verifies the release manifest and digests, the sidecar,
archive checksums, PDF/DOCX/HTML accessibility and freshness, and renders the
maintained publication artifacts to page images. Rendering needs `soffice`
(LibreOffice), `qpdf`, `pdftotext`, `pdfinfo`, and `pdftoppm`; CI installs
them. The gate's other checks run without them.

The GNN conformance pin and its two arms are documented in
[`docs/gnn-conformance.md`](docs/gnn-conformance.md).

Sidecar conventions for `.aii/` are in [`.aii/AGENTS.md`](.aii/AGENTS.md).

## Ecosystem

`docs/ecosystem.md` records the verified cross-reference to GNN (v5.0.3,
commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`), the Active Inference
Ontology release v5 bridge, and ATLAS. These are cross-references, not
identifier mappings: do not equate AEOS identifiers with another vocabulary,
and do not add a mapping without the reviewed-input and resolution process the
ontology bridge uses.
