"""Command-line interface for AEOS validation and exports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (
    DEFAULT_INPUT,
    DEFAULT_OUTPUT,
    DEFAULT_SCHEMA,
    ROOT,
    OntologyError,
    build_document,
    diff_documents,
    load_schema,
    load_source,
    report,
    serialize,
    validate_document,
)


def _path(value: str) -> Path:
    return Path(value).expanduser()


def _source_label(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _write_or_check(output: Path, content: str, check: bool, output_format: str) -> int:
    def emit(payload: dict) -> None:
        if output_format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

    if check:
        try:
            current = output.read_text(encoding="utf-8")
        except FileNotFoundError:
            if output_format == "json":
                emit({"valid": False, "output": str(output), "error": "missing-export"})
            else:
                print(f"Generated export is missing: {output}", file=sys.stderr)
            return 1
        if current != content:
            if output_format == "json":
                emit({"valid": False, "output": str(output), "error": "stale-export"})
            else:
                print(f"Generated export is stale: {output}", file=sys.stderr)
            return 1
        if output_format == "json":
            emit({"valid": True, "output": str(output), "status": "current"})
        else:
            print(f"Generated export is current: {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    if output_format == "json":
        emit({"valid": True, "output": str(output), "status": "written"})
    else:
        print(f"Wrote {output}")
    return 0


def _load_and_validate(input_path: Path, schema_path: Path) -> tuple[dict, list[OntologyError]]:
    document = load_source(input_path)
    errors = validate_document(document, load_schema(schema_path))
    return document, errors


def command_validate(args: argparse.Namespace) -> int:
    try:
        document, errors = _load_and_validate(args.input, args.schema)
    except OntologyError as error:
        errors = [error]
    payload = {"valid": not errors, "errors": [error.as_dict() for error in errors]}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if errors:
            for error in errors:
                location = f" ({error.path})" if error.path else ""
                print(f"ERROR {error.code}{location}: {error.message}")
        else:
            print(f"Valid AEOS source: {args.input}")
    return 1 if errors else 0


def command_build(args: argparse.Namespace) -> int:
    try:
        document, errors = _load_and_validate(args.input, args.schema)
    except OntologyError as error:
        if args.format == "json":
            print(
                json.dumps({"valid": False, "errors": [error.as_dict()]}, ensure_ascii=False, indent=2, sort_keys=True)
            )
        else:
            print(f"ERROR {error.code}: {error.message}", file=sys.stderr)
        return 1
    if errors:
        if args.format == "json":
            print(
                json.dumps(
                    {"valid": False, "errors": [error.as_dict() for error in errors]},
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            for error in errors:
                print(f"ERROR {error.code} ({error.path}): {error.message}", file=sys.stderr)
        return 1
    source_label = _source_label(args.input)
    built = build_document(document, source_label)
    return _write_or_check(args.output, serialize(built), args.check, args.format)


def command_report(args: argparse.Namespace) -> int:
    try:
        document, errors = _load_and_validate(args.input, args.schema)
    except OntologyError as error:
        payload = {"valid": False, "source": _source_label(args.input), "errors": [error.as_dict()]}
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1
    payload = report(document, errors, _source_label(args.input))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


def command_diff(args: argparse.Namespace) -> int:
    try:
        result = diff_documents(load_source(args.old), load_source(args.new))
    except OntologyError as error:
        if args.format == "json":
            print(
                json.dumps(
                    {"has_changes": False, "errors": [error.as_dict()]}, ensure_ascii=False, indent=2, sort_keys=True
                )
            )
        else:
            print(f"ERROR {error.code}: {error.message}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if not result["has_changes"]:
            print("No ontology changes.")
        else:
            for kind in ("added", "removed", "changed"):
                for collection, identifiers in result[kind].items():
                    print(f"{kind} {collection}: {', '.join(identifiers)}")
    return 0 if not result["has_changes"] else 2


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="aeos", description="Validate and export the Active Entity Ontology for Science."
    )
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="Validate an ontology source file.")
    validate.add_argument("--input", type=_path, default=DEFAULT_INPUT)
    validate.add_argument("--schema", type=_path, default=DEFAULT_SCHEMA)
    validate.add_argument("--format", choices=("text", "json"), default="text")
    validate.set_defaults(function=command_validate)

    build = commands.add_parser("build", help="Build or check the deterministic JSON export.")
    build.add_argument("--input", type=_path, default=DEFAULT_INPUT)
    build.add_argument("--schema", type=_path, default=DEFAULT_SCHEMA)
    build.add_argument("--output", type=_path, default=DEFAULT_OUTPUT)
    build.add_argument("--check", action="store_true")
    build.add_argument("--format", choices=("text", "json"), default="text")
    build.set_defaults(function=command_build)

    report_command = commands.add_parser("report", help="Print a machine-readable validation report.")
    report_command.add_argument("--input", type=_path, default=DEFAULT_INPUT)
    report_command.add_argument("--schema", type=_path, default=DEFAULT_SCHEMA)
    report_command.add_argument("--format", choices=("json",), default="json")
    report_command.set_defaults(function=command_report)

    diff = commands.add_parser("diff", help="Compare two ontology source or export files.")
    diff.add_argument("old", type=_path)
    diff.add_argument("new", type=_path)
    diff.add_argument("--format", choices=("text", "json"), default="text")
    diff.set_defaults(function=command_diff)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
