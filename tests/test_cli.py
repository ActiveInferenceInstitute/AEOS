from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from aeos.cli import main
from aeos.core import DEFAULT_INPUT, DEFAULT_SCHEMA


def test_validate_json_success(capsys) -> None:
    assert main(["validate", "--input", str(DEFAULT_INPUT), "--schema", str(DEFAULT_SCHEMA), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["errors"] == []


def test_build_check_accepts_current_export(tmp_path: Path, capsys) -> None:
    output = tmp_path / "aeos.json"
    assert main(["build", "--output", str(output)]) == 0
    capsys.readouterr()
    assert main(["build", "--output", str(output), "--check"]) == 0
    assert "current" in capsys.readouterr().out


def test_build_check_rejects_stale_export(tmp_path: Path, capsys) -> None:
    output = tmp_path / "aeos.json"
    assert main(["build", "--output", str(output)]) == 0
    capsys.readouterr()
    output.write_text(output.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert main(["build", "--output", str(output), "--check"]) == 1
    assert "stale" in capsys.readouterr().err


def test_build_json_failure_is_structured(tmp_path: Path, capsys) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("schema_version: '1.0.0'\n", encoding="utf-8")
    result = main(["build", "--input", str(invalid), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["valid"] is False
    assert payload["errors"]


def test_validate_failure_has_nonzero_exit(tmp_path: Path, capsys) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("schema_version: '1.0.0'\n", encoding="utf-8")
    result = main(["validate", "--input", str(invalid)])
    assert result == 1
    assert "ERROR" in capsys.readouterr().out


def test_report_invalid_source_returns_json_failure(tmp_path: Path, capsys) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("schema_version: '1.0.0'\n", encoding="utf-8")
    result = main(["report", "--input", str(invalid)])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["valid"] is False
    assert payload["errors"]


def test_report_is_machine_readable(capsys) -> None:
    assert main(["report"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["source"] == "data/aeos.yaml"
    assert payload["summary"]["motif_count"] > 0


def test_validate_success_text(capsys) -> None:
    assert main(["validate"]) == 0
    assert "Valid AEOS source" in capsys.readouterr().out


def test_validate_missing_input_is_structured(tmp_path: Path, capsys) -> None:
    absent = tmp_path / "absent.yaml"
    result = main(["validate", "--input", str(absent), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["errors"][0]["code"] == "missing-input"


def test_build_missing_input_is_structured(tmp_path: Path, capsys) -> None:
    absent = tmp_path / "absent.yaml"
    result = main(["build", "--input", str(absent), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["valid"] is False
    assert payload["errors"][0]["code"] == "missing-input"


def test_build_errors_report_to_stderr(tmp_path: Path, capsys) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("schema_version: '1.0.0'\n", encoding="utf-8")
    result = main(["build", "--input", str(invalid)])
    assert result == 1
    assert "ERROR" in capsys.readouterr().err


def test_build_json_written_and_current(tmp_path: Path, capsys) -> None:
    output = tmp_path / "aeos.json"
    assert main(["build", "--output", str(output), "--format", "json"]) == 0
    written = json.loads(capsys.readouterr().out)
    assert written["valid"] is True and written["status"] == "written"
    assert main(["build", "--output", str(output), "--check", "--format", "json"]) == 0
    current = json.loads(capsys.readouterr().out)
    assert current["valid"] is True and current["status"] == "current"


def test_build_check_json_missing_export(tmp_path: Path, capsys) -> None:
    output = tmp_path / "missing.json"
    result = main(["build", "--output", str(output), "--check", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["error"] == "missing-export"


def test_build_check_json_stale_export(tmp_path: Path, capsys) -> None:
    output = tmp_path / "aeos.json"
    assert main(["build", "--output", str(output)]) == 0
    capsys.readouterr()
    output.write_text(output.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = main(["build", "--output", str(output), "--check", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["error"] == "stale-export"


def test_report_missing_input_is_structured(tmp_path: Path, capsys) -> None:
    absent = tmp_path / "absent.yaml"
    result = main(["report", "--input", str(absent)])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["errors"][0]["code"] == "missing-input"


def test_diff_json_reports_change(tmp_path: Path, capsys) -> None:
    old = tmp_path / "old.yaml"
    new = tmp_path / "new.yaml"
    old.write_text("schema_version: '1.0.0'\nontology:\n  version: '1.0.0'\n  description: a\n", encoding="utf-8")
    new.write_text("schema_version: '1.0.0'\nontology:\n  version: '1.0.1'\n  description: b\n", encoding="utf-8")
    result = main(["diff", str(old), str(new), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 2
    assert payload["has_changes"] is True


def test_diff_text_no_changes(tmp_path: Path, capsys) -> None:
    body = "schema_version: '1.0.0'\n"
    left = tmp_path / "left.yaml"
    right = tmp_path / "right.yaml"
    left.write_text(body, encoding="utf-8")
    right.write_text(body, encoding="utf-8")
    result = main(["diff", str(left), str(right)])
    assert result == 0
    assert "No ontology changes." in capsys.readouterr().out


def test_diff_text_reports_collection_kinds(tmp_path: Path, capsys) -> None:
    old = tmp_path / "old.yaml"
    new = tmp_path / "new.yaml"
    old.write_text(
        "schema_version: '1.0.0'\nentity_types:\n"
        "  - id: type-a\n    label: A\n    class: class-active\n    description: d\n",
        encoding="utf-8",
    )
    new.write_text(
        "schema_version: '1.0.0'\nentity_types:\n"
        "  - id: type-a\n    label: A\n    class: class-active\n    description: d\n"
        "  - id: type-b\n    label: B\n    class: class-active\n    description: d\n",
        encoding="utf-8",
    )
    result = main(["diff", str(old), str(new)])
    assert result == 2
    assert "added entity_types: type-b" in capsys.readouterr().out


def test_diff_missing_input_is_structured(tmp_path: Path, capsys) -> None:
    right = tmp_path / "right.yaml"
    right.write_text("schema_version: '1.0.0'\n", encoding="utf-8")
    result = main(["diff", str(tmp_path / "absent.yaml"), str(right), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["has_changes"] is False
    assert payload["errors"]


def test_python_dash_m_entrypoint() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "aeos", "validate", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["valid"] is True


def test_cli_module_entrypoint() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "aeos.cli", "validate", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["valid"] is True
