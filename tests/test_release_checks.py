from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_release  # noqa: E402

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
