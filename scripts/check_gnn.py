#!/usr/bin/env python3
"""Verify the GNN importer pin, its records, and the pinned parser conformance.

The static checks need no network and no third-party packages. They read the
pin, the workflow that consumes it, and every document that restates it, so a
stale revision, a renamed job, or a second copy of the parser logic fails here
instead of silently drifting.

``--parser`` additionally imports the pinned ``gnn`` package and runs the
conformance steps in one place; the workflow calls this mode through
``./run.sh gnn-parser`` and holds no copy of them.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PIN_PATH = Path(".github/gnn-pin.json")
POINTER_PATH = Path(".github/GNN.md")
WORKFLOW_PATH = Path(".github/workflows/aeos.yml")
RUN_GUIDE_PATH = Path("docs/RUN_GUIDE.md")
CONFORMANCE_DOC_PATH = Path("docs/gnn-conformance.md")
ECOSYSTEM_DOC_PATH = Path("docs/ecosystem.md")

PIN_SCHEMA = "gnn-importer-pin/v1"
PACKAGE = "generalized-notation-notation"
JOB_KEY = "gnn-conformance"
JOB_NAME = "gnn conformance (pinned)"
COMPOSITE_ACTION = (
    "ActiveInferenceInstitute/.github/.github/actions/setup-python-uv"
    "@7159e67315330aac8e414aebae0ad1e999a41448"
)
PARSER_DEPENDENCIES = ("defusedxml", "psutil", "pyyaml")
EXEMPLAR = "input/gnn_files/basics/static_perception.md"
SKIP_PARTS = {".git", "qa", "node_modules"}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def read_pin() -> dict[str, Any]:
    return json.loads((ROOT / PIN_PATH).read_text(encoding="utf-8"))


def check_pin(failures: list[str]) -> dict[str, Any]:
    try:
        pin = read_pin()
    except (OSError, json.JSONDecodeError) as error:
        fail(f"{PIN_PATH} is unreadable: {error}", failures)
        return {}
    if not isinstance(pin, dict):
        fail(f"{PIN_PATH} must contain a JSON object", failures)
        return {}
    if pin.get("schema") != PIN_SCHEMA:
        fail(f"{PIN_PATH} schema is not {PIN_SCHEMA}", failures)
    repository = str(pin.get("repository", ""))
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        fail(f"{PIN_PATH} repository is not an owner/name pair", failures)
    if not re.fullmatch(r"[0-9a-f]{40}", str(pin.get("revision", ""))):
        fail(f"{PIN_PATH} revision is not a 40-character commit id", failures)
    if not re.fullmatch(r"v\d+\.\d+\.\d+", str(pin.get("tag", ""))):
        fail(f"{PIN_PATH} tag is not a vX.Y.Z release tag", failures)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(pin.get("recorded", ""))):
        fail(f"{PIN_PATH} recorded is not a YYYY-MM-DD date", failures)
    return pin


def check_workflow(failures: list[str]) -> None:
    try:
        workflow = (ROOT / WORKFLOW_PATH).read_text(encoding="utf-8")
    except OSError as error:
        fail(f"{WORKFLOW_PATH} is unreadable: {error}", failures)
        return
    if f"  {JOB_KEY}:" not in workflow:
        fail(f"{WORKFLOW_PATH} no longer defines the {JOB_KEY} job", failures)
    if f"name: {JOB_NAME}" not in workflow:
        fail(f"{WORKFLOW_PATH} no longer names the job {JOB_NAME!r}", failures)
    if "./run.sh gnn-parser" not in workflow:
        fail(f"{WORKFLOW_PATH} does not call ./run.sh gnn-parser", failures)
    if "parse_gnn_formal" in workflow or "validate_gnn_files" in workflow:
        fail(f"{WORKFLOW_PATH} holds a second copy of the parser conformance", failures)
    if COMPOSITE_ACTION not in workflow:
        fail(f"{WORKFLOW_PATH} does not use the pinned setup-python-uv action", failures)


def check_documents(pin: dict[str, Any], failures: list[str]) -> None:
    documents = (
        (POINTER_PATH, True),
        (CONFORMANCE_DOC_PATH, True),
        (ECOSYSTEM_DOC_PATH, False),
    )
    for document, names_job in documents:
        try:
            text = (ROOT / document).read_text(encoding="utf-8")
        except OSError as error:
            fail(f"{document} is unreadable: {error}", failures)
            continue
        if PIN_PATH.as_posix() not in text:
            fail(f"{document} does not name {PIN_PATH.as_posix()}", failures)
        if names_job and JOB_NAME not in text:
            fail(f"{document} does not name the {JOB_NAME!r} job", failures)
        for field in ("tag", "revision"):
            value = str(pin.get(field, ""))
            if value and value not in text:
                fail(f"{document} does not record the pinned {field} {value}", failures)
    try:
        guide = (ROOT / RUN_GUIDE_PATH).read_text(encoding="utf-8")
    except OSError as error:
        fail(f"{RUN_GUIDE_PATH} is unreadable: {error}", failures)
        return
    if COMPOSITE_ACTION not in guide:
        fail(f"{RUN_GUIDE_PATH} does not record the pinned setup-python-uv action", failures)
    if JOB_KEY not in guide:
        fail(f"{RUN_GUIDE_PATH} does not name the {JOB_KEY} job", failures)
    try:
        doc = (ROOT / CONFORMANCE_DOC_PATH).read_text(encoding="utf-8")
    except OSError:
        return
    if PIN_SCHEMA not in doc:
        fail(f"{CONFORMANCE_DOC_PATH} does not name the {PIN_SCHEMA} schema", failures)
    if JOB_KEY not in doc:
        fail(f"{CONFORMANCE_DOC_PATH} does not name the {JOB_KEY} job key", failures)
    if POINTER_PATH.as_posix() not in doc:
        fail(f"{CONFORMANCE_DOC_PATH} does not point at {POINTER_PATH.as_posix()}", failures)


def print_requirements() -> int:
    pin = read_pin()
    for dependency in PARSER_DEPENDENCIES:
        print(dependency)
    print(f"{PACKAGE} @ git+https://github.com/{pin['repository']}.git@{pin['revision']}")
    return 0


def repository_sketches() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.gnn.md")
        if not SKIP_PARTS.intersection(path.relative_to(ROOT).parts)
        and not any(part.startswith(".venv") for part in path.relative_to(ROOT).parts)
    )


def conformance_failures(failures: list[str]) -> dict[str, Any]:
    pin = read_pin()
    try:
        import gnn
        from gnn.parsers.basic import parse_gnn_formal, validate_gnn_syntax
        from gnn.type_checker import GNNTypeChecker
    except ImportError as error:
        fail(f"pinned GNN parser is not importable ({error}); run ./run.sh gnn-parser", failures)
        return {}
    expected_version = str(pin.get("tag", "")).removeprefix("v")
    if gnn.__version__ != expected_version:
        fail(f"installed GNN {gnn.__version__!r} does not match the pinned tag {pin.get('tag')!r}", failures)
        return {}

    sketches = repository_sketches()
    with tempfile.TemporaryDirectory(prefix="aeos-gnn-") as temporary:
        output_dir = Path(temporary)
        model_dir = output_dir / "models"
        model_dir.mkdir()
        if sketches:
            for sketch in sketches:
                parsed = parse_gnn_formal(sketch)
                if parsed is None or getattr(parsed, "parse_errors", None):
                    fail(f"{sketch.relative_to(ROOT)} did not parse cleanly", failures)
                valid, errors = validate_gnn_syntax(sketch.read_text(encoding="utf-8"))
                if not valid:
                    fail(f"{sketch.relative_to(ROOT)} syntax errors: {errors!r}", failures)
            for index, sketch in enumerate(sketches):
                shutil.copy2(sketch, model_dir / f"{index:03d}_{sketch.name}")
            source = "repository"
            models = len(sketches)
        else:
            url = (
                "https://raw.githubusercontent.com/"
                f"{pin['repository']}/{pin['revision']}/{EXEMPLAR}"
            )
            exemplar = output_dir / Path(EXEMPLAR).name
            try:
                urllib.request.urlretrieve(url, exemplar)
            except OSError as error:
                fail(f"pinned exemplar could not be downloaded from {url}: {error}", failures)
                return {}
            parsed = parse_gnn_formal(exemplar)
            if parsed is None or getattr(parsed, "parse_errors", None):
                fail("pinned exemplar did not parse cleanly", failures)
            valid, errors = validate_gnn_syntax(exemplar.read_text(encoding="utf-8"))
            if not valid:
                fail(f"pinned exemplar syntax errors: {errors!r}", failures)
            shutil.copy2(exemplar, model_dir / exemplar.name)
            source = "pinned-exemplar"
            models = 1
        result = GNNTypeChecker().validate_gnn_files(model_dir, output_dir)
        if not result:
            fail(f"GNN type checker rejected the {source} sketches", failures)
    return {
        "gnn-version": gnn.__version__,
        "models": models,
        "pin-revision": pin.get("revision"),
        "result": "verified",
        "source": source,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parser",
        action="store_true",
        help="also import the pinned gnn package and run the conformance steps",
    )
    parser.add_argument(
        "--print-requirements",
        action="store_true",
        help="print the pinned parser requirements, one per line",
    )
    args = parser.parse_args()

    if args.print_requirements:
        return print_requirements()

    failures: list[str] = []
    pin = check_pin(failures)
    check_workflow(failures)
    if pin:
        check_documents(pin, failures)
    receipt = conformance_failures(failures) if args.parser else {}
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    if receipt:
        print(json.dumps(receipt, sort_keys=True))
    else:
        print(f"GNN pin {pin.get('tag')} at {pin.get('revision')} matches its records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
