# Data contract

`data/aeos.yaml` must contain `schema_version: "1.0.0"` and the following
collections:

| Collection | Required identity and references |
| --- | --- |
| `entity_classes` | `id`, `label`, `description`; exactly `class-active` and `class-informational`. |
| `entity_types` | `id`, `label`, `class`, `description`; `class` references an entity class. |
| `areas_of_concern` | `id`, `label`, `description`. |
| `roles` | `id`, `label`, `description`, `entity_types`, `affordances`. |
| `affordances` | `id`, `label`, `description`, `areas`, `actors`, `targets`, `objects`. |
| `states` | `id`, `label`, `kind`, `description`; `kind` is `internal`, `sense`, or `active`. |
| `relationships` | `id`, `source`, kebab-case `relation`, `target`, `description`. |
| `motifs` | `id`, `label`, `area`, `context`, `description`, ordered `steps`. |

IDs are globally unique kebab-case identifiers. References must resolve to an
existing ID of the appropriate collection. Motif sequences start at one and
must be contiguous. `context` is either `cesci` or `desci`.

`aeos.json` is generated and must not be edited directly. Its top-level source
collections preserve the YAML data, while `graph.nodes` and `graph.edges` are
derived deterministically. Consumers should join by ID and display labels.

The schema file checks shape and scalar constraints. The `aeos validate`
command additionally checks cross-collection references and semantic rules.

`aeos diff` canonicalizes both inputs before comparison, reports metadata
changes as well as collection changes, and returns exit code `2` when any
change is present.
