"""Tests for IP classification and connection modelling."""

from __future__ import annotations

from reimap.model import Connection, ConnectionKind, GeoLocation
from reimap.scanner import classify_ip


def test_classify_loopback():
    assert classify_ip("127.0.0.1") is ConnectionKind.LOCAL
    assert classify_ip("::1") is ConnectionKind.LOCAL


def test_classify_private():
    assert classify_ip("192.168.1.10") is ConnectionKind.LAN
    assert classify_ip("10.0.0.5") is ConnectionKind.LAN
    assert classify_ip("172.16.4.4") is ConnectionKind.LAN


def test_classify_public():
    assert classify_ip("140.82.113.25") is ConnectionKind.REMOTE
    assert classify_ip("8.8.8.8") is ConnectionKind.REMOTE


def test_classify_garbage_is_remote():
    assert classify_ip("not-an-ip") is ConnectionKind.REMOTE


def test_connection_key_is_stable():
    c1 = Connection(remote_ip="1.2.3.4", remote_port=443, local_port=51000, protocol="tcp")
    c2 = Connection(remote_ip="1.2.3.4", remote_port=443, local_port=51000, protocol="tcp")
    assert c1.key == c2.key


def test_connection_is_mapped():
    c = Connection(remote_ip="1.2.3.4")
    assert c.is_mapped is False
    c.location = GeoLocation(latitude=1.0, longitude=2.0, city="Berlin", country="Germany")
    assert c.is_mapped is True
    assert c.location.label == "Berlin, Germany"


def test_geolocation_label_unknown():
    assert GeoLocation(latitude=0.0, longitude=0.0).label == "Unknown location"
