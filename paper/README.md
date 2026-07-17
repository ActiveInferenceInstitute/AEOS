# AEOS publication source

The maintained local source is [`aeos.md`](aeos.md). It is a repository-owned
editable representation of the AEOS publication material and documentation;
the published DOI record remains authoritative for the 2022/v3 paper.

The original 2022/v2 binary artifacts are preserved under
[`../archive/2022-v2/`](../archive/2022-v2/). Keep their filenames and checksums
in the archive manifest. Use the local source for editorial improvements and
new generated artifacts.

`paper/aeos-local.html` is the accessible browser-readable export of the same
maintained source.

## Rendering

```bash
pandoc paper/aeos.md --from=gfm --standalone --pdf-engine=xelatex -o paper/aeos-local.pdf
pandoc paper/aeos.md --from=gfm --standalone -o paper/aeos-local.docx
pandoc paper/aeos.md --from=gfm --standalone --metadata lang=en -o paper/aeos-local.html
qpdf --linearize paper/aeos-local.pdf /tmp/aeos-local.linearized.pdf
mv /tmp/aeos-local.linearized.pdf paper/aeos-local.pdf
```

After rendering, inspect every page and run the publication checks described in
[`../docs/publication.md`](../docs/publication.md).

The normalized historical copies are rebuilt from the preserved versioned pair
with:

```bash
qpdf --linearize archive/2022-v2/7_20_2022_v2_ActInf-DeSci-AEOS-2022.pdf /tmp/aeos-2022-v2.linearized.pdf
mv /tmp/aeos-2022-v2.linearized.pdf paper/aeos-2022-v2.pdf
python scripts/add_docx_alt_text.py archive/2022-v2/7_20_2022_v2_ActInf-DeSci-AEOS-2022.docx paper/aeos-2022-v2.docx
```
