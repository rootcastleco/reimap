"""Tests for configuration validation and insights computation."""

from __future__ import annotations

from reimap.config import Config
from reimap.insights import InsightsEngine
from reimap.model import Connection, ConnectionKind, GeoLocation
from reimap.state import HistoryStore, LiveStore


def test_config_validate_clamps():
    cfg = Config(scan_interval_seconds=0.1, marker_size=99, theme="does-not-exist")
    cfg.validate()
    assert cfg.scan_interval_seconds >= 0.5
    assert cfg.marker_size <= 30
    assert cfg.theme == "midnight"


def test_config_load_ignores_unknown_keys(tmp_path, monkeypatch):
    import reimap.config as config_mod

    path = tmp_path / "config.json"
    path.write_text('{"theme": "aurora", "totally_unknown": 42}', encoding="utf-8")
    monkeypatch.setattr(config_mod, "config_file", lambda: path)

    cfg = Config.load()
    assert cfg.theme == "aurora"
    assert not hasattr(cfg, "totally_unknown")


def test_insights_counts_and_top_lists(tmp_path, monkeypatch):
    import reimap.state.history as history_mod

    monkeypatch.setattr(history_mod, "data_dir", lambda: tmp_path)

    store = LiveStore()
    history = HistoryStore(retention_days=30)

    berlin = GeoLocation(latitude=52.5, longitude=13.4, city="Berlin", country="Germany")
    remote = ConnectionKind.REMOTE
    conns = [
        Connection(remote_ip="1.1.1.1", process="firefox", kind=remote, location=berlin),
        Connection(remote_ip="2.2.2.2", process="firefox", kind=remote, location=berlin),
        Connection(remote_ip="3.3.3.3", process="curl", kind=remote),
    ]
    store.update(conns, duration=0.0)
    history.record(conns)

    engine = InsightsEngine(store, history, frequent_threshold=1)
    snap = engine.compute()

    assert snap.total_connections == 3
    assert snap.mapped_connections == 2
    assert ("Germany", 2) in snap.top_countries
    assert ("firefox", 2) in snap.top_processes


def test_history_new_and_frequent(tmp_path, monkeypatch):
    import reimap.state.history as history_mod

    monkeypatch.setattr(history_mod, "data_dir", lambda: tmp_path)
    history = HistoryStore(retention_days=30)

    conn = Connection(remote_ip="9.9.9.9", kind=ConnectionKind.REMOTE)
    for _ in range(4):
        history.record([conn])

    assert history.is_new("9.9.9.9") is True  # first_seen within a day
    assert history.is_new("nonexistent") is True
    frequent = history.frequent(threshold=3)
    assert any(e.ip == "9.9.9.9" for e in frequent)
