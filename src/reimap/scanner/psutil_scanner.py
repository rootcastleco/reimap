"""psutil-based socket scanner.

Works on Linux and Windows without elevation for the current user's own sockets,
and on macOS with appropriate permissions. Enriches each socket with its owning
process name where possible.
"""

from __future__ import annotations

import time

from ..logging_config import get_logger
from ..model import Connection, ConnectionKind
from .base import Scanner, classify_ip

log = get_logger("scanner.psutil")

try:  # psutil is a hard dependency but we degrade gracefully if it is missing.
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]


# Map psutil socket "kind" to our protocol string.
_PROTO_MAP = {
    getattr(__import__("socket"), "SOCK_STREAM", 1): "tcp",
    getattr(__import__("socket"), "SOCK_DGRAM", 2): "udp",
}


class PsutilScanner(Scanner):
    """Enumerate connections using :mod:`psutil`."""

    name = "psutil"

    def available(self) -> bool:
        """Whether :mod:`psutil` is importable in this environment."""
        return psutil is not None

    def _process_name(self, pid: int | None, cache: dict[int, str]) -> str:
        if pid is None:
            return ""
        if pid in cache:
            return cache[pid]
        try:
            name = psutil.Process(pid).name()
        except (psutil.Error, ValueError):  # type: ignore[union-attr]
            name = ""
        cache[pid] = name
        return name

    def scan(self) -> list[Connection]:
        """Return the current connection snapshot via ``psutil.net_connections``."""
        if psutil is None:  # pragma: no cover
            return []

        now = time.time()
        results: list[Connection] = []
        proc_cache: dict[int, str] = {}

        try:
            raw = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, psutil.Error, PermissionError) as exc:
            log.warning("psutil.net_connections failed: %s", exc)
            return []

        for row in raw:
            try:
                protocol = _PROTO_MAP.get(row.type, "tcp")
                local_port = row.laddr.port if row.laddr else 0

                if row.raddr:  # active connection to a peer
                    remote_ip = row.raddr.ip
                    remote_port = row.raddr.port
                    kind = classify_ip(remote_ip)
                else:  # listening / bound socket
                    remote_ip = row.laddr.ip if row.laddr else "0.0.0.0"
                    remote_port = 0
                    kind = ConnectionKind.LISTEN

                conn = Connection(
                    remote_ip=remote_ip,
                    remote_port=remote_port,
                    local_port=local_port,
                    protocol=protocol,
                    status=row.status or "",
                    pid=row.pid,
                    process=self._process_name(row.pid, proc_cache),
                    kind=kind,
                    first_seen=now,
                    last_seen=now,
                )
                results.append(conn)
            except (AttributeError, ValueError) as exc:  # skip malformed rows
                log.debug("Skipping malformed connection row: %s", exc)
                continue

        return results
