# Generated documents

Files here are produced by a script and checked by the gate. Editing them by
hand fails `./run.sh docs`.

| File | Producer | Check |
| --- | --- | --- |
| [`gate-metrics.json`](gate-metrics.json) | `./run.sh measure` | Schema, complete arm set and live test count. |
| [`gate-metrics.md`](gate-metrics.md) | `./run.sh measure` | Exact rendering of the JSON's before/after observations. |

`./run.sh docs` re-collects the suite and checks the recorded test count.
The producer measures every substantive arm, including composites and the
default invocation. `measure` itself and the discovery commands are excluded.
Use `./run.sh measure --baseline PATH --output-dir PATH` to retain a saved
baseline and keep new evidence outside the source tree. To publish evidence
already measured once, run `uv run --locked --extra test python
scripts/gate_metrics.py --record PATH --baseline BASELINE`.
Failed baseline samples remain failures; they are not speedup evidence.

Numbers belong here, not in prose: link this folder from a guide instead of
copying a count, a duration, or a percentage into it.
