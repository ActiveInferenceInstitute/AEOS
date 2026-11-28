# Forking AEOS

1. Fork or clone the repository and install the locked environment with
   `./run.sh setup`.
2. Copy the current release in `releases.json` and choose a new ontology
   version for your fork.
3. Edit `data/aeos.yaml`. Keep IDs stable when the concept is unchanged; add a
   new ID when the concept is materially different.
4. Run:

   ```bash
   ./run.sh validate
   ./run.sh build
   ./run.sh test
   ```

5. Review the generated JSON and record your source, version, differences, and
   attribution in the release manifest.

The build does not call Coda, GitHub, Zenodo, or any other network service.
Forks may keep the interactive link as an upstream reference while maintaining
their own validated local data.

Redistributions must retain CC BY 4.0 attribution, the AEOS name, the source
release, and the DOI/publication citation where the paper is included.
