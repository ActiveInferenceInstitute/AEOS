# AEOS command-line reference

The `aeos` package provides four local, deterministic commands for working
with an AEOS ontology source. Install the package (see the repository
[`README.md`](../README.md)) to get the `aeos` console script; the same
interface is available as `python -m aeos` or `python -m aeos.cli`.

All commands operate on local files only. None of them call Coda, GitHub,
Zenodo, or any network service.

## Common options

Every command accepts `--help`. Commands that read an ontology source accept
`--input` and `--schema`, defaulting to the canonical repository files;
`build` additionally accepts `--output`:

| Option | Default | Commands |
| --- | --- | --- |
| `--input` | `data/aeos.yaml` | `validate`, `build`, `report` |
| `--schema` | `schema/aeos.schema.json` | `validate`, `build`, `report` |
| `--output` | `aeos.json` | `build` |

The `--format` option selects `text` (default) or `json` output where
available. `report` always emits JSON.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success; for `diff`, no changes detected. |
| `1` | Validation, build, or report failure; stale or missing export; `diff` input error. |
| `2` | `diff` detected changes between the two documents. |

## `validate`

Validate an ontology source against the schema and semantic rules.

```bash
aeos validate [--input PATH] [--schema PATH] [--format {text,json}]
```

Text mode prints `Valid AEOS source: <path>` or one `ERROR` line per problem.
JSON mode prints `{"valid": bool, "errors": [...]}`, where each error carries
a `code`, a `message`, and a `path` when one applies. The validator checks
structure, IDs, references, roles, affordances, states, relationships, and
motif steps.

## `build`

Build the deterministic JSON export from a validated source, or check that an
existing export is current.

```bash
aeos build [--input PATH] [--schema PATH] [--output PATH]
           [--check] [--format {text,json}]
```

Without `--check`, writes the export (creating parent directories as needed)
and reports `Wrote <path>`. With `--check`, compares the existing file against
what would be written and reports `Generated export is current` or
`Generated export is stale`; a missing export is reported as such. Any stale
or missing state returns exit code `1`.

The export contains the source collections plus a deterministic derived
`graph` (`nodes`, `edges`) and a `summary` of collection and graph counts.

## `report`

Print a machine-readable report for a source document.

```bash
aeos report [--input PATH] [--schema PATH] [--format json]
```

Always prints JSON: `{"valid": bool, "errors": [...], "source": str,
"ontology": {...}, "summary": {...}}`. Returns `1` when the source has
validation errors.

## `diff`

Compare two ontology source or export files (YAML or JSON).

```bash
aeos diff OLD NEW [--format {text,json}]
```

Both documents are canonicalized (collections sorted by ID, reference lists
sorted, motif steps ordered by sequence) before comparison. The result lists
`added`, `removed`, and `changed` identifiers per collection, plus `metadata`
changes (for example `schema_version` or `ontology`). Text mode prints one
line per change; JSON mode prints the full structured result with a
`has_changes` flag. Returns `0` when there are no changes and `2` when there
are.

## See also

- [`README.md`](../README.md) — quick start and canonical surfaces.
- [`model.md`](model.md) — the conceptual model behind the data.
- [`data-contract.md`](data-contract.md) — source fields, IDs, references,
  and export stability.
- [`contributing.md`](contributing.md) — the required check commands,
  including the coverage gate.
