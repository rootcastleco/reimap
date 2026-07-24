"""lsof-based socket scanner (macOS fallback).

Some macOS configurations restrict ``psutil.net_connections`` without root. This
backend parses ``lsof`` output as a fallback. It is intentionally best-effort and
only used when the psutil backend is unavailable.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time

from ..logging_config import get_logger
from ..model import Connection, ConnectionKind
from .base import Scanner, classify_ip

log = get_logger("scanner.lsof")

# Example lsof -i line:
#   Chrome  512 user  40u  IPv4 0x...  0t0  TCP 10.0.0.2:52344->140.82.113.25:443 (ESTABLISHED)
_LINE = re.compile(
    r"^(?P<command>\S+)\s+(?P<pid>\d+)\s+\S+\s+\S+\s+(?P<family>IPv4|IPv6)\s+"
    r"\S+\s+\S+\s+(?P<proto>TCP|UDP)\s+(?P<addrs>\S+)(?:\s+\((?P<state>\w+)\))?"
)
_ENDPOINT = re.compile(r"^(?P<local>.+?)(?:->(?P<remote>.+))?$")


def _split_host_port(text: str) -> tuple[str, int]:
    """Split ``host:port`` (IPv4/IPv6) into a ``(host, port)`` tuple."""
    if "]" in text:  # bracketed IPv6, e.g. [::1]:443
        host, _, port = text.rpartition("]:")
        return host.lstrip("[").rstrip("]"), int(port) if port.isdigit() else 0
    host, _, port = text.rpartition(":")
    return host, int(port) if port.isdigit() else 0


class LsofScanner(Scanner):
    """Enumerate connections by parsing ``lsof -i -n -P`` output."""

    name = "lsof"

    def available(self) -> bool:
        """Whether the ``lsof`` binary is present on ``PATH``."""
        return shutil.which("lsof") is not None

    def scan(self) -> list[Connection]:
        """Return the current connection snapshot by parsing ``lsof`` output."""
        if not self.available():  # pragma: no cover
            return []

        now = time.time()
        try:
            output = subprocess.run(
                ["lsof", "-i", "-n", "-P"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            ).stdout
        except (subprocess.SubprocessError, OSError) as exc:
            log.warning("lsof invocation failed: %s", exc)
            return []

        results: list[Connection] = []
        for line in output.splitlines()[1:]:  # skip header
            m = _LINE.match(line)
            if not m:
                continue
            endpoints = _ENDPOINT.match(m.group("addrs"))
            if not endpoints:
                continue

            local_host, local_port = _split_host_port(endpoints.group("local"))
            remote = endpoints.group("remote")
            protocol = m.group("proto").lower()
            pid = int(m.group("pid"))
            process = m.group("command")

            if remote:
                remote_ip, remote_port = _split_host_port(remote)
                kind = classify_ip(remote_ip)
            else:
                remote_ip, remote_port = local_host, 0
                kind = ConnectionKind.LISTEN

            results.append(
                Connection(
                    remote_ip=remote_ip,
                    remote_port=remote_port,
                    local_port=local_port,
                    protocol=protocol,
                    status=m.group("state") or "",
                    pid=pid,
                    process=process,
                    kind=kind,
                    first_seen=now,
                    last_seen=now,
                )
            )
        return results
