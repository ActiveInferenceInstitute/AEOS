#!/usr/bin/env python3
"""Check the documentation tree: relative links, anchors, and the flat index.

The repository has no published documentation site, so this script is the
documentation gate. It resolves every relative link and in-page anchor in every
tracked Markdown file, and it keeps ``docs/documentation-index.md`` in step with
``docs/`` so the index cannot omit a long-lived page or list one that is gone.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HUB = DOCS / "README.md"
INDEX = DOCS / "documentation-index.md"
SKIP_PARTS = {".git", ".pytest_cache", ".ruff_cache", "qa", "node_modules"}
INDEX_EXEMPT = {"README.md", "documentation-index.md"}

LINK = re.compile(r"!?\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
REFERENCE = re.compile(r"^\[(?P<label>[^\]]+)\]:\s*(?P<target>\S+)")
HEADING = re.compile(r"^(?P<level>#{1,6})\s+(?P<text>.+?)\s*$")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not SKIP_PARTS.intersection(path.relative_to(ROOT).parts)
        and not any(part.startswith(".venv") for part in path.relative_to(ROOT).parts)
    )


def slugify(heading: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*~]", "", text).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors_of(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = HEADING.match(line)
        if not match:
            continue
        slug = slugify(match.group("text"))
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def link_targets(path: Path) -> list[tuple[int, str]]:
    targets: list[tuple[int, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        for match in LINK.finditer(line):
            targets.append((number, match.group("target")))
        reference = REFERENCE.match(line)
        if reference:
            targets.append((number, reference.group("target")))
    return targets


def check_links(failures: list[str]) -> None:
    for path in markdown_files():
        relative = path.relative_to(ROOT)
        for number, target in link_targets(path):
            if not target or SCHEME.match(target) or target.startswith("/"):
                continue
            location = f"{relative.as_posix()}:{number}"
            if target.startswith("#"):
                if target[1:] not in anchors_of(path):
                    fail(f"{location} anchor does not exist: {target}", failures)
                continue
            location_rel, _, fragment = target.partition("#")
            resolved = (path.parent / location_rel.rstrip("/")).resolve()
            if not resolved.exists():
                fail(f"{location} link target does not exist: {target}", failures)
                continue
            if (
                fragment
                and resolved.is_file()
                and resolved.suffix == ".md"
                and fragment not in anchors_of(resolved)
            ):
                fail(f"{location} anchor does not exist in {location_rel}: #{fragment}", failures)


def indexed_documents() -> set[str]:
    linked: set[str] = set()
    for _, target in link_targets(INDEX):
        if SCHEME.match(target) or target.startswith(("/", "#")):
            continue
        path = (INDEX.parent / target.partition("#")[0]).resolve()
        if path.parent == DOCS.resolve() and path.suffix == ".md":
            linked.add(path.name)
    return linked


def check_index(failures: list[str]) -> None:
    if not INDEX.exists():
        fail(f"{INDEX.relative_to(ROOT)} is missing", failures)
        return
    present = {path.name for path in DOCS.glob("*.md")} - INDEX_EXEMPT
    linked = indexed_documents()
    for name in sorted(present - linked):
        fail(f"docs/{name} is not listed in docs/documentation-index.md", failures)
    for name in sorted(linked - present - INDEX_EXEMPT):
        fail(f"docs/documentation-index.md lists a page that does not exist: docs/{name}", failures)
    if not any(
        (HUB.parent / target.partition("#")[0]).resolve() == INDEX.resolve()
        for _, target in link_targets(HUB)
        if not SCHEME.match(target) and not target.startswith("#")
    ):
        fail("docs/README.md does not link the documentation index", failures)


def main() -> int:
    failures: list[str] = []
    check_links(failures)
    check_index(failures)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"Documentation checks passed for {len(markdown_files())} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
