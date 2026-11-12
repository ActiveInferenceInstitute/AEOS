# Generated documents

Files here are produced by a script and checked by the gate. Editing them by
hand fails `./run.sh docs`.

| File | Producer | Check |
| --- | --- | --- |
| [`gate-metrics.json`](gate-metrics.json) | `./run.sh measure` | Schema and arm coverage. |
| [`gate-metrics.md`](gate-metrics.md) | `./run.sh measure` | Must equal the Markdown rendered from `gate-metrics.json`. |

`./run.sh docs` also re-collects the suite and fails when the recorded test
count in `gate-metrics.json` no longer matches. Coverage and arm wall times are
recorded from the measuring run, so refresh them with `./run.sh measure` when a
change could move them.

Numbers belong here, not in prose: link this folder from a guide instead of
copying a count, a duration, or a percentage into it.
