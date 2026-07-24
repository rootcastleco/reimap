"""Network connection model."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .location import GeoLocation


class ConnectionKind(enum.Enum):
    """Classification of an observed socket endpoint."""

    REMOTE = "remote"
    """A routable connection to a public IP address."""

    LAN = "lan"
    """A connection to a private/LAN address (RFC 1918 and friends)."""

    LOCAL = "local"
    """A loopback connection (127.0.0.0/8, ::1)."""

    LISTEN = "listen"
    """A listening/bound local port with no remote peer."""


@dataclass(slots=True)
class Connection:
    """A single observed socket, optionally enriched with geolocation.

    Attributes:
        remote_ip: The remote peer address (or local bind address for listeners).
        remote_port: The remote peer port.
        local_port: The local port on this machine.
        protocol: ``"tcp"`` or ``"udp"``.
        status: OS-reported socket status (e.g. ``ESTABLISHED``).
        pid: Owning process id, if resolvable.
        process: Owning process name, if resolvable.
        kind: The :class:`ConnectionKind` classification.
        location: Resolved :class:`GeoLocation`, or ``None`` when unmapped.
        first_seen: Unix timestamp the connection was first observed this session.
        last_seen: Unix timestamp the connection was most recently observed.
    """

    remote_ip: str
    remote_port: int = 0
    local_port: int = 0
    protocol: str = "tcp"
    status: str = ""
    pid: int | None = None
    process: str = ""
    kind: ConnectionKind = ConnectionKind.REMOTE
    location: GeoLocation | None = field(default=None)
    first_seen: float = 0.0
    last_seen: float = 0.0

    @property
    def key(self) -> str:
        """A stable identity for deduplication within a scan window."""
        return f"{self.protocol}:{self.remote_ip}:{self.remote_port}:{self.local_port}"

    @property
    def is_mapped(self) -> bool:
        """Whether the connection has a resolved geographic location."""
        return self.location is not None

    def endpoint_label(self) -> str:
        """A concise ``ip:port`` representation of the remote peer."""
        if self.remote_port:
            return f"{self.remote_ip}:{self.remote_port}"
        return self.remote_ip
