"""Tests for the live store new/closed diffing."""

from __future__ import annotations

from reimap.model import Connection, ConnectionKind
from reimap.state import LiveStore


def _conn(ip: str, port: int = 443) -> Connection:
    return Connection(remote_ip=ip, remote_port=port, local_port=5000, kind=ConnectionKind.REMOTE)


def test_first_update_all_new():
    store = LiveStore()
    new, closed = store.update([_conn("1.1.1.1"), _conn("2.2.2.2")], duration=0.01)
    assert len(new) == 2
    assert closed == []
    assert store.stats()["total"] == 2


def test_second_update_detects_new_and_closed():
    store = LiveStore()
    store.update([_conn("1.1.1.1"), _conn("2.2.2.2")], duration=0.01)
    new, closed = store.update([_conn("2.2.2.2"), _conn("3.3.3.3")], duration=0.01)

    new_ips = {c.remote_ip for c in new}
    closed_ips = {c.remote_ip for c in closed}
    assert new_ips == {"3.3.3.3"}
    assert closed_ips == {"1.1.1.1"}


def test_first_seen_preserved_across_updates():
    store = LiveStore()
    store.update([_conn("1.1.1.1")], duration=0.01)
    first_ts = store.all()[0].first_seen
    store.update([_conn("1.1.1.1")], duration=0.01)
    assert store.all()[0].first_seen == first_ts


def test_stats_counts_kinds():
    store = LiveStore()
    store.update(
        [
            _conn("1.1.1.1"),
            Connection(remote_ip="192.168.0.2", kind=ConnectionKind.LAN),
            Connection(remote_ip="0.0.0.0", local_port=8080, kind=ConnectionKind.LISTEN),
        ],
        duration=0.0,
    )
    stats = store.stats()
    assert stats["remote"] == 1
    assert stats["lan"] == 1
    assert stats["listening"] == 1
