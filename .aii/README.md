# `.aii` sidecar

This directory contains the standalone InstituteOS metadata for AEOS. The
sidecar describes the repository without replacing its ontology source,
generated export, documentation, or paper artifacts.

| File | Purpose |
| --- | --- |
| [`config.yaml`](config.yaml) | Machine-readable metadata using `aii-sidecar/v1`. |
| [`AGENTS.md`](AGENTS.md) | Maintenance guidance for repository agents. |
| [`readiness.json`](readiness.json) | This repository's tier, baseline commit and waivers for the organization's agent-readiness standard. |

The canonical ontology source is `../data/aeos.yaml`. Runnable repository tasks
are declared in `config.yaml` and use the local AEOS CLI after installation.
