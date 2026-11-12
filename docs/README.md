# AEOS Documentation

Hub for everything outside the code. Start with the [documentation
index](documentation-index.md) for a flat list, or go straight to a page below.

**Quick reference:** [Documentation index](documentation-index.md) |
[Gate and CI run guide](RUN_GUIDE.md) | [Generated gate metrics](_generated/gate-metrics.md) |
[GNN conformance](gnn-conformance.md)

| Document | Use it for |
| --- | --- |
| [Model](model.md) | The conceptual entities, states, roles, affordances, and motifs. |
| [Data contract](data-contract.md) | Source fields, IDs, references, and export stability. |
| [CLI reference](cli.md) | Every command, option, default, exit code, and JSON payload. |
| [Forking](forking.md) | Creating an independent, validated AEOS derivative. |
| [Contributing](contributing.md) | Curation, review, validation, and release steps. |
| [Gate and CI run guide](RUN_GUIDE.md) | Fast default, explicit full gates, shared CI environment and local acceptance. |
| [Publication](publication.md) | Source paper, archived artifacts, and rendering rules. |
| [Ecosystem cross-reference](ecosystem.md) | How AEOS relates to GNN, the Active Inference Ontology, and ATLAS; verified overlaps only. |
| [GNN conformance](gnn-conformance.md) | The importer pin, the `.github/GNN.md` pointer, and the two conformance arms. |
| [Documentation index](documentation-index.md) | The flat index of long-lived documents. |
| [Generated metrics](_generated/gate-metrics.md) | Scripted before/after arm wall times, results, collected tests and coverage. |

Measured facts live in one place: [`_generated/`](_generated/README.md). Guides
link it instead of repeating a count or a duration, and its files come from a
script rather than an edit.

The local source file is authoritative for repository builds. The Coda page is
an interactive reference and the DOI is the publication record. Artifact-level
rendering notes live in [`../paper/README.md`](../paper/README.md), and the
release and accessibility scripts are described in
[`../scripts/README.md`](../scripts/README.md).
