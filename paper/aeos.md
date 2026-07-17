---
title: "Active Entity Ontology for Science (AEOS)"
subtitle: "A portable, versioned model for scientific entities and interaction motifs"
author: "Active Inference Institute"
date: "2026-07-17"
license: "CC BY 4.0"
---

# Publication note

This maintained repository source turns the AEOS conceptual framework into a
portable, versioned, and locally validated ontology model. It is intended to
support forks, downstream tools, and future publication revisions.

The complete 2022/v2 binary source snapshot is preserved in
[`../archive/2022-v2/`](../archive/2022-v2/). The published work is identified
by [DOI 10.5281/zenodo.7484994](https://doi.org/10.5281/zenodo.7484994).

# Abstract

The Active Entity Ontology for Science (AEOS) describes scientific ecosystems
as networks of active and informational entities. Active entities select
policies and enact affordances, while informational entities contain or
represent the resources acted upon. AEOS organizes these concepts through
entity classes, entity types, roles, affordances, internal/sense/active states,
and explicit interaction motifs.

This repository provides a source-controlled representation of those concepts
in `data/aeos.yaml`, a JSON Schema contract, and a deterministic JSON export.
The design keeps relationships explicit so that forks and downstream systems
can validate and render AEOS without depending on an external interactive
application.

# Model

## Entity classes and types

AEOS has two entity classes: **Active Entity** and **Informational Entity**.
Active entities include humans, teams, organizations, computer systems, DAOs,
communities, laboratories, funding agencies, publishers, and knowledge
markets. Informational entities include knowledge artifacts, papers, datasets,
grants, code, intellectual property, assets, metadata, blockchains,
cryptographic identities, smart contracts, and project catechisms.

Each type belongs to exactly one class. The complete versioned list and each
definition are maintained in [`../data/aeos.yaml`](../data/aeos.yaml).

## States, roles, and affordances

An active entity is modeled through internal states, incoming sense states, and
outgoing active states. Roles describe contextual responsibilities. Affordances
describe possible actions and declare their actors, targets, informational
objects, and areas of concern.

The six current areas of concern are funding, communication, cryptographic
relationships, scientific review, research and analysis, and publishing.

## Interaction motifs

Motifs are ordered examples of ecosystem coordination. The source includes
centralized and decentralized motifs for funding, communication, scientific
review, research and analysis, and publishing. Each step names an actor,
affordance, target, and optional informational object. This makes the examples
machine-checkable while preserving the natural-language intent of the original
publication.

# Reproducible use

```bash
python3 -m pip install -e '.[test]'
aeos validate
aeos build
aeos build --check
```

The generated [`../aeos.json`](../aeos.json) contains the source collections
and a derived graph of typed nodes and edges. See
[`../docs/data-contract.md`](../docs/data-contract.md) for the stable contract.

# Attribution

This work is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Derived works should credit the Active Inference Institute, identify their AEOS
source release, and link to the publication DOI.
