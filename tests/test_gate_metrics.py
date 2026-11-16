from __future__ import annotations

import copy
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gate_metrics


@pytest.fixture
def tree(tmp_path: Path, monkeypatch) -> Path:
    for key in gate_metrics.OVERRIDES:
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ontology.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "gnn-pin.json").write_text('{"revision":"one"}', encoding="utf-8")
    (tmp_path / ".github" / "workflows" / "aeos.yml").write_text("run: ./run.sh ci-project\n", encoding="utf-8")
    runner = tmp_path / "run.sh"
    runner.write_text("#!/bin/sh\nprintf '%s\\n' '" + " ".join(
        list(gate_metrics.MEASURED_ARMS[:-1]) + ["measure"]
    ) + "'\n", encoding="utf-8")
    runner.chmod(0o755)
    monkeypatch.setattr(gate_metrics, "ROOT", tmp_path)
    monkeypatch.setattr(gate_metrics, "GENERATED", tmp_path / "docs" / "_generated")
    return tmp_path


def observed(root: Path, output: Path | None = None) -> dict:
    return {
        "schema": gate_metrics.OBSERVATION_SCHEMA,
        "measured_at": "2026-11-13T00:00:00+00:00", "source_revision": "fixture-revision",
        "host": {"platform": "fixture-host", "python": "fixture-python", "uv": "fixture-uv"},
        "input_binding": gate_metrics.source_fingerprint(root, output),
        "tests": {"collected": 3, "coverage_percent": 95.0},
        "arms": [{"name": arm, "seconds": 1.25, "status": "passed"} for arm in gate_metrics.MEASURED_ARMS],
    }


def report(current: dict) -> dict:
    return {"schema": gate_metrics.SCHEMA, "current": current, "history": []}


def test_legacy_observations_are_preserved_without_inventing_current_results(tree: Path, capsys) -> None:
    baseline = {
        "schema": gate_metrics.LEGACY_SCHEMA, "measured_at": "2026-11-12T00:00:00+00:00",
        "source_revision": "historical-fixture-before",
        "host": {"platform": "fixture-host", "python": "fixture-python", "uv": "fixture-uv"},
        "tests": {"collected": 68, "coverage_percent": 97.13},
        "arms": [{"name": arm, "seconds": 2.5, "status": "passed"} for arm in gate_metrics.LEGACY_ARMS],
    }
    original = {
        **copy.deepcopy(baseline), "baseline": baseline,
        "measured_at": "2026-11-12T01:00:00+00:00", "source_revision": "historical-fixture-after",
    }
    original["arms"][gate_metrics.LEGACY_ARMS.index("gnn")]["status"] = "failed (7)"
    saved = tree / "saved.json"
    saved.write_text(json.dumps(original), encoding="utf-8")
    output = tree / "evidence"
    assert gate_metrics.main(["--record", str(saved), "--output-dir", str(output)]) == 0
    capsys.readouterr()
    data = gate_metrics.load(output / "gate-metrics.json")
    assert data["history"] == [original]
    assert data["current"]["host"] is None
    assert data["current"]["tests"] == {"collected": None, "coverage_percent": None}
    assert next(row for row in data["current"]["arms"] if row["name"] == "ci-project") == {
        "name": "ci-project", "seconds": None, "status": "unmeasured",
    }
    rendered = (output / "gate-metrics.md").read_text(encoding="utf-8")
    assert "Historical observation 1" in rendered and "Historical observation 2" in rendered
    assert original["measured_at"] in rendered and original["baseline"]["measured_at"] in rendered
    assert "| ci-project | unmeasured | unmeasured |" in rendered
    assert gate_metrics.eligibility(data, tree) == "unmeasured"


@pytest.mark.parametrize("relative", ["src/ontology.py", "run.sh", ".github/gnn-pin.json", ".github/workflows/aeos.yml"])
def test_same_size_content_changes_invalidate_current_evidence(relative: str, tree: Path) -> None:
    data = report(observed(tree))
    assert gate_metrics.eligibility(data, tree) == "current"
    path = tree / relative
    original = path.read_bytes()
    times = path.stat()
    changed = bytes([original[0] ^ 1]) + original[1:]
    path.write_bytes(changed)
    os.utime(path, ns=(times.st_atime_ns, times.st_mtime_ns))
    assert gate_metrics.eligibility(data, tree) == "stale"


@pytest.mark.parametrize("change", ["add", "delete", "rename", "executable-mode"])
def test_membership_and_executable_mode_are_bound(change: str, tree: Path) -> None:
    data = report(observed(tree))
    source = tree / "src" / "ontology.py"
    if change == "add":
        (tree / "src" / "added.py").write_text("value = 2\n", encoding="utf-8")
    elif change == "delete":
        source.unlink()
    elif change == "rename":
        source.rename(source.with_name("renamed.py"))
    else:
        (tree / "run.sh").chmod(0o644)
    assert gate_metrics.eligibility(data, tree) == "stale"


def test_generated_outputs_do_not_bind_themselves_but_policy_does(tree: Path) -> None:
    generated = tree / "docs" / "_generated"
    custom = tree / "measurements"
    data = report(observed(tree, custom))
    binding = data["current"]["input_binding"]
    gate_metrics.write(data, generated)
    gate_metrics.write(data, custom)
    assert gate_metrics.source_fingerprint(tree, custom) == binding
    (generated / "README.md").write_text("# Evidence policy\n", encoding="utf-8")
    assert gate_metrics.eligibility(data, tree) == "stale"


def test_binding_is_checkout_location_independent(tree: Path, tmp_path: Path) -> None:
    destination = tmp_path.parent / (tmp_path.name + "-copy")
    try:
        shutil.copytree(tree, destination)
        assert gate_metrics.source_fingerprint(tree) == gate_metrics.source_fingerprint(destination)
    finally:
        if destination.exists():
            shutil.rmtree(destination)


def test_command_vectors_and_effective_overrides_are_bound(tree: Path, monkeypatch) -> None:
    data = report(observed(tree))
    original_commands = gate_metrics.commands()
    changed = copy.deepcopy(original_commands)
    changed["default"] = ["./run.sh", "fast"]
    monkeypatch.setattr(gate_metrics, "commands", lambda: changed)
    assert gate_metrics.eligibility(data, tree) == "stale"
    monkeypatch.setattr(gate_metrics, "commands", lambda: original_commands)
    monkeypatch.setenv("GNN_PYTHON", "different-interpreter")
    assert gate_metrics.eligibility(data, tree) == "stale"


def test_source_symlink_cannot_silently_escape_membership(tree: Path) -> None:
    (tree / "src" / "external.py").symlink_to(tree / "src" / "ontology.py")
    with pytest.raises(ValueError, match="nonregular source"):
        gate_metrics.source_fingerprint(tree)


def test_check_separates_current_stale_and_historical_evidence(tree: Path, monkeypatch) -> None:
    generated = tree / "docs" / "_generated"
    data = report(observed(tree))
    gate_metrics.write(data, generated)
    monkeypatch.setattr(gate_metrics, "collected_tests", lambda: 3)
    assert gate_metrics.check() == "current"
    monkeypatch.setattr(gate_metrics, "collected_tests", lambda: 4)
    with pytest.raises(ValueError, match="test count"):
        gate_metrics.check()
    (tree / "src" / "ontology.py").write_text("value = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="content, membership"):
        gate_metrics.check()
    archived = gate_metrics._archive(data)
    gate_metrics.write(archived, generated)
    assert gate_metrics.check() == "unmeasured"
    assert archived["history"] == [data["current"]]
    (generated / "gate-metrics.md").write_text("unrelated page", encoding="utf-8")
    with pytest.raises(ValueError, match="Markdown differs"):
        gate_metrics.check()


def test_historical_recording_does_not_execute_acquisition_or_collection(tree: Path, monkeypatch) -> None:
    data = report(observed(tree))
    saved = tree / "saved.json"
    saved.write_text(json.dumps(data), encoding="utf-8")

    def prohibited(*args, **kwargs):
        raise AssertionError("recording must not execute a subprocess or collect tests")

    monkeypatch.setattr(gate_metrics.subprocess, "run", prohibited)
    monkeypatch.setattr(gate_metrics, "collected_tests", prohibited)
    output = tree / "published"
    assert gate_metrics.main(["--record", str(saved), "--historical", "--output-dir", str(output)]) == 0
    published = gate_metrics.load(output / "gate-metrics.json")
    assert published["history"] == [data["current"]]
    assert published["current"] == gate_metrics.unmeasured()


@pytest.mark.parametrize("duration", [-1, True, float("nan"), float("inf")])
def test_invalid_observation_durations_are_refused(duration, tree: Path) -> None:
    data = report(observed(tree))
    data["current"]["arms"][0]["seconds"] = duration
    with pytest.raises(ValueError, match="duration/result"):
        gate_metrics.validate(data)


def test_unmeasured_inventory_cannot_inherit_old_observations(tree: Path) -> None:
    data = report(gate_metrics.unmeasured())
    data["current"]["tests"]["collected"] = 68
    with pytest.raises(ValueError, match="inherit test"):
        gate_metrics.validate(data)
    data = report(gate_metrics.unmeasured())
    data["current"]["arms"][0]["seconds"] = 0
    with pytest.raises(ValueError, match="cannot have durations"):
        gate_metrics.validate(data)


def test_measurement_records_failures_and_refuses_midrun_source_changes(tree: Path, monkeypatch) -> None:
    fixture_observation = observed(tree)

    def measure(arm):
        return {"name": arm, "seconds": 1.25, "status": "failed (7)" if arm == "gnn" else "passed"}, "Total coverage: 95.0%"

    def snapshot(rows, coverage, binding):
        return {**fixture_observation, "arms": rows, "input_binding": binding,
                "tests": {"collected": 3, "coverage_percent": coverage}}

    monkeypatch.setattr(gate_metrics, "measure_arm", measure)
    monkeypatch.setattr(gate_metrics, "snapshot", snapshot)
    output = tree / "docs" / "_generated"
    assert gate_metrics.main(["--measure", "--output-dir", str(output)]) == 1
    recorded = gate_metrics.load(output / "gate-metrics.json")
    assert next(row for row in recorded["current"]["arms"] if row["name"] == "gnn")["status"] == "failed (7)"
    assert gate_metrics.eligibility(recorded, tree) == "current"

    def changing_measure(arm):
        if arm == "gnn":
            (tree / "src" / "ontology.py").write_text("value = 9\n", encoding="utf-8")
        return measure(arm)

    monkeypatch.setattr(gate_metrics, "measure_arm", changing_measure)
    assert gate_metrics.main(["--measure", "--output-dir", str(output)]) == 1
    preserved = gate_metrics.load(output / "gate-metrics.json")
    assert preserved["current"] == gate_metrics.unmeasured()
    assert recorded["current"] in preserved["history"]


def test_explicit_missing_baseline_is_not_silently_replaced(tree: Path, monkeypatch) -> None:
    def prohibited(*args):
        raise AssertionError("cannot measure after an explicit baseline admission failure")

    monkeypatch.setattr(gate_metrics, "measure_arm", prohibited)
    assert gate_metrics.main(["--measure", "--baseline", str(tree / "absent.json")]) == 1
