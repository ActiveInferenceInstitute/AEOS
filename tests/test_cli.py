from __future__ import annotations

import json
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
