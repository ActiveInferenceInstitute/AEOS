from __future__ import annotations

import copy
import json

from aeos.core import (
    DEFAULT_INPUT,
    DEFAULT_OUTPUT,
    DEFAULT_SCHEMA,
    build_document,
    diff_documents,
    load_schema,
    load_source,
    serialize,
    validate_document,
)


def source() -> dict:
    return load_source(DEFAULT_INPUT)


def test_repository_source_is_valid() -> None:
    errors = validate_document(source(), load_schema(DEFAULT_SCHEMA))
    assert errors == []


def test_generated_graph_is_deterministic() -> None:
    document = source()
    first = serialize(build_document(document))
    second = serialize(build_document(copy.deepcopy(document)))
    assert first == second


def test_generated_graph_contains_all_nodes_and_edges() -> None:
    built = build_document(source())
    assert built["summary"]["graph_node_count"] == len(built["graph"]["nodes"])
    assert built["summary"]["graph_edge_count"] == len(built["graph"]["edges"])
    assert {node["id"] for node in built["graph"]["nodes"]}


def test_generated_export_satisfies_the_same_schema() -> None:
    errors = validate_document(load_source(DEFAULT_OUTPUT), load_schema(DEFAULT_SCHEMA))
    assert errors == []


def test_missing_required_field_is_rejected() -> None:
    document = source()
    del document["entity_types"][0]["label"]
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "schema" for error in errors)


def test_duplicate_ids_are_rejected() -> None:
    document = source()
    document["entity_types"].append(copy.deepcopy(document["entity_types"][0]))
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "duplicate-id" for error in errors)


def test_unknown_role_affordance_is_rejected() -> None:
    document = source()
    document["roles"][0]["affordances"].append("affordance-does-not-exist")
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)


def test_unknown_entity_class_reference_is_rejected() -> None:
    document = source()
    document["entity_types"][0]["class"] = "class-does-not-exist"
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)


def test_unknown_entity_type_reference_is_rejected() -> None:
    document = source()
    document["roles"][0]["entity_types"].append("type-does-not-exist")
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)


def test_unknown_area_reference_is_rejected() -> None:
    document = source()
    document["affordances"][0]["areas"].append("area-does-not-exist")
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)


def test_unknown_affordance_endpoint_is_rejected() -> None:
    document = source()
    document["affordances"][0]["actors"].append("type-does-not-exist")
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)


def test_invalid_state_kind_is_rejected() -> None:
    document = source()
    document["states"][0]["kind"] = "unknown"
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "schema" for error in errors)


def test_invalid_motif_sequence_is_rejected() -> None:
    document = source()
    document["motifs"][0]["steps"][0]["sequence"] = 2
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "sequence-contract" for error in errors)


def test_malformed_motif_endpoint_is_rejected() -> None:
    document = source()
    document["motifs"][0]["steps"][0]["target"] = "type-does-not-exist"
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)


def test_malformed_motif_step_is_rejected() -> None:
    document = source()
    del document["motifs"][0]["steps"][0]["target"]
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "schema" for error in errors)


def test_malformed_collection_values_return_structured_errors() -> None:
    document = source()
    document["roles"][0]["entity_types"] = None
    document["motifs"][0]["steps"] = None
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert sum(error.code == "schema" for error in errors) >= 2


def test_diff_reports_added_and_changed_records() -> None:
    old = source()
    new = copy.deepcopy(old)
    new["ontology"]["description"] = "Updated description"
    new["entity_classes"].append({"id": "class-example", "label": "Example", "description": "An additional class."})
    result = diff_documents(old, new)
    assert result["has_changes"] is True
    assert "class-example" in result["added"]["entity_classes"]
    assert "ontology" in result["changed"]["metadata"]


def test_export_is_json_serializable() -> None:
    built = build_document(source())
    parsed = json.loads(serialize(built))
    assert parsed["ontology"]["id"] == "aeos"
    assert parsed["source"] == "data/aeos.yaml"


def test_diff_ignores_export_wrappers_and_source_order() -> None:
    result = diff_documents(source(), load_source(DEFAULT_OUTPUT))
    assert result["has_changes"] is False
