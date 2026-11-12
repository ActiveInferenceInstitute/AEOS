from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

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
