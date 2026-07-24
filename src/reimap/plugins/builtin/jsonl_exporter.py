"""Built-in plugin: stream every completed scan to a JSONL file.

Demonstrates subscribing to ``scan.completed`` to build an external, append-only
audit trail that other tools can tail. The output path lives in the data dir.
"""

from __future__ import annotations

import json

from ...app_dirs import data_dir
from ...logging_config import get_logger

log = get_logger("plugin.jsonl_exporter")


def register(hooks, runtime) -> None:
    """Append one JSON line per scan cycle to ``scans.jsonl``."""
    from ...hooks import HookName

    output = data_dir() / "scans.jsonl"

    @hooks.on(HookName.SCAN_COMPLETED, name="jsonl_exporter", priority=200)
    def _on_scan(ctx) -> None:
        connections = ctx.get("connections", [])
        record = {
            "duration": round(ctx.get("duration", 0.0), 3),
            "count": len(connections),
            "new": len(ctx.get("new", [])),
            "endpoints": [
                {
                    "ip": c.remote_ip,
                    "port": c.remote_port,
                    "kind": c.kind.value,
                    "process": c.process,
                    "country": c.location.country if c.location else None,
                }
                for c in connections
            ],
        }
        try:
            with open(output, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            log.error("Could not write JSONL export: %s", exc)
