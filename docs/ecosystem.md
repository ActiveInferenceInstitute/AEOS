# Ecosystem cross-reference

This page records how AEOS relates to the other notation and vocabulary
surfaces of the Active Inference Institute ecosystem. It is a cross-reference,
not a semantic mapping: AEOS identifiers are never equated with identifiers
from another vocabulary, and every statement below was checked against the
pinned revision named in the table.

## Surfaces

| Surface | Repository | Revision used for this cross-reference | Role |
| --- | --- | --- | --- |
| GNN | `ActiveInferenceInstitute/Generalized_Notation_Notation` | v5.0.3, commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1` | Notation and 25-step pipeline for specifying, validating, rendering, and executing active inference generative models. |
| Active Inference Ontology | `ActiveInferenceInstitute/Active_Inference_Ontology` | release v5, `main` = `0e127a5b5ed5db33a9fdd06be65c1dfca730dcf4`; bridge artifact `GNN/act_inf_ontology_terms.json` SHA-256 `b19e3d4c70cb7d47276978f4b1f21777089243f6a8514e86656b9e15f639656a` (64 declared labels, 12 resolved, 52 unresolved) | Controlled vocabulary of active inference and FEP concepts (429 terms, 238 typed relations) with a generated GNN vocabulary bridge. |
| ATLAS | `ActiveInferenceInstitute/ATLAS` | `main` | Question-oriented discovery over entity, pattern, and typed-relationship graphs. |
| AEOS | this repository | release v1.0.0 | Domain ontology of active and informational entities, roles, affordances, states, and interaction motifs in scientific ecosystems. |

## Verified overlaps (2026-11-01)

Method: casefold each label, remove every character outside `[a-z0-9]`, then
require a unique counterpart in the target surface. This is the rule the
ontology repository uses for its GNN vocabulary bridge, so both results are
directly comparable with that artifact.

- **AEOS vs. the ontology release v5.** 2 of the 71 AEOS records resolve:
  `state-internal` to `term-internal-state`, and `state-sense` to
  `term-sense-state`. No other AEOS record resolves.
- **AEOS vs. GNN's annotation surface.** 0 of the 71 AEOS records match any of
  the 64 labels GNN declares for `ActInfOntologyAnnotation` (Step 10).

## What is not claimed

- AEOS is not part of GNN's `ActInfOntologyAnnotation` surface: GNN model
  files do not annotate variables with AEOS identifiers, and no AEOS file is a
  GNN model source.
- AEOS is not part of the ontology's generated bridge
  (`GNN/act_inf_ontology_terms.json`); that artifact projects the 429-term
  ontology release only.
- The two resolved labels above are exact-label coincidences under a shared
  normalization rule. This repository does not treat them as an integration,
  and does not assert identifier equivalence.

## Where each surface documents itself

- GNN: `docs/gnn/integration/README.md` and
  `docs/gnn/integration/framework_integration_guide.md` (integration),
  `docs/gnn/advanced/ontology_system.md` (annotation surface) at the pinned
  revision.
- Active Inference Ontology: `docs/downstream-integration.md` and
  `GNN/README.md` (bridge artifact and freshness contract).
- ATLAS: `README.md` and `docs/index.md`.

## If a real integration is added later

Follow the ontology bridge precedent: declare the target labels as a reviewed
input, resolve them with one explicit rule, record every unresolved label with
a null target, and gate the projection so it cannot drift from its source. Do
not hand-write mappings in prose or code, and do not adopt another project's
local identifiers as canonical.
