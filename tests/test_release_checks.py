from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_release

needs_pdftotext = pytest.mark.skipif(
    shutil.which("pdftotext") is None,
    reason="pdftotext is not available on this host",
)


@needs_pdftotext
def test_paper_freshness_passes_on_maintained_artifacts() -> None:
    failures: list[str] = []
    check_release.check_paper_freshness(failures)
    assert failures == []


def test_paper_freshness_detects_stale_html(tmp_path: Path) -> None:
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "aeos.md").write_text("# Title\n\n## Alpha\n\n## Beta\n\n", encoding="utf-8")
    (paper / "aeos-local.html").write_text(
        "<html><body><h1>Active Entity Ontology for Science (AEOS)</h1>"
        "<p>informational entity</p><p>10.5281/zenodo.7484994</p><h2>Alpha</h2></body></html>",
        encoding="utf-8",
    )
    failures: list[str] = []
    check_release.check_paper_freshness(failures, root=tmp_path)
    stale = [message for message in failures if "stale" in message]
    assert any("aeos-local.html" in message and "Beta" in message for message in stale)


def test_paper_headings_parses_source() -> None:
    headings = check_release._paper_headings(ROOT / "paper" / "aeos.md")
    assert "Abstract" in headings
    assert "Interaction motifs" in headings


def test_normalize_collapses_whitespace_and_lowercases() -> None:
    assert check_release._normalize("  Active  Entity \n\tOntology  ") == "active entity ontology"


def test_release_digests_pass_on_current_tree() -> None:
    failures: list[str] = []
    check_release.check_release_digests(failures)
    assert failures == []


def test_release_digests_detect_edited_artifact(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    artifact = data / "aeos.yaml"
    artifact.write_text('schema_version: "1.0.0"\n', encoding="utf-8")
    manifest = {
        "currentRelease": "v1.0.0",
        "releases": [
            {
                "version": "v1.0.0",
                "status": "current",
                "sourceFiles": ["data/aeos.yaml"],
                "generatedFiles": [],
                "digests": {
                    "algorithm": "sha256",
                    "recorded": "2026-11-01",
                    "files": {"data/aeos.yaml": hashlib.sha256(artifact.read_bytes()).hexdigest()},
                },
            }
        ],
    }
    (tmp_path / "releases.json").write_text(json.dumps(manifest), encoding="utf-8")

    failures: list[str] = []
    check_release.check_release_digests(failures, root=tmp_path)
    assert failures == []

    artifact.write_text('schema_version: "1.0.1"\n', encoding="utf-8")
    failures = []
    check_release.check_release_digests(failures, root=tmp_path)
    assert any("digest mismatch" in message and "data/aeos.yaml" in message for message in failures)


def test_release_digests_require_all_listed_files(tmp_path: Path) -> None:
    manifest = {
        "currentRelease": "v1.0.0",
        "releases": [
            {
                "version": "v1.0.0",
                "status": "current",
                "sourceFiles": ["data/aeos.yaml"],
                "generatedFiles": ["aeos.json"],
                "digests": {"algorithm": "sha256", "recorded": "2026-11-01", "files": {}},
            }
        ],
    }
    (tmp_path / "releases.json").write_text(json.dumps(manifest), encoding="utf-8")
    failures: list[str] = []
    check_release.check_release_digests(failures, root=tmp_path)
    assert any("omit listed files" in message for message in failures)
