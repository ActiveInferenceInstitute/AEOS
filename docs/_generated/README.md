# Generated documents

Files here are produced by a script and checked by the gate. Editing them by
hand fails `./run.sh docs`.

| File | Producer | Check |
| --- | --- | --- |
| [`gate-metrics.json`](gate-metrics.json) | `scripts/gate_metrics.py` | v3 current/history separation and input/command/environment identity; preserved complete prior observations. |
| [`gate-metrics.md`](gate-metrics.md) | `scripts/gate_metrics.py` | Exact projection of current/unmeasured and retained historical observations. |

Current evidence binds content, membership, commands, requested per-arm interpreter overrides, and runner implementation. Host Python identifies the measurement driver; HEAD is descriptive, and generated metrics do not fingerprint themselves.

Use `--record PATH --historical --output-dir PATH` to preserve prior observations without executing arms or relabeling them as current. `ci-project` may remain null/unmeasured. Historical consistency does not prove current measurements; source drift refuses publication and measured failures remain failures.

Full measurement requires all final inputs and actual tool/network/runtime admission. Apply documentation first. No duration, success, or source binding may be invented to fill an unmeasured row.

Numbers belong here, not in prose: link this folder from a guide instead of
copying a count, a duration, or a percentage into it.
