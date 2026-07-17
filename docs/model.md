# AEOS model

AEOS has two entity classes:

- **Active entities** select policies and enact affordances through perception,
  cognition, and action.
- **Informational entities** contain information or represent epistemic
  resources acted upon by active entities.

Entity types belong to exactly one class. Roles describe contextual work an
entity may perform. Affordances describe capacities for action and identify
their possible areas, actors, targets, and informational objects.

Every active entity is modeled with three state categories:

- **Internal state**: the entity's modeled generative process;
- **Sense state**: incoming statistical dependencies from the niche;
- **Active state**: outgoing dependencies enacted through action selection.

Areas of concern group scientific coordination patterns: funding,
communication, cryptographic relationships, scientific review, research and
analysis, and publishing. Motifs are ordered, typed examples that connect an
actor, an affordance, a target, and optionally an informational object.

The model is intentionally explicit. Relationships are data, not inferred from
free prose, so downstream tools can validate and render them consistently.
