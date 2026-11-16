from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_artifacts


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch):
    root = tmp_path.resolve() / "repository"
    paper = root / "paper"
    paper.mkdir(parents=True)
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_bytes(b"ref: refs/heads/fixture\n")
    (root / "README.md").write_bytes(b"authored repository content\n")
    (root / "archive").mkdir()
    (root / "archive" / "published.pdf").write_bytes(b"historical publication\n")
    (paper / "aeos-local.pdf").write_bytes(b"12")
    (paper / "aeos-local.docx").write_bytes(b"3")
    monkeypatch.setattr(render_artifacts, "ROOT", root)
    monkeypatch.setattr(render_artifacts.tempfile, "tempdir", str(root.parent))
    monkeypatch.chdir(root)
    return root, paper


@pytest.fixture
def commands(monkeypatch):
    calls: list[list[str]] = []

    def controlled_run(command: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
        calls.append(command.copy())
        stdout = ""
        if command[0] == "pdfinfo":
            stdout = f"Pages: {int(Path(command[1]).read_bytes())}\n"
        elif command[0] == "pdftoppm":
            source, prefix = Path(command[-2]), Path(command[-1])
            pages = int(source.read_bytes())
            for number in range(1, pages + 1):
                image = prefix.parent / f"{prefix.name}-{number:0{len(str(pages))}d}.png"
                image.write_bytes(f"rendered {number} of {pages}".encode("ascii"))
        elif command[0] == "soffice":
            source = Path(command[-1])
            pdf_dir = Path(command[command.index("--outdir") + 1])
            (pdf_dir / f"{source.stem}.pdf").write_bytes(source.read_bytes())
        else:
            raise AssertionError(f"unexpected external command: {command}")
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(render_artifacts, "run", controlled_run)
    return calls


def snapshot(root: Path) -> dict[Path, bytes | str | None]:
    contents: dict[Path, bytes | str | None] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if path.is_symlink():
            contents[relative] = str(path.readlink())
        elif path.is_dir():
            contents[relative] = None
        else:
            contents[relative] = path.read_bytes()
    return contents


def run_main(monkeypatch, *, output: Path | None = None, input_dir: Path | None = None) -> int:
    arguments = ["render_artifacts.py"]
    if output is not None:
        arguments.extend(["--output-dir", str(output)])
    if input_dir is not None:
        arguments.extend(["--input-dir", str(input_dir)])
    monkeypatch.setattr(sys, "argv", arguments)
    return render_artifacts.main()


@pytest.mark.parametrize(
    "target",
    ["repository", "repository-ancestor", "input", "input-descendant", "input-file", "input-ancestor"],
)
def test_main_refuses_overlapping_output(workspace, commands, monkeypatch, capsys, target: str) -> None:
    root, paper = workspace
    if target == "input-ancestor":
        paper = root.parent / "external" / "source"
        paper.mkdir(parents=True)
        (paper / "source.pdf").write_bytes(b"1")
        output = paper.parent
    else:
        output = {
            "repository": root,
            "repository-ancestor": root.parent,
            "input": paper,
            "input-descendant": paper / "rendered",
            "input-file": paper / "aeos-local.pdf",
        }[target]
    before = snapshot(root.parent)

    assert run_main(monkeypatch, output=output, input_dir=paper) == 1

    assert "ERROR:" in capsys.readouterr().out
    assert snapshot(root.parent) == before
    assert commands == []


@pytest.mark.parametrize("kind", ["output", "parent", "pdf-page", "docx-directory", "docx-page", "dangling-page"])
def test_main_refuses_output_symlinks(workspace, commands, monkeypatch, capsys, kind: str) -> None:
    root, _ = workspace
    valuable = root.parent / "valuable"
    valuable.mkdir()
    saved = valuable / "saved.png"
    saved.write_bytes(b"irreplaceable original bytes")
    rendered = valuable / "rendered"
    rendered.mkdir()
    (rendered / "aeos-local-99.png").write_bytes(b"valuable content behind a directory symlink")
    output = root.parent / "output"
    if kind == "output":
        output.symlink_to(rendered, target_is_directory=True)
    elif kind == "parent":
        alias = root.parent / "alias"
        alias.symlink_to(valuable, target_is_directory=True)
        output = alias / "rendered"
    else:
        output.mkdir()
        (output / "aeos-local-99.png").write_bytes(b"previous PDF page")
        if kind == "pdf-page":
            (output / "aeos-local-1.png").symlink_to(saved)
        elif kind == "docx-directory":
            (output / "aeos-local").symlink_to(rendered, target_is_directory=True)
        elif kind == "docx-page":
            (output / "aeos-local").mkdir()
            (output / "aeos-local" / "aeos-local-1.png").symlink_to(saved)
        else:
            (output / "aeos-local-1.png").symlink_to(valuable / "missing.png")
    before = snapshot(root.parent)

    assert run_main(monkeypatch, output=output) == 1

    assert "ERROR:" in capsys.readouterr().out
    assert snapshot(root.parent) == before
    assert commands == []


def test_main_refuses_output_containing_a_resolved_input(workspace, commands, monkeypatch, capsys) -> None:
    root, paper = workspace
    output = root.parent / "output"
    output.mkdir()
    source = output / "aeos-local-1.png"
    source.write_bytes(b"2")
    (paper / "linked.pdf").symlink_to(source)
    before = snapshot(root.parent)

    assert run_main(monkeypatch, output=output) == 1

    assert "ERROR:" in capsys.readouterr().out
    assert snapshot(root.parent) == before
    assert commands == []


@pytest.mark.parametrize(
    "unknown",
    [
        "notes.txt",
        "unrelated-1.png",
        "aeos-local-cover.png",
        "aeos-local-0.png",
        "backup/notes.txt",
        "aeos-local/notes.txt",
        "aeos-local/nested/notes.txt",
    ],
)
def test_main_refuses_unknown_existing_content(workspace, commands, monkeypatch, capsys, unknown: str) -> None:
    root, _ = workspace
    output = root.parent / "output"
    (output / "aeos-local").mkdir(parents=True)
    (output / "aeos-local-99.png").write_bytes(b"previous PDF page")
    (output / "aeos-local" / "aeos-local-99.png").write_bytes(b"previous DOCX page")
    valuable = output / unknown
    valuable.parent.mkdir(parents=True, exist_ok=True)
    valuable.write_bytes(b"valuable content must survive refusal")
    before = snapshot(root.parent)

    assert run_main(monkeypatch, output=output) == 1

    assert "ERROR:" in capsys.readouterr().out
    assert snapshot(root.parent) == before
    assert commands == []


@pytest.mark.parametrize("kind", ["missing", "empty", "file", "pdf-directory", "dangling-pdf", "reserved-pdf", "reserved-docx"])
def test_main_validates_inputs_before_changing_output(workspace, commands, monkeypatch, capsys, kind: str) -> None:
    root, _ = workspace
    paper = root.parent / "invalid-input"
    if kind == "file":
        paper.write_bytes(b"not a directory")
    elif kind != "missing":
        paper.mkdir()
        if kind == "pdf-directory":
            (paper / "directory.pdf").mkdir()
        elif kind == "dangling-pdf":
            (paper / "broken.pdf").symlink_to(root.parent / "missing.pdf")
        elif kind == "reserved-pdf":
            (paper / "..pdf").write_bytes(b"1")
        elif kind == "reserved-docx":
            (paper / "...docx").write_bytes(b"1")
    output = root.parent / "output"
    output.mkdir()
    (output / "aeos-local-1.png").write_bytes(b"previous rendered page")
    before = snapshot(root.parent)

    assert run_main(monkeypatch, output=output, input_dir=paper) == 1

    assert "ERROR:" in capsys.readouterr().out
    assert snapshot(root.parent) == before
    assert commands == []


@pytest.mark.parametrize("custom_output", [False, True], ids=["default", "isolated"])
def test_main_renders_and_replaces_only_owned_pages(workspace, commands, monkeypatch, capsys, custom_output: bool) -> None:
    root, paper = workspace
    output = root.parent / "isolated" if custom_output else root / "qa" / "rendered"
    argument = output if custom_output else None

    assert run_main(monkeypatch, output=argument) == 0

    expected_names = {Path(f"aeos-local-{number:02d}.png") for number in range(1, 13)}
    expected_names.update(Path("aeos-local") / f"aeos-local-{number}.png" for number in range(1, 4))
    expected_names.add(Path("aeos-local"))
    assert set(snapshot(output)) == expected_names
    assert (output / "aeos-local-12.png").read_bytes() == b"rendered 12 of 12"
    assert (output / "aeos-local" / "aeos-local-3.png").read_bytes() == b"rendered 3 of 3"
    assert capsys.readouterr().out.splitlines() == [
        "aeos-local.pdf: 12 PDF pages",
        "aeos-local.docx: 3 DOCX pages",
        f"Rendered 2 maintained publication artifacts to {output}",
    ]

    (paper / "aeos-local.pdf").write_bytes(b"1")
    (paper / "aeos-local.docx").write_bytes(b"2")
    (output / "aeos-local-99.png").write_bytes(b"stale PDF page")
    (output / "aeos-local" / "aeos-local-99.png").write_bytes(b"stale DOCX page")

    assert run_main(monkeypatch, output=argument) == 0

    assert snapshot(output) == {
        Path("aeos-local-1.png"): b"rendered 1 of 1",
        Path("aeos-local"): None,
        Path("aeos-local/aeos-local-1.png"): b"rendered 1 of 2",
        Path("aeos-local/aeos-local-2.png"): b"rendered 2 of 2",
    }
    assert capsys.readouterr().out.splitlines() == [
        "aeos-local.pdf: 1 PDF pages",
        "aeos-local.docx: 2 DOCX pages",
        f"Rendered 2 maintained publication artifacts to {output}",
    ]
    assert (root / ".git" / "HEAD").read_bytes() == b"ref: refs/heads/fixture\n"
    assert (root / "README.md").read_bytes() == b"authored repository content\n"
    assert (root / "archive" / "published.pdf").read_bytes() == b"historical publication\n"


@pytest.mark.parametrize("incomplete", ["pdf", "docx"])
def test_main_preserves_previous_pages_on_incomplete_render(workspace, commands, monkeypatch, capsys, incomplete: str) -> None:
    root, paper = workspace
    output = root.parent / "output"
    (output / "aeos-local").mkdir(parents=True)
    (output / "aeos-local-1.png").write_bytes(b"previous PDF page")
    (output / "aeos-local" / "aeos-local-1.png").write_bytes(b"previous DOCX page")
    controlled_run = render_artifacts.run

    def incomplete_run(command: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
        completed = controlled_run(command, timeout=timeout)
        if command[0] == "pdftoppm":
            is_pdf_input = Path(command[-2]).parent == paper
            if is_pdf_input == (incomplete == "pdf"):
                prefix = Path(command[-1])
                sorted(prefix.parent.glob(f"{prefix.name}-*.png"))[-1].unlink()
        return completed

    monkeypatch.setattr(render_artifacts, "run", incomplete_run)
    before = snapshot(root.parent)

    assert run_main(monkeypatch, output=output) == 1

    assert "ERROR:" in capsys.readouterr().out
    assert snapshot(root.parent) == before
