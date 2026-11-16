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
    """Raised when rendering or input/output safety checks fail."""


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


def is_page_image(path: Path, stem: str) -> bool:
    match = re.fullmatch(rf"{re.escape(stem)}-([0-9]+)\.png", path.name)
    return match is not None and int(match.group(1)) > 0


def owned_images(output_dir: Path, pdfs: list[Path], docxs: list[Path]) -> list[Path]:
    """Refuse everything except page files in the renderer's established layout."""
    if output_dir.is_symlink():
        raise RenderError(f"unsafe output symlink: {output_dir}")
    if not output_dir.exists():
        return []
    if not output_dir.is_dir():
        raise RenderError(f"output is not a directory: {output_dir}")

    images: list[Path] = []
    docx_stems = {path.stem for path in docxs}
    for path in sorted(output_dir.iterdir()):
        if path.is_symlink():
            raise RenderError(f"unsafe output symlink: {path}")
        if path.is_file() and any(is_page_image(path, pdf.stem) for pdf in pdfs):
            images.append(path)
        elif path.is_dir() and path.name in docx_stems:
            for image in sorted(path.iterdir()):
                if image.is_symlink() or not image.is_file() or not is_page_image(image, path.name):
                    raise RenderError(f"not a renderer-owned page image: {image}")
                images.append(image)
        else:
            raise RenderError(f"not renderer-owned output: {path}")
    return images


def validate_output(
    output_path: Path, input_dir: Path, pdfs: list[Path], docxs: list[Path]
) -> tuple[Path, list[Path]]:
    output_path = output_path.absolute()
    for path in (output_path, *output_path.parents):
        if path.is_symlink():
            raise RenderError(f"unsafe output symlink: {path}")
    output_dir = output_path.resolve()
    if ROOT.resolve().is_relative_to(output_dir):
        raise RenderError(f"output overlaps the repository or its ancestors: {output_dir}")
    for source in (input_dir, *pdfs, *docxs):
        source = source.resolve()
        if source.is_relative_to(output_dir) or output_dir.is_relative_to(source):
            raise RenderError(f"output overlaps an input: {output_dir} and {source}")
    return output_dir, owned_images(output_dir, pdfs, docxs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "qa" / "rendered")
    parser.add_argument(
        "--input-dir", type=Path, default=ROOT / "paper", help="directory containing maintained artifacts"
    )
    args = parser.parse_args()
    results: list[str] = []
    try:
        input_dir = args.input_dir.resolve()
        if not input_dir.is_dir():
            raise RenderError(f"input is not a directory: {input_dir}")
        pdfs = sorted(input_dir.glob("*.pdf"))
        docxs = sorted(input_dir.glob("*.docx"))
        if not pdfs and not docxs:
            raise RenderError(f"no PDF or DOCX inputs found in {input_dir}")
        for path in (*pdfs, *docxs):
            if not path.is_file() or path.stem in {".", ".."}:
                raise RenderError(f"unsafe or non-file input: {path}")
        output_dir, _ = validate_output(args.output_dir, input_dir, pdfs, docxs)

        # Finish rendering privately before replacing any previously owned pages.
        with tempfile.TemporaryDirectory(prefix="aeos-render-") as temporary:
            staged_dir = Path(temporary)
            for path in pdfs:
                results.append(f"{path.name}: {render_pdf(path, staged_dir)} PDF pages")
            for path in docxs:
                results.append(f"{path.name}: {render_docx(path, staged_dir)} DOCX pages")
            images = owned_images(staged_dir, pdfs, docxs)
            output_dir, previous_images = validate_output(args.output_dir, input_dir, pdfs, docxs)
            output_dir.mkdir(parents=True, exist_ok=True)
            for image in previous_images:
                image.unlink()
            for image in images:
                destination = output_dir / image.relative_to(staged_dir)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(image, destination)
    except (OSError, RuntimeError) as error:
        print(f"ERROR: {error}")
        return 1
    for result in results:
        print(result)
    print(f"Rendered {len(results)} maintained publication artifacts to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
