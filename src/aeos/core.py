"""Loading, validating, building, and comparing AEOS source documents."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import IO, Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "aeos.yaml"
DEFAULT_SCHEMA = ROOT / "schema" / "aeos.schema.json"
DEFAULT_OUTPUT = ROOT / "aeos.json"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
COLLECTIONS = (
    "entity_classes",
    "entity_types",
    "areas_of_concern",
    "roles",
    "affordances",
    "states",
    "relationships",
    "motifs",
)
REFERENCE_COLLECTIONS = {
    "class": "entity_classes",
    "type": "entity_types",
    "area": "areas_of_concern",
    "role": "roles",
    "affordance": "affordances",
    "state": "states",
    "relationship": "relationships",
    "motif": "motifs",
}


class OntologyError(Exception):
    """A user-correctable ontology loading or validation error."""

    def __init__(self, code: str, message: str, path: str = "") -> None:
        self.code = code
        self.message = message
        self.path = path
        super().__init__(message)

    def as_dict(self) -> dict[str, str]:
        result = {"code": self.code, "message": self.message}
        if self.path:
            result["path"] = self.path
        return result


def _read_mapping(
    path: Path,
    parse: Callable[[IO[str]], Any],
    syntax: str,
    parse_code: str,
) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            document = parse(handle)
    except FileNotFoundError as exc:
        raise OntologyError("missing-input", f"Input file does not exist: {path}") from exc
    except IsADirectoryError as exc:
        raise OntologyError("unreadable-input", f"Input path is a directory, not a file: {path}") from exc
    except PermissionError as exc:
        raise OntologyError("unreadable-input", f"Input file is not readable: {path}") from exc
    except OSError as exc:
        raise OntologyError("unreadable-input", f"Input file could not be read: {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise OntologyError("unreadable-input", f"Input file is not valid UTF-8 text: {path}") from exc
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise OntologyError(parse_code, f"Could not parse {syntax} in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise OntologyError("root-type", "Ontology source must contain a mapping at the root.")
    return document


def read_yaml(path: Path) -> dict[str, Any]:
    return _read_mapping(path, yaml.safe_load, "YAML", "yaml-parse")


def read_json(path: Path) -> dict[str, Any]:
    return _read_mapping(path, json.load, "JSON", "json-parse")


def load_source(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".json", ".jsonld"}:
        return read_json(path)
    return read_yaml(path)


def load_schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    return read_json(path)


def error_from_schema(error: Any) -> OntologyError:
    location = "".join(f"[{part!r}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path).lstrip(
        "."
    )
    return OntologyError("schema", error.message, location)


def structural_errors(document: dict[str, Any], schema: dict[str, Any]) -> list[OntologyError]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        error_from_schema(error)
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]


def _items(document: dict[str, Any], collection: str) -> list[dict[str, Any]]:
    value = document.get(collection, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _ids(document: dict[str, Any], collection: str) -> set[str]:
    return {item.get("id") for item in _items(document, collection) if isinstance(item.get("id"), str)}


def _all_records(document: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    records: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection in COLLECTIONS:
        for item in _items(document, collection):
            identifier = item.get("id")
            if isinstance(identifier, str) and identifier not in records:
                records[identifier] = (collection, item)
    return records


def _check_ref(
    errors: list[OntologyError],
    records: dict[str, tuple[str, dict[str, Any]]],
    identifier: Any,
    path: str,
    allowed: Iterable[str] | None = None,
) -> None:
    if not isinstance(identifier, str):
        return
    if identifier not in records:
        errors.append(OntologyError("unknown-reference", f"Unknown reference: {identifier}", path))
        return
    if allowed and records[identifier][0] not in allowed:
        expected = ", ".join(sorted(allowed))
        errors.append(OntologyError("reference-type", f"Reference {identifier} must target {expected}.", path))


def semantic_errors(document: dict[str, Any]) -> list[OntologyError]:
    errors: list[OntologyError] = []
    records = _all_records(document)
    seen: dict[str, str] = {}
    for collection in COLLECTIONS:
        for index, item in enumerate(_items(document, collection)):
            identifier = item.get("id")
            path = f"{collection}[{index}].id"
            if not isinstance(identifier, str):
                continue
            if not ID_PATTERN.fullmatch(identifier):
                errors.append(OntologyError("invalid-id", f"ID is not kebab-case: {identifier}", path))
            if identifier in seen:
                errors.append(
                    OntologyError(
                        "duplicate-id", f"ID {identifier} is duplicated in {seen[identifier]} and {path}.", path
                    )
                )
            else:
                seen[identifier] = path

    class_ids = _ids(document, "entity_classes")
    if class_ids != {"class-active", "class-informational"}:
        errors.append(
            OntologyError(
                "class-contract", "AEOS requires exactly class-active and class-informational.", "entity_classes"
            )
        )

    for index, item in enumerate(_items(document, "entity_types")):
        _check_ref(errors, records, item.get("class"), f"entity_types[{index}].class", {"entity_classes"})

    for index, item in enumerate(_items(document, "roles")):
        for field in ("entity_types", "affordances"):
            allowed = {"entity_types"} if field == "entity_types" else {"affordances"}
            references = item.get(field, [])
            if not isinstance(references, list):
                continue
            for ref_index, identifier in enumerate(references):
                _check_ref(errors, records, identifier, f"roles[{index}].{field}[{ref_index}]", allowed)

    for index, item in enumerate(_items(document, "affordances")):
        areas = item.get("areas", [])
        if isinstance(areas, list):
            for ref_index, identifier in enumerate(areas):
                _check_ref(
                    errors, records, identifier, f"affordances[{index}].areas[{ref_index}]", {"areas_of_concern"}
                )
        for field in ("actors", "targets", "objects"):
            references = item.get(field, [])
            if not isinstance(references, list):
                continue
            for ref_index, identifier in enumerate(references):
                _check_ref(
                    errors,
                    records,
                    identifier,
                    f"affordances[{index}].{field}[{ref_index}]",
                    {"entity_classes", "entity_types"},
                )

    for index, item in enumerate(_items(document, "relationships")):
        _check_ref(errors, records, item.get("source"), f"relationships[{index}].source")
        _check_ref(errors, records, item.get("target"), f"relationships[{index}].target")

    for index, item in enumerate(_items(document, "motifs")):
        _check_ref(errors, records, item.get("area"), f"motifs[{index}].area", {"areas_of_concern"})
        sequences: list[int] = []
        steps = item.get("steps", [])
        if not isinstance(steps, list):
            continue
        for step_index, step in enumerate(steps):
            step_path = f"motifs[{index}].steps[{step_index}]"
            if isinstance(step, dict):
                sequence = step.get("sequence")
                if isinstance(sequence, int):
                    sequences.append(sequence)
                _check_ref(errors, records, step.get("actor"), f"{step_path}.actor", {"entity_classes", "entity_types"})
                _check_ref(errors, records, step.get("affordance"), f"{step_path}.affordance", {"affordances"})
                _check_ref(
                    errors, records, step.get("target"), f"{step_path}.target", {"entity_classes", "entity_types"}
                )
                if "object" in step:
                    _check_ref(
                        errors, records, step.get("object"), f"{step_path}.object", {"entity_classes", "entity_types"}
                    )
        if sequences and sequences != list(range(1, len(sequences) + 1)):
            errors.append(
                OntologyError(
                    "sequence-contract",
                    "Motif step sequences must be contiguous starting at 1.",
                    f"motifs[{index}].steps",
                )
            )

    ontology = document.get("ontology", {})
    if isinstance(ontology, dict):
        provenance = ontology.get("provenance", {})
        if isinstance(provenance, dict) and ontology.get("license") != "CC-BY-4.0":
            errors.append(OntologyError("license-contract", "Ontology license must be CC-BY-4.0.", "ontology.license"))
    return errors


def validate_document(document: dict[str, Any], schema: dict[str, Any] | None = None) -> list[OntologyError]:
    schema = schema or load_schema()
    return structural_errors(document, schema) + semantic_errors(document)


def _sort_collection(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((copy.deepcopy(item) for item in items), key=lambda item: item.get("id", ""))


def canonical_document(document: dict[str, Any], source_label: str = "data/aeos.yaml") -> dict[str, Any]:
    result = copy.deepcopy(document)
    for collection in COLLECTIONS:
        result[collection] = _sort_collection(_items(result, collection))
    for item in result.get("roles", []) + result.get("affordances", []):
        for field in ("entity_types", "affordances", "areas", "actors", "targets", "objects"):
            if isinstance(item.get(field), list):
                item[field] = sorted(item[field])
    for motif in result.get("motifs", []):
        motif["steps"] = sorted(motif.get("steps", []), key=lambda item: item.get("sequence", 0))
    result["source"] = source_label
    return result


def graph_for(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for collection in COLLECTIONS:
        if collection in {"relationships", "motifs"}:
            continue
        for item in _items(document, collection):
            identifier = item["id"]
            node = {"id": identifier, "label": item.get("label", identifier), "type": collection}
            if item.get("description"):
                node["description"] = item["description"]
            nodes.append(node)

    for item in _items(document, "entity_types"):
        edges.append({"source": item["id"], "target": item["class"], "relation": "member-of"})
    for item in _items(document, "roles"):
        for identifier in item.get("entity_types", []):
            edges.append({"source": item["id"], "target": identifier, "relation": "applies-to"})
        for identifier in item.get("affordances", []):
            edges.append({"source": item["id"], "target": identifier, "relation": "enables"})
    for item in _items(document, "affordances"):
        for field, relation in (
            ("areas", "concerns"),
            ("actors", "actor"),
            ("targets", "target"),
            ("objects", "object"),
        ):
            for identifier in item.get(field, []):
                edges.append({"source": item["id"], "target": identifier, "relation": relation})
    for item in _items(document, "relationships"):
        edges.append(
            {"source": item["source"], "target": item["target"], "relation": item["relation"], "id": item["id"]}
        )
    for motif in _items(document, "motifs"):
        for step in motif.get("steps", []):
            edge = {
                "source": step["actor"],
                "target": step["target"],
                "relation": step["affordance"],
                "motif": motif["id"],
                "sequence": step["sequence"],
            }
            if step.get("object"):
                edge["object"] = step["object"]
            edges.append(edge)
    nodes.sort(key=lambda item: item["id"])
    edges.sort(
        key=lambda item: (
            item["source"],
            item["relation"],
            item["target"],
            item.get("motif", ""),
            item.get("sequence", 0),
        )
    )
    return {"nodes": nodes, "edges": edges}


def build_document(document: dict[str, Any], source_label: str = "data/aeos.yaml") -> dict[str, Any]:
    result = canonical_document(document, source_label)
    result["graph"] = graph_for(result)
    result["summary"] = {
        "class_count": len(result["entity_classes"]),
        "type_count": len(result["entity_types"]),
        "area_count": len(result["areas_of_concern"]),
        "role_count": len(result["roles"]),
        "affordance_count": len(result["affordances"]),
        "state_count": len(result["states"]),
        "relationship_count": len(result["relationships"]),
        "motif_count": len(result["motifs"]),
        "graph_node_count": len(result["graph"]["nodes"]),
        "graph_edge_count": len(result["graph"]["edges"]),
    }
    return result


def serialize(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def report(
    document: dict[str, Any], errors: list[OntologyError], source_label: str = "data/aeos.yaml"
) -> dict[str, Any]:
    if errors:
        summary = {
            "class_count": len(_items(document, "entity_classes")),
            "type_count": len(_items(document, "entity_types")),
            "area_count": len(_items(document, "areas_of_concern")),
            "role_count": len(_items(document, "roles")),
            "affordance_count": len(_items(document, "affordances")),
            "state_count": len(_items(document, "states")),
            "relationship_count": len(_items(document, "relationships")),
            "motif_count": len(_items(document, "motifs")),
        }
        summary.update({"graph_node_count": 0, "graph_edge_count": 0})
        ontology = document.get("ontology", {}) if isinstance(document.get("ontology"), dict) else {}
        source = source_label
    else:
        built = build_document(document, source_label)
        summary = built.get("summary", {})
        ontology = built.get("ontology", {})
        source = built.get("source")
    return {
        "valid": not errors,
        "errors": [error.as_dict() for error in errors],
        "source": source,
        "ontology": ontology,
        "summary": summary,
    }


def diff_documents(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old = canonical_document(old)
    new = canonical_document(new)
    result: dict[str, Any] = {"added": {}, "removed": {}, "changed": {}}
    metadata_changes = []
    if old.get("schema_version") != new.get("schema_version"):
        metadata_changes.append("schema_version")
    if old.get("ontology") != new.get("ontology"):
        metadata_changes.append("ontology")
    if metadata_changes:
        result["changed"]["metadata"] = metadata_changes
    for collection in COLLECTIONS:
        old_items = {item.get("id"): item for item in _items(old, collection)}
        new_items = {item.get("id"): item for item in _items(new, collection)}
        added = sorted(set(new_items) - set(old_items))
        removed = sorted(set(old_items) - set(new_items))
        changed = sorted(
            identifier
            for identifier in set(old_items) & set(new_items)
            if old_items[identifier] != new_items[identifier]
        )
        if added:
            result["added"][collection] = added
        if removed:
            result["removed"][collection] = removed
        if changed:
            result["changed"][collection] = changed
    result["has_changes"] = any(result[key] for key in ("added", "removed", "changed"))
    return result
