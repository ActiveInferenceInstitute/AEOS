# Publication package

The repository distinguishes the maintained ontology from the published paper.

- `paper/aeos.md` is the editable Markdown source for the maintained local
  publication package.
- `paper/aeos-local.html` is the accessible browser-readable export of that
  source.
- `paper/README.md` records source lineage and rendering commands.
- `archive/2022-v2/` preserves the original 2022/v2 DOCX and PDF filenames.

The DOI record remains the authoritative publication record. Local changes to
the maintained source receive a repository release identifier and do not claim
to replace the DOI record.

Before delivery, render the DOCX and PDF outputs to page images and inspect all
pages for clipping, overlap, broken tables, missing glyphs, captions, page
numbers, and references. Run `qpdf --check` on every active PDF and require no
warnings. Linearize maintained PDFs with
`qpdf --object-streams=disable --linearize` as recorded in
[`../paper/README.md`](../paper/README.md): qpdf 11.x and 12.x disagree about
the outline hint table of documents that keep object streams, and both accept
the file written without them, so the check passes with the qpdf generation the
environment provides (CI uses the Ubuntu package). DOCX figures must have descriptive accessibility text and core title
and creator metadata. The HTML export must retain a language declaration and a
single descriptive document title.

The release gate (`python scripts/check_release.py`) also verifies that the
maintained exports stay fresh against their sources: `paper/aeos-local.*` must
contain every current heading and identity token from `paper/aeos.md`, and
`paper/aeos-2022-v2.pdf` must remain content-faithful to the archived 2022/v2
source PDF. This prevents a stale maintained paper from silently passing as
current.

Two gate arms cover this page: `./run.sh render` renders every maintained PDF
and DOCX page to images for inspection, and `./run.sh release` runs the full
release gate including that rendering check. [`RUN_GUIDE.md`](RUN_GUIDE.md)
lists both with their prerequisites.
