from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed")

MENU = ("run.sh", "pyproject.toml", "uv.lock")


def gate_copy(destination: Path) -> Path:
    """Copy the gate entry point and its lockfile inputs into a bounded tree."""
    for name in MENU:
        shutil.copy2(ROOT / name, destination / name)
    return destination / "run.sh"


@needs_uv
def test_lock_arm_refuses_stale_lockfile(tmp_path: Path) -> None:
    """A dependency change without `uv lock` must fail before any arm runs."""
    runner = gate_copy(tmp_path)
    original_lock = (tmp_path / "uv.lock").read_bytes()
    fresh = subprocess.run(
        [str(runner), "lock"], cwd=tmp_path, capture_output=True, text=True, check=False, timeout=120
    )
    assert fresh.returncode == 0, fresh.stderr

    project = tmp_path / "pyproject.toml"
    edited = project.read_text(encoding="utf-8").replace('"PyYAML>=6.0,<7"', '"PyYAML>=6.0,<6.1"')
    project.write_text(edited, encoding="utf-8")

    stale = subprocess.run(
        [str(runner), "lock"], cwd=tmp_path, capture_output=True, text=True, check=False, timeout=120
    )
    assert stale.returncode != 0
    assert (tmp_path / "uv.lock").read_bytes() == original_lock


UV_BOUNDARY = r'''
import os
import subprocess
import sys
from pathlib import Path

root = Path.cwd()
args = sys.argv[1:]
if args[:2] == ["lock", "--check"]:
    raise SystemExit(0)
if args and args[0] in {"venv", "pip"}:
    print("fixture GNN acquisition unavailable", file=sys.stderr)
    raise SystemExit(23)
if args[:4] != ["run", "--locked", "--extra", "test"]:
    raise SystemExit("unexpected external-tool boundary")
selected = args[4:]
if selected[0] == "aeos":
    command = [sys.executable, "-B", "-m", "aeos", *selected[1:],
               "--input", str(root / "data" / "aeos.yaml"),
               "--schema", str(root / "schema" / "aeos.schema.json")]
    if selected[1] == "build":
        command += ["--output", str(root / "aeos.json")]
    raise SystemExit(subprocess.run(command, check=False).returncode)
if selected[0] == "python":
    raise SystemExit(subprocess.run([sys.executable, "-B", *selected[1:]], check=False).returncode)
if selected[0] in {"ruff", "pytest"}:
    raise SystemExit(0)
raise SystemExit("unexpected project boundary")
'''

RELEASE_BOUNDARY = '''
import json
from pathlib import Path
value = json.loads(Path("release-input.json").read_text())
if value.get("approved") is not True:
    raise SystemExit("fixture publication refused")
Path("release-outcome.json").write_text(json.dumps({"published": True}))
'''


def composition_tree(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("check_docs.py", "gate_metrics.py"):
        shutil.copy2(ROOT / "scripts" / name, scripts / name)
    (scripts / "check_release.py").write_text(RELEASE_BOUNDARY, encoding="utf-8")
    runner = gate_copy(tmp_path)
    for name in ("data", "schema", ".github"):
        (tmp_path / name).mkdir()
    for relative in ("data/aeos.yaml", "schema/aeos.schema.json", ".github/gnn-pin.json"):
        shutil.copy2(ROOT / relative, tmp_path / relative)
    subprocess.run(
        [sys.executable, "-B", "-m", "aeos", "build",
         "--input", str(tmp_path / "data" / "aeos.yaml"),
         "--schema", str(tmp_path / "schema" / "aeos.schema.json"),
         "--output", str(tmp_path / "aeos.json")],
        check=True,
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("[index](documentation-index.md)\n", encoding="utf-8")
    (docs / "documentation-index.md").write_text("# Index\n", encoding="utf-8")
    sys.path.insert(0, str(ROOT / "scripts"))
    import gate_metrics

    gate_metrics.write({"schema": gate_metrics.SCHEMA, "current": gate_metrics.unmeasured(), "history": []},
                       docs / "_generated")
    (tmp_path / "release-input.json").write_text('{"approved":true}', encoding="utf-8")
    tools = tmp_path / "tools"
    tools.mkdir()
    uv = tools / "uv"
    uv.write_text("#!" + sys.executable + "\n" + UV_BOUNDARY, encoding="utf-8")
    uv.chmod(0o755)
    environment = {**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"],
                   "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    return runner, environment


def invoke_composition(runner: Path, environment: dict[str, str], arm: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(runner), arm], cwd=runner.parent, env=environment,
                          capture_output=True, text=True, check=False, timeout=60)


def test_project_ci_reaches_release_without_gnn_acquisition(tmp_path: Path) -> None:
    runner, environment = composition_tree(tmp_path)
    result = invoke_composition(runner, environment, "ci-project")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads((tmp_path / "release-outcome.json").read_text()) == {"published": True}


@pytest.mark.parametrize("arm", ["gate", "ci"])
def test_full_local_composites_do_not_silently_skip_gnn(arm: str, tmp_path: Path) -> None:
    runner, environment = composition_tree(tmp_path)
    result = invoke_composition(runner, environment, arm)
    assert result.returncode == 23
    assert "GNN acquisition unavailable" in result.stderr
    assert not (tmp_path / "release-outcome.json").exists()


@pytest.mark.parametrize("arm", ["ci-project", "gate", "ci"])
@pytest.mark.parametrize("invalid", ["source", "export"])
def test_project_failure_refuses_before_release_or_gnn(arm: str, invalid: str, tmp_path: Path) -> None:
    runner, environment = composition_tree(tmp_path)
    if invalid == "source":
        (tmp_path / "data" / "aeos.yaml").write_text("schema_version: '1.0.0'\n", encoding="utf-8")
    else:
        (tmp_path / "aeos.json").write_text("stale bytes", encoding="utf-8")
    before = (tmp_path / "aeos.json").read_bytes()
    result = invoke_composition(runner, environment, arm)
    assert result.returncode == 1
    assert "GNN acquisition unavailable" not in result.stderr
    assert not (tmp_path / "release-outcome.json").exists()
    assert (tmp_path / "aeos.json").read_bytes() == before


def test_project_ci_propagates_release_failure(tmp_path: Path) -> None:
    runner, environment = composition_tree(tmp_path)
    (tmp_path / "release-input.json").write_text('{"approved":false}', encoding="utf-8")
    result = invoke_composition(runner, environment, "ci-project")
    assert result.returncode != 0
    assert "publication refused" in result.stderr
    assert not (tmp_path / "release-outcome.json").exists()


def test_hosted_selected_commands_have_separate_project_and_gnn_outcomes(tmp_path: Path) -> None:
    runner, environment = composition_tree(tmp_path)
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "aeos.yml").read_text(encoding="utf-8"))
    project_step = next(step for step in workflow["jobs"]["validate"]["steps"]
                        if step.get("run", "").startswith("./run.sh "))
    gnn_step = next(step for step in workflow["jobs"]["gnn-conformance"]["steps"]
                    if step.get("run", "").startswith("./run.sh "))
    project = invoke_composition(runner, environment, project_step["run"].split()[1])
    assert project.returncode == 0, project.stderr
    assert (tmp_path / "release-outcome.json").exists()
    gnn = invoke_composition(runner, environment, gnn_step["run"].split()[1])
    assert gnn.returncode == 23
    assert "GNN acquisition unavailable" in gnn.stderr
