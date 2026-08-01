from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from aeos.core import (
    DEFAULT_INPUT,
    DEFAULT_OUTPUT,
    DEFAULT_SCHEMA,
    OntologyError,
    build_document,
    diff_documents,
    load_schema,
    load_source,
    read_json,
    read_yaml,
    semantic_errors,
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


def test_diff_reports_removed_records() -> None:
    old = source()
    new = copy.deepcopy(old)
    del new["entity_classes"][0]
    result = diff_documents(old, new)
    assert result["has_changes"] is True
    assert "class-active" in result["removed"]["entity_classes"]


def test_read_yaml_missing_input_raises(tmp_path: Path) -> None:
    with pytest.raises(OntologyError) as excinfo:
        read_yaml(tmp_path / "absent.yaml")
    assert excinfo.value.code == "missing-input"


def test_read_yaml_malformed_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(": :\n  - broken\n", encoding="utf-8")
    with pytest.raises(OntologyError) as excinfo:
        read_yaml(bad)
    assert excinfo.value.code == "yaml-parse"


def test_read_yaml_non_mapping_root_raises(tmp_path: Path) -> None:
    bad = tmp_path / "list.yaml"
    bad.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(OntologyError) as excinfo:
        read_yaml(bad)
    assert excinfo.value.code == "root-type"


def test_read_json_missing_input_raises(tmp_path: Path) -> None:
    with pytest.raises(OntologyError) as excinfo:
        read_json(tmp_path / "absent.json")
    assert excinfo.value.code == "missing-input"


def test_read_json_malformed_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(OntologyError) as excinfo:
        read_json(bad)
    assert excinfo.value.code == "json-parse"


def test_read_json_non_mapping_root_raises(tmp_path: Path) -> None:
    bad = tmp_path / "array.json"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(OntologyError) as excinfo:
        read_json(bad)
    assert excinfo.value.code == "root-type"


def test_non_list_collection_value_is_ignored() -> None:
    document = source()
    document["roles"] = "not-a-list"
    errors = semantic_errors(document)
    assert isinstance(errors, list)


def test_reference_type_mismatch_is_rejected() -> None:
    document = source()
    document["roles"][0]["entity_types"] = ["affordance-publishes-knowledge-artifact"]
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "reference-type" for error in errors)


def test_invalid_kebab_case_id_is_rejected() -> None:
    document = source()
    document["entity_types"][0]["id"] = "Bad ID!"
    errors = semantic_errors(document)
    assert any(error.code == "invalid-id" for error in errors)


def test_non_string_id_is_skipped() -> None:
    document = source()
    document["entity_types"][0]["id"] = 123
    errors = semantic_errors(document)
    assert not any(error.code == "invalid-id" for error in errors)


def test_unknown_relationship_reference_is_rejected() -> None:
    document = source()
    document["relationships"][0]["source"] = "does-not-exist"
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)


def test_unknown_affordance_object_is_rejected() -> None:
    document = source()
    document["affordances"][0]["objects"].append("does-not-exist")
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    assert any(error.code == "unknown-reference" for error in errors)
