#!/usr/bin/env python3
"""Render maintained PDF and DOCX artifacts and verify complete page coverage."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RenderError(RuntimeError):
    """Raised when an artifact cannot be rendered or fully enumerated."""


def run(command: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
    except FileNotFoundError as error:
        raise RenderError(f"required command is unavailable: {command[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise RenderError(f"command timed out after {timeout}s: {' '.join(command)}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RenderError(f"command failed ({completed.returncode}): {' '.join(command)}\n{detail}")
    return completed


def page_count(pdf_path: Path) -> int:
    output = run(["pdfinfo", str(pdf_path)]).stdout
    match = re.search(r"^Pages:\s+(\d+)$", output, flags=re.MULTILINE)
    if not match or int(match.group(1)) < 1:
        raise RenderError(f"could not determine a positive page count for {pdf_path}")
    return int(match.group(1))


def render_pdf(pdf_path: Path, output_dir: Path) -> int:
    pages = page_count(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / pdf_path.stem
    run(["pdftoppm", "-png", "-r", "96", str(pdf_path), str(prefix)])
    images = sorted(output_dir.glob(f"{pdf_path.stem}-*.png"))
    if len(images) != pages:
        raise RenderError(f"{pdf_path} rendered {len(images)} pages; expected {pages}")
    return pages


def render_docx(docx_path: Path, output_dir: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="aeos-soffice-") as temporary:
        temporary_path = Path(temporary)
        user_profile = temporary_path / "profile"
        pdf_dir = temporary_path / "pdf"
        pdf_dir.mkdir()
        run(
            [
                "soffice",
                f"-env:UserInstallation={user_profile.as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(pdf_dir),
                str(docx_path),
            ]
        )
        rendered_pdf = pdf_dir / f"{docx_path.stem}.pdf"
        if not rendered_pdf.exists():
            raise RenderError(f"LibreOffice did not create a PDF for {docx_path}")
        return render_pdf(rendered_pdf, output_dir / docx_path.stem)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "qa" / "rendered")
    parser.add_argument(
        "--input-dir", type=Path, default=ROOT / "paper", help="directory containing maintained artifacts"
    )
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    input_dir = args.input_dir.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[str] = []
    try:
        for path in sorted(input_dir.glob("*.pdf")):
            results.append(f"{path.name}: {render_pdf(path, output_dir)} PDF pages")
        for path in sorted(input_dir.glob("*.docx")):
            results.append(f"{path.name}: {render_docx(path, output_dir)} DOCX pages")
    except RenderError as error:
        print(f"ERROR: {error}")
        return 1
    for result in results:
        print(result)
    print(f"Rendered {len(results)} maintained publication artifacts to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
