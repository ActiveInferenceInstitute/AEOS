#!/usr/bin/env python3
"""Run repository-level release checks for AEOS."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aeos.core import (
    DEFAULT_INPUT,
    DEFAULT_SCHEMA,
    build_document,
    load_schema,
    load_source,
    validate_document,
)

ACTIVE_TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".toml", ".py"}
# Paths exempt from the authored-prose scan: `aeos.json` is the deterministic
# machine export of `data/aeos.yaml` (already scanned), and `TODO.md` is the
# project's task backlog whose checklist headings legitimately use the term
# "todo". Both are covered by their own dedicated checks instead.
ACTIVE_TEXT_EXEMPT_PATHS = {"TODO.md", "aeos.json"}
FORBIDDEN_TERMS = ("legacy", "stub", "mock", "placeholder", "todo", "fixme", "tbd", "wip", "dummy", "lorem")

# Distinctive identity tokens that every maintained "local" publication export
# must contain if it was regenerated from the current paper/aeos.md source.
PAPER_LOCAL_IDENTITY_TOKENS = (
    "active entity ontology for science (aeos)",
    "informational entity",
    "10.5281/zenodo.7484994",
)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def check_paths(failures: list[str]) -> None:
    required = [
        "README.md",
        "LICENSE",
        "data/aeos.yaml",
        "aeos.json",
        "schema/aeos.schema.json",
        "releases.json",
        "pyproject.toml",
        "uv.lock",
        "run.sh",
        ".gitattributes",
        ".aii/README.md",
        ".aii/AGENTS.md",
        ".github/workflows/aeos.yml",
        ".github/gnn-pin.json",
        ".github/GNN.md",
        "docs/",
        "docs/RUN_GUIDE.md",
        "docs/gnn-conformance.md",
        "docs/documentation-index.md",
        "docs/_generated/gate-metrics.md",
        "paper/",
        "paper/aeos-local.html",
        "archive/2022-v2/",
        "archive/2022-v2/checksums.json",
        ".aii/config.yaml",
    ]
    for relative in required:
        if not (ROOT / relative.rstrip("/")).exists():
            fail(f"missing required path: {relative}", failures)


def check_ontology(failures: list[str]) -> None:
    document = load_source(DEFAULT_INPUT)
    errors = validate_document(document, load_schema(DEFAULT_SCHEMA))
    for error in errors:
        fail(f"ontology {error.code} at {error.path}: {error.message}", failures)


def check_sidecar(failures: list[str]) -> None:
    sidecar_path = ROOT / ".aii" / "config.yaml"
    try:
        sidecar = yaml.safe_load(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        fail(f"sidecar parse failed: {error}", failures)
        return
    if not isinstance(sidecar, dict):
        fail("sidecar must contain a mapping at the root", failures)
        return
    if sidecar.get("schema") != "aii-sidecar/v1":
        fail("sidecar schema is not aii-sidecar/v1", failures)
    if sidecar.get("provenance", {}).get("license") != "CC-BY-4.0":
        fail("sidecar license is not CC-BY-4.0", failures)
    required_tasks = {"validate", "build", "check", "report", "test", "lint", "release-check", "render"}
    tasks = sidecar.get("tasks", {})
    if not isinstance(tasks, dict) or not required_tasks.issubset(tasks):
        fail("sidecar runnable task set is incomplete", failures)
    artifacts = sidecar.get("artifacts", [])
    if not isinstance(artifacts, list):
        fail("sidecar artifacts must be a list", failures)
        return
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            fail("sidecar artifact entries must be mappings", failures)
            continue
        path = str(artifact.get("path", "")).rstrip("/")
        if path and not (ROOT / path).exists():
            fail(f"sidecar artifact does not exist: {path}", failures)


def check_release_manifest(failures: list[str]) -> None:
    path = ROOT / "releases.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        current = next(item for item in manifest["releases"] if item.get("status") == "current")
        archived = next(item for item in manifest["releases"] if item.get("status") == "archived")
    except (OSError, json.JSONDecodeError, KeyError, StopIteration, TypeError) as error:
        fail(f"release manifest is invalid: {error}", failures)
        return
    source_document = load_source(DEFAULT_INPUT)
    if validate_document(source_document, load_schema(DEFAULT_SCHEMA)):
        return
    document = build_document(source_document)
    expected_counts = {
        "entityClasses": "class_count",
        "entityTypes": "type_count",
        "areasOfConcern": "area_count",
        "roles": "role_count",
        "affordances": "affordance_count",
        "states": "state_count",
        "relationships": "relationship_count",
        "motifs": "motif_count",
        "graphNodes": "graph_node_count",
        "graphEdges": "graph_edge_count",
    }
    if manifest.get("currentRelease") != current.get("version"):
        fail("release manifest currentRelease does not match its current entry", failures)
    sidecar_path = ROOT / ".aii" / "config.yaml"
    try:
        sidecar = yaml.safe_load(sidecar_path.read_text(encoding="utf-8"))
        sidecar_release = sidecar.get("provenance", {}).get("current_release")
    except (OSError, AttributeError, TypeError, yaml.YAMLError) as error:
        fail(f"sidecar release metadata could not be read: {error}", failures)
        sidecar_release = None
    if sidecar_release != current.get("version"):
        fail("sidecar current_release does not match releases.json", failures)
    if archived.get("checksums") != "archive/2022-v2/checksums.json":
        fail("archived release does not point to its checksum manifest", failures)
    if current.get("version") != f"v{document['ontology']['version']}":
        fail("release manifest version does not match ontology version", failures)
    for output in current.get("sourceFiles", []) + current.get("generatedFiles", []):
        if not (ROOT / output).exists():
            fail(f"release manifest file does not exist: {output}", failures)
    for manifest_key, summary_key in expected_counts.items():
        if current.get("counts", {}).get(manifest_key) != document["summary"].get(summary_key):
            fail(f"release manifest count is stale: {manifest_key}", failures)


def check_release_digests(failures: list[str], root: Path | None = None) -> None:
    """Verify the current release's recorded SHA-256 file digests.

    ``releases.json`` binds the current release to the exact bytes of its
    source and generated files. Without digests the manifest proves only that
    files exist and that counts match; with them, any edited or regenerated
    artifact that was not re-recorded fails the gate.

    ``root`` defaults to the repository root; callers may pass an alternative
    root so the oracle is testable against a small synthetic tree.
    """
    root = ROOT if root is None else root
    try:
        manifest = json.loads((root / "releases.json").read_text(encoding="utf-8"))
        current = next(item for item in manifest["releases"] if item.get("status") == "current")
    except (OSError, json.JSONDecodeError, KeyError, StopIteration, TypeError) as error:
        fail(f"release digests could not be read: {error}", failures)
        return
    digests = current.get("digests")
    if (
        not isinstance(digests, dict)
        or digests.get("algorithm") != "sha256"
        or not isinstance(digests.get("files"), dict)
    ):
        fail("current release must record sha256 file digests", failures)
        return
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(digests.get("recorded", ""))):
        fail("release digests must record the date they were taken", failures)
    for relative, expected in sorted(digests["files"].items()):
        path = root / relative
        if not path.is_file():
            fail(f"release digest file does not exist: {relative}", failures)
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            fail(f"release digest mismatch: {relative}", failures)
    listed = set(current.get("sourceFiles", [])) | set(current.get("generatedFiles", []))
    omitted = sorted(listed - set(digests["files"]))
    if omitted:
        fail(f"release digests omit listed files: {', '.join(omitted)}", failures)


def check_archive_checksums(failures: list[str]) -> None:
    checksum_path = ROOT / "archive" / "2022-v2" / "checksums.json"
    try:
        checksum_manifest = json.loads(checksum_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"archive checksum manifest is invalid: {error}", failures)
        return
    if checksum_manifest.get("algorithm") != "sha256" or not isinstance(checksum_manifest.get("files"), dict):
        fail("archive checksum manifest must declare sha256 file hashes", failures)
        return
    for relative, expected in sorted(checksum_manifest["files"].items()):
        path = checksum_path.parent / relative
        if not path.is_file():
            fail(f"archive checksum file does not exist: {path}", failures)
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            fail(f"archive checksum mismatch: {path}", failures)


def check_version_consistency(failures: list[str]) -> None:
    try:
        import tomllib

        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        package_init = (ROOT / "src" / "aeos" / "__init__.py").read_text(encoding="utf-8")
        package_match = re.search(r'__version__\s*=\s*"([^"]+)"', package_init)
        ontology = load_source(DEFAULT_INPUT)["ontology"]
        project_version = project["project"]["version"]
        package_version = package_match.group(1) if package_match else ""
        ontology_version = ontology["version"]
    except (OSError, KeyError, TypeError, ValueError) as error:
        fail(f"version metadata could not be read: {error}", failures)
        return
    if len({project_version, package_version, ontology_version}) != 1:
        fail("pyproject, package, and ontology versions are inconsistent", failures)


def check_archives(failures: list[str]) -> None:
    for path in sorted((ROOT / "archive").rglob("*.docx")):
        try:
            with zipfile.ZipFile(path) as archive:
                bad = archive.testzip()
        except zipfile.BadZipFile as error:
            fail(f"invalid DOCX archive {path}: {error}", failures)
            continue
        if bad:
            fail(f"corrupt DOCX member in {path}: {bad}", failures)


def check_pdfs(failures: list[str]) -> None:
    pdfs = sorted((ROOT / "paper").glob("*.pdf"))
    qpdf = "qpdf"
    for path in pdfs:
        try:
            completed = subprocess.run(
                [qpdf, "--check", str(path)], capture_output=True, text=True, check=False, timeout=60
            )
        except FileNotFoundError:
            fail("qpdf is required for PDF release checks", failures)
            return
        output = completed.stdout + completed.stderr
        warning_or_error = re.search(r"(?im)^\s*(?:warning|error)(?:\s|:)", output)
        if completed.returncode != 0 or warning_or_error or "File is linearized" not in output:
            fail(f"PDF check failed for {path}: {output.strip()}", failures)


def check_pdf_text(failures: list[str]) -> None:
    for path in sorted((ROOT / "paper").glob("*.pdf")):
        try:
            completed = subprocess.run(
                ["pdftotext", str(path), "-"], capture_output=True, text=True, check=False, timeout=60
            )
        except FileNotFoundError:
            fail("pdftotext is required for PDF text checks", failures)
            return
        text = completed.stdout.strip()
        if completed.returncode != 0 or len(text) < 200 or "AEOS" not in text:
            fail(f"PDF text extraction failed or is incomplete for {path}", failures)


def check_docx_accessibility(failures: list[str]) -> None:
    for path in sorted((ROOT / "paper").glob("*.docx")):
        try:
            with zipfile.ZipFile(path) as archive:
                document = archive.read("word/document.xml").decode("utf-8", errors="replace")
                core = archive.read("docProps/core.xml").decode("utf-8", errors="replace")
        except (KeyError, zipfile.BadZipFile) as error:
            fail(f"DOCX accessibility inspection failed for {path}: {error}", failures)
            continue
        docpr = re.findall(r"<wp:docPr\b[^>]*>", document)
        cnvpr = re.findall(r"<pic:cNvPr\b[^>]*>", document)
        described = [tag for tag in docpr if re.search(r'\bdescr="[^\"]+"', tag)]
        if len(docpr) != len(cnvpr) or len(docpr) != len(described):
            fail(f"DOCX figure descriptions are incomplete for {path}", failures)
        if not re.search(r"<dc:title>[^<]+</dc:title>", core) or not re.search(r"<dc:creator>[^<]+</dc:creator>", core):
            fail(f"DOCX core accessibility metadata is incomplete for {path}", failures)


def check_html_accessibility(failures: list[str]) -> None:
    path = ROOT / "paper" / "aeos-local.html"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if not re.search(r'<html[^>]+\blang="[a-z]{2}"', text):
        fail("HTML export is missing a language declaration", failures)
    if len(re.findall(r"<title>[^<]+</title>", text)) != 1 or "Active Entity Ontology for Science" not in text:
        fail("HTML export is missing its single descriptive title", failures)


def _extract_pdf_text(path: Path) -> str:
    completed = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True, check=False, timeout=60)
    if completed.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {path}")
    return completed.stdout


def _html_text(path: Path) -> str:
    return re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8", errors="replace"))


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml").decode("utf-8", errors="replace")
    return re.sub(r"<[^>]+>", " ", document)


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def _paper_headings(source: Path) -> list[str]:
    text = source.read_text(encoding="utf-8")
    return [re.sub(r"[#\s]+", " ", line).strip() for line in text.splitlines() if re.match(r"^#{1,2} ", line)]


def check_paper_freshness(failures: list[str], root: Path | None = None) -> None:
    """Verify maintained publication exports reflect the current source.

    The release gate otherwise validates only that the paper artifacts exist
    and are structurally sound, which lets a stale maintained paper pass as
    "current". This oracle closes that gap: the local exports must contain
    every current heading and identity token from paper/aeos.md, and the
    maintained 2022/v2 PDF must remain content-faithful to the preserved
    archive source.

    ``root`` defaults to the repository root; callers may pass an alternative
    root so the oracle is testable against a small synthetic tree.
    """
    root = ROOT if root is None else root
    source = root / "paper" / "aeos.md"
    try:
        headings = _paper_headings(source)
    except OSError as error:
        fail(f"paper source could not be read: {error}", failures)
        return
    identity = list(PAPER_LOCAL_IDENTITY_TOKENS)
    local_artifacts = {
        "paper/aeos-local.pdf": _extract_pdf_text,
        "paper/aeos-local.html": _html_text,
        "paper/aeos-local.docx": _docx_text,
    }
    for relative, extractor in local_artifacts.items():
        path = root / relative
        if not path.exists():
            fail(f"missing maintained paper artifact: {relative}", failures)
            continue
        try:
            text = _normalize(extractor(path))
        except (OSError, RuntimeError, zipfile.BadZipFile, KeyError) as error:
            fail(f"could not read {relative}: {error}", failures)
            continue
        missing = [heading for heading in headings if heading.lower() not in text]
        missing += [token for token in identity if token not in text]
        if missing:
            fail(
                f"maintained paper artifact {relative} is stale and does not reflect "
                f"the current source (missing: {', '.join(missing)})",
                failures,
            )

    preserved = root / "archive" / "2022-v2" / "7_20_2022_v2_ActInf-DeSci-AEOS-2022.pdf"
    maintained_v2 = root / "paper" / "aeos-2022-v2.pdf"
    if preserved.exists() and maintained_v2.exists():
        try:
            preserved_text = _normalize(_extract_pdf_text(preserved))
            maintained_text = _normalize(_extract_pdf_text(maintained_v2))
        except (OSError, RuntimeError) as error:
            fail(f"could not compare the maintained 2022/v2 PDF: {error}", failures)
            return
        if preserved_text != maintained_text:
            fail("paper/aeos-2022-v2.pdf does not match the archived 2022/v2 source PDF", failures)


def check_rendering(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="aeos-render-check-") as output_dir:
        try:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "render_artifacts.py"), "--output-dir", output_dir],
                capture_output=True,
                text=True,
                check=False,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            fail("publication rendering timed out after 600s", failures)
            return
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            fail(f"publication rendering failed: {detail}", failures)


def check_archive_pdfs(failures: list[str]) -> None:
    for path in sorted((ROOT / "archive").rglob("*.pdf")):
        try:
            completed = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=False, timeout=60)
        except FileNotFoundError:
            fail("pdfinfo is required for archived PDF inventory checks", failures)
            return
        if completed.returncode != 0 or not re.search(r"Pages:\s+[1-9][0-9]*", completed.stdout):
            fail(f"archived PDF inventory failed for {path}: {completed.stderr.strip()}", failures)


def check_active_text(failures: list[str]) -> None:
    ignored_parts = {".git", ".venv", ".venv-gnn", "archive"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ACTIVE_TEXT_SUFFIXES:
            continue
        if ignored_parts.intersection(path.parts):
            continue
        if path == Path(__file__).resolve():
            continue
        if path.relative_to(ROOT).as_posix() in ACTIVE_TEXT_EXEMPT_PATHS:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in FORBIDDEN_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", text):
                fail(f"prohibited authored term {term!r} found in {path.relative_to(ROOT)}", failures)


def main() -> int:
    failures: list[str] = []
    check_paths(failures)
    check_ontology(failures)
    check_sidecar(failures)
    check_release_manifest(failures)
    check_release_digests(failures)
    check_archive_checksums(failures)
    check_version_consistency(failures)
    check_archives(failures)
    check_pdfs(failures)
    check_pdf_text(failures)
    check_docx_accessibility(failures)
    check_html_accessibility(failures)
    check_paper_freshness(failures)
    check_rendering(failures)
    check_archive_pdfs(failures)
    check_active_text(failures)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("AEOS release checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
