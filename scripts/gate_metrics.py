#!/usr/bin/env python3
"""Measure content-bound gate observations without relabelling historical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import stat
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "docs" / "_generated"
SCHEMA = "aeos-gate-metrics/v3"
OBSERVATION_SCHEMA = "aeos-gate-observation/v1"
LEGACY_SCHEMA = "aeos-gate-metrics/v2"
LEGACY_ARMS = (
    "setup", "lock", "validate", "build", "lint", "fast", "test", "compat",
    "docs", "gnn", "release", "render", "gate", "ci", "default",
)
MEASURED_ARMS = LEGACY_ARMS[:-2] + ("ci-project", "ci", "default")
DECLARED_OTHER_ARMS = {"measure"}
COVERAGE = re.compile(r"Total coverage:\s*([\d.]+)%")
SKIP_DIRECTORIES = {
    ".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "node_modules", "qa", "build", "dist", "tmp", "htmlcov",
}
OVERRIDES = ("GNN_PYTHON", "COMPAT_PYTHON", "UV_PYTHON", "UV_PROJECT_ENVIRONMENT")


def commands() -> dict[str, list[str]]:
    return {arm: ["./run.sh"] + ([] if arm == "default" else [arm]) for arm in MEASURED_ARMS}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def source_fingerprint(root: Path = ROOT, output_directory: Path | None = None) -> dict[str, Any]:
    """Re-enumerate actual input membership and content, never just a saved file list."""
    root = root.resolve()
    output = None
    if output_directory is not None:
        try:
            output = output_directory.resolve().relative_to(root).as_posix()
        except ValueError:
            pass
    excluded = {"docs/_generated/gate-metrics.json", "docs/_generated/gate-metrics.md"}
    if output is not None:
        excluded.update((Path(output) / name).as_posix() for name in ("gate-metrics.json", "gate-metrics.md"))
    files = []
    for directory, directories, names in os.walk(root, topdown=True, followlinks=False):
        parent = Path(directory)
        directories[:] = sorted(
            name for name in directories
            if name not in SKIP_DIRECTORIES and not name.startswith(".venv") and not name.endswith(".egg-info")
        )
        for name in directories:
            if (parent / name).is_symlink():
                raise ValueError(f"cannot bind a source directory symlink: {(parent / name).relative_to(root)}")
        for name in sorted(names):
            path = parent / name
            relative = path.relative_to(root).as_posix()
            if relative in excluded or name in {".git", ".DS_Store", "coverage.xml"} or name.startswith(".coverage"):
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"cannot bind a nonregular source input: {relative}")
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            files.append({"path": relative, "sha256": digest.hexdigest(), "mode": stat.S_IMODE(path.stat().st_mode)})
    value = {
        "files": sorted(files, key=lambda item: item["path"]), "commands": commands(),
        "output_directory": output, "environment": {key: os.environ.get(key) for key in OVERRIDES},
    }
    return {**value, "sha256": _digest(value)}


def collected_tests() -> int | None:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "--no-cov"],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=120,
    )
    if completed.returncode != 0:
        return None
    counts = re.findall(r":\s*(\d+)\s*$", completed.stdout, re.MULTILINE)
    return sum(map(int, counts)) if counts else None


def command(arm: str) -> list[str]:
    return [str(ROOT / "run.sh")] + ([] if arm == "default" else [arm])


def measure_arm(arm: str) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    completed = subprocess.run(command(arm), cwd=ROOT, capture_output=True, text=True, check=False)
    row = {
        "name": arm, "seconds": round(time.monotonic() - started, 2),
        "status": "passed" if completed.returncode == 0 else f"failed ({completed.returncode})",
    }
    print(f"{arm}: {row['seconds']:.2f}s {row['status']}", file=sys.stderr)
    if completed.returncode:
        print(completed.stdout + completed.stderr, file=sys.stderr)
    return row, completed.stdout


def unmeasured() -> dict[str, Any]:
    return {
        "schema": OBSERVATION_SCHEMA, "measured_at": None, "source_revision": None,
        "host": None, "input_binding": None,
        "tests": {"collected": None, "coverage_percent": None},
        "arms": [{"name": arm, "seconds": None, "status": "unmeasured"} for arm in MEASURED_ARMS],
    }


def snapshot(rows: list[dict[str, Any]], coverage: float | None, binding: dict[str, Any]) -> dict[str, Any]:
    uv = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=False, timeout=30)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, check=False, timeout=30,
    )
    return {
        "schema": OBSERVATION_SCHEMA, "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_revision": revision.stdout.strip(),
        "host": {"platform": platform.platform(terse=True), "python": platform.python_version(), "uv": uv.stdout.strip()},
        "input_binding": binding, "tests": {"collected": collected_tests(), "coverage_percent": coverage},
        "arms": rows,
    }


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _validate_observation(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or data.get("schema") not in {LEGACY_SCHEMA, OBSERVATION_SCHEMA}:
        raise ValueError("invalid historical/current observation schema")
    prior_schema = data["schema"] == LEGACY_SCHEMA
    inventory = LEGACY_ARMS if prior_schema else MEASURED_ARMS
    if tuple(row["name"] for row in data["arms"]) != inventory:
        raise ValueError("observation must cover its own schema's arms exactly once, in order")
    empty = not prior_schema and all(row["status"] == "unmeasured" for row in data["arms"])
    for row in data["arms"]:
        if empty:
            if row["seconds"] is not None:
                raise ValueError("unmeasured arms cannot have durations")
        elif not _number(row["seconds"]) or not (
            row["status"] == "passed" or re.fullmatch(r"failed \(-?\d+\)", row["status"])
        ):
            raise ValueError(f"invalid duration/result for {row['name']}")
    if empty:
        if any(data.get(key) is not None for key in ("measured_at", "source_revision", "host", "input_binding")):
            raise ValueError("unmeasured current inventory cannot inherit observation provenance")
        if data["tests"] != {"collected": None, "coverage_percent": None}:
            raise ValueError("unmeasured current inventory cannot inherit test observations")
        return
    measured_at = datetime.fromisoformat(data["measured_at"])
    if measured_at.tzinfo is None:
        raise ValueError("measurement timestamp must have a timezone")
    if any(not isinstance(data["host"].get(key), str) or not data["host"][key] for key in ("platform", "python", "uv")):
        raise ValueError("measurement host/runtime identity is incomplete")
    count = data["tests"]["collected"]
    coverage = data["tests"]["coverage_percent"]
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError("invalid collected count")
    if coverage is not None and (not _number(coverage) or coverage > 100):
        raise ValueError("invalid coverage observation")
    if not prior_schema:
        binding = data["input_binding"]
        if not isinstance(binding, dict) or binding.get("sha256") != _digest(
            {key: value for key, value in binding.items() if key != "sha256"}
        ):
            raise ValueError("invalid content/membership binding")
    if data.get("baseline") is not None:
        _validate_observation(data["baseline"])


def validate(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise TypeError("metrics must be a mapping")
    if data.get("schema") == LEGACY_SCHEMA:
        _validate_observation(data)
        return
    if data.get("schema") != SCHEMA or not isinstance(data.get("history"), list):
        raise ValueError(f"metrics schema must be {SCHEMA}")
    _validate_observation(data["current"])
    if data["current"]["schema"] != OBSERVATION_SCHEMA:
        raise ValueError("prior-schema observations must remain historical, not current")
    for observation in data["history"]:
        _validate_observation(observation)


def normalize(data: dict[str, Any]) -> dict[str, Any]:
    validate(data)
    if data["schema"] == LEGACY_SCHEMA:
        return {"schema": SCHEMA, "current": unmeasured(), "history": [data]}
    return data


def load(path: Path) -> dict[str, Any]:
    return normalize(json.loads(path.read_text(encoding="utf-8")))


def eligibility(data: dict[str, Any], root: Path = ROOT) -> str:
    current = normalize(data)["current"]
    binding = current["input_binding"]
    if binding is None:
        return "unmeasured"
    output = binding.get("output_directory")
    actual = source_fingerprint(root, root / output if output is not None else None)
    return "current" if binding == actual else "stale"


def _observations(data: dict[str, Any]):
    for observation in data["history"]:
        if observation.get("baseline") is not None:
            yield from _historical_baselines(observation["baseline"])
        yield observation


def _historical_baselines(observation: dict[str, Any]):
    if observation.get("baseline") is not None:
        yield from _historical_baselines(observation["baseline"])
    yield observation


def render_markdown(data: dict[str, Any]) -> str:
    data = normalize(data)
    current = data["current"]
    lines = [
        "# Gate metrics", "",
        "<!-- generated by scripts/gate_metrics.py; refresh with ./run.sh measure -->", "",
        "Observations are not a statistical speedup claim. Historical measurements",
        "retain their original source/runtime/date and do not qualify current inputs.",
        "A bound observation is current only when --check matches its content, membership,",
        "selected commands and environment. GNN acquisition requires separate admission.", "",
        "## Current observation", "",
        f"- Measured at: {current['measured_at'] or 'unmeasured'}",
        f"- Input fingerprint: {current['input_binding']['sha256'] if current['input_binding'] else 'unmeasured'}",
        f"- Descriptive source HEAD: {current['source_revision'] or 'unmeasured'}",
        f"- Host/runtime: {json.dumps(current['host'], sort_keys=True) if current['host'] else 'unmeasured'}",
        f"- Collected tests: {current['tests']['collected'] if current['tests']['collected'] is not None else 'unmeasured'}",
        f"- Coverage (%): {current['tests']['coverage_percent'] if current['tests']['coverage_percent'] is not None else 'unmeasured'}",
        "", "| Arm | Command | Seconds | Result |", "| --- | --- | --- | --- |",
    ]
    for row in current["arms"]:
        invocation = "./run.sh" + ("" if row["name"] == "default" else " " + row["name"])
        duration = f"{row['seconds']:.2f}" if row["seconds"] is not None else "unmeasured"
        lines.append(f"| {row['name']} | `{invocation}` | {duration} | {row['status']} |")
    for index, observation in enumerate(_observations(data), 1):
        lines += [
            "", f"## Historical observation {index}", "",
            f"- Measured at: {observation['measured_at']}",
            f"- Descriptive source HEAD: {observation['source_revision']}",
            f"- Host/runtime: {json.dumps(observation['host'], sort_keys=True)}",
            f"- Collected tests: {observation['tests']['collected']}",
            f"- Coverage (%): {observation['tests']['coverage_percent']}",
            "", "| Arm | Seconds | Recorded result |", "| --- | --- | --- |",
        ]
        rows = {row["name"]: row for row in observation["arms"]}
        for arm in MEASURED_ARMS:
            row = rows.get(arm)
            duration = f"{row['seconds']:.2f}" if row and row["seconds"] is not None else "unmeasured"
            lines.append(f"| {arm} | {duration} | {row['status'] if row else 'unmeasured'} |")
    return "\n".join(lines) + "\n"


def write(data: dict[str, Any], directory: Path) -> None:
    data = normalize(data)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "gate-metrics.json").write_text(
        json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (directory / "gate-metrics.md").write_text(render_markdown(data), encoding="utf-8")


def check() -> str:
    data = load(GENERATED / "gate-metrics.json")
    if (GENERATED / "gate-metrics.md").read_text(encoding="utf-8") != render_markdown(data):
        raise ValueError("generated Markdown differs from JSON; publish recorded history with --record before measuring")
    arms = subprocess.run(
        [str(ROOT / "run.sh"), "list"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=30
    )
    if set(arms.stdout.split()) != (set(MEASURED_ARMS) - {"default"}) | DECLARED_OTHER_ARMS:
        raise ValueError("run.sh arm set differs from the current metric inventory")
    state = eligibility(data, ROOT)
    if state == "stale":
        raise ValueError("recorded input content, membership, commands or environment differs from current source")
    if state == "current":
        count = data["current"]["tests"]["collected"]
        if count is None or count != collected_tests():
            raise ValueError("recorded test count differs from the suite")
    return state


def _archive(data: dict[str, Any]) -> dict[str, Any]:
    history = list(data["history"])
    if data["current"]["input_binding"] is not None:
        history.append(data["current"])
    return {"schema": SCHEMA, "current": unmeasured(), "history": history}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--measure", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--record", type=Path, help="publish recorded observations without executing them")
    parser.add_argument("--historical", action="store_true", help="archive --record's current observation without relabelling it")
    parser.add_argument("--baseline", type=Path, help="retain all observations from an earlier report")
    parser.add_argument("--output-dir", type=Path, default=GENERATED)
    args = parser.parse_args(argv)
    if args.historical and not args.record:
        parser.error("--historical requires --record")
    if args.check and args.baseline:
        parser.error("--baseline does not apply to --check")
    try:
        if args.check:
            state = check()
            print("Gate metrics match current inputs." if state == "current" else
                  "Historical gate metrics are consistent; current measurements are unmeasured.")
            return 0
        if args.record:
            data = load(args.record)
            if args.historical:
                data = _archive(data)
        else:
            prior = args.baseline or (GENERATED / "gate-metrics.json")
            if args.baseline is not None or prior.exists():
                data = _archive(load(prior))
            else:
                data = {"schema": SCHEMA, "current": unmeasured(), "history": []}
            binding = source_fingerprint(ROOT, args.output_dir)
            if args.output_dir.resolve() == GENERATED.resolve():
                write(data, args.output_dir)
            rows = []
            coverage = None
            for arm in MEASURED_ARMS:
                row, output = measure_arm(arm)
                rows.append(row)
                if arm == "test":
                    match = COVERAGE.search(output)
                    coverage = float(match.group(1)) if match else None
            current = snapshot(rows, coverage, binding)
            if source_fingerprint(ROOT, args.output_dir) != binding:
                raise ValueError("source inputs changed during measurement; cannot publish a current observation")
            data["current"] = current
        if args.baseline and args.record:
            baseline = _archive(load(args.baseline))
            data = {**data, "history": baseline["history"] + data["history"]}
        write(data, args.output_dir)
        print(render_markdown(data), end="")
        return int(any(row["status"].startswith("failed") for row in data["current"]["arms"]))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
