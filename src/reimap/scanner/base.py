"""Scanner interface and IP classification helpers."""

from __future__ import annotations

import abc
import ipaddress

from ..model import Connection, ConnectionKind


def classify_ip(ip: str) -> ConnectionKind:
    """Classify an IP address into a :class:`ConnectionKind`.

    Args:
        ip: A textual IPv4 or IPv6 address.

    Returns:
        ``LOCAL`` for loopback, ``LAN`` for private/link-local ranges, otherwise
        ``REMOTE``. Unparseable addresses are treated as ``REMOTE`` so they still
        surface to the user rather than being silently dropped.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ConnectionKind.REMOTE

    if addr.is_loopback:
        return ConnectionKind.LOCAL
    if addr.is_private or addr.is_link_local or addr.is_reserved or addr.is_unspecified:
        return ConnectionKind.LAN
    return ConnectionKind.REMOTE


class Scanner(abc.ABC):
    """Abstract base class for socket scanners.

    A scanner returns the current set of connections owned by processes on this
    machine. Concrete implementations wrap ``psutil`` (Windows/Linux/mac) or
    ``lsof`` (macOS fallback).
    """

    name: str = "base"

    @abc.abstractmethod
    def scan(self) -> list[Connection]:
        """Return the current snapshot of connections.

        Implementations must never raise for individual bad rows; skip them.
        """

    def available(self) -> bool:  # pragma: no cover - trivial default
        """Whether this scanner can run in the current environment."""
        return True


def get_scanner() -> Scanner:
    """Return the best available scanner for this platform.

    Prefers the ``psutil`` backend everywhere; falls back to the ``lsof`` backend
    on macOS when ``psutil`` cannot enumerate connections without elevated
    privileges.
    """
    from .lsof_scanner import LsofScanner
    from .psutil_scanner import PsutilScanner

    psutil_scanner = PsutilScanner()
    if psutil_scanner.available():
        return psutil_scanner

    lsof_scanner = LsofScanner()
    if lsof_scanner.available():
        return lsof_scanner

    return psutil_scanner
