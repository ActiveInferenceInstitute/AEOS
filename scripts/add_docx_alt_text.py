#!/usr/bin/env python3
"""Add figure descriptions to a DOCX package without changing its content."""

from __future__ import annotations

import argparse
import html
import os
import re
import tempfile
import zipfile
from pathlib import Path

DESCRIPTIONS = {
    "image1.png": "Figure 4. Active entity action selection using sensing, inference, and action.",
    "image2.png": "Figure 3. Entity classes in the Active Entity Ontology for Science.",
    "image3.png": "Figure 5. Entity roles and affordances.",
    "image4.png": "Figure 1. Dynamic research funding model of Science Fund.",
    "image5.png": "Figure 6. Example funding motifs in CeSci and DeSci.",
    "image6.png": "Figure 2. Two active entities interacting via a shared epistemic niche.",
    "image7.png": "Figure 8. Example scientific review motifs in CeSci and DeSci.",
    "image8.png": "Figure 7. Example communication motifs in CeSci and DeSci.",
}
CORE_PROPERTIES = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <dc:title>An Active Inference Ontology for Decentralized Science: 2022/v2 historical snapshot</dc:title>
 <dc:creator>Daniel Friedman; Shaun Applegate-Swanson</dc:creator>
 <cp:subject>Historical AEOS publication snapshot</cp:subject>
 <cp:keywords>AEOS, Active Inference, Decentralized Science</cp:keywords>
 <dcterms:created xsi:type="dcterms:W3CDTF">2022-08-19T00:00:00Z</dcterms:created>
 <dcterms:modified xsi:type="dcterms:W3CDTF">2026-07-17T00:00:00Z</dcterms:modified>
</cp:coreProperties>
"""


def update_tag(xml: bytes, tag: bytes) -> tuple[bytes, int]:
    pattern = re.compile(rb"<" + tag + rb"\b([^>]*?)(/?)>")
    changed = 0

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal changed
        attributes = match.group(1)
        name_match = re.search(rb'\bname="([^"]+)"', attributes)
        if not name_match:
            return match.group(0)
        name = name_match.group(1).decode("utf-8")
        description = DESCRIPTIONS.get(name)
        if not description:
            return match.group(0)
        escaped = html.escape(description, quote=True).encode("utf-8")
        attribute = b' descr="' + escaped + b'"'
        if re.search(rb'\bdescr="[^"]*"', attributes):
            attributes = re.sub(rb'\bdescr="[^"]*"', attribute, attributes)
        else:
            attributes += attribute
        changed += 1
        return b"<" + tag + attributes + match.group(2) + b">"

    return pattern.sub(replace, xml), changed


def add_descriptions(input_path: Path, output_path: Path) -> int:
    with zipfile.ZipFile(input_path, "r") as source:
        document = source.read("word/document.xml")
        document, docpr_count = update_tag(document, b"wp:docPr")
        document, cnvpr_count = update_tag(document, b"pic:cNvPr")
        if docpr_count == 0 or docpr_count != cnvpr_count:
            raise ValueError(f"figure description counts do not match in {input_path}")
        members = set(source.namelist())
        package_updates: dict[str, bytes] = {"word/document.xml": document}
        additions: dict[str, bytes] = {}
        if "docProps/core.xml" not in members:
            content_types = source.read("[Content_Types].xml")
            content_types = content_types.replace(
                b"</Types>",
                b'<Override PartName="/docProps/core.xml" '
                b'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>',
            )
            root_relationships = source.read("_rels/.rels")
            root_relationships = root_relationships.replace(
                b"</Relationships>",
                b'<Relationship Id="rIdCoreProperties" '
                b'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
                b'Target="docProps/core.xml"/></Relationships>',
            )
            package_updates["[Content_Types].xml"] = content_types
            package_updates["_rels/.rels"] = root_relationships
            additions["docProps/core.xml"] = CORE_PROPERTIES
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w") as target:
            for item in source.infolist():
                data = package_updates.get(item.filename, source.read(item.filename))
                target.writestr(item, data)
            for name, data in additions.items():
                target.writestr(name, data)
    return min(docpr_count, cnvpr_count)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temporary:
            temporary_path = Path(temporary.name)
        try:
            count = add_descriptions(args.input, temporary_path)
            os.replace(temporary_path, args.output)
        finally:
            temporary_path.unlink(missing_ok=True)
    else:
        count = add_descriptions(args.input, args.output)
    print(f"Added descriptions to {count} figures in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
